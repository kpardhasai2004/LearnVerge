from django.contrib import admin

# Register your models here.
from .models import Answer, Question, Assessment, Topic
admin.site.register(Answer)
admin.site.register(Question)
admin.site.register(Assessment)
admin.site.register(Topic)