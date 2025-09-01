from rest_framework import serializers
from content.models import Page, Video, Audio


class VideoSerializer(serializers.ModelSerializer):
    content_type = serializers.ReadOnlyField(default='video')
    
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'counter', 'video_url', 
            'subtitles_url', 'content_type', 'created_at'
        ]


class AudioSerializer(serializers.ModelSerializer):
    content_type = serializers.ReadOnlyField(default='audio')
    
    class Meta:
        model = Audio
        fields = [
            'id', 'title', 'counter', 'transcript', 
            'content_type', 'created_at'
        ]


class ContentObjectRelatedField(serializers.RelatedField):
    """Универсальное поле для отображения связанного контента."""
    
    def to_representation(self, value):
        if isinstance(value, Video):
            return VideoSerializer(value).data
        elif isinstance(value, Audio):
            return AudioSerializer(value).data
        raise Exception("Unexpected type of content object")


class PageContentSerializer(serializers.ModelSerializer):
    content_object = ContentObjectRelatedField(read_only=True)
    
    class Meta:
        #model = PageContent
        fields = ['order', 'content_object']


class PageListSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='api:page-detail',
        lookup_field='pk'
    )
    
    class Meta:
        model = Page
        fields = ['id', 'title', 'url']


class PageDetailSerializer(serializers.ModelSerializer):
    contents = PageContentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Page
        fields = ['id', 'title', 'contents']