from django import forms
from .models import Booking, Accommodation, Aditional_service
from django.core.exceptions import ValidationError
from datetime import date

class BookingForm(forms.ModelForm):
    # Override the accommodation field to use a ModelChoiceField
    # This allows users to select an accommodation from a dropdown
    accommodation = forms.ModelChoiceField(
        queryset=Accommodation.objects.all(),
        label="Wybierz zakwaterowanie",
        empty_label="--- Wybierz ---",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    # Override additional_services to use a CheckboxSelectMultiple
    additional_services = forms.ModelMultipleChoiceField(
        queryset=Aditional_service.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Usługi dodatkowe"
    )

    class Meta:
        model = Booking
        fields = [
            'accommodation',
            'start_date',
            'end_date',
            'number_of_adults',
            'number_of_children',
            'additional_services',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'number_of_adults': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'number_of_children': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
        }
        labels = {
            'start_date': 'Data przyjazdu',
            'end_date': 'Data wyjazdu',
            'number_of_adults': 'Liczba dorosłych',
            'number_of_children': 'Liczba dzieci',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customizing the queryset and label for additional_services
        # This ensures that the label for each checkbox includes the price per night
        self.fields['additional_services'].queryset = Aditional_service.objects.all()
        self.fields['additional_services'].label_from_instance = self.label_for_additional_service

    def label_for_additional_service(self, obj):
        """
        Generates the label for each additional service checkbox, including its price per night.
        """
        return f"{obj.aditional_service} ({obj.price:.2f} PLN/doba)"

    def clean(self):
        # Call the parent clean method to get initial cleaned data
        cleaned_data = super().clean()

        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        accommodation = cleaned_data.get('accommodation')
        number_of_adults = cleaned_data.get('number_of_adults')
        number_of_children = cleaned_data.get('number_of_children')

        # Validate dates
        if start_date and end_date:
            if start_date >= end_date:
                self.add_error('end_date', "Data wyjazdu musi być późniejsza niż data przyjazdu.")
            if start_date < date.today():
                self.add_error('start_date', "Data przyjazdu nie może być w przeszłości.")

        # Validate availability and guest count only if accommodation is selected and dates are valid
        if accommodation and start_date and end_date and not self.errors:
            # Check for overlapping bookings
            if not accommodation.is_available_for_dates(start_date, end_date):
                raise ValidationError(
                    "Wybrane zakwaterowanie jest niedostępne w tym terminie. Proszę wybrać inny termin lub obiekt."
                )

            # Check guest count against accommodation capacity
            total_guests = (number_of_adults or 0) + (number_of_children or 0)
            if total_guests > accommodation.number_of_guests:
                self.add_error('number_of_adults',
                               f"Liczba gości ({total_guests}) przekracza maksymalną pojemność zakwaterowania ({accommodation.number_of_guests}).")

        return cleaned_data

    def save(self, commit=True):
        booking = super().save(commit=False) # Pobierz niezapisaną instancję
        if commit:
            booking.save() # Zapisz instancję, jeśli commit=True
            self.save_m2m() # Zapisz relacje ManyToMany (np. additional_services)
        return booking # ZWRÓĆ instancję booking
