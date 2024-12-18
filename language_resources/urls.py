from django.urls import path

from . import views


app_name = 'dictionaries'


urlpatterns = [
    path('', views.fetch_word_data_from_openai, name='fetch_data'),
]