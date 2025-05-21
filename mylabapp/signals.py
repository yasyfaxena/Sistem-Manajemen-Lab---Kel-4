from django.db.models.signals import post_save
from django.dispatch import receiver
from labApp.models import Praktikum, LaporanKerusakan
from .models import DataPraktikum, Notifikasi, Kerusakan
from django.utils import timezone

@receiver(post_save, sender=Praktikum)
def sync_praktikum_to_mylabapp(sender, instance, created, **kwargs):
    """
    Signal handler untuk menyinkronkan data praktikum dari labApp ke mylabapp
    """
    if created:
        # Buat data praktikum baru di mylabapp
        DataPraktikum.objects.create(
            nama=instance.nama,
            kode=instance.kode,
            deskripsi=instance.deskripsi or '',
            dosen_pengampu=f"{instance.dosen.first_name} {instance.dosen.last_name}".strip() or instance.dosen.username
        )
    else:
        # Update data praktikum yang sudah ada
        try:
            data_praktikum = DataPraktikum.objects.get(kode=instance.kode)
            data_praktikum.nama = instance.nama
            data_praktikum.deskripsi = instance.deskripsi or ''
            data_praktikum.dosen_pengampu = f"{instance.dosen.first_name} {instance.dosen.last_name}".strip() or instance.dosen.username
            data_praktikum.save()
        except DataPraktikum.DoesNotExist:
            # Jika data tidak ditemukan, buat baru
            DataPraktikum.objects.create(
                nama=instance.nama,
                kode=instance.kode,
                deskripsi=instance.deskripsi or '',
                dosen_pengampu=f"{instance.dosen.first_name} {instance.dosen.last_name}".strip() or instance.dosen.username
            )

@receiver(post_save, sender='labApp.LaporanKerusakan')
def handle_laporan_kerusakan(sender, instance, created, **kwargs):
    """
    Signal untuk menangani laporan kerusakan:
    1. Membuat notifikasi di mylabapp
    2. Membuat entri kerusakan di mylabapp dengan status 'pending'
    """
    if created:
        # Buat notifikasi
        Notifikasi.objects.create(
            pesan=f"Laporan kerusakan baru: Perangkat {instance.perangkat} di {instance.ruangan}. Deskripsi: {instance.deskripsi}",
            dibaca=False
        )
        
        # Buat entri kerusakan
        Kerusakan.objects.create(
            nama_perangkat=instance.perangkat,
            ruangan=instance.ruangan,
            deskripsi=instance.deskripsi,
            tanggal_laporan=instance.tanggal_laporan,
            status='pending'
        )
    else:
        # Update existing Kerusakan record
        try:
            kerusakan = Kerusakan.objects.filter(
                nama_perangkat=instance.perangkat,
                tanggal_laporan=instance.tanggal_laporan
            ).first()
            
            if kerusakan:
                kerusakan.deskripsi = instance.deskripsi
                if instance.status == 'selesai':
                    kerusakan.status = 'selesai'
                    kerusakan.tanggal_selesai = timezone.now()
                elif instance.status == 'batal':
                    kerusakan.status = 'batal'
                kerusakan.save()
        except Exception as e:
            print(f"Error updating Kerusakan from LaporanKerusakan signal: {e}")

@receiver(post_save, sender='mylabapp.Kerusakan')
def sync_laporan_kerusakan(sender, instance, created, **kwargs):
    """Sync Kerusakan to LaporanKerusakan"""
    from labApp.models import LaporanKerusakan
    
    try:
        laporan = LaporanKerusakan.objects.filter(
            perangkat=instance.nama_perangkat,
            tanggal_laporan=instance.tanggal_laporan
        ).first()
        
        if laporan:
            laporan.deskripsi = instance.deskripsi
            if instance.status == 'selesai':
                laporan.status = 'selesai'
            elif instance.status == 'batal':
                laporan.status = 'batal'
            laporan.save()
    except Exception as e:
        print(f"Error updating LaporanKerusakan from Kerusakan signal: {e}")