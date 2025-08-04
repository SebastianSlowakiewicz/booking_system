from django.shortcuts import render
from datetime import datetime
from django.contrib.auth.decorators import login_required
from accommodation_facilities.models import Notification

def index(request):
    """
    Wersja diagnostyczna widoku strony głównej.
    """
    print("\n--- TEST: Rozpoczynam widok 'index' ---")
    
    try:
        oferty = Notification.objects.filter(is_active=True)
        liczba_ofert = oferty.count()
        print(f"--- TEST: Znalazłem {liczba_ofert} AKTYWNYCH ofert w bazie danych. ---")
        
        special_offers = oferty.select_related('seasonal_price__accommodation__address')
        
    except Exception as e:
        print(f"--- BŁĄD KRYTYCZNY W WIDOKU: {e} ---")
        special_offers = [] # W razie błędu przekaż pustą listę

    print(f"--- TEST: Przekazuję {len(special_offers)} ofert do szablonu. ---\n")

    context = {
        "current_year": datetime.now().year,
        "special_offers": special_offers,
    }
    return render(request, "index.html.jinja", context)

@login_required
def dashboard(request):
    return render(request, 'dashboard.html.jinja')