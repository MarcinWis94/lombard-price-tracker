from django.db import models


class Produkt(models.Model):
    produkt_id = models.CharField(max_length=255, primary_key=True)
    nazwa = models.CharField(max_length=255)
    cena = models.CharField(max_length=50)
    lokalizacja = models.CharField(max_length=255)
    stan = models.CharField(max_length=100)
    link = models.URLField()
    kategoria = models.CharField(max_length=100)
    data_pobrania = models.DateField()


    def __str__(self):
        return self.nazwa

    class Meta:
        db_table = "produkty"
        

class HistoriaCen(models.Model):
    produkt = models.ForeignKey(Produkt, on_delete=models.CASCADE)
    cena = models.CharField(max_length=50)
    data_zmiany = models.DateField()
