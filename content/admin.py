from django.contrib import admin
from django.utils.html import format_html
from django.contrib.contenttypes.models import ContentType
from .models import (
    Page, ContentOnPage, Contents,
    Video, Audio, Text, BaseContent
    )


# ---------------- Inline ----------------
class ContentOnPageInline(admin.TabularInline):
    """Элементы контента на странице."""
    model = ContentOnPage
    extra = 1
    fields = ("order", "content", "preview_object")
    readonly_fields = ("preview_object",)
    ordering = ("order",)

    def preview_object(self, obj):
        """Показывает реальный объект контента (Video, Audio, Text...)"""
        if obj.pk and obj.content and obj.content.content_object:
            co = obj.content.content_object
            return format_html("<b>{}</b> <i>({})</i>", co.title, co.__class__.__name__)
        return "—"
    preview_object.short_description = "Объект контента"


# ---------------- Page ----------------
@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Страницы."""
    list_display = ("title", "created_at", "contents_count")
    search_fields = ("^title",)
    ordering = ("-created_at",)
    inlines = [ContentOnPageInline]

    def contents_count(self, obj):
        return obj.content_items.count()
    contents_count.short_description = "Кол-во элементов"


# ---------------- Base Content Models ----------------
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Видео."""
    list_display = ("title", "created_at", "counter")
    search_fields = ("^title",)
    ordering = ("-created_at",)


@admin.register(Audio)
class AudioAdmin(admin.ModelAdmin):
    """Аудио."""
    list_display = ("title", "created_at", "counter")
    search_fields = ("^title",)
    ordering = ("-created_at",)


@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    """Текст."""
    list_display = ("title", "created_at", "counter")
    search_fields = ("^title",)
    ordering = ("-created_at",)


# ---------------- Contents Wrapper ----------------
@admin.register(Contents)
class ContentsAdmin(admin.ModelAdmin):
    """Обёртка для конкретного объекта контента (Video/Audio/Text/...)."""
    list_display = ("id", "content_type", "object_id", "preview_object")
    search_fields = ("object_id", "content_type__model")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Ограничиваем список content_type только моделями,
        унаследованными от BaseContent (Video, Audio, Text и др.).
        """
        if db_field.name == "content_type":
            # Получаем все ContentType для наследников BaseContent
            allowed_models = BaseContent.__subclasses__()
            allowed_cts = ContentType.objects.get_for_models(*allowed_models).values()
            kwargs["queryset"] = ContentType.objects.filter(id__in=[ct.id for ct in allowed_cts])
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def preview_object(self, obj):
        return str(obj.content_object)
    preview_object.short_description = "Контент"
