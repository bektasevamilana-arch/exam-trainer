from django.db import models


class Topic(models.Model):
    name = models.CharField("Название", max_length=120)
    slug = models.SlugField("Код", unique=True)
    description = models.TextField("Описание", blank=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "тема"
        verbose_name_plural = "темы"

    def __str__(self):
        return self.name


class Question(models.Model):
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Тема",
    )
    key = models.SlugField("Код вопроса")
    text = models.TextField("Вопрос")
    explanation = models.TextField("Пояснение", blank=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["topic", "key"],
                name="unique_question_key_per_topic",
            )
        ]
        verbose_name = "вопрос"
        verbose_name_plural = "вопросы"

    def __str__(self):
        return self.text


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
        verbose_name="Вопрос",
    )
    text = models.TextField("Вариант ответа")
    is_correct = models.BooleanField("Правильный", default=False)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["question", "text"],
                name="unique_choice_text_per_question",
            )
        ]
        verbose_name = "вариант ответа"
        verbose_name_plural = "варианты ответа"

    def __str__(self):
        return self.text
