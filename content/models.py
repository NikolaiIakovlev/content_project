from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Page(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class ContentBase(models.Model):

    title = models.CharField(max_length=255)
    counter = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True


class Video(ContentBase):
    """Модель видео. """
    video_url = models.URLField()
    subtitles_url = models.URLField(blank=True, null=True)


class Audio(ContentBase):
    """Модель аудио. """
    transcript = models.TextField(blank=True)


class PageContent(models.Model):
    """Модель связи страницы с контентом. """
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="contents")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.content_object.title


# from django.db import models
# from django.db import models
# from django.core.exceptions import ValidationError
# from django.urls import reverse


# class Page(models.Model):
#     """Модель страницы сайта"""
#     title = models.CharField(max_length=255)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ['-created_at']

#     def __str__(self):
#         return self.title

# class ContentBase(models.Model):
#     """Базовая модель контента"""
#     title = models.CharField(max_length=255)
#     counter = models.PositiveIntegerField(default=0)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     order = models.PositiveIntegerField(default=0)

#     class Meta:
#         abstract = True
#         ordering = ['order']

#     def __str__(self):
#         return self.title


# class Video(ContentBase):
#     """Модель видео"""
#     video_url = models.URLField(max_length=500)
#     subtitles_url = models.URLField(max_length=500, blank=True, null=True)

#     class Meta:
#         ordering = ['order']

# class Audio(ContentBase):
#     """Модель аудио"""
#     text = models.TextField()

#     class Meta:
#         ordering = ['order']

# class PageContent(models.Model):
#     """Модель связи страницы с контентом"""
#     page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='contents')
#     content_type = models.CharField(max_length=50)
#     content_id = models.PositiveIntegerField()
#     order = models.PositiveIntegerField(default=0)

#     class Meta:
#         ordering = ['order']
#         unique_together = ['page', 'content_type', 'content_id']

#     def get_content_object(self):
#         if self.content_type == 'video':
#             return Video.objects.get(id=self.content_id)
#         elif self.content_type == 'audio':
#             return Audio.objects.get(id=self.content_id)
#         return None

#     def clean(self):
#         # Проверка, что объект контента существует
#         if self.content_type == 'video':
#             if not Video.objects.filter(id=self.content_id).exists():
#                 raise ValidationError('Video with this ID does not exist')
#         elif self.content_type == 'audio':
#             if not Audio.objects.filter(id=self.content_id).exists():
#                 raise ValidationError('Audio with this ID does not exist')
#         else:
#             raise ValidationError('Invalid content type')

#     def save(self, *args, **kwargs):
#         self.clean()
#         super().save(*args, **kwargs)