from .models import Accommodation

def special_offers_processor(request):
    special_offers_list = []
    try:
        main_accommodation_obj = Accommodation.objects.first()
        if main_accommodation_obj:
            special_offers_list = list(
                main_accommodation_obj.seasonal_prices.filter(notification=True).prefetch_related('included_services')
            )
    except Accommodation.DoesNotExist:
        pass

    return {'special_offers': special_offers_list}