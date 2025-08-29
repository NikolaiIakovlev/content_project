from rest_framework import viewsets, mixins
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import Page
from .serializers import PageListSerializer, PageDetailSerializer
from .tasks import increment_view_counter


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class PageViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = Page.objects.all().prefetch_related("contents__content_object")
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == "list":
            return PageListSerializer
        return PageDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        page = self.get_object()
        # фоновое обновление счётчиков просмотров через celery
        for pc in page.contents.all():
            increment_view_counter.delay(
                pc.content_type_id, pc.object_id
            )
        serializer = self.get_serializer(page)
        return Response(serializer.data)
