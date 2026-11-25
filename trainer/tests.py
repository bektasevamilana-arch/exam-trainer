from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .management.commands.load_questions import SEED_DATA
from .models import Choice, Question, Topic
from .services import TOPICS_CACHE_KEY, get_topics

LOCMEM_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "exam-trainer-tests",
    }
}


class QuizFlowTests(TestCase):
    def setUp(self):
        self.topic = Topic.objects.create(
            name="Процессы и потоки", slug="processes-and-threads"
        )
        self.questions = []
        for question_number in range(1, 4):
            question = Question.objects.create(
                topic=self.topic,
                key=f"question-{question_number}",
                text=f"Вопрос {question_number}",
                explanation=f"Пояснение {question_number}",
            )
            choices = [
                Choice.objects.create(
                    question=question,
                    text=f"Вопрос {question_number} вариант {choice_number}",
                    is_correct=choice_number == 1,
                )
                for choice_number in range(1, 5)
            ]
            self.questions.append((question, choices))

    def test_two_correct_and_one_wrong_answer(self):
        answers = {}
        for index, (question, choices) in enumerate(self.questions):
            answer = choices[0] if index < 2 else choices[1]
            answers[f"question_{question.pk}"] = str(answer.pk)

        response = self.client.post(
            reverse("quiz", args=[self.topic.slug]), answers
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2 из 3")
        self.assertContains(response, "Правильный ответ: Вопрос 3 вариант 1")
        self.assertContains(response, "Пояснение 3")
        self.assertNotContains(response, "Пояснение 1")

    def test_missing_answer_keeps_selected_answers(self):
        first_question, first_choices = self.questions[0]
        answers = {f"question_{first_question.pk}": str(first_choices[0].pk)}

        response = self.client.post(
            reverse("quiz", args=[self.topic.slug]), answers
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ответьте на этот вопрос.")
        self.assertEqual(len(response.context["form"].errors), 2)
        self.assertEqual(
            response.context["form"].data[f"question_{first_question.pk}"],
            str(first_choices[0].pk),
        )
        self.assertIn("checked", response.content.decode())


class LoaderTests(TestCase):
    def test_reloading_questions_does_not_create_duplicates(self):
        call_command("load_questions", verbosity=0)
        counts = (Topic.objects.count(), Question.objects.count(), Choice.objects.count())

        call_command("load_questions", verbosity=0)

        self.assertEqual(
            counts, (Topic.objects.count(), Question.objects.count(), Choice.objects.count())
        )
        self.assertEqual(counts, (len(SEED_DATA), 6, 24))
        for question in Question.objects.all():
            self.assertEqual(question.choices.filter(is_correct=True).count(), 1)


@override_settings(CACHES=LOCMEM_CACHE)
class TopicsCacheTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_second_read_comes_from_cache(self):
        Topic.objects.create(name="Управление памятью", slug="memory-management")

        first_topics, first_source = get_topics()
        second_topics, second_source = get_topics()

        self.assertEqual((first_source, second_source), ("database", "cache"))
        self.assertEqual(first_topics, second_topics)
        self.assertEqual(len(first_topics), 1)
        self.assertIsNotNone(cache.get(TOPICS_CACHE_KEY))

    def test_home_page_shows_cache_source(self):
        Topic.objects.create(name="Процессы и потоки", slug="processes-and-threads")

        first_response = self.client.get(reverse("home"))
        second_response = self.client.get(reverse("home"))

        self.assertContains(first_response, "PostgreSQL")
        self.assertContains(second_response, "Valkey")
