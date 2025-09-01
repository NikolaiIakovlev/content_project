from rest_framework import viewsets, generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from content.models import Page, ContentOnPage
from .serializers import PageListSerializer, PageDetailSerializer

# Пагинация
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


# Список страниц с пагинацией
class PageListAPIView(generics.ListAPIView):
    queryset = Page.objects.all().order_by("-created_at")
    serializer_class = PageListSerializer
    pagination_class = StandardResultsSetPagination


# Детальная страница
class PageDetailAPIView(generics.RetrieveAPIView):
    queryset = Page.objects.all()
    serializer_class = PageDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # увеличиваем счетчики всех контентов на странице
        for item in instance.get_ordered_items():
            content_obj = item.content.content_object
            if content_obj:
                content_obj.increment_counter()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
