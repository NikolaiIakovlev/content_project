from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db.models import Count, Prefetch, F
from django.contrib.contenttypes.models import ContentType
from content.models import Page, ContentOnPage, BaseContent, Video, Audio, Text
from .serializers import PageListSerializer, PageDetailSerializer


class StandardResultsSetPagination(PageNumberPagination):
    """
    Стандартная пагинация для API с настройкой размера страницы.
    
    Attributes:
        page_size: Количество элементов на странице по умолчанию
        page_size_query_param: Параметр запроса для изменения размера страницы
        max_page_size: Максимальный разрешенный размер страницы
    """
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class PageListAPIView(generics.ListAPIView):
    """
    API endpoint для получения paginated списка всех страниц.
    
    Оптимизации:
        - Аннотация количества контента за один SQL запрос
        - Выбор только необходимых полей для уменьшения объема данных
        - Сортировка по индексированному полю created_at
    """
    serializer_class = PageListSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        Оптимизированный queryset для списка страниц.
        
        Returns:
            QuerySet: Аннотированный queryset с количеством контент-элементов
        """
        return Page.objects.annotate(
            content_count=Count('content_items')
        ).order_by("-created_at").only('id', 'title', 'created_at')


class PageDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint для получения детальной информации о странице.
    
    Оптимизации:
        - Prefetch related для загрузки всех связанных данных за минимальное количество SQL запросов
        - Select related для уменьшения количества JOIN операций
        - Массовое обновление счетчиков вместо N+1 запросов
    """
    serializer_class = PageDetailSerializer

    def get_queryset(self):
        """
        Оптимизированный queryset для детальной страницы с предзагрузкой.
        
        Returns:
            QuerySet: Queryset с предзагруженными связанными объектами
        """
        return Page.objects.prefetch_related(
            Prefetch(
                'content_items',
                queryset=ContentOnPage.objects.select_related(
                    'content__content_type'
                ).order_by('order')
            )
        )

    def retrieve(self, request, *args, **kwargs):
        """
        Обработчик GET запроса для детальной страницы.
        
        Оптимизации:
            - Массовое обновление счетчиков через F expressions
            - Минимизация количества SQL запросов
            
        Returns:
            Response: Сериализованные данные страницы
        """
        instance = self.get_object()

        # Оптимизированное увеличение счетчиков всех контентов на странице
        self._bulk_increment_counters(instance)

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def _bulk_increment_counters(self, instance):
        """
        Массовое увеличение счетчиков просмотров контент-объектов.
        
        Вместо N отдельных запросов выполняется групповое обновление по типам контента.
        
        Args:
            instance: Объект Page для обработки
        """
        # Получаем все контент-элементы страницы с предзагрузкой
        content_items = instance.content_items.select_related(
            'content', 'content__content_type'
        ).all()
        
        # Группируем ID объектов по их типам контента
        content_ids_by_type = {}
        
        for item in content_items:
            if not item.content.content_object:
                continue
                
            content_type_id = item.content.content_type_id
            object_id = item.content.object_id
            
            if content_type_id not in content_ids_by_type:
                content_ids_by_type[content_type_id] = []
            content_ids_by_type[content_type_id].append(object_id)
        
        # Массовое обновление счетчиков для каждого типа контента
        for content_type_id, object_ids in content_ids_by_type.items():
            try:
                content_type = ContentType.objects.get(id=content_type_id)
                model_class = content_type.model_class()
                
                if model_class and issubclass(model_class, BaseContent):
                    # Выполняем массовое обновление счетчиков
                    model_class.objects.filter(
                        id__in=object_ids
                    ).update(counter=F('counter') + 1)
                    
            except (ContentType.DoesNotExist, AttributeError):
                # Пропускаем невалидные типы контента
                continue
