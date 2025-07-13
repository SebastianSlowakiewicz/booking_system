from django.shortcuts import render,redirect
from .forms import BookingForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import BookingForm
from .models import Amenity


@login_required
def index(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.save()
            return redirect('dashboard')  # Zamień na swoją nazwę URL do dashboardu
    else:
        form = BookingForm()

    return render(request, 'index.html', {'form': form})

def amenities_view(request):
    grouped_amenities = {}
    for room_type, display_name in Amenity.ROOM_TYPES:
        grouped_amenities[display_name] = Amenity.objects.filter(room_type=room_type)
    
    grouped_amenities["Inne"] = Amenity.objects.filter(room_type__isnull=True)

    return render(request, "amenities.html.jinja", {
        "grouped_amenities": grouped_amenities
    })