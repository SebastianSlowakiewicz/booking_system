from django.urls import path
from . import views

urlpatterns = [
    path('udogodnienia/', views.amenities_view, name='amenities_view'),
]