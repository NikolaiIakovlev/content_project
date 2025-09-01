
from celery import shared_task
from django.db.models import F
from django.contrib.contenttypes.models import ContentType
from content.models import Page, BaseContent, ContentOnPage


@shared_task
def increment_page_content_counters(page_id):
    """
    Фоновая задача для атомарного увеличения счетчиков просмотров
    всех контент-объектов, привязанных к странице.
    
    Логика:
        - Получаем все ContentOnPage для страницы
        - Группируем объекты по типу контента
        - Для каждого типа выполняем массовое обновление через F expression
        - Атомарность гарантируется на уровне базы данных
    """
    try:
        page = Page.objects.prefetch_related('content_items').get(id=page_id)
    except Page.DoesNotExist:
        return

    # Группируем ID объектов по их типам контента
    content_ids_by_type = {}
    for item in page.content_items.all():
        content_obj = item.content.content_object
        if not content_obj:
            continue

        content_type_id = item.content.content_type_id
        object_id = item.content.object_id

        if content_type_id not in content_ids_by_type:
            content_ids_by_type[content_type_id] = []
        content_ids_by_type[content_type_id].append(object_id)

    # Массовое атомарное обновление для каждого типа контента
    for content_type_id, object_ids in content_ids_by_type.items():
        try:
            content_type = ContentType.objects.get(id=content_type_id)
            model_class = content_type.model_class()
            
            if model_class and issubclass(model_class, BaseContent):
                # Атомарное увеличение счетчиков через F
                model_class.objects.filter(id__in=object_ids).update(counter=F('counter') + 1)

        except (ContentType.DoesNotExist, AttributeError):
            # Пропускаем невалидные типы
            continue
