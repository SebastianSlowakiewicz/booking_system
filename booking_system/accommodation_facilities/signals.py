from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import SeasonalPrice, Notification, Accommodation

@receiver(post_save, sender=SeasonalPrice)
def create_or_update_special_offer_notification(sender, instance, created, **kwargs):
    if instance.notification:
        title = f"Oferta Specjalna: {instance.accommodation.name}"
        message = (
            f"Skorzystaj z wyjątkowej oferty w obiekcie {instance.accommodation.name}! "
            f"W terminie od {instance.start_date.strftime('%d.%m.%Y')} do {instance.end_date.strftime('%d.%m.%Y')} "
            f"cena za noc wynosi tylko {instance.price_per_night} PLN. "
        )
        if instance.description:
            message += instance.description

        notification, created = Notification.objects.get_or_create(
            seasonal_price=instance,
            defaults={'title': title, 'message': message}
        )
        if not created:
            notification.title = title
            notification.message = message
            notification.is_active = True
            notification.save()
            
    else:
        Notification.objects.filter(seasonal_price=instance).delete()

@receiver(post_delete, sender=SeasonalPrice)
def delete_special_offer_notification(sender, instance, **kwargs):
    Notification.objects.filter(seasonal_price=instance).delete()