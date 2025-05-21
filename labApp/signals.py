from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Praktikum, LaporanKerusakan
from mylabapp.models import DataPraktikum, Notifikasi, Kerusakan, PerangkatInventaris

@receiver(post_save, sender=Praktikum)
def create_data_praktikum(sender, instance, created, **kwargs):
    """
    Signal untuk menyimpan data praktikum ke mylabapp saat praktikum dibuat di labApp
    """
    if created:
        DataPraktikum.objects.create(
            nama=instance.nama,
            kode=instance.kode,
            deskripsi=instance.deskripsi or ''
        )