from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = (
        ('dosen', 'Dosen'),
        ('asisten', 'Asisten'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    
    def is_dosen(self):
        return self.role == 'dosen'
    
    def is_asisten(self):
        return self.role == 'asisten'

class Praktikum(models.Model):
    nama = models.CharField(max_length=100)
    kode = models.CharField(max_length=20)
    deskripsi = models.TextField(blank=True, null=True)
    tanggal = models.DateTimeField(auto_now_add=True)
    dosen = models.ForeignKey(User, on_delete=models.CASCADE, related_name='praktikum_dosen', limit_choices_to={'role': 'dosen'})
    
    def __str__(self):
        return f"{self.kode} - {self.nama}"
    
    class Meta:
        ordering = ['nama']
        verbose_name_plural = 'Praktikum'

class Jadwal(models.Model):
    HARI_CHOICES = (
        ('senin', 'Senin'),
        ('selasa', 'Selasa'),
        ('rabu', 'Rabu'),
        ('kamis', 'Kamis'),
        ('jumat', 'Jumat'),
        ('sabtu', 'Sabtu'),
    )

    RUANGAN_CHOICES = (
        ('IoT', 'IoT'),
        ('Start Up', 'Start Up'),
        ('Multimedia', 'Multimedia'),
        ('Microcontroller', 'Microcontroller'),
        ('Computer Vision', 'Computer Vision'),
        ('Networking', 'Networking'),
        ('Data Science', 'Data Science'),
    )
    
    praktikum = models.ForeignKey(Praktikum, on_delete=models.CASCADE)
    hari = models.CharField(max_length=10, choices=HARI_CHOICES)
    waktu_mulai = models.TimeField()
    waktu_selesai = models.TimeField()
    ruangan = models.CharField(max_length=50, choices=RUANGAN_CHOICES)
    dosen = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jadwal_dosen', limit_choices_to={'role': 'dosen'})
    asisten = models.ManyToManyField(User, related_name='jadwal_asisten', limit_choices_to={'role': 'asisten'})
    
    def __str__(self):
        return f"{self.praktikum} - {self.hari} ({self.waktu_mulai} - {self.waktu_selesai})"
    
    class Meta:
        ordering = ['hari', 'waktu_mulai']

class Mahasiswa(models.Model):
    nama = models.CharField(max_length=100)
    nim = models.CharField(max_length=20, unique=True)
    angkatan = models.CharField(max_length=10, default='2024')
    jadwal = models.ManyToManyField(Jadwal, blank=True, related_name='mahasiswa_set')
    dosen = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='mahasiswa_dosen', 
        limit_choices_to={'role': 'dosen'},
        null=True,  # Allow null temporarily for migration
        blank=True  # Allow blank temporarily for migration
    )
    
    def __str__(self):
        return f"{self.nim} - {self.nama}"
    
    class Meta:
        ordering = ['nim']

class Kehadiran(models.Model):
    jadwal = models.ForeignKey(Jadwal, on_delete=models.CASCADE)
    mahasiswa = models.ForeignKey(Mahasiswa, on_delete=models.CASCADE)
    tanggal = models.DateField(default=timezone.now)
    hadir = models.BooleanField(default=False)
    keterangan = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['jadwal', 'mahasiswa', 'tanggal']
        ordering = ['tanggal', 'jadwal']
    
    def __str__(self):
        status = "Hadir" if self.hadir else "Tidak Hadir"
        return f"{self.mahasiswa} - {self.jadwal} - {self.tanggal} - {status}"

class LaporanKerusakan(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Menunggu'),
        ('proses', 'Diproses'),
        ('selesai', 'Selesai'),
    )
    
    perangkat = models.CharField(max_length=100)
    deskripsi = models.TextField()
    ruangan = models.CharField(max_length=50)
    tanggal_laporan = models.DateTimeField(default=timezone.now)
    pelapor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'asisten'})
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return f"{self.perangkat} - {self.ruangan} - {self.status}"
    
    class Meta:
        ordering = ['-tanggal_laporan']
        verbose_name_plural = 'Laporan Kerusakan'

class JadwalPraktikum(models.Model):
    mata_kuliah = models.CharField(max_length=100)
    dosen = models.CharField(max_length=100)
    waktu = models.DateTimeField()