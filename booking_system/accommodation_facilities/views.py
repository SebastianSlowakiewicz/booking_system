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

        current_date = start_date
        while current_date < end_date:
            accommodation_price += accommodation.get_price_for_date(current_date)
            current_date += timedelta(days=1)

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
    
def offer_page_view(request):
    """
    View to display the accommodation offers and pricing information.
    """
    try:
        main_accommodation_obj = Accommodation.objects.first()
        seasonal_price_data = []
        low_season_combined = {
            'season_name': 'Sezon niski',
            'dates': [],
            'price_per_night': None,
            'description': '',
            'included_services': [],
            'photo': None, # Dodajemy pole na zdjęcie
        }
        low_season_price_set = False

        if main_accommodation_obj:
            seasonal_prices = main_accommodation_obj.seasonal_prices.all().order_by('start_date')

            for sp in seasonal_prices:
                included_service_names = [service.aditional_service for service in sp.included_services.all()]

                if "Sezon niski" in sp.season_name:
                    low_season_combined['dates'].append({
                        'start_date': sp.start_date,
                        'end_date': sp.end_date
                    })
                    if not low_season_price_set:
                        low_season_combined['price_per_night'] = sp.price_per_night
                        low_season_combined['description'] = sp.description
                        low_season_combined['included_services'] = included_service_names
                        # ZMIANA: Przypisujemy zdjęcie do połączonego sezonu
                        low_season_combined['photo'] = sp.photo.url if sp.photo else None
                        low_season_price_set = True
                else:
                    seasonal_price_data.append({
                        'season_name': sp.season_name,
                        'start_date': sp.start_date,
                        'end_date': sp.end_date,
                        'price_per_night': sp.price_per_night,
                        'description': sp.description,
                        'included_services': included_service_names,
                        'photo': sp.photo.url if sp.photo else None,
                    })

            if low_season_combined['dates']:
                seasonal_price_data.insert(0, low_season_combined)

            main_accommodation_context = {
                'seasonal_prices': seasonal_price_data,
            }
        else:
            main_accommodation_context = None

    except Accommodation.DoesNotExist:
        main_accommodation_context = None
    
    context = {
        'main_accommodation': main_accommodation_context,
    }
    return render(request, 'accommodation_facilities/offer.html.jinja', context)

def gallery_view(request):
    return render(request, 'accommodation_facilities/gallery.html.jinja',)
def contact_view(request):
    return render(request, 'accommodation_facilities/contact.html.jinja',)

@login_required
def booking_detail(request, booking_id):
    """
    Widok wyświetlający szczegóły rezerwacji dla jej właściciela lub admina.
    """
    booking = get_object_or_404(
        Booking.objects.select_related('user', 'accommodation'),
        pk=booking_id
    )

    # KLUCZOWE ZABEZPIECZENIE: Sprawdź, czy użytkownik jest właścicielem rezerwacji LUB adminem
    if booking.user != request.user and not request.user.is_staff:
        # Jeśli nie, rzuć błąd 404 (ukrywamy fakt, że rezerwacja istnieje)
        return render(request, '404.html.jinja', status=404)

    context = {
        'booking': booking
    }
    
    return render(request, "accommodation_facilities/booking_detail.html.jinja", context)