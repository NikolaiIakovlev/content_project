from typing import List, Tuple, Optional, Dict, Set

from django.db import models
from django.db.models import F
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError


# ---------------- Base Content ----------------
class BaseContent(models.Model):
    """Базовая модель с общими полями для всех видов контента."""
    title = models.CharField(max_length=255, db_index=True)
    counter = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def increment_counter(self, by: int = 1):
        """Атомарное увеличение счётчика просмотров."""
        self.__class__.objects.filter(pk=self.pk).update(counter=F("counter") + by)


class Video(BaseContent):
    video_url = models.URLField()
    subtitles_url = models.URLField(blank=True, null=True)
    # обратная связь к Contents
    contents = GenericRelation("Contents", related_query_name="video")

    def __str__(self):
        return f"🎬 {self.title}"


class Audio(BaseContent):
    transcript = models.TextField(blank=True, null=True)
    contents = GenericRelation("Contents", related_query_name="audio")

    def __str__(self):
        return f"🎧 {self.title}"


class Text(BaseContent):
    body = models.TextField()
    contents = GenericRelation("Contents", related_query_name="text")

    def __str__(self):
        return f"📝 {self.title}"


# ---------------- Contents Manager ----------------
class ContentsManager(models.Manager):
    def get_queryset(self):
        # можно добавить select_related('content_type') для лёгкого доступа к content_type
        return super().get_queryset().select_related("content_type")

    def for_model(self, model_class):
        ct = ContentType.objects.get_for_model(model_class)
        return self.get_queryset().filter(content_type=ct)

    def for_object(self, obj):
        """Возвращает Contents для конкретного объекта (или None)."""
        ct = ContentType.objects.get_for_model(obj)
        return self.get_queryset().filter(content_type=ct, _object_id=obj.pk)

    def get_or_create_for_object(self, obj):
        ct = ContentType.objects.get_for_model(obj)
        return self.get_or_create(content_type=ct, _object_id=obj.pk)


# ---------------- Contents ----------------
class Contents(models.Model):
    """
    Обёртка для конкретного объекта контента (Video/Audio/Text/...).
    Здесь имеет смысл хранить одну запись на каждый реальный объект контента,
    чтобы многократно не дублировать мета-информацию.
    """
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Тип контента",
        help_text="Выберите модель контента (Video, Audio, Text и др.)",
        db_index=True,
    )
    _object_id = models.PositiveIntegerField(
        db_column="object_id",
        verbose_name="ID объекта контента",
        help_text="ID конкретного объекта выбранного типа контента",
        db_index=True,
    )
    # GenericForeignKey к реальному объекту
    content_object = GenericForeignKey("content_type", "_object_id")

    objects = ContentsManager()

    class Meta:
        verbose_name = "Контент"
        verbose_name_plural = "Контент"
        # Обычно удобно иметь только одну запись-обёртку на реальный объект:
        # constraints = [
        #     models.UniqueConstraint(
        #         fields=["content_type", "_object_id"], name="unique_content_object"
        #     )
        # ]
        indexes = [
            models.Index(fields=["content_type", "_object_id"]),
        ]

    def __str__(self):
        # если объект удалён, content_object может быть None
        return str(self.content_object) if self.content_object is not None else f"Contents({self.content_type}, {self._object_id})"

    @property
    def object_id(self) -> int:
        return self._object_id

    @object_id.setter
    def object_id(self, value: int):
        if value <= 0:
            raise ValueError("object_id должен быть положительным числом")
        self._object_id = value

    def clean(self):
        """
        Проверяем, что content_type соответствует классу-наследнику BaseContent,
        и что целевой объект действительно существует.
        Используем content_type.model_class() — безопасно при валидации перед сохранением.
        """
        if not self.content_type_id or not self._object_id:
            # неполные данные — пропускаем (валидация дальше будет в save/DB)
            return

        model_class = self.content_type.model_class()
        if model_class is None:
            raise ValidationError("Неверный тип контента")

        # Проверяем наследование от BaseContent
        try:
            is_sub = issubclass(model_class, BaseContent)
        except TypeError:
            is_sub = False

        if not is_sub:
            raise ValidationError("Можно добавлять только объекты, унаследованные от BaseContent")

        # Проверим, что объект с таким ID существует
        if not model_class.objects.filter(pk=self._object_id).exists():
            raise ValidationError(f"Объект {model_class.__name__} с id={self._object_id} не найден")


# ---------------- Page ----------------
class Page(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Страница"
        verbose_name_plural = "Страницы"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return self.title

    # ---- выборки: ----
    def get_ordered_items(self) -> List["ContentOnPage"]:
        """
        Возвращает список ContentOnPage, отсортированный по order.
        select_related('content__content_type') подгружает FK на Contents и ContentType
        (сам content_object — generic, его надо загружать отдельно).
        """
        return list(self.content_items.select_related("content__content_type").order_by("order"))

    def get_ordered_contents(self) -> List[Optional[BaseContent]]:
        """
        Возвращает список самих контент-объектов (Video/Audio/Text/...),
        эффективно подгружая их пакетно:

        - 1 запрос для получения ContentOnPage
        - N запросов, где N = число *разных* типов контента на странице
        """
        items = self.get_ordered_items()
        if not items:
            return []

        # сгруппируем по content_type_id -> список object_id
        ct_to_ids: Dict[int, Set[int]] = {}
        for item in items:
            ct_id = item.content.content_type_id
            ct_to_ids.setdefault(ct_id, set()).add(item.content.object_id)

        # загрузим объекты пакетно и соберём мапу (ct_id, pk) -> объект
        fetched: Dict[Tuple[int, int], BaseContent] = {}
        for ct_id, ids in ct_to_ids.items():
            try:
                ct = ContentType.objects.get(pk=ct_id)
            except ContentType.DoesNotExist:
                continue
            model_class = ct.model_class()
            if model_class is None:
                continue
            qs = model_class.objects.filter(pk__in=list(ids))
            for obj in qs:
                fetched[(ct_id, obj.pk)] = obj

        # сформируем результат в порядке items
        results: List[Optional[BaseContent]] = []
        for item in items:
            key = (item.content.content_type_id, item.content.object_id)
            results.append(fetched.get(key))  # если объект удалили — будет None

        return results

    def get_ordered_contents_with_wrappers(self) -> List[Tuple["ContentOnPage", Optional[BaseContent]]]:
        """
        Если нужен доступ к ContentOnPage + реальному объекту одновременно.
        """
        items = self.get_ordered_items()
        contents = self.get_ordered_contents()
        return list(zip(items, contents))


# ---------------- ContentOnPage ----------------
class ContentOnPage(models.Model):
    """
    Связующая модель: конкретный Contents размещён на конкретной странице.
    Поле `order` управляет порядком. Поле `alias` даёт опциональный локальный slug/name.
    """
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="content_items")
    content = models.ForeignKey(Contents, on_delete=models.CASCADE, related_name="page_items")
    order = models.PositiveIntegerField(default=0, db_index=True)

    # локальный alias/slug для этого встраивания (опционально)
    alias = models.SlugField(max_length=150, blank=True, null=True, help_text="Необязательный alias на странице")

    class Meta:
        ordering = ["order"]
        verbose_name = "Элемент контента на странице"
        verbose_name_plural = "Элементы контента на странице"
        constraints = [
            # один и тот же обёрточный объект нельзя дублировать в рамках одной страницы
            models.UniqueConstraint(fields=["page", "content"], name="unique_page_content"),
            # при желании можно добавить уникальность alias в рамках page
            # models.UniqueConstraint(fields=['page', 'alias'], name='unique_page_alias')
        ]
        indexes = [
            models.Index(fields=["page", "order"]),
        ]

    def __str__(self):
        return f"{self.page} → {self.content}"

    def save(self, *args, **kwargs):
        # автозаполнение order (если 0 — считаем как "append")
        if not self.pk and (self.order is None or self.order == 0):
            last = ContentOnPage.objects.filter(page=self.page).aggregate(models.Max("order"))["order__max"]
            self.order = (last or 0) + 1
        super().save(*args, **kwargs)
