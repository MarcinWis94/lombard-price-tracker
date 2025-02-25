from django.db import models


class Produkt(models.Model):
    produkt_id = models.CharField(primary_key=True, max_length=32)
    nazwa = models.CharField(max_length=255)
    cena = models.CharField(max_length=50)
    lokalizacja = models.CharField(max_length=255)
    stan = models.CharField(max_length=100)
    link = models.CharField(max_length=200)
    kategoria = models.CharField(max_length=100)
    data_pobrania = models.DateField()
    historia_cen = models.TextField(null=True, blank=True)


    def __str__(self):
        return self.nazwa

    class Meta:
        db_table = "produkty"