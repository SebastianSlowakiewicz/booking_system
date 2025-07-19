from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from datetime import date, timedelta
import json
from decimal import Decimal # Import Decimal for precise calculations

from .forms import BookingForm
from .models import Accommodation, Booking, Aditional_service, SeasonalPrice

@login_required
def create_booking(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user

            try:
                booking.save()
                form.save_m2m()

                messages.success(request, 'Twoja rezerwacja została pomyślnie utworzona!')
                return redirect('accommodation_facilities:booking_success', booking_id=booking.pk)
            except Exception as e:
                messages.error(request, f'Wystąpił błąd podczas tworzenia rezerwacji: {e}')
        else:
            messages.error(request, 'Proszę poprawić błędy w formularzu.')
    else:
        initial_data = {}
        try:
            janicka_chata = Accommodation.objects.get(name='Janicka Chata')
            initial_data['accommodation'] = janicka_chata
        except Accommodation.DoesNotExist:
            messages.warning(request, "Zakwaterowanie 'Janicka Chata' nie zostało znalezione w bazie danych. Proszę je dodać.")

        form = BookingForm(initial=initial_data)

    context = {
        'form': form,
        'page_title': 'Zarezerwuj swój pobyt',
    }
    return render(request, 'accommodation_facilities/create_booking.html.jinja', context)

@login_required
def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    context = {
        'page_title': 'Rezerwacja potwierdzona!',
        'booking': booking,
    }
    return render(request, 'accommodation_facilities/booking_success.html.jinja', context)

@require_POST
# @csrf_exempt # TYLKO DO CELÓW ROZWOJOWYCH! W PRODUKCJI UŻYJ django.middleware.csrf.CsrfViewMiddleware i dodaj {% csrf_token %} do formularza AJAX
def calculate_booking_price_ajax(request):
    """
    Oblicza cenę rezerwacji na podstawie danych przesłanych przez AJAX.
    """
    try:
        data = json.loads(request.body)
        accommodation_id = data.get('accommodation_id')
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        selected_services_ids = data.get('additional_services', [])
        number_of_adults = data.get('number_of_adults')
        number_of_children = data.get('number_of_children')

        if not all([accommodation_id, start_date_str, end_date_str, number_of_adults is not None, number_of_children is not None]):
            return JsonResponse({'error': 'Brak wymaganych danych.'}, status=400)

        try:
            accommodation = Accommodation.objects.get(pk=accommodation_id)
        except Accommodation.DoesNotExist:
            return JsonResponse({'error': 'Nieprawidłowe zakwaterowanie.'}, status=400)

        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
        except ValueError:
            return JsonResponse({'error': 'Nieprawidłowy format daty.'}, status=400)

        if start_date >= end_date:
            return JsonResponse({'error': 'Data wyjazdu musi być późniejsza niż data przyjazdu.'}, status=400)
        if start_date < date.today():
            return JsonResponse({'error': 'Data przyjazdu nie może być w przeszłości.'}, status=400)

        total_guests = number_of_adults + number_of_children
        if total_guests > accommodation.number_of_guests:
            return JsonResponse({'error': f'Liczba gości ({total_guests}) przekracza maksymalną pojemność zakwaterowania ({accommodation.number_of_guests}).'}, status=400)

        accommodation_price = Decimal('0.00')
        services_price = Decimal('0.00')
        extra_guest_fee = Decimal('0.00')
        detailed_services_prices = []
        is_seasonal_services_locked = False
        locked_services_ids = []

        num_nights = (end_date - start_date).days
        if num_nights <= 0: # Handle cases where dates are invalid or same
            return JsonResponse({
                'total_price': float(Decimal('0.00')),
                'accommodation_subtotal_price': float(Decimal('0.00')),
                'additional_services_subtotal_price': float(Decimal('0.00')),
                'extra_guest_fee': float(Decimal('0.00')),
                'detailed_services_prices': [],
                'is_seasonal_services_locked': False,
                'locked_services_ids': []
            })

        # Sprawdź, czy dla wybranych dat obowiązuje cena sezonowa i jakie usługi są wliczone
        seasonal_prices_in_range = SeasonalPrice.objects.filter(
            accommodation=accommodation,
            start_date__lte=end_date,
            end_date__gte=start_date
        ).distinct()

        included_services_in_season = set()
        if seasonal_prices_in_range.exists():
            is_seasonal_services_locked = True
            for sp in seasonal_prices_in_range:
                for service in sp.included_services.all():
                    if service.pk not in locked_services_ids: # Ensure unique IDs
                        locked_services_ids.append(service.pk)
                    included_services_in_season.add(service.pk) # For pricing logic

        # Obliczanie ceny zakwaterowania
        current_date = start_date
        while current_date < end_date:
            accommodation_price += accommodation.get_price_for_date(current_date)
            current_date += timedelta(days=1)

        # Obliczanie ceny usług dodatkowych:
        # Przetwarzaj tylko te usługi, które użytkownik zaznaczył (selected_services_ids)
        # ORAZ które NIE są wliczone w cenę sezonową (included_services_in_season).
        # To jest kluczowa zmiana, aby dopasować zachowanie do models.py.
        if selected_services_ids:
            additional_services_queryset = Aditional_service.objects.filter(pk__in=selected_services_ids)
            for service in additional_services_queryset:
                if service.pk not in included_services_in_season: # TYLKO jeśli nie jest wliczona w sezonową
                    service_total_price = service.price
                    services_price += service_total_price
                    detailed_services_prices.append({
                        'name': service.aditional_service,
                        'price_per_night': float(service.price),
                        'total_for_service': float(service_total_price)
                    })

        # Obliczanie opłaty za dodatkowych gości
        if total_guests > 6:
            extra_guests = total_guests - 6
            extra_guest_fee = Decimal(str(extra_guests * 50)) * num_nights

        total_price = accommodation_price + services_price + extra_guest_fee

        return JsonResponse({
            'total_price': float(total_price),
            'accommodation_subtotal_price': float(accommodation_price),
            'additional_services_subtotal_price': float(services_price), # Teraz będzie poprawnie obliczone
            'extra_guest_fee': float(extra_guest_fee),
            'detailed_services_prices': detailed_services_prices,
            'is_seasonal_services_locked': is_seasonal_services_locked,
            'locked_services_ids': locked_services_ids
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Nieprawidłowy format JSON.'}, status=400)
    except Exception as e:
        print(f"Błąd w calculate_booking_price_ajax: {e}")
        return JsonResponse({'error': f'Wystąpił błąd serwera: {str(e)}'}, status=500)

