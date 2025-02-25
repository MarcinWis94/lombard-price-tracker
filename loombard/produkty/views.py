from django.shortcuts import render
from .models import Produkt
from django.db import connection

def lista_produktow(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM produkty")
        row = cursor.fetchone()
        print(f"🧐 Znaleziono {row[0]} produktów w bazie!")  # Sprawdź, ile produktów widzi Django
        
    produkty = Produkt.objects.all()
    return render(request, "lista_produktow.html", {"produkty": produkty})
    
from django.shortcuts import render
from .models import HistoriaCen, Produkt

def historia_cen(request, produkt_id):
    produkt = Produkt.objects.get(produkt_id=produkt_id)
    historia = HistoriaCen.objects.filter(produkt=produkt).order_by('-data_zmiany')
    return render(request, "historia_cen.html", {"produkt": produkt, "historia": historia})
