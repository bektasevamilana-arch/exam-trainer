from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from trainer.models import Choice, Question, Topic


SEED_DATA = [
    {
        "slug": "processes-and-threads",
        "name": "Процессы и потоки",
        "description": "Состояния процессов, переключение контекста и синхронизация потоков.",
        "questions": [
            {
                "key": "process-vs-thread",
                "text": "Чем процесс отличается от потока?",
                "choices": [
                    (
                        "У процесса своё адресное пространство, потоки одного процесса разделяют его",
                        True,
                    ),
                    ("Поток — это процесс, который не занимает память", False),
                    ("Процессы всегда выполняются быстрее потоков", False),
                    ("Поток не может обращаться к открытым файлам процесса", False),
                ],
                "explanation": (
                    "Процесс — единица владения ресурсами с отдельным адресным пространством. "
                    "Потоки являются единицами выполнения внутри процесса и разделяют его память и файлы."
                ),
            },
            {
                "key": "context-switch",
                "text": "Что происходит при переключении контекста между потоками одного процесса?",
                "choices": [
                    (
                        "Сохраняются регистры, стек и состояние потока; адресное пространство остаётся общим",
                        True,
                    ),
                    ("Создаётся новое адресное пространство для каждого потока", False),
                    ("ОС выгружает весь процесс на диск и загружает его заново", False),
                    ("Все потоки процесса принудительно завершаются", False),
                ],
                "explanation": (
                    "Потоки одного процесса используют одинаковую таблицу страниц, поэтому адресное пространство "
                    "не меняется. Сохраняются только регистры, указатель стека и данные планировщика потока."
                ),
            },
            {
                "key": "mutex",
                "text": "Для чего используется мьютекс?",
                "choices": [
                    (
                        "Чтобы в каждый момент времени к общему ресурсу имел доступ только один поток",
                        True,
                    ),
                    ("Чтобы увеличить приоритет потока", False),
                    ("Чтобы создать дополнительное адресное пространство", False),
                    ("Чтобы автоматически освободить всю память процесса", False),
                ],
                "explanation": (
                    "Мьютекс реализует взаимное исключение: поток захватывает его перед входом в критическую "
                    "секцию и освобождает после выхода, поэтому потоки не меняют общие данные одновременно."
                ),
            },
        ],
    },
    {
        "slug": "memory-management",
        "name": "Управление памятью",
        "description": "Виртуальная память, страницы и фрагментация.",
        "questions": [
            {
                "key": "lru",
                "text": "Какую страницу вытесняет стратегия LRU?",
                "choices": [
                    ("Ту, к которой дольше всего не обращались", True),
                    ("Ту, которая была загружена первой", False),
                    ("Самую большую по размеру", False),
                    ("Ту, которая хранится только в кэше процессора", False),
                ],
                "explanation": (
                    "LRU (Least Recently Used) опирается на локальность ссылок: страница, к которой давно не "
                    "обращались, с наименьшей вероятностью понадобится в ближайшее время."
                ),
            },
            {
                "key": "virtual-memory",
                "text": "В чём главная идея виртуальной памяти?",
                "choices": [
                    (
                        "У каждого процесса есть своё виртуальное адресное пространство, отображаемое в физическую память",
                        True,
                    ),
                    ("Вся память процесса постоянно хранится на диске", False),
                    ("Процессы используют физические адреса без преобразования", False),
                    ("ОС полностью отказывается от подкачки страниц", False),
                ],
                "explanation": (
                    "Виртуальная память отделяет адреса процесса от физических адресов. Таблица страниц и MMU "
                    "преобразуют виртуальные адреса, а при нехватке ОЗУ страницы могут выгружаться на диск."
                ),
            },
            {
                "key": "fragmentation",
                "text": "Что такое фрагментация памяти?",
                "choices": [
                    (
                        "Свободной памяти достаточно в сумме, но она разбита на мелкие несмежные участки",
                        True,
                    ),
                    ("Вся оперативная память занята одним процессом", False),
                    ("Процесс получил больше памяти, чем запросил", False),
                    ("Виртуальный адрес совпадает с физическим", False),
                ],
                "explanation": (
                    "При фрагментации суммарный объём свободной памяти есть, но нет одного непрерывного участка "
                    "нужного размера, поэтому запрос на выделение памяти может не выполниться."
                ),
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Загружает две темы и шесть демонстрационных вопросов (идемпотентно)."

    @transaction.atomic
    def handle(self, *args, **options):
        for topic_order, topic_data in enumerate(SEED_DATA, start=1):
            topic, _ = Topic.objects.update_or_create(
                slug=topic_data["slug"],
                defaults={
                    "name": topic_data["name"],
                    "description": topic_data["description"],
                    "order": topic_order,
                },
            )

            for order, question_data in enumerate(topic_data["questions"], start=1):
                choices = question_data["choices"]
                if len(choices) != 4:
                    raise CommandError(
                        f"В вопросе {question_data['key']!r} должно быть 4 варианта."
                    )
                if sum(1 for _, is_correct in choices if is_correct) != 1:
                    raise CommandError(
                        f"В вопросе {question_data['key']!r} должен быть ровно один верный вариант."
                    )

                question, _ = Question.objects.update_or_create(
                    topic=topic,
                    key=question_data["key"],
                    defaults={
                        "text": question_data["text"],
                        "explanation": question_data["explanation"],
                        "order": order,
                    },
                )

                kept_choice_ids = []
                for text, is_correct in choices:
                    choice, _ = Choice.objects.update_or_create(
                        question=question,
                        text=text,
                        defaults={"is_correct": is_correct},
                    )
                    kept_choice_ids.append(choice.pk)

                question.choices.exclude(pk__in=kept_choice_ids).delete()

        self.stdout.write(
            self.style.SUCCESS(
                "Загружены темы и вопросы: "
                f"{Topic.objects.count()} тем, "
                f"{Question.objects.count()} вопросов, "
                f"{Choice.objects.count()} вариантов ответа."
            )
        )
