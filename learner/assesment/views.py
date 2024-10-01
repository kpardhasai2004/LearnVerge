from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Topic, Assessment, Question, Answer
from .forms import AnswerForm  # Form for submitting answers
from django.contrib.auth.decorators import login_required
import requests  # For calling the Gemini API
import os
import google.generativeai as genai
from dotenv import load_dotenv
import typing_extensions as typing
import json
import re
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)




def call_gemini_api(file: None, topic: str, difficulty: str, num_questions: int = 10):
    # Initialize the Gemini GenerativeModel
    model = genai.GenerativeModel("gemini-1.5-pro-latest")

    # Define the prompt based on the topic, difficulty, and number of questions
    prompt = f"""
    Generate {num_questions} high-quality, topic-related questions based on the subject "{topic}".
    The difficulty level of the questions should be {difficulty}. Avoid using weak language; instead, ensure all questions are clearly framed and concise.
    Do not use double quotes inside sentences. Instead, emphasize key terms by making them strong using alternative formatting."""+"""
    
    Use this JSON schema:
    Questions = [{"question": str, "correct_answer": str}]
    Return Questions"""

    if file:
        temp_file_path = os.path.join(settings.MEDIA_ROOT, file.name)
        with open(temp_file_path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)
        genfile = genai.upload_file(temp_file_path)
        result = model.generate_content([genfile, prompt])
        os.remove(temp_file_path)
        genfile.delete()
    else:
        result = model.generate_content(prompt)

    clean_response = result.text.replace("Questions = ", "").replace("json","").replace("```python", "").replace("```", "").replace("    ", "").replace("\n", "").replace("\t", "")


    print(clean_response)
    return clean_response

def parse_markdown(text):
    # Convert Markdown to HTML
    text = re.sub(r'###### (.*?)\n', r'\n<h6>\1</h6>\n', text)
    text = re.sub(r'##### (.*?)\n', r'\n<h5>\1</h5>\n', text)
    text = re.sub(r'#### (.*?)\n', r'\n<h4>\1</h4>\n', text)
    text = re.sub(r'### (.*?)\n', r'\n<h3>\1</h3>\n', text)
    text = re.sub(r'## (.*?)\n', r'\n<h2>\1</h2>\n', text)
    text = re.sub(r'# (.*?)\n', r'\n<h1>\1</h1>\n', text)
    text = re.sub(r'\*\*(.*?)\*\*|__(.*?)__', r'<strong>\1\2</strong>', text)
    text = re.sub(r'\*(.*?)\*|_(.*?)_', r'<em>\1\2</em>', text)
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    text = re.sub(r'\n\n+', r'<br><br>', text)
    return text

@login_required
def start_assessment(request):
    if request.method == 'POST':
        topic_name = request.POST['topic']
        difficulty = request.POST['difficulty']
        num_questions = 10
        uploaded_file = request.FILES.get('file')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        questions_data = json.loads(call_gemini_api(uploaded_file, topic.name, difficulty, num_questions))

        assessment = Assessment.objects.create(
            user=request.user,
            topic=topic,
            difficulty=difficulty
        )

        for question_data in questions_data:
            Question.objects.create(
                assessment=assessment,
                text=parse_markdown(question_data['question']),
                correct_answer=parse_markdown(question_data['correct_answer'])
            )

        return redirect('take_assessment', assessment_id=assessment.id)

    return render(request, 'start_assessment.html')


@login_required
def take_assessment(request, assessment_id):
    assessment = Assessment.objects.get(id=assessment_id)
    questions = assessment.questions.all()
    
    if request.method == 'POST':
        for question in questions:
            answer_text = request.POST.get(f'answer_{question.id}')
            is_correct = (answer_text == question.correct_answer)
            Answer.objects.create(question=question, user=request.user, answer_text=answer_text, is_correct=is_correct)
        
        correct_answers = Answer.objects.filter(question__assessment=assessment, is_correct=True).count()
        total_questions = questions.count()
        assessment.score = (correct_answers / total_questions) * 100
        assessment.save()
        
        return redirect('show_results', assessment_id=assessment.id)
    
    return render(request, 'take_assessment.html', {'questions': questions, 'assessment' : assessment })

@login_required
def show_results(request, assessment_id):
    assessment = Assessment.objects.get(id=assessment_id)
    return render(request, 'show_results.html', {'assessment': assessment})

@login_required
def view_analytics(request):
    assessments = Assessment.objects.filter(user=request.user)
    
    topic_performance = {}
    for assessment in assessments:
        if assessment.topic.name not in topic_performance:
            topic_performance[assessment.topic.name] = {'total': 0, 'count': 0}
        
        score = assessment.score if assessment.score is not None else 0
        topic_performance[assessment.topic.name]['total'] += score
        topic_performance[assessment.topic.name]['count'] += 1
    
    for topic, data in topic_performance.items():
        topic_performance[topic]['average_score'] = data['total'] / data['count']
    
    return render(request, 'view_analytics.html', {'topic_performance': topic_performance})

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password == confirm_password:
            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                messages.success(request, 'Registration successful. You can now log in.')
                return redirect('login')
            except Exception as e:
                messages.error(request, 'Registration failed: {}'.format(e))
        else:
            messages.error(request, 'Passwords do not match.')
    
    return render(request, 'register.html')

class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('chat_view')


class CustomLogoutView(LogoutView):
    next_page = 'login'