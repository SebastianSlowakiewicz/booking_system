from django.urls import path
from booking_system import views
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('users/', include('users.urls')),
    path('accommodation_facilities/', include('accommodation_facilities.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
