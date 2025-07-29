from .models import SeasonalPrice
from django.utils import timezone

def special_offers_processor(request):

    today = timezone.now().date()
    
    special_offers = SeasonalPrice.objects.filter(
        notification=True,
        end_date__gte=today
    ).select_related('accommodation')

    return {'special_offers': special_offers}