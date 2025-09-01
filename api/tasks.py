from celery import shared_task
from django.db import transaction
from django.db.models import F
from content.models import Video, Audio


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def increment_content_counters(self, content_ids, content_types):
    """
    Фоновая задача для атомарного увеличения счетчиков просмотров.
    Обеспечивает корректное увеличение даже при параллельных запросах.
    
    Args:
        content_ids (list): Список ID контента
        content_types (list): Список типов контента (video, audio)
    """
    try:
        with transaction.atomic():
            # Разделяем ID по типам контента
            video_ids = [
                content_id for content_id, content_type 
                in zip(content_ids, content_types) 
                if content_type == 'video'
            ]
            audio_ids = [
                content_id for content_id, content_type 
                in zip(content_ids, content_types) 
                if content_type == 'audio'
            ]
            
            # Атомарное обновление счетчиков
            if video_ids:
                Video.objects.filter(id__in=video_ids).update(
                    counter=F('counter') + 1
                )
            
            if audio_ids:
                Audio.objects.filter(id__in=audio_ids).update(
                    counter=F('counter') + 1
                )
            
        return f"Updated {len(video_ids)} videos and {len(audio_ids)} audios"
    
    except Exception as exc:
        # Повторяем задачу в случае ошибки
        self.retry(exc=exc)