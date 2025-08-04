from django.db import models
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from users.models import Users 
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from decimal import Decimal

class Amenity(models.Model):
    ROOM_TYPES = [
        ("kuchnia", "kuchnia"),
        ("salon", "łazienka"),
        ("sypialnia_1", "sypialnia 1"),
        ("sypialnia_2", "sypialnia 2"),
        ("strefa_odpoczynku", "strefa odpoczynku"),
        ("plac_zabaw", "plac zabaw"),
        ("parking", "parking"),
    ]
    amenity = models.CharField(max_length=50, verbose_name="Udogodnienie")
    room_type = models.CharField(max_length=50, blank=True, null=True, choices=ROOM_TYPES, verbose_name="Typ pokoju", help_text="Opcjonalne, jeśli udogodnienie jest specyficzne dla typu pokoju")
    description = models.TextField(blank=True, null=True, verbose_name="Opis udogodnienia", help_text="Opcjonalny opis udogodnienia")

    def __str__(self):
        return self.amenity
        
    class Meta:
        verbose_name = "Udogodnienie"
        verbose_name_plural = "Udogodnienia"

class Status(models.Model):
    Status_CHOICES = [
        ("available", "Dostępne"),
        ("booked", "Zarezerwowane"),
        ("maintenance", "W konserwacji"),
        ("unavailable", "Niedostępne"),
        ("pending", "Oczekujące na potwierdzenie/zadatek"),
        ("cancelled", "Anulowane"),
        ("checked_in", "Zameldowane"),
        ("checked_out", "Wymeldowane"),
    ]


class Aditional_service(models.Model):
    CALCULATION_CHOICES = [
        ('per_stay', 'Opłata jednorazowa'),
        ('per_night', 'Opłata za dobę'),
    ]

    aditional_service = models.CharField(max_length=50, verbose_name="Usługa dodatkowa")
    description = models.TextField(blank=True, null=True, verbose_name="Opis usługi dodatkowej")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cena usługi", default=0.00)
    calculation_method = models.CharField(
        max_length=10,
        choices=CALCULATION_CHOICES,
        default='per_stay',
        verbose_name="Sposób naliczania"
    )

    def __str__(self):
        return f"{self.aditional_service} ({self.price:.2f} PLN / {self.get_calculation_method_display()})"
    
    class Meta:
        verbose_name = "Dodatkowa usługa"
        verbose_name_plural = "Dodatkowe usługi"


class Accommodation(models.Model):
    ACCOMMODATION_TYPES = [
        ("hotel", "Hotel"),
        ("apartment", "Apartament"),
        ("room", "Pokój"),
        ("hostel", "Hostel"),
        ("house", "Dom"),
        ("cottage", "Domek letniskowy"),
        ("guest_house", "Pensjonat"),
        ("motel", "Motel"),
        ("villa", "Willa"),
        ("bed_and_breakfast", "Bed & Breakfast"),
    ]

    ROOM_TYPES = [
        ("single", "Jednoosobowy"),
        ("double", "Dwuosobowy"),
        ("triple", "Trzyosobowy"),
        ("suite", "Apartament"),
    ]

    name = models.CharField(max_length=100, verbose_name="Nazwa zakwaterowania")
    accommodation_type = models.CharField(max_length=50, choices=ACCOMMODATION_TYPES, verbose_name="Typ zakwaterowania")
    room_type = models.CharField(max_length=50, choices=ROOM_TYPES, verbose_name="Typ pokoju", blank=True, null=True)
    description = models.TextField(blank=True, null=True, verbose_name="Opis zakwaterowania")
    number_of_guests = models.PositiveIntegerField(verbose_name="Maksymalna liczba gości", default=1)
    number_of_bedrooms = models.PositiveIntegerField(verbose_name="Liczba sypialni", default=1)
    number_of_beds = models.PositiveIntegerField(verbose_name="Liczba łóżek", default=1)
    number_of_bathrooms = models.PositiveIntegerField(verbose_name="Liczba łazienek", default=1)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cena za noc", default=0.00)
    available = models.BooleanField(default=True, verbose_name="Dostępne")
    amenities = models.ManyToManyField(Amenity, verbose_name="Udogodnienia")
    image = models.ImageField(upload_to="accommodation_images", verbose_name="Zdjęcie zakwaterowania", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")

    def __str__(self):
        return f"{self.name} ({self.address.city})" if hasattr(self, "address") else self.name

    def get_price_for_date(self, query_date: date):
        seasonal = self.seasonal_prices.filter(start_date__lte=query_date, end_date__gte=query_date).first()
        return seasonal.price_per_night if seasonal else self.price_per_night

    def is_available_for_dates(self, start_date, end_date):
        return not self.bookings.filter(start_date__lt=end_date, end_date__gt=start_date).exists()
        
    class Meta:
        verbose_name = "Obiekt"
        verbose_name_plural = "Obiekty i ceny sezonowe"

class Address(models.Model):
    accommodation = models.OneToOneField(Accommodation, on_delete=models.CASCADE, related_name="address", verbose_name="Adres zakwaterowania")
    country = models.CharField(max_length=100, default="Polska", verbose_name="Kraj")
    city = models.CharField(max_length=100, verbose_name="Miasto")
    postal_code = models.CharField(max_length=20, verbose_name="Kod pocztowy")
    street = models.CharField(max_length=100, verbose_name="Ulica")
    building_number = models.CharField(max_length=10, verbose_name="Numer budynku")
    apartment_number = models.CharField(max_length=10, blank=True, null=True, verbose_name="Numer mieszkania")

    def __str__(self):
        parts = [self.street, self.building_number]
        if self.apartment_number:
            parts.append(f"/{self.apartment_number}")
        return f"{' '.join(parts)}, {self.postal_code} {self.city}, {self.country}"
        
    class Meta:
        verbose_name = "Adres obiektu"
        verbose_name_plural = "Adresy obiektów"

class SeasonalPrice(models.Model):
    season_name = models.CharField(max_length=100, verbose_name="Nazwa sezonu", help_text="Nazwa sezonu, np. 'Lato 2025'", blank=True)
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE, related_name="seasonal_prices", verbose_name="Zakwaterowanie")
    start_date = models.DateField(verbose_name="Data początkowa sezonu")
    end_date = models.DateField(verbose_name="Data końcowa sezonu")
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cena za noc w sezonie", default=0.00)
    included_services = models.ManyToManyField(
        Aditional_service,
        blank=True,
        verbose_name="Usługi wliczone w cenę sezonową",
        help_text="Usługi dodatkowe, które są wliczone w cenę zakwaterowania w tym sezonie i nie mogą być odznaczone.")
    description = models.TextField(blank=True, null=True, verbose_name="Opis sezonu")
    photo = models.ImageField(upload_to="seasonal_prices", verbose_name="Zdjęcie sezonu", blank=True, null=True)
    notification = models.BooleanField(default=False, verbose_name="Powiadomienie o ofercie specjalnej/last minute", help_text="Dodaj powiadomienie o ofercie specjalnej lub last minute, jeśli chcesz, aby ta cena sezonowa była promowana w serwisie.")

    class Meta:
        ordering = ["start_date"]
        verbose_name = "Cena sezonowa"
        verbose_name_plural = "Ceny sezonowe"

    def __str__(self):
        return f"{self.accommodation.name}: {self.start_date}–{self.end_date} → {self.price_per_night} PLN"

    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("Data początkowa musi być wcześniejsza niż data końcowa.")
        if self.price_per_night <= 0:
            raise ValidationError("Cena za noc musi być większa niż zero.")

class Booking(models.Model):
    accommodation = models.ForeignKey(
        'Accommodation',
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Zakwaterowanie",
    )
    user = models.ForeignKey(Users, on_delete=models.CASCADE, verbose_name="Użytkownik dokonujący rezerwacji")
    start_date = models.DateField(verbose_name="Data przyjazdu")
    end_date = models.DateField(verbose_name="Data wyjazdu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia rezerwacji")
    modified_at = models.DateTimeField(auto_now=True, verbose_name="Data modyfikacji rezerwacji")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cena całkowita")
    accommodation_subtotal_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cena zakwaterowania")
    additional_services_subtotal_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Cena usług dodatkowych")
    extra_guest_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=Decimal('0.00'), verbose_name="Opłata za dodatkowych gości")
    additional_services = models.ManyToManyField(
        'Aditional_service',
        blank=True,
        related_name="bookings",
        verbose_name="Usługi dodatkowe"
    )
    number_of_adults = models.PositiveIntegerField(default=1, verbose_name="Liczba Dorosłych")
    number_of_children = models.PositiveIntegerField(default=0, verbose_name="Liczba dzieci")
    status= models.CharField(choices=Status.Status_CHOICES,verbose_name="Status rezerwacji", max_length=50, default="booked")

    class Meta:
        ordering = ["start_date"]
        verbose_name = "Rezerwacja"
        verbose_name_plural = "Rezerwacje"

    def __str__(self):
        return f"Rezerwacja dla {self.accommodation.name} , zarezerwowane przez {self.user.username} od {self.start_date} do {self.end_date}"

    @property
    def num_nights(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0
    
    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("Data początkowa musi być wcześniejsza niż data końcowa.")

        overlapping = Booking.objects.filter(
            accommodation=self.accommodation,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date,
        )
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)

        if overlapping.exists():
            raise ValidationError("W tym terminie istnieje już rezerwacja dla tego obiektu.")

    def save(self, *args, **kwargs):
        self.clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)

        self.calculate_total_price()
        super().save(update_fields=["total_price", "accommodation_subtotal_price", "additional_services_subtotal_price", "extra_guest_fee"])

    def calculate_total_price(self):
        accommodation_price = Decimal('0.00')
        services_price = Decimal('0.00')
        extra_guest_cost = Decimal('0.00')

        num_nights = (self.end_date - self.start_date).days
        if num_nights <= 0:
            self.accommodation_subtotal_price = Decimal('0.00')
            self.additional_services_subtotal_price = Decimal('0.00')
            self.extra_guest_fee = Decimal('0.00')
            self.total_price = Decimal('0.00')
            return

        # Ulepszona logika obliczania ceny zakwaterowania
        # Pobieramy wszystkie sezony cenowe, które pokrywają się z okresem rezerwacji
        overlapping_seasons = self.accommodation.seasonal_prices.filter(
            start_date__lt=self.end_date,
            end_date__gte=self.start_date
        ).order_by('start_date')

        price_map = {}
        # Wypełniamy mapę ceną domyślną dla każdego dnia rezerwacji
        current_date = self.start_date
        while current_date < self.end_date:
            price_map[current_date] = self.accommodation.price_per_night
            current_date += timedelta(days=1)

        # Nadpisujemy ceny dniami z cenami sezonowymi
        for season in overlapping_seasons:
            iter_date = max(self.start_date, season.start_date)
            while iter_date <= min(self.end_date - timedelta(days=1), season.end_date):
                price_map[iter_date] = season.price_per_night
                iter_date += timedelta(days=1)
        
        accommodation_price = sum(price_map.values())
        
        # Logika obliczania cen za usługi dodatkowe
        seasonal_prices_in_range = SeasonalPrice.objects.filter(
            accommodation=self.accommodation,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date
        ).distinct()

        included_services_in_season = set()
        if seasonal_prices_in_range.exists():
            for sp in seasonal_prices_in_range:
                for service in sp.included_services.all():
                    included_services_in_season.add(service.pk)

        for service in self.additional_services.all():
            if service.pk not in included_services_in_season:
                if service.calculation_method == 'per_night':
                    services_price += service.price * num_nights
                else:
                    services_price += service.price

        total_guests = self.number_of_adults + self.number_of_children
        if total_guests > 6:
            extra_guests = total_guests - 6
            extra_guest_cost = Decimal(str(extra_guests * 50)) * num_nights

        self.accommodation_subtotal_price = accommodation_price
        self.additional_services_subtotal_price = services_price
        self.extra_guest_fee = extra_guest_cost
        self.total_price = accommodation_price + services_price + extra_guest_cost
    

    def get_detailed_services(self):
        details = []
        num_nights = (self.end_date - self.start_date).days
        if num_nights <= 0:
            return []

        seasonal_prices = self.accommodation.seasonal_prices.filter(
            start_date__lte=self.end_date, end_date__gte=self.start_date
        )
        included_services_pks = set()
        for season in seasonal_prices:
            included_services_pks.update(season.included_services.values_list('pk', flat=True))

        for service in self.additional_services.all():
            is_included = service.pk in included_services_pks
            total_price = Decimal('0.00')
            note = ""

            if is_included:
                note = "(w cenie sezonu)"
            else:
                if service.calculation_method == 'per_night':
                    total_price = service.price * num_nights
                    note = f"({service.price:.2f} PLN x {num_nights} nocy)"
                else:
                    total_price = service.price
                    note = "(opłata jednorazowa)"
            
            details.append({
                'name': service.aditional_service,
                'total_price': total_price,
                'note': note,
                'is_included': is_included,
            })
        return details

    @property
    def number_of_guests(self):
        return self.number_of_adults + self.number_of_children
    number_of_guests.fget.short_description = "Liczba gości"

@receiver(m2m_changed, sender=Booking.additional_services.through)
def update_booking_total_price(sender, instance, action, **kwargs):
    if instance.pk and action in ["post_add", "post_remove", "post_clear"]:
        instance.calculate_total_price()
        instance.save(update_fields=["total_price", "accommodation_subtotal_price", "additional_services_subtotal_price", "extra_guest_fee"])


class Notification(models.Model):
    seasonal_price = models.OneToOneField(
        SeasonalPrice, 
        on_delete=models.CASCADE, 
        verbose_name="Cena sezonowa źródłowa",
        related_name='notification_details'
    )
    title = models.CharField(max_length=200, verbose_name="Tytuł powiadomienia")
    message = models.TextField(verbose_name="Treść powiadomienia")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    is_active = models.BooleanField(default=True, verbose_name="Aktywne")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Powiadomienie o ofercie specjalnej"
        verbose_name_plural = "Powiadomienia o ofertach specjalnych"
        ordering = ['-created_at']