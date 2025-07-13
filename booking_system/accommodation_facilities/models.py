from django.db import models
from datetime import date
from users.models import Users


class Amenity(models.Model):
    amenity = models.CharField(max_length=50)

    def __str__(self):
        return self.amenity


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

    name = models.CharField(max_length=100)
    accommodation_type = models.CharField(max_length=50, choices=ACCOMMODATION_TYPES)
    room_type = models.CharField(max_length=50, choices=ROOM_TYPES)
    description = models.TextField(blank=True, null=True)
    number_of_guests = models.PositiveIntegerField()
    number_of_bedrooms = models.PositiveIntegerField()
    number_of_beds = models.PositiveIntegerField()
    number_of_bathrooms = models.PositiveIntegerField()
    price_per_night = models.DecimalField( max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    amenities = models.ManyToManyField(Amenity)
    image = models.ImageField(upload_to="accommodation_images")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.address.city})" if hasattr(self, "address") else self.name

    def get_price_for_date(self, query_date: date):
        seasonal = self.seasonal_prices.filter(start_date__lte=query_date, end_date__gte=query_date).first()
        return seasonal.price_per_night if seasonal else self.price_per_night
    def is_available_for_dates(self, start_date, end_date):
        # Sprawdź, czy istnieje rezerwacja kolidująca z podanym terminem
        conflicting_bookings = self.bookings.filter(
            start_date__lt=end_date,
            end_date__gt=start_date
        )
        return not conflicting_bookings.exists()


class Address(models.Model):
    accommodation = models.OneToOneField(Accommodation, on_delete=models.CASCADE, related_name="address")
    country = models.CharField(max_length=100, default="Polska")
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    street = models.CharField(max_length=100)
    building_number = models.CharField(max_length=10)
    apartment_number = models.CharField(max_length=10, blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    def __str__(self):
        parts = [self.street, self.building_number]
        if self.apartment_number:
            parts.append(f"/{self.apartment_number}")
        return f"{' '.join(parts)}, {self.postal_code} {self.city}, {self.country}"

class SeasonalPrice(models.Model):
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE, related_name="seasonal_prices")
    start_date = models.DateField()
    end_date = models.DateField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["start_date"]
        verbose_name = "Cena sezonowa"
        verbose_name_plural = "Ceny sezonowe"

    def __str__(self):
        return f"{self.accommodation.name}: {self.start_date}–{self.end_date} → {self.price_per_night} PLN"
    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError("Data początkowa musi być wcześniejsza niż data końcowa.")
        if self.start_date < date.today():
            raise ValidationError("Data początkowa nie może być w przeszłości.")
        if self.price_per_night <= 0:
            raise ValidationError("Cena za noc musi być większa niż zero.")
from django.core.exceptions import ValidationError

class Booking(models.Model):
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE, related_name="bookings")
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rezerwacja {self.accommodation.name} od {self.start_date} do {self.end_date} przez {self.user.username}"
