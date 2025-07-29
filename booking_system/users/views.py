from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from .forms import RegisterUserForm
from accommodation_facilities.models import Booking, SeasonalPrice, Accommodation

def register(request):
    if request.method == 'POST':
        form_user_register = RegisterUserForm(request.POST)
        if form_user_register.is_valid():
            form_user_register.save()
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
    return redirect("login")

@login_required(login_url='login')
def dashboard(request):
    """Widok dla panelu zwykłego użytkownika."""
    # [cite_start]Oryginalna zawartość z pliku views.py [cite: 1]
    return render(request, "users/dashboard.html.jinja", {"user": request.user})

def is_admin(user):
    """Sprawdza, czy użytkownik ma status personelu (admina)."""
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin, login_url='login')
def admin_dashboard(request):
    """
    Panel administracyjny wyświetlający kluczowe informacje o rezerwacjach i sezonach.
    """
    today = timezone.now().date()
    
    # Znajdź wszystkie aktywne sezony dla dzisiejszej daty
    active_seasons = SeasonalPrice.objects.filter(
        start_date__lte=today,
        end_date__gte=today
    ).select_related('accommodation')

    # Pobierz nadchodzące i aktywne rezerwacje
    upcoming_bookings = Booking.objects.filter(
        end_date__gte=today
    ).select_related('user', 'accommodation').order_by('start_date')

    # Statystyki globalne
    stats = {
        'total_bookings': Booking.objects.count(),
        'active_bookings_count': upcoming_bookings.count(),
        'total_users': request.user.__class__.objects.filter(is_staff=False).count()
    }

    context = {
        'active_seasons': active_seasons,
        'upcoming_bookings': upcoming_bookings,
        'stats': stats,
        'page_title': 'Panel Administratora',
        'today': today
    }
    return render(request, "users/admin_dashboard.html.jinja", context)