from django import forms


class QuizForm(forms.Form):
    """A dynamically built form: one required radio group per question."""

    def __init__(self, *args, questions=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.questions = list(questions)

        for question in self.questions:
            choices = [("", "Выберите вариант")]
            choices.extend(
                (str(choice.pk), choice.text) for choice in question.choices.all()
            )
            self.fields[f"question_{question.pk}"] = forms.ChoiceField(
                label=question.text,
                choices=choices,
                required=True,
                error_messages={"required": "Ответьте на этот вопрос."},
                widget=forms.RadioSelect(attrs={"class": "answer-radio"}),
            )
