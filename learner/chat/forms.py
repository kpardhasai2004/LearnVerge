from django import forms
from .models import ChatCollection

class ChatCollectionForm(forms.ModelForm):
    class Meta:
        model = ChatCollection
        fields = ['name']  # Form to edit the collection name

class UploadFileForm(forms.Form):
    file = forms.FileField(required=False)
