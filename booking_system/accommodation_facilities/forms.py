from django import forms
from .models import Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['accommodation', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'accommodation': forms.Select(attrs={'class': 'form-control'}),
            'number_of_guests': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            
        }

    def __str__(self):
        return f'{self.user} - {self.accommodation} ({self.start_date} to {self.end_date})'