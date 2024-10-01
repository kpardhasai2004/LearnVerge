from django.shortcuts import render, redirect, get_object_or_404
from .models import Chat, ChatCollection
from .forms import ChatCollectionForm
import google.generativeai as genai
import os
import re
import pathlib
from django.conf import settings
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

def generate(prompt, file):
    if file:
        temp_file_path = os.path.join(settings.MEDIA_ROOT, file.name)
        with open(temp_file_path, 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)

        # Upload file to Gemini and generate content
        genfile = genai.upload_file(temp_file_path)
        response = genai.GenerativeModel(model_name="gemini-1.5-pro").generate_content([genfile, prompt])

        # Clean up uploaded file
        os.remove(temp_file_path)
        genfile.delete()
    else:
        # Generate response with only prompt
        response = genai.GenerativeModel(model_name="gemini-1.5-pro").generate_content(prompt)
    
    return parse_markdown(response.text)

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

def chat_view(request, collection_id=None):
    collections = ChatCollection.objects.all()
    chatCollectionForm = ChatCollectionForm()

    if collection_id:
        collection = get_object_or_404(ChatCollection, id=collection_id)
        chats = collection.chats.all().order_by('created_at')

        if request.method == 'POST':
            # Handle chat creation
            user_prompt = request.POST.get('prompt')
            uploaded_file = request.FILES.get('file')
            response_text = generate(user_prompt, uploaded_file)

            Chat.objects.create(
                collection=collection,
                user_input=user_prompt,
                response=response_text
            )
            return redirect('chat_view', collection_id=collection_id)

        return render(request, 'chat.html', {
            'collection': collection,
            'chats': chats,
            'collections': collections
        })

    # Handle creating a new collection via POST
    if request.method == 'POST':
        chatCollectionForm = ChatCollectionForm(request.POST)
        if chatCollectionForm.is_valid():
            new_collection = chatCollectionForm.save()
            return redirect('chat_view', collection_id=new_collection.id)

    return render(request, 'chat_collection_list.html', {
        'collections': collections,
        'chatCollectionForm': chatCollectionForm
    })

def chat_collection_create_view(request, collection_id=None):
    if request.method == 'POST':
        collection_name = request.POST.get('collectionName')
        if collection_id:
            collection = get_object_or_404(ChatCollection, id=collection_id)
            collection.name = collection_name
            collection.save()
            return redirect('chat_view', collection_id=collection_id)
        else:
            new_collection = ChatCollection.objects.create(name=collection_name)
            return redirect('chat_view', collection_id=new_collection.id)

    return redirect('chat_view')

def chat_collection_delete_view(request, collection_id):
    collection = get_object_or_404(ChatCollection, id=collection_id)
    if request.method == 'POST':
        collection.delete()
        return redirect('chat_view')

def calculator(request):
    return render(request, 'calculator.html')
