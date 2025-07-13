from django.db import models
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from users.models import Users
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

class Amenity(models.Model):
    amenity = models.CharField(max_length=50)

    def __str__(self):
        return self.amenity

class Aditional_service(models.Model):
    aditional_service = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.aditional_service

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
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
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
        return not self.bookings.filter(start_date__lt=end_date, end_date__gt=start_date).exists()

class Address(models.Model):
    accommodation = models.OneToOneField(Accommodation, on_delete=models.CASCADE, related_name="address")
    country = models.CharField(max_length=100, default="Polska")
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    street = models.CharField(max_length=100)
    building_number = models.CharField(max_length=10)
    apartment_number = models.CharField(max_length=10, blank=True, null=True)

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
        if self.price_per_night <= 0:
            raise ValidationError("Cena za noc musi być większa niż zero.")

class Booking(models.Model):
    accommodation = models.ForeignKey('Accommodation', on_delete=models.CASCADE, related_name="bookings")
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    additional_services = models.ManyToManyField('Aditional_service', blank=True)
    number_of_guests = models.PositiveIntegerField(default=1)
    class Meta:
        ordering = ["start_date"]
        verbose_name = "Rezerwacja"
        verbose_name_plural = "Rezerwacje"

    def __str__(self):
        return f"Booking for {self.accommodation.name} by {self.user.username} from {self.start_date} to {self.end_date}"

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
        super().save(*args, **kwargs)  # Zapisz do DB, żeby mieć ID

    def calculate_total_price(self):
        num_nights = (self.end_date - self.start_date).days
        total = 0
        current_date = self.start_date

        while current_date < self.end_date:
            total += self.accommodation.get_price_for_date(current_date)
            current_date += timedelta(days=1)

        for service in self.additional_services.all():
            total += service.price

        self.total_price = total
        self.save(update_fields=["total_price"])

@receiver(m2m_changed, sender=Booking.additional_services.through)
def update_booking_total_price(sender, instance, action, **kwargs):
    if action in ["post_add", "post_remove", "post_clear"]:
        instance.calculate_total_price()