from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from .forms import RegisterUserForm
from accommodation_facilities.models import Booking, SeasonalPrice, Accommodation, Users
from django.db.models import Sum, F, ExpressionWrapper, fields
from decimal import Decimal

def register(request):
    if request.method == 'POST':
        form_user_register = RegisterUserForm(request.POST)
        if form_user_register.is_valid():
            form_user_register.save()
            messages.success(request, 'Konto zostało pomyślnie utworzone! Możesz się teraz zalogować.')
            return redirect('login')
    else:
        form_user_register = RegisterUserForm()

    context = {'form_user_register': form_user_register}
    return render(request, 'users/register.html.jinja', context)

def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect("admin_dashboard")
            else:
                return redirect("dashboard")
        else:
            messages.error(request, "Nieprawidłowa nazwa użytkownika lub hasło.")
    
    return render(request, "users/login.html.jinja")

def user_logout(request):
    logout(request)
    messages.info(request, "Zostałeś pomyślnie wylogowany.")
    return redirect("login")

@login_required(login_url='login')
def dashboard(request):
    """Widok dla panelu zwykłego użytkownika."""
    user_bookings = Booking.objects.filter(user=request.user).order_by('-start_date')
    today = timezone.now().date()
    
    upcoming_bookings = user_bookings.filter(end_date__gte=today)
    past_bookings = user_bookings.filter(end_date__lt=today)
    
    # Obliczanie statystyk dla użytkownika
    total_bookings = user_bookings.count()
    nights_stayed_expression = ExpressionWrapper(F('end_date') - F('start_date'), output_field=fields.DurationField())
    total_nights_stayed_result = user_bookings.aggregate(total_duration=Sum(nights_stayed_expression))
    total_nights_stayed = total_nights_stayed_result['total_duration'].days if total_nights_stayed_result['total_duration'] else 0
    total_spent_result = user_bookings.aggregate(total=Sum('total_price'))
    total_spent = total_spent_result['total'] or Decimal('0.00')

    user_stats = {
        'total_bookings': total_bookings,
        'total_nights_stayed': total_nights_stayed,
        'total_spent': total_spent,
    }
    
    context = {
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'user_stats': user_stats,
    }
    
    return render(request, "users/dashboard.html.jinja", context)

def is_admin(user):
    """Sprawdza, czy użytkownik ma status personelu (admina)."""
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin, login_url='login')
def admin_dashboard(request):
    """Panel administracyjny z zakładkami dla rezerwacji i globalnymi statystykami."""
    today = timezone.now().date()
    
    # --- Statystyki ogólne ---
    total_bookings_count = Booking.objects.count()
    active_and_upcoming_count = Booking.objects.filter(end_date__gte=today).count()
    total_users_count = Users.objects.count()
    
    stats = {
        'total_bookings': total_bookings_count,
        'active_bookings_count': active_and_upcoming_count,
        'total_users': total_users_count,
    }

    # --- Rezerwacje (dla zakładek) ---
    all_bookings = Booking.objects.select_related('user').order_by('start_date')
    active_bookings = all_bookings.filter(start_date__lte=today, end_date__gte=today)
    upcoming_bookings = all_bookings.filter(start_date__gt=today)
    past_bookings = all_bookings.filter(end_date__lt=today).order_by('-start_date')

    # --- Aktywne sezony ---
    active_seasons = SeasonalPrice.objects.filter(
        start_date__lte=today,
        end_date__gte=today
    ).select_related('accommodation').prefetch_related('included_services')

    context = {
        'stats': stats,
        'active_bookings': active_bookings,
        'upcoming_bookings': upcoming_bookings,
        'past_bookings': past_bookings,
        'all_bookings': all_bookings,
        'active_seasons': active_seasons,
        'today': today,
    }
    
    return render(request, "users/admin_dashboard.html.jinja", context)