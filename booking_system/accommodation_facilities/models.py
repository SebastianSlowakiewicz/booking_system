from django.db import models
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from users.models import Users # Upewnij się, że ten import jest poprawny dla Twojego modelu użytkownika
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from decimal import Decimal # Import Decimal dla precyzyjnych obliczeń pieniężnych

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
    # Jeśli to jest tylko zbiór wyborów, a nie model do przechowywania instancji statusów,
    # to możesz usunąć ten model i używać Status_CHOICES bezpośrednio w Booking.status.
    # Jeśli ma to być model, potrzebuje pola do przechowywania statusu.
    # Przykład:
    # name = models.CharField(max_length=50, choices=Status_CHOICES, unique=True, verbose_name="Nazwa Statusu")
    # def __str__(self):
    #     return self.get_name_display()
    # class Meta:
    #     verbose_name = "Status"
    #     verbose_name_plural = "Statusy"
    pass # Pozostawiam pass, jeśli jest to tylko definicja choices

class Aditional_service(models.Model):
    aditional_service = models.CharField(max_length=50, verbose_name="Usługa dodatkowa")
    description = models.TextField(blank=True, null=True, verbose_name="Opis usługi dodatkowej")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cena usługi dodatkowej", default=0.00)

    def __str__(self):
        return self.aditional_service
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
        """Pobiera cenę za noc dla danej daty, uwzględniając ceny sezonowe."""
        seasonal = self.seasonal_prices.filter(start_date__lte=query_date, end_date__gte=query_date).first()
        return seasonal.price_per_night if seasonal else self.price_per_night

    def is_available_for_dates(self, start_date, end_date):
        """Sprawdza, czy zakwaterowanie jest dostępne w danym zakresie dat."""
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
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE, related_name="seasonal_prices", verbose_name="Zakwaterowanie")
    start_date = models.DateField(verbose_name="Data początkowa sezonu")
    end_date = models.DateField(verbose_name="Data końcowa sezonu")
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cena za noc w sezonie", default=0.00)
    # NOWE POLE: Usługi dodatkowe wliczone w cenę sezonową
    included_services = models.ManyToManyField(
        Aditional_service,
        blank=True,
        verbose_name="Usługi wliczone w cenę sezonową",
        help_text="Usługi dodatkowe, które są wliczone w cenę zakwaterowania w tym sezonie i nie mogą być odznaczone."
    )

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
        # default="Janicka Chata", # Usuń lub zmień to w produkcji, gdy będziesz mieć prawdziwe dane
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
        # Zapisz instancję, aby mieć pewność, że ma PK przed calculate_total_price
        super().save(*args, **kwargs)

        # Oblicz total_price i subtotal_prices.
        # Używamy update_fields, aby uniknąć rekurencji, jeśli calculate_total_price
        # zmienia pola, które wywołują save.
        self.calculate_total_price()
        super().save(update_fields=["total_price", "accommodation_subtotal_price", "additional_services_subtotal_price", "extra_guest_fee"])


    def calculate_total_price(self):
        accommodation_price = Decimal('0.00')
        services_price = Decimal('0.00')
        extra_guest_cost = Decimal('0.00')

        num_nights = (self.end_date - self.start_date).days
        if num_nights <= 0:
            # Jeśli data wyjazdu jest taka sama lub wcześniejsza niż data przyjazdu,
            # ustaw ceny na 0 i zakończ
            self.accommodation_subtotal_price = Decimal('0.00')
            self.additional_services_subtotal_price = Decimal('0.00')
            self.extra_guest_fee = Decimal('0.00')
            self.total_price = Decimal('0.00')
            return

        # Sprawdź, czy dla rezerwacji obowiązuje cena sezonowa i jakie usługi są wliczone
        # Zakładamy, że jeśli jakikolwiek dzień w rezerwacji jest w sezonie, to usługi są blokowane
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

        # Obliczanie ceny zakwaterowania
        current_date = self.start_date
        while current_date < self.end_date:
            accommodation_price += self.accommodation.get_price_for_date(current_date)
            current_date += timedelta(days=1)

        # Obliczanie ceny usług dodatkowych
        # Usługi wliczone w cenę sezonową nie są dodawane do 'services_price'
        for service in self.additional_services.all():
            if service.pk not in included_services_in_season:
                services_price += service.price

        # Obliczanie opłaty za dodatkowych gości
        total_guests = self.number_of_adults + self.number_of_children
        if total_guests > 6:
            extra_guests = total_guests - 6
            extra_guest_cost = Decimal(str(extra_guests * 50)) * num_nights # 50 PLN za osobę za dobę

        self.accommodation_subtotal_price = accommodation_price
        self.additional_services_subtotal_price = services_price
        self.extra_guest_fee = extra_guest_cost
        self.total_price = accommodation_price + services_price + extra_guest_cost

    @property
    def number_of_guests(self):
        return self.number_of_adults + self.number_of_children
    number_of_guests.fget.short_description = "Liczba gości"


@receiver(m2m_changed, sender=Booking.additional_services.through)
def update_booking_total_price(sender, instance, action, **kwargs):
    # Upewnij się, że instance ma już PK (jest zapisana)
    if instance.pk and action in ["post_add", "post_remove", "post_clear"]:
        instance.calculate_total_price()
        # Zapisz tylko zmienione pola, aby uniknąć rekurencji
        instance.save(update_fields=["total_price", "accommodation_subtotal_price", "additional_services_subtotal_price", "extra_guest_fee"])