from django.shortcuts import render
from .models import Produkt
from django.db import connection

def lista_produktow(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM produkty_produkt")
        row = cursor.fetchone()
        print(f"🧐 Znaleziono {row[0]} produktów w bazie!")  # Sprawdź, ile produktów widzi Django
        
    produkty = Produkt.objects.all()
    return render(request, "lista_produktow.html", {"produkty": produkty})