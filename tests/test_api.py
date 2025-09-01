import pytest
from rest_framework.test import APIClient
from content.models import Page, Contents, Video, Audio, Text, ContentOnPage


@pytest.mark.django_db
def test_page_list_api():
    """
    Позитивный тест: проверяем, что API списка страниц возвращает созданную страницу.
    """
    client = APIClient()

    # Создаём страницу
    page = Page.objects.create(title="Test Page")

    response = client.get("/api/pages/")
    assert response.status_code == 200
    data = response.json()
    assert len(data['results']) == 1
    assert data['results'][0]['id'] == page.id
    assert data['results'][0]['title'] == "Test Page"
    assert 'detail_url' in data['results'][0]


@pytest.mark.django_db
def test_page_detail_api():
    """
    Позитивный тест: проверяем детальный API страницы с контентом.
    """
    client = APIClient()

    # Создаём страницу
    page = Page.objects.create(title="Detail Page")

    # Создаём видео контент и обертку Contents
    video = Video.objects.create(title="Video 1", video_url="http://video.url")
    contents = Contents.objects.create(content_object=video)
    ContentOnPage.objects.create(page=page, content=contents, order=1)

    response = client.get(f"/api/pages/{page.id}/")
    assert response.status_code == 200

    data = response.json()
    assert data['id'] == page.id
    assert data['title'] == "Detail Page"
    assert 'contents' in data
    assert len(data['contents']) == 1
    content_item = data['contents'][0]
    assert content_item['title'] == "Video 1"
    assert content_item['type'] == "Video"
    assert content_item['video_url'] == "http://video.url"


@pytest.mark.django_db
def test_page_list_pagination():
    """
    Проверяем пагинацию списка страниц.
    """
    client = APIClient()
    # создаём 15 страниц
    for i in range(15):
        Page.objects.create(title=f"Page {i+1}")

    response = client.get("/api/pages/")
    data = response.json()
    # page_size=10, значит на первой странице 10 элементов
    assert len(data['results']) == 10
    assert data['count'] == 15
    assert 'next' in data and data['next'] is not None


@pytest.mark.django_db
def test_content_counter_increment():
    """
    Проверяем, что при обращении к детальной странице контент увеличивает счетчик просмотров.
    """
    client = APIClient()
    page = Page.objects.create(title="Counter Page")
    video = Video.objects.create(title="Video Counter", video_url="http://video.url")
    contents = Contents.objects.create(content_object=video)
    ContentOnPage.objects.create(page=page, content=contents, order=1)

    # Счётчик до запроса
    assert video.counter == 0

    # Обращение к детальной странице
    client.get(f"/api/pages/{page.id}/")

    # Перезагружаем объект из базы
    video.refresh_from_db()
    assert video.counter == 1


@pytest.mark.django_db
def test_page_with_mixed_content():
    """
    Проверяем, что детальная страница возвращает контент разных типов в порядке order.
    """
    client = APIClient()
    page = Page.objects.create(title="Mixed Page")

    video = Video.objects.create(title="Video 1", video_url="http://video.url")
    audio = Audio.objects.create(title="Audio 1", transcript="Text")
    text = Text.objects.create(title="Text 1", body="Body text")

    video_content = Contents.objects.create(content_object=video)
    audio_content = Contents.objects.create(content_object=audio)
    text_content = Contents.objects.create(content_object=text)

    ContentOnPage.objects.create(page=page, content=text_content, order=2)
    ContentOnPage.objects.create(page=page, content=video_content, order=1)
    ContentOnPage.objects.create(page=page, content=audio_content, order=3)

    response = client.get(f"/api/pages/{page.id}/")
    data = response.json()
    contents = data['contents']

    # Проверяем порядок
    assert [c['title'] for c in contents] == ["Video 1", "Text 1", "Audio 1"]
    # Проверяем типы
    assert [c['type'] for c in contents] == ["Video", "Text", "Audio"]


@pytest.mark.django_db
def test_multiple_counter_increments():
    """
    Проверяем атомарное увеличение счетчика при нескольких запросах.
    """
    client = APIClient()
    page = Page.objects.create(title="Atomic Page")
    video = Video.objects.create(title="Video Atomic", video_url="http://video.url")
    contents = Contents.objects.create(content_object=video)
    ContentOnPage.objects.create(page=page, content=contents, order=1)

    # Делаем два запроса подряд
    client.get(f"/api/pages/{page.id}/")
    client.get(f"/api/pages/{page.id}/")

    video.refresh_from_db()
    # Должно увеличиться на 2
    assert video.counter == 2


@pytest.mark.django_db
def test_empty_page_content():
    """
    Проверяем корректную работу детальной страницы без контента.
    """
    client = APIClient()
    page = Page.objects.create(title="Empty Page")

    response = client.get(f"/api/pages/{page.id}/")
    data = response.json()

    assert data['id'] == page.id
    assert data['title'] == "Empty Page"
    # Содержимого нет
    assert data['contents'] == []
