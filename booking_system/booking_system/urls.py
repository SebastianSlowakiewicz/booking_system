from django.urls import path
from booking_system import views
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from booking_system import views as booking_views
from accommodation_facilities import views as amenities_views



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('users/', include('users.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
