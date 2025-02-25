from django.urls import path
from .views import lista_produktow

urlpatterns = [
    path('', lista_produktow, name='lista_produktow'),
]