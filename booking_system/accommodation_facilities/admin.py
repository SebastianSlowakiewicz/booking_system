from django.contrib import admin
from datetime import date
from django.conf import settings
from .models import Accommodation, Address, Amenity, SeasonalPrice, Booking, Aditional_service

class AddressInline(admin.StackedInline):
    model = Address
    extra = 0
    max_num = 1
    can_delete = False

class SeasonalPriceInline(admin.TabularInline):
    model = SeasonalPrice
    extra = 1
    fields = ("start_date", "end_date", "price_per_night")
    # NOWOŚĆ: Dodaj included_services do SeasonalPriceInline
    # Użyj filter_horizontal dla ManyToManyField w inlines
    filter_horizontal = ("included_services",)


class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    # NOWOŚĆ: Dodaj nowe pola do readonly_fields i fields
    readonly_fields = (
        "user", "start_date", "end_date", "created_at",
        "total_price", "accommodation_subtotal_price", "additional_services_subtotal_price", "extra_guest_fee", # Nowe pola
        "number_of_adults", "number_of_children", "number_of_guests", "status" # Status dodany, bo jest w list_display BookingAdmin
    )
    fields = (
        "start_date", "end_date",
        "total_price", "accommodation_subtotal_price", "additional_services_subtotal_price", "extra_guest_fee", # Nowe pola
        "user", "created_at", "number_of_adults", "number_of_children", "number_of_guests", "status"
    )
    show_change_link = True
    verbose_name = "Rezerwacja"
    can_delete = False


@admin.register(Accommodation)
class AccommodationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "get_accommodation_type_display",
        "get_room_type_display",
        "number_of_guests",
        "current_price_per_night",
        "available",
    )
    list_filter = ("accommodation_type", "room_type", "available")
    search_fields = ("name", "address__city", "address__street")
    inlines = [AddressInline, SeasonalPriceInline]
    filter_horizontal = ("amenities",)

    def current_price_per_night(self, obj):
        today = date.today()
        return obj.get_price_for_date(today)
    current_price_per_night.short_description = "Cena za noc (aktualna)"


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("amenity", "room_type") # Dodano room_type dla lepszej widoczności
    search_fields = ("amenity", "room_type")
    list_filter = ("room_type",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    # NOWOŚĆ: Dodaj nowe pola do list_display
    list_display = (
        "accommodation", "start_date", "end_date",
        "total_price", "accommodation_subtotal_price", "additional_services_subtotal_price", "extra_guest_fee", # Nowe pola
        "number_of_guests", "user", "created_at", "status"
    )
    list_filter = ("start_date", "end_date", "accommodation", "status") # Dodano status do filtrów
    search_fields = ("accommodation__name", "user__username", "user__email")
    # NOWOŚĆ: Dodaj nowe pola do fields/readonly_fields dla widoku edycji Booking
    fieldsets = (
        (None, {
            'fields': (
                'accommodation', 'user', 'start_date', 'end_date',
                'number_of_adults', 'number_of_children', 'status'
            )
        }),
        ('Szczegóły cenowe', {
            'fields': (
                'accommodation_subtotal_price', 'additional_services_subtotal_price',
                'extra_guest_fee', 'total_price'
            ),
            'classes': ('collapse',), # Opcjonalnie: zwijanie sekcji
        }),
        ('Usługi dodatkowe', {
            'fields': ('additional_services',),
            'classes': ('collapse',),
        }),
        ('Daty', {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = (
        "total_price", "accommodation_subtotal_price", "additional_services_subtotal_price",
        "extra_guest_fee", "created_at", "modified_at"
    )
    filter_horizontal = ("additional_services",) # Użyj filter_horizontal dla ManyToManyField


@admin.register(Aditional_service)
class AditionalServiceAdmin(admin.ModelAdmin):
    list_display = ("aditional_service", "price")
    search_fields = ("aditional_service",)
    list_filter = ("price",)

# Rejestracja SeasonalPrice jako osobnego modelu w adminie (opcjonalne, jeśli nie jest inlinem)
# Jeśli chcesz zarządzać cenami sezonowymi bezpośrednio, a nie tylko przez Accommodation Inline:
@admin.register(SeasonalPrice)
class SeasonalPriceAdmin(admin.ModelAdmin):
    list_display = ("accommodation", "start_date", "end_date", "price_per_night")
    list_filter = ("accommodation", "start_date")
    search_fields = ("accommodation__name",)
    filter_horizontal = ("included_services",) # Dodano included_servic