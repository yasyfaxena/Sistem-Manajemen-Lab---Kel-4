from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from labApp.models import Praktikum

class PerangkatInventaris(models.Model):
    nama = models.CharField(max_length=100)
    kondisi = models.CharField(max_length=50)
    lokasi = models.CharField(max_length=100)

    def __str__(self):
        return self.nama
    
class Kerusakan(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('selesai', 'Selesai'),
        ('batal', 'Batal')
    ]
    
    nama_perangkat = models.CharField(max_length=100, default='Perangkat Tidak Diketahui')
    ruangan = models.CharField(max_length=50, default='Ruangan Tidak Diketahui')
    deskripsi = models.TextField(default='')
    tanggal_laporan = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tanggal_selesai = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Kerusakan {self.nama_perangkat} - {self.status}"
    
class DataPraktikum(models.Model):
    praktikum = models.OneToOneField(Praktikum, on_delete=models.CASCADE, related_name='data_praktikum', null=True, blank=True)
    nama = models.CharField(max_length=100)
    kode = models.CharField(max_length=20)
    deskripsi = models.TextField(blank=True, null=True)
    dosen_pengampu = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.kode} - {self.nama}"

    class Meta:
        ordering = ['kode']
        verbose_name_plural = 'Data Praktikum'

    @classmethod
    def sync_with_praktikum(cls):
        """Metode untuk menyinkronkan data dengan Praktikum"""
        from labApp.models import Praktikum
        
        # Hapus semua DataPraktikum yang ada
        deleted_count = cls.objects.all().delete()[0]
        print(f"Deleted {deleted_count} existing DataPraktikum records")
        
        # Buat ulang DataPraktikum untuk setiap Praktikum
        created_count = 0
        for praktikum in Praktikum.objects.all():
            try:
                cls.objects.create(
                    praktikum=praktikum,
                    nama=praktikum.nama,
                    kode=praktikum.kode,
                    deskripsi=praktikum.deskripsi,
                    dosen_pengampu=praktikum.dosen.get_full_name() if praktikum.dosen else None
                )
                created_count += 1
                print(f"Created DataPraktikum for {praktikum.kode} - {praktikum.nama}")
            except Exception as e:
                print(f"Error creating DataPraktikum for {praktikum.kode}: {str(e)}")
        
        print(f"Successfully created {created_count} DataPraktikum records")

@receiver(post_save, sender=Praktikum)
def create_data_praktikum(sender, instance, created, **kwargs):
    if created:
        try:
            DataPraktikum.objects.create(
                praktikum=instance,
                nama=instance.nama,
                kode=instance.kode,
                deskripsi=instance.deskripsi,
                dosen_pengampu=instance.dosen.get_full_name() if instance.dosen else None
            )
        except Exception as e:
            print(f"Error creating DataPraktikum for {instance.kode}: {str(e)}")

@receiver(post_save, sender=Praktikum)
def update_data_praktikum(sender, instance, created, **kwargs):
    if not created:
        try:
            data_praktikum = DataPraktikum.objects.get(praktikum=instance)
            data_praktikum.nama = instance.nama
            data_praktikum.kode = instance.kode
            data_praktikum.deskripsi = instance.deskripsi
            data_praktikum.dosen_pengampu = instance.dosen.get_full_name() if instance.dosen else None
            data_praktikum.save()
        except DataPraktikum.DoesNotExist:
            DataPraktikum.objects.create(
                praktikum=instance,
                nama=instance.nama,
                kode=instance.kode,
                deskripsi=instance.deskripsi,
                dosen_pengampu=instance.dosen.get_full_name() if instance.dosen else None
            )
        except Exception as e:
            print(f"Error updating DataPraktikum for {instance.kode}: {str(e)}")

class Notifikasi(models.Model):
    pesan = models.TextField()
    tanggal = models.DateTimeField(auto_now_add=True)
    dibaca = models.BooleanField(default=False)

    def __str__(self):
        return self.pesan

class Pengguna(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    is_admin = models.BooleanField(default=False)
    tanggal_bergabung = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
