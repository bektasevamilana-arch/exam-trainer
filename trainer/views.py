from django.shortcuts import get_object_or_404, render

from .forms import QuizForm
from .models import Topic
from .services import get_topics


def home(request):
    topics, topics_source = get_topics()
    return render(
        request,
        "trainer/home.html",
        {"topics": topics, "topics_source": topics_source},
    )


def quiz(request, slug):
    topic = get_object_or_404(
        Topic.objects.prefetch_related("questions__choices"), slug=slug
    )
    questions = list(topic.questions.all())

    if request.method == "POST":
        form = QuizForm(request.POST, questions=questions)
        if form.is_valid():
            results = []
            score = 0

            for question in questions:
                choices = list(question.choices.all())
                selected = next(
                    choice
                    for choice in choices
                    if choice.pk == int(form.cleaned_data[f"question_{question.pk}"])
                )
                correct = next(choice for choice in choices if choice.is_correct)
                is_correct = selected.is_correct
                if is_correct:
                    score += 1

                results.append(
                    {
                        "question_text": question.text,
                        "selected_text": selected.text,
                        "correct_text": correct.text,
                        "explanation": question.explanation,
                        "is_correct": is_correct,
                    }
                )

            return render(
                request,
                "trainer/result.html",
                {
                    "topic": topic,
                    "score": score,
                    "total": len(questions),
                    "results": results,
                },
            )
    else:
        form = QuizForm(questions=questions)

    return render(
        request,
        "trainer/quiz.html",
        {"topic": topic, "form": form, "questions": questions},
    )
