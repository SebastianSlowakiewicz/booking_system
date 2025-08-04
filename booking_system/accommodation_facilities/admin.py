from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import format_html
from .models import (
    Amenity,
    Aditional_service,
    Accommodation,
    Address,
    SeasonalPrice,
    Booking,
    Notification
)

# --- BLOK ROZWIĄZUJĄCY PROBLEM Z WYSZUKIWANIEM UŻYTKOWNIKÓW ---

# Pobieramy aktualny model użytkownika (standardowy lub customowy)
User = get_user_model()

# Tworzymy nową klasę Admina dla użytkownika, dziedzicząc po domyślnej,
# aby nie stracić istniejącej funkcjonalności (zarządzanie hasłami, uprawnieniami etc.)
class CustomUserAdmin(UserAdmin):
    # Dodajemy kluczowe pole 'search_fields', którego wymaga 'autocomplete_fields'
    search_fields = ('username', 'first_name', 'last_name', 'email')

# Jeśli model User jest już zarejestrowany, wyrejestrowujemy go
if admin.site.is_registered(User):
    admin.site.unregister(User)

# Rejestrujemy nasz własny, rozszerzony panel admina dla modelu User
admin.site.register(User, CustomUserAdmin)

# --- KONIEC BLOKU ---


# Uwaga: Model 'Status' z pliku models.py jest pusty i zawiera tylko listę 'Status_CHOICES'.
# Ta lista jest używana bezpośrednio w modelu 'Booking' i nie ma potrzeby rejestrowania
# pustego modelu 'Status' w panelu admina.


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    """
    Panel administracyjny dla modelu Udogodnień.
    """
    list_display = ('amenity', 'room_type', 'description')
    list_filter = ('room_type',)
    search_fields = ('amenity', 'description')


@admin.register(Aditional_service)
class AditionalServiceAdmin(admin.ModelAdmin):
    """
    Panel administracyjny dla modelu Usług Dodatkowych.
    """
    list_display = ('aditional_service', 'price', 'calculation_method')
    list_filter = ('calculation_method',)
    search_fields = ('aditional_service',)


class AddressInline(admin.StackedInline):
    """
    Umożliwia edycję adresu bezpośrednio na stronie obiektu (Accommodation).
    Używamy StackedInline dla lepszej czytelności, bo to relacja jeden-do-jednego.
    """
    model = Address
    can_delete = False
    verbose_name_plural = 'Adres obiektu'


class SeasonalPriceInline(admin.TabularInline):
    """
    Umożliwia szybkie dodawanie i przeglądanie cen sezonowych na stronie obiektu.
    """
    model = SeasonalPrice
    extra = 1  # Domyślnie pokazuje jedno dodatkowe pole do wypełnienia
    ordering = ('start_date',)


@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    """
    Rozbudowany panel administracyjny dla Obiektów Noclegowych.
    """
    list_display = ('name', 'accommodation_type', 'price_per_night', 'number_of_guests', 'available')
    list_filter = ('available', 'accommodation_type', 'room_type')
    search_fields = ('name', 'description', 'address__city', 'address__street')
    inlines = [AddressInline, SeasonalPriceInline]


@admin.register(SeasonalPrice)
class SeasonalPriceAdmin(admin.ModelAdmin):
    """
    Osobny panel dla Cen Sezonowych, dla bardziej szczegółowego zarządzania.
    """
    list_display = ('season_name', 'accommodation', 'start_date', 'end_date', 'price_per_night', 'notification')
    list_filter = ('accommodation', 'notification')
    search_fields = ('season_name', 'accommodation__name')
    autocomplete_fields = ['accommodation'] # Ułatwia wybór obiektu, jeśli jest ich dużo
    date_hierarchy = 'start_date'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """
    Zaawansowany panel do zarządzania rezerwacjami.
    """
    list_display = ('id', 'accommodation', 'user', 'start_date', 'end_date', 'total_price', 'status')
    list_filter = ('status', 'start_date', 'accommodation')
    search_fields = ('user__username', 'user__email', 'accommodation__name')
    date_hierarchy = 'start_date'
    autocomplete_fields = ['accommodation', 'user']
    filter_horizontal = ('additional_services',) # Lepszy interfejs dla pól ManyToMany

    # Dzielimy formularz na czytelne sekcje
    fieldsets = (
        ('Dane Główne Rezerwacji', {
            'fields': ('accommodation', 'user', 'status', ('start_date', 'end_date'))
        }),
        ('Szczegóły Gości', {
            'fields': (('number_of_adults', 'number_of_children'),)
        }),
        ('Usługi i Koszty', {
            'classes': ('collapse',), # Domyślnie zwinięta sekcja
            'fields': ('additional_services', 'accommodation_subtotal_price', 'additional_services_subtotal_price', 'extra_guest_fee', 'total_price')
        }),
        ('Daty systemowe', {
            'fields': ('created_at', 'modified_at'),
        }),
    )

    # Pola obliczane automatycznie powinny być tylko do odczytu
    readonly_fields = ('total_price', 'accommodation_subtotal_price', 'additional_services_subtotal_price',
                       'extra_guest_fee', 'created_at', 'modified_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Panel do podglądu powiadomień o ofertach specjalnych.
    Powiadomienia są tworzone automatycznie, więc większość pól jest tylko do odczytu.
    """
    list_display = ('title', 'seasonal_price_link', 'created_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'message')
    readonly_fields = ('seasonal_price', 'title', 'message', 'created_at')

    def seasonal_price_link(self, obj):
        if obj.seasonal_price:
            # Upewnij się, że 'accommodation_facilities' to poprawna nazwa Twojej aplikacji
            link = reverse("admin:accommodation_facilities_seasonalprice_change", args=[obj.seasonal_price.id])
            return format_html('<a href="{}">{}</a>', link, obj.seasonal_price)
        return "Brak"
    seasonal_price_link.short_description = "Cena Sezonowa"