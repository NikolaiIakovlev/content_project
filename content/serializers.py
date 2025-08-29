from rest_framework import serializers
from content.models import Page, PageContent, Video, Audio


class VideoSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ["id", "title", "counter", "video_url", "subtitles_url", "type"]

    def get_type(self, obj):
        return "video"


class AudioSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = Audio
        fields = ["id", "title", "counter", "transcript", "type"]

    def get_type(self, obj):
        return "audio"


class PageContentSerializer(serializers.Serializer):
    def to_representation(self, obj):
        if isinstance(obj.content_object, Video):
            return VideoSerializer(obj.content_object).data
        elif isinstance(obj.content_object, Audio):
            return AudioSerializer(obj.content_object).data
        return {"id": obj.object_id, "title": "Unknown type"}


class PageListSerializer(serializers.ModelSerializer):
    detail_url = serializers.HyperlinkedIdentityField(
        view_name="page-detail", lookup_field="pk"
    )

    class Meta:
        model = Page
        fields = ["id", "title", "detail_url"]


class PageDetailSerializer(serializers.ModelSerializer):
    contents = PageContentSerializer(source="contents.all", many=True)

    class Meta:
        model = Page
        fields = ["id", "title", "contents"]
