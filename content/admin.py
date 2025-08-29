from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import Page, Video, Audio, PageContent


class PageContentInline(GenericTabularInline):
    model = PageContent
    extra = 1


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ["title"]
    search_fields = ["title"]
    inlines = [PageContentInline]


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ["title", "counter"]
    search_fields = ["title"]


@admin.register(Audio)
class AudioAdmin(admin.ModelAdmin):
    list_display = ["title", "counter"]
    search_fields = ["title"]
