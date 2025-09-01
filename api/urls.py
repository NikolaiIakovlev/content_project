from django.urls import path
from api.views import PageListAPIView, PageDetailAPIView

app_name = "api"

urlpatterns = [
    path("pages/", PageListAPIView.as_view(), name="page-list"),
    path("pages/<int:pk>/", PageDetailAPIView.as_view(), name="page-detail"),
]
