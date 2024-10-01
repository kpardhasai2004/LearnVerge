from django.urls import path
from . import views
from assesment import views as views_assess
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.chat_view, name='chat_view'),
    path('calculator', views.calculator, name='calculator'),
    path('collections/create/', views.chat_collection_create_view, name='chat_collection_create'),
    path('collections/<int:collection_id>/', views.chat_view, name='chat_view'),
    path('collections/<int:collection_id>/delete/', views.chat_collection_delete_view, name='chat_collection_delete'),

    path('register/', views_assess.register, name='register'),
    path('login/', views_assess.CustomLoginView.as_view(), name='login'),
    path('logout/', views_assess.CustomLogoutView.as_view(), name='logout'),

    path('start/', views_assess.start_assessment, name='start_assessment'),
    path('take/<int:assessment_id>/', views_assess.take_assessment, name='take_assessment'),
    path('results/<int:assessment_id>/', views_assess.show_results, name='show_results'),
    path('analytics/', views_assess.view_analytics, name='view_analytics'),
]
