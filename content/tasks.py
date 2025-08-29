from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.db.models import F


@shared_task
def increment_view_counter(content_type_id, object_id):
    model = ContentType.objects.get_for_id(content_type_id).model_class()
    model.objects.filter(pk=object_id).update(counter=F("counter") + 1)
