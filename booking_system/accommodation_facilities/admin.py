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

class BookingInline(admin.TabularInline):
    model = Booking
    extra = 0
    readonly_fields = ("user", "start_date", "end_date", "created_at", "total_price")
    fields = ("user", "start_date", "end_date", "created_at", "total_price")
    can_delete = False
    show_change_link = True


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
    list_display = ("amenity",)
    search_fields = ("amenity",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("accommodation", "user", "start_date", "end_date", "created_at", "total_price")
    list_filter = ("start_date", "end_date", "accommodation")
    search_fields = ("accommodation__name", "user__username", "user__email")

@admin.register(Aditional_service)
class AditionalServiceAdmin(admin.ModelAdmin):
    list_display = ("aditional_service", "price")
    search_fields = ("aditional_service",)
    list_filter = ("price",)
