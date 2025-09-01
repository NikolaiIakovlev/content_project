from rest_framework import generics
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from content.models import Page
from .serializers import PageListSerializer, PageDetailSerializer
from .tasks import increment_content_counters


class PageListView(generics.ListAPIView):
    """
    API для получения списка всех страниц с пагинацией.
    Возвращает ID, заголовок и URL для детальной информации.
    """
    queryset = Page.objects.all().prefetch_related('contents')
    serializer_class = PageListSerializer
    #pagination_class = generics.pagination.PageNumberPagination


class PageDetailView(generics.RetrieveAPIView):
    """
    API для получения детальной информации о странице.
    Включает все привязанные объекты контента с атрибутами.
    Запускает фоновую задачу для увеличения счетчиков просмотров.
    """
    queryset = Page.objects.all().prefetch_related(
        'contents__content_object'
    )
    serializer_class = PageDetailSerializer
    lookup_field = 'pk'
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        # Собираем ID всего контента на странице
        content_ids = []
        content_types = []
        
        for page_content in instance.contents.all():
            content_obj = page_content.content_object
            content_ids.append(content_obj.id)
            content_types.append(content_obj._meta.model_name)
        
        # Запускаем фоновую задачу для атомарного увеличения счетчиков
        if content_ids:
            increment_content_counters.delay(content_ids, content_types)
        
        return Response(serializer.data)