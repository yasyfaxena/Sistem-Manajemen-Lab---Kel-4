from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import DataPraktikum, PerangkatInventaris, Kerusakan, Notifikasi
from .forms import PraktikumForm, PerangkatInventarisForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from labApp.models import Jadwal, Praktikum

# Logout
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Anda berhasil keluar dari sistem')
    return redirect('mylabapp:login')

# Login
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('mylabapp:dashboard')
        else:
            messages.error(request, 'Username atau password salah!')
    return render(request, 'mylabapp/login.html')


# Dashboard
@login_required
def dashboard(request):
    # Ambil jadwal praktikum dari labApp
    jadwal_list = Jadwal.objects.all().order_by('hari', 'waktu_mulai')
    
    # Hitung statistik
    jumlah_praktikum = DataPraktikum.objects.count()
    jumlah_inventaris = PerangkatInventaris.objects.count()
    jumlah_kerusakan_ditangani = Kerusakan.objects.filter(status='selesai').count()
    
    # Ambil riwayat kerusakan terbaru (5 data terakhir)
    riwayat_kerusakan = Kerusakan.objects.all().order_by('-tanggal_laporan')[:5]
    
    # Ambil notifikasi yang belum dibaca
    notifikasi = Notifikasi.objects.filter(dibaca=False).order_by('-tanggal')
    
    context = {
        'jadwal_list': jadwal_list,
        'jumlah_praktikum': jumlah_praktikum,
        'jumlah_inventaris': jumlah_inventaris,
        'jumlah_kerusakan_ditangani': jumlah_kerusakan_ditangani,
        'riwayat_kerusakan': riwayat_kerusakan,
        'notifikasi': notifikasi,
    }
    
    return render(request, 'mylabapp/dashboard.html', context)

# Data Praktikum
@login_required
def data_praktikum(request):
    # Hanya menampilkan data, tidak ada input manual
    data = DataPraktikum.objects.all().order_by('-created_at')
    return render(request, 'mylabapp/data_praktikum.html', {'data': data})


@login_required
def tambah_praktikum(request):
    if request.method == 'POST':
        form = PraktikumForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('mylabapp:data_praktikum')
    else:
        form = PraktikumForm()
    return render(request, 'mylabapp/forms_praktikum.html', {'form': form})


@login_required
def edit_praktikum(request, pk):
    praktikum = get_object_or_404(DataPraktikum, pk=pk)
    if request.method == 'POST':
        form = PraktikumForm(request.POST, instance=praktikum)
        if form.is_valid():
            form.save()
            return redirect('mylabapp:data_praktikum')
    else:
        form = PraktikumForm(instance=praktikum)
    return render(request, 'mylabapp/forms_praktikum.html', {'form': form})


@login_required
def hapus_praktikum(request, pk):
    praktikum = get_object_or_404(DataPraktikum, pk=pk)
    praktikum.delete()
    return redirect('mylabapp:data_praktikum')


# Halaman Lain
@login_required
def inventaris(request):
    data = PerangkatInventaris.objects.all()
    return render(request, 'mylabapp/inventaris.html', {'data': data})

def tambah_inventaris(request):
    if request.method == 'POST':
        nama = request.POST.get('nama')
        kondisi = request.POST.get('kondisi')
        lokasi = request.POST.get('lokasi')
        
        PerangkatInventaris.objects.create(
            nama=nama,
            kondisi=kondisi,
            lokasi=lokasi
        )
        messages.success(request, 'Data berhasil ditambahkan')
        return redirect('mylabapp:inventaris')
    return render(request, 'mylabapp/inventaris.html')

def edit_inventaris(request, id):
    data = PerangkatInventaris.objects.get(id=id)
    if request.method == 'POST':
        data.nama = request.POST.get('nama')
        data.kondisi = request.POST.get('kondisi')
        data.lokasi = request.POST.get('lokasi')
        data.save()
        messages.success(request, 'Data berhasil diupdate')
        return redirect('mylabapp:inventaris')
    return render(request, 'mylabapp/inventaris.html', {'data': data})

def inventaris_list(request):
    q = request.GET.get('q')
    data = PerangkatInventaris.objects.filter(nama__icontains=q) if q else PerangkatInventaris.objects.all()
    return render(request, 'mylabapp/inventaris.html', {'data': data})

@login_required
def set_kerusakan_selesai(request, pk):
    kerusakan = Kerusakan.objects.get(pk=pk)
    kerusakan.status = 'selesai'
    kerusakan.save()
    messages.success(request, 'Status kerusakan berhasil diupdate')
    return redirect('mylabapp:penanganan_kerusakan')

def set_kerusakan_batal(request, pk):
    kerusakan = Kerusakan.objects.get(pk=pk)
    kerusakan.status = 'batal'
    kerusakan.save()
    messages.success(request, 'Status kerusakan berhasil diupdate')
    return redirect('mylabapp:penanganan_kerusakan')

def penanganan_kerusakan(request):
    data = Kerusakan.objects.all().order_by('-tanggal_laporan')
    return render(request, 'mylabapp/penanganan_kerusakan.html', {'data': data})



@login_required
def laporan_view(request):
    data = Kerusakan.objects.all().order_by('-tanggal_laporan')
    return render(request, 'mylabapp/laporan.html', {'data': data})

@login_required
def hapus_inventaris(request, id):
    data = get_object_or_404(PerangkatInventaris, id=id)
    data.delete()
    messages.success(request, 'Data berhasil dihapus')
    return redirect('mylabapp:inventaris')

# Mark notification as read and redirect to penanganan kerusakan
@login_required
def mark_notification_read_and_redirect(request, pk):
    notification = get_object_or_404(Notifikasi, pk=pk)
    notification.dibaca = True
    notification.save()
    # Assuming there's a way to link notification to Kerusakan, perhaps via message content or a new field
    # For now, we will just redirect to the penanganan_kerusakan page.
    # A more robust solution might involve creating a Kerusakan object here if one doesn't exist
    messages.success(request, 'Notifikasi ditandai sudah dibaca.')
    return redirect('mylabapp:penanganan_kerusakan')
