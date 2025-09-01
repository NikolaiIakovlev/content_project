from rest_framework import serializers
from content.models import Page, ContentOnPage, Video, Audio, Text

# Сериализатор для контента
class BaseContentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    title = serializers.CharField()
    counter = serializers.IntegerField()
    order = serializers.IntegerField()
    # специфичные поля
    video_url = serializers.CharField(required=False)
    subtitles_url = serializers.CharField(required=False)
    transcript = serializers.CharField(required=False)
    body = serializers.CharField(required=False)

    def to_representation(self, obj: ContentOnPage):
        content_obj = obj.content.content_object
        data = {
            "id": content_obj.pk,
            "type": content_obj.__class__.__name__,
            "title": content_obj.title,
            "counter": content_obj.counter,
            "order": obj.order,
        }
        # специфичные поля
        if isinstance(content_obj, Video):
            data["video_url"] = content_obj.video_url
            data["subtitles_url"] = content_obj.subtitles_url
        elif isinstance(content_obj, Audio):
            data["transcript"] = content_obj.transcript
        elif isinstance(content_obj, Text):
            data["body"] = content_obj.body
        return data


# Сериализатор для списка страниц
class PageListSerializer(serializers.ModelSerializer):
    detail_url = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ("id", "title", "created_at", "detail_url")

    def get_detail_url(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/api/pages/{obj.pk}/")
        return f"/api/pages/{obj.pk}/"


# Сериализатор для детальной страницы
class PageDetailSerializer(serializers.ModelSerializer):
    contents = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = ("id", "title", "created_at", "contents")

    def get_contents(self, obj):
        # берем контент в порядке order
        items = obj.get_ordered_items()
        return BaseContentSerializer(items, many=True).data
