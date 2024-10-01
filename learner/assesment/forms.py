from django import forms
from .models import Answer

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text']

    def __init__(self, *args, **kwargs):
        self.question_id = kwargs.pop('question_id', None)
        super().__init__(*args, **kwargs)
        self.fields['answer_text'].label = f'Answer for Question {self.question_id}'
