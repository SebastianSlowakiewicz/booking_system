from django.shortcuts import render,redirect
from .forms import BookingForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import BookingForm

from django.shortcuts import render, redirect
from .forms import BookingForm
from django.contrib.auth.decorators import login_required

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