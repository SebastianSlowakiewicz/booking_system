from django.shortcuts import render, HttpResponse
from datetime import datetime, date
from accommodation_facilities.models import SeasonalPrice
from django.contrib.auth.decorators import login_required


def index(request):
    return render(request, 'index.html.jinja')
def index(request):
    return render(request, "index.html.jinja", {
        "current_year": datetime.now().year,
    })
@login_required
def dashboard(request):
    return render(request, 'dashboard.html.jinja')
