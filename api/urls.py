from django.urls import path
from .views import PageListView, PageDetailView

app_name = 'api'

urlpatterns = [
    path('pages/', PageListView.as_view(), name='page-list'),
    path('pages/<int:pk>/', PageDetailView.as_view(), name='page-detail'),
]