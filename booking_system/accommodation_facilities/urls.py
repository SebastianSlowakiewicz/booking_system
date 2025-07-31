from django.urls import path
from . import views

app_name = 'accommodation_facilities'

urlpatterns = [
    path('rezerwuj/', views.create_booking, name='create_booking'),
    path('rezerwacja-potwierdzona/<int:booking_id>/', views.booking_success, name='booking_success'),
    path('szczegoly_rezerwacji/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('calculate_price_ajax/', views.calculate_booking_price_ajax, name='calculate_booking_price_ajax'), 
    path('oferta/', views.offer_page_view, name='offer'),
    path('galeria_zdjec/', views.gallery_view, name='gallery'),
    path('kontakt/', views.contact_view, name='contact'),
]