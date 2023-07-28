from django.urls import path
from mimir import views

urlpatterns = [
    path('knowledgeTree', views.buildKnowledgeTree, name='knowledgeTree'),
    path('card', views.createCard, name='cardCreate'),
    path('card/<int:card_id>', views.updateOrDeleteCard, name='cardUpdateOrDelete'),
    path('category', views.createCategory, name='categoryCreate'),
    path('category/<int:category_id>', views.updateOrDeleteCategory, name='categoryUpdateOrDelete'),
    path('review', views.reviewCard, name='reviewCard')
]