from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.forms import formset_factory
from django.views.decorators.csrf import csrf_protect
from .models import Mahasiswa, Jadwal, Kehadiran, Praktikum, LaporanKerusakan, User

from .forms import (
    UserLoginForm, UserRegisterForm, JadwalForm, KehadiranForm, 
    LaporanKerusakanForm, PraktikumForm, MahasiswaForm, KehadiranBulkForm, KehadiranFilterForm,
    KehadiranFormSet
)

@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect('labApp:dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('labApp:dashboard')
    else:
        form = UserLoginForm()
    
    return render(request, 'labApp/login.html', {'form': form})

@csrf_protect
def register_view(request):
    if request.user.is_authenticated:
        return redirect('labApp:dashboard')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, 'Akun berhasil dibuat! Silahkan login.')
                return redirect('labApp:login')
            except IntegrityError:
                messages.error(request, 'Akun dengan username tersebut sudah terdaftar. Silahkan login.')
                return redirect('labApp:login')
    else:
        form = UserRegisterForm()
    
    return render(request, 'labApp/register.html', {'form': form})

@csrf_protect
def logout_view(request):
    logout(request)
    return redirect('labApp:login')

@login_required
def dashboard_view(request):
    user = request.user
    context = {
        'user': user,
    }
    
    if user.is_dosen():
        jadwal_list = Jadwal.objects.filter(dosen=user)
        context['jadwal_list'] = jadwal_list
    elif user.is_asisten():
        jadwal_list = Jadwal.objects.filter(asisten=user)
        laporan_list = LaporanKerusakan.objects.filter(pelapor=user)
        context['jadwal_list'] = jadwal_list
        context['laporan_list'] = laporan_list
    
    return render(request, 'labApp/dashboard.html', context)

# Jadwal Views
@login_required
def jadwal_list(request):
    if not (request.user.is_dosen() or request.user.is_asisten()):
        messages.error(request, 'Anda tidak memiliki izin untuk melihat jadwal.')
        return redirect('labApp:dashboard')
    
    # Filter jadwal berdasarkan role user
    if request.user.is_dosen():
        jadwal_list = Jadwal.objects.filter(dosen=request.user).select_related('praktikum', 'dosen')
    else:  # asisten
        jadwal_list = Jadwal.objects.filter(asisten=request.user).select_related('praktikum', 'dosen')
    
    context = {
        'jadwal_list': jadwal_list,
    }
    
    # Gunakan template yang berbeda untuk asisten
    template = 'dosen/jadwal.html' if request.user.is_dosen() else 'asisten/jadwal.html'
    return render(request, template, context)

@login_required
@csrf_protect
def jadwal_create(request):
    if not request.user.is_dosen():
        messages.error(request, 'Anda tidak memiliki izin untuk membuat jadwal.')
        return redirect('labApp:jadwal_list')
    
    if request.method == 'POST':
        form = JadwalForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                jadwal = form.save(commit=False)
                jadwal.dosen = request.user  # Set dosen ke user yang login
                jadwal.save()
                form.save_m2m()  # Simpan relasi many-to-many
                messages.success(request, 'Jadwal berhasil dibuat!')
                return redirect('labApp:jadwal_list')
            except Exception as e:
                messages.error(request, f'Terjadi kesalahan: {str(e)}')
    else:
        form = JadwalForm(user=request.user)
    
    return render(request, 'dosen/jadwal_form.html', {'form': form, 'title': 'Tambah Jadwal'})

@login_required
@csrf_protect
def jadwal_update(request, pk):
    if not request.user.is_dosen():
        messages.error(request, 'Anda tidak memiliki izin untuk mengubah jadwal.')
        return redirect('labApp:jadwal_list')
    
    # Tambahkan filter untuk memastikan jadwal milik dosen yang login
    jadwal = get_object_or_404(Jadwal, pk=pk, dosen=request.user)
    
    if request.method == 'POST':
        form = JadwalForm(request.POST, instance=jadwal, user=request.user)
        if form.is_valid():
            try:
                jadwal = form.save(commit=False)
                jadwal.dosen = request.user  # Pastikan dosen tetap sama
                jadwal.save()
                form.save_m2m()
                messages.success(request, 'Jadwal berhasil diperbarui!')
                return redirect('labApp:jadwal_list')
            except Exception as e:
                messages.error(request, f'Terjadi kesalahan: {str(e)}')
    else:
        form = JadwalForm(instance=jadwal, user=request.user)
    
    return render(request, 'dosen/jadwal_form.html', {'form': form, 'title': 'Edit Jadwal'})

@login_required
@csrf_protect
def jadwal_delete(request, pk):
    if not request.user.is_dosen():
        messages.error(request, 'Anda tidak memiliki izin untuk menghapus jadwal.')
        return redirect('labApp:jadwal_list')
    
    # Tambahkan filter untuk memastikan jadwal milik dosen yang login
    jadwal = get_object_or_404(Jadwal, pk=pk, dosen=request.user)
    
    if request.method == 'POST':
        try:
            jadwal.delete()
            messages.success(request, 'Jadwal berhasil dihapus!')
        except Exception as e:
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
        return redirect('labApp:jadwal_list')
    
    return render(request, 'dosen/jadwal_confirm_delete.html', {'jadwal': jadwal})

# Kehadiran Views
@login_required
def kehadiran_list(request):
    user = request.user
    
    if user.is_dosen():
        jadwal_list = Jadwal.objects.filter(dosen=user)
    else:
        jadwal_list = Jadwal.objects.filter(asisten=user)
    
    jadwal_id = request.GET.get('jadwal')
    tanggal = request.GET.get('tanggal', timezone.now().date())
    
    if jadwal_id:
        jadwal = get_object_or_404(Jadwal, pk=jadwal_id)
        kehadiran_list = Kehadiran.objects.filter(jadwal=jadwal, tanggal=tanggal).select_related('mahasiswa', 'jadwal')
    else:
        kehadiran_list = []
    
    context = {
        'jadwal_list': jadwal_list,
        'kehadiran_list': kehadiran_list,
        'selected_jadwal': jadwal_id,
        'selected_tanggal': tanggal,
    }
    
    template = 'dosen/kehadiran.html' if user.is_dosen() else 'asisten/kehadiran.html'
    return render(request, template, context)

@login_required
@csrf_protect
def kehadiran_bulk_create(request):
    if request.method == 'POST':
        form = KehadiranBulkForm(request.POST)
        if form.is_valid():
            jadwal = form.cleaned_data['jadwal']
            tanggal = form.cleaned_data['tanggal']
            
            # Verifikasi akses
            if request.user.is_dosen() and jadwal.dosen != request.user:
                messages.error(request, 'Anda tidak memiliki izin untuk mengelola kehadiran jadwal ini.')
                return redirect('labApp:kehadiran_list')
            
            if request.user.is_asisten() and request.user not in jadwal.asisten.all():
                messages.error(request, 'Anda tidak memiliki izin untuk mengelola kehadiran jadwal ini.')
                return redirect('labApp:kehadiran_list')
            
            # Proses kehadiran
            for mahasiswa in jadwal.mahasiswa.all():
                status = form.cleaned_data.get(f'status_{mahasiswa.id}')
                if status:
                    Kehadiran.objects.update_or_create(
                        jadwal=jadwal,
                        mahasiswa=mahasiswa,
                        tanggal=tanggal,
                        defaults={'status': status}
                    )
            
            messages.success(request, 'Data kehadiran berhasil disimpan!')
            return redirect('labApp:kehadiran_list')
    else:
        form = KehadiranBulkForm()
    
    return render(request, 'dosen/kehadiran_bulk_form.html', {'form': form})

# Laporan Kerusakan Views (Khusus Asisten)
@login_required
def laporan_list(request):
    if not request.user.is_asisten():
        messages.error(request, 'Anda tidak memiliki izin untuk mengakses halaman ini.')
        return redirect('dashboard')
    
    laporan_list = LaporanKerusakan.objects.filter(pelapor=request.user)
    
    return render(request, 'asisten/laporan.html', {'laporan_list': laporan_list})

@login_required
@csrf_protect
def laporan_create(request):
    if not request.user.is_asisten():
        messages.error(request, 'Anda tidak memiliki izin untuk membuat laporan.')
        return redirect('labApp:laporan_list')
    
    if request.method == 'POST':
        form = LaporanKerusakanForm(request.POST)
        if form.is_valid():
            laporan = form.save(commit=False)
            laporan.pelapor = request.user
            laporan.save()
            messages.success(request, 'Laporan berhasil dibuat!')
            return redirect('labApp:laporan_list')
    else:
        form = LaporanKerusakanForm()
    
    return render(request, 'asisten/laporan_form.html', {'form': form, 'title': 'Tambah Laporan'})

@login_required
@csrf_protect
def laporan_update(request, pk):
    if not request.user.is_asisten():
        messages.error(request, 'Anda tidak memiliki izin untuk mengubah laporan.')
        return redirect('labApp:laporan_list')
    
    laporan = get_object_or_404(LaporanKerusakan, pk=pk)
    
    if laporan.pelapor != request.user:
        messages.error(request, 'Anda tidak memiliki izin untuk mengubah laporan ini.')
        return redirect('labApp:laporan_list')
    
    if request.method == 'POST':
        form = LaporanKerusakanForm(request.POST, instance=laporan)
        if form.is_valid():
            form.save()
            messages.success(request, 'Laporan berhasil diperbarui!')
            return redirect('labApp:laporan_list')
    else:
        form = LaporanKerusakanForm(instance=laporan)
    
    return render(request, 'asisten/laporan_form.html', {'form': form, 'title': 'Edit Laporan'})

@login_required
@csrf_protect
def laporan_delete(request, pk):
    if not request.user.is_asisten():
        messages.error(request, 'Anda tidak memiliki izin untuk menghapus laporan.')
        return redirect('labApp:laporan_list')
    
    laporan = get_object_or_404(LaporanKerusakan, pk=pk)
    
    if laporan.pelapor != request.user:
        messages.error(request, 'Anda tidak memiliki izin untuk menghapus laporan ini.')
        return redirect('labApp:laporan_list')
    
    if request.method == 'POST':
        laporan.delete()
        messages.success(request, 'Laporan berhasil dihapus!')
        return redirect('labApp:laporan_list')
    
    return render(request, 'asisten/laporan_confirm_delete.html', {'laporan': laporan})

# Praktikum Views
@login_required
def praktikum_list(request):
    if not request.user.is_dosen():
        messages.error(request, 'Anda tidak memiliki izin untuk mengakses halaman ini.')
        return redirect('labApp:dashboard')
    
    try:
        # Filter praktikum berdasarkan dosen yang login
        praktikum_list = Praktikum.objects.filter(dosen=request.user).order_by('kode')
        for m in messages.get_messages(request):
            print("DEBUG: message di-render:", m)
        return render(request, 'dosen/praktikum.html', {'praktikum_list': praktikum_list})
    except Exception as e:
        print(f"Error in praktikum_list: {str(e)}")
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
        return redirect('labApp:dashboard')

@login_required
@csrf_protect
def praktikum_create(request):
    if not request.user.is_dosen():
        messages.error(request, 'Anda tidak memiliki izin untuk membuat praktikum.')
        return redirect('labApp:dashboard')
    
    if request.method == 'POST':
        form = PraktikumForm(request.POST)
        if form.is_valid():
            try:
                praktikum = form.save(commit=False)
                praktikum.dosen = request.user
                praktikum.save()
                messages.success(request, 'Praktikum berhasil ditambahkan.')
                return redirect('labApp:praktikum_list')
                print("DEBUG: message ditambahkan")
            except Exception as e:
                messages.error(request, f'Error in praktikum_create: {str(e)}')
                return redirect('labApp:praktikum_list')
    else:
        form = PraktikumForm()
    return render(request, 'dosen/praktikum_form.html', {'form': form})

@login_required
@csrf_protect
def praktikum_update(request, pk):
    if not request.user.is_dosen():
        messages.error(request, 'Anda tidak memiliki izin untuk mengubah praktikum.')
        return redirect('labApp:dashboard')
    
    try:
        # Tambahkan filter untuk memastikan praktikum milik dosen yang login
        praktikum = get_object_or_404(Praktikum, pk=pk, dosen=request.user)
        
        if request.method == 'POST':
            form = PraktikumForm(request.POST, instance=praktikum)
            if form.is_valid():
                form.save()
                messages.success(request, 'Praktikum berhasil diperbarui!')
                return redirect('labApp:praktikum_list')
            else:
                print(f"Form errors: {form.errors}")
                messages.error(request, 'Terjadi kesalahan. Silakan periksa form Anda.')
        else:
            form = PraktikumForm(instance=praktikum)
        
        return render(request, 'dosen/praktikum_form.html', {'form': form, 'title': 'Edit Praktikum'})
    except Praktikum.DoesNotExist:
        messages.error(request, 'Praktikum tidak ditemukan atau Anda tidak memiliki akses.')
        return redirect('labApp:praktikum_list')
    except Exception as e:
        print(f"Error in praktikum_update: {str(e)}")
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
        return redirect('labApp:praktikum_list')

@login_required
def praktikum_delete(request, pk):
    if not request.user.is_dosen():
        messages.error(request, 'Anda tidak memiliki izin untuk menghapus praktikum.')
        return redirect('labApp:dashboard')
    
    try:
        # Tambahkan filter untuk memastikan praktikum milik dosen yang login
        praktikum = get_object_or_404(Praktikum, pk=pk, dosen=request.user)
        
        if request.method == 'POST':
            try:
                praktikum.delete()
                messages.success(request, 'Praktikum berhasil dihapus!')
            except Exception as e:
                print(f"Error deleting praktikum: {str(e)}")
                messages.error(request, f'Gagal menghapus praktikum. Error: {str(e)}')
            return redirect('labApp:praktikum_list')
        
        return render(request, 'dosen/praktikum_confirm_delete.html', {'praktikum': praktikum})
    except Praktikum.DoesNotExist:
        messages.error(request, 'Praktikum tidak ditemukan atau Anda tidak memiliki akses.')
        return redirect('labApp:praktikum_list')
    except Exception as e:
        print(f"Error in praktikum_delete: {str(e)}")
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
        return redirect('labApp:praktikum_list')

@login_required
def mahasiswa_list(request):
    if not request.user.is_dosen():
        messages.error(request, 'Anda tidak memiliki izin untuk melihat daftar mahasiswa.')
        return redirect('dashboard')
    
    search_query = request.GET.get('search', '')
    jadwal_filter = request.GET.get('jadwal', '')
    
    # Filter mahasiswa berdasarkan dosen yang login
    mahasiswa_list = Mahasiswa.objects.filter(dosen=request.user)
    
    if search_query:
        mahasiswa_list = mahasiswa_list.filter(
            Q(nim__icontains=search_query) | 
            Q(nama__icontains=search_query)
        )
    
    if jadwal_filter:
        # Pastikan jadwal juga milik dosen yang login
        jadwal = get_object_or_404(Jadwal, pk=jadwal_filter, dosen=request.user)
        mahasiswa_list = mahasiswa_list.filter(jadwal__id=jadwal_filter).distinct()
    
    # Untuk filter dropdown jadwal
    all_jadwal = Jadwal.objects.filter(dosen=request.user).select_related('praktikum').order_by('praktikum__nama', 'hari', 'waktu_mulai')
    
    paginator = Paginator(mahasiswa_list, 10)
    page = request.GET.get('page')
    mahasiswa_list = paginator.get_page(page)
    
    context = {
        'mahasiswa_list': mahasiswa_list,
        'all_jadwal': all_jadwal,
    }
    
    return render(request, 'dosen/mahasiswa_list.html', context)

@login_required
def mahasiswa_create(request):
    if not request.user.is_dosen():
        messages.error(request, 'Anda tidak memiliki izin untuk menambah data mahasiswa.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = MahasiswaForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                mahasiswa = form.save()
                messages.success(request, 'Data mahasiswa berhasil ditambahkan.')
                return redirect('labApp:mahasiswa_list')
            except Exception as e:
                messages.error(request, f'Terjadi kesalahan saat menyimpan data: {str(e)}')
    else:
        form = MahasiswaForm(user=request.user)
    
    return render(request, 'dosen/mahasiswa_form.html', {'form': form})

@login_required
@csrf_protect
def mahasiswa_update(request, pk):
    if not request.user.is_dosen():
        messages.error(request, 'Anda tidak memiliki izin untuk mengubah data mahasiswa.')
        return redirect('labApp:mahasiswa_list')
    
    # Tambahkan filter untuk memastikan mahasiswa milik dosen yang login
    mahasiswa = get_object_or_404(Mahasiswa, pk=pk, dosen=request.user)
    
    if request.method == 'POST':
        print("=== DEBUG: Processing POST request ===")
        print("POST data:", request.POST)
        
        form = MahasiswaForm(request.POST, instance=mahasiswa, user=request.user)
        if form.is_valid():
            try:
                print("=== DEBUG: Form is valid ===")
                print("Cleaned data:", form.cleaned_data)
                
                mahasiswa = form.save()
                messages.success(request, 'Data mahasiswa berhasil diperbarui!')
                return redirect('labApp:mahasiswa_list')
            except Exception as e:
                print(f"=== DEBUG: Error saving form: {str(e)}")
                messages.error(request, f'Terjadi kesalahan saat menyimpan data: {str(e)}')
        else:
            print("=== DEBUG: Form is invalid ===")
            print("Form errors:", form.errors)
            messages.error(request, 'Terjadi kesalahan. Silakan periksa form Anda.')
    else:
        form = MahasiswaForm(instance=mahasiswa, user=request.user)
    
    return render(request, 'dosen/mahasiswa_form.html', {'form': form, 'title': 'Edit Mahasiswa'})

@login_required
def mahasiswa_detail(request, pk):
    if not request.user.is_dosen():
        messages.error(request, 'Anda tidak memiliki izin untuk melihat detail mahasiswa.')
        return redirect('dashboard')

    # Tambahkan filter untuk memastikan mahasiswa milik dosen yang login
    mahasiswa = get_object_or_404(Mahasiswa, pk=pk, dosen=request.user)
    kehadiran_list = Kehadiran.objects.filter(mahasiswa=mahasiswa).order_by('-tanggal')

    context = {
        'mahasiswa': mahasiswa,
        'kehadiran_list': kehadiran_list,
    }

    return render(request, 'dosen/mahasiswa_detail.html', context)

@login_required
@csrf_protect
def mahasiswa_delete(request, pk):
    if not request.user.is_dosen():
        messages.error(request, 'Anda tidak memiliki izin untuk menghapus mahasiswa.')
        return redirect('labApp:mahasiswa_list')
    
    # Tambahkan filter untuk memastikan mahasiswa milik dosen yang login
    mahasiswa = get_object_or_404(Mahasiswa, pk=pk, dosen=request.user)
    
    if request.method == 'POST':
        mahasiswa.delete()
        messages.success(request, 'Mahasiswa berhasil dihapus!')
        return redirect('labApp:mahasiswa_list')
    
    return render(request, 'dosen/mahasiswa_confirm_delete.html', {'mahasiswa': mahasiswa})

@login_required
def kehadiran_form(request):
    if not (request.user.is_dosen() or request.user.is_asisten()):
        messages.error(request, 'Anda tidak memiliki izin untuk mengisi kehadiran.')
        return redirect('dashboard')
    
    print("=== DEBUG: Starting kehadiran_form view ===")
    print(f"Request method: {request.method}")
    
    # Form untuk memilih jadwal dan tanggal
    filter_form = KehadiranFilterForm(request.GET or None, user=request.user)
    
    # Inisialisasi variabel untuk template
    show_formset = False
    formset = None
    jadwal = None
    tanggal = None
    mahasiswa_count = 0
    
    # Jika form filter valid (jadwal dan tanggal sudah dipilih)
    if filter_form.is_valid() and 'jadwal' in request.GET and 'tanggal' in request.GET:
        jadwal = filter_form.cleaned_data['jadwal']
        tanggal = filter_form.cleaned_data['tanggal']
        
        print(f"=== DEBUG: Filter form is valid ===")
        print(f"Selected jadwal: {jadwal}")
        print(f"Selected tanggal: {tanggal}")
        
        # Ambil semua mahasiswa yang terdaftar di jadwal tersebut
        mahasiswa_list = Mahasiswa.objects.filter(jadwal__in=[jadwal]).order_by('nim')
        mahasiswa_count = mahasiswa_list.count()
        
        print(f"Found {mahasiswa_count} students for this schedule")
        
        if not mahasiswa_list.exists():
            messages.warning(request, f'Tidak ada mahasiswa yang terdaftar pada jadwal {jadwal}.')
            show_formset = False
        else:
            show_formset = True
            
            # Buat formset untuk kehadiran, secara eksplisit menggunakan class yang diimpor
            # Debug: Print imported classes before factory call
            print("=== DEBUG: Imported KehadiranForm:", KehadiranForm)
            print("=== DEBUG: Imported KehadiranFormSet:", KehadiranFormSet)
            
            KehadiranFormSetClass = formset_factory(form=KehadiranForm, formset=KehadiranFormSet, extra=0)
            
            # Debug: Print created FormSetClass
            print("=== DEBUG: Created KehadiranFormSetClass:", KehadiranFormSetClass)

            # Siapkan data awal untuk formset
            initial_data = []
            for mahasiswa in mahasiswa_list:
                # Cek apakah sudah ada data kehadiran
                try:
                    kehadiran = Kehadiran.objects.get(jadwal=jadwal, mahasiswa=mahasiswa, tanggal=tanggal)
                    initial = {
                        'mahasiswa_id': mahasiswa.id,
                        'nama_mahasiswa': mahasiswa.nama,
                        'nim_mahasiswa': mahasiswa.nim,
                        'hadir': kehadiran.hadir,
                        'keterangan': kehadiran.keterangan or ''
                    }
                except Kehadiran.DoesNotExist:
                    initial = {
                        'mahasiswa_id': mahasiswa.id,
                        'nama_mahasiswa': mahasiswa.nama,
                        'nim_mahasiswa': mahasiswa.nim,
                        'hadir': False,
                        'keterangan': ''
                    }
                initial_data.append(initial)
            
            if request.method == 'POST':
                print("=== DEBUG: Processing POST request ===")
                print("POST data:", request.POST)
                
                formset = KehadiranFormSetClass(request.POST, initial=initial_data, jadwal=jadwal, tanggal=tanggal)
                
                if formset.is_valid():
                    print("=== DEBUG: Formset is valid ===")
                    # Simpan data kehadiran
                    saved_count = 0
                    for i, form in enumerate(formset):
                        print(f"Processing form {i+1}")
                        if form.is_valid():
                            try:
                                kehadiran = form.save()
                                if kehadiran:
                                    saved_count += 1
                                    print(f"Successfully saved attendance for student {kehadiran.mahasiswa.nama}")
                            except Exception as e:
                                print(f"Error saving form {i+1}: {str(e)}")
                                messages.error(request, f'Error saving attendance: {str(e)}')
                                return redirect('labApp:kehadiran_list')
                    
                    print(f"=== DEBUG: Saved {saved_count} attendance records ===")
                    messages.success(request, f'Berhasil menyimpan data kehadiran untuk {saved_count} mahasiswa.')
                    return redirect('labApp:kehadiran_list')
                else:
                    print("=== DEBUG: Formset is invalid ===")
                    print("Formset errors:", formset.errors)
                    print("Non-form errors:", formset.non_form_errors())
                    for i, form in enumerate(formset):
                        if not form.is_valid():
                            print(f"Form {i+1} errors:", form.errors)
                    messages.error(request, 'Terjadi kesalahan saat menyimpan data kehadiran.')
            else:
                # For GET requests, create the formset with initial data
                formset = KehadiranFormSetClass(initial=initial_data, jadwal=jadwal, tanggal=tanggal)
                # Ensure the formset is bound with the initial data
                for form in formset.forms:
                    form.initial = initial_data[formset.forms.index(form)]
    
    # Render template dengan konteks yang sesuai
    context = {
        'filter_form': filter_form,
        'formset': formset,
        'jadwal': jadwal,
        'tanggal': tanggal,
        'show_formset': show_formset,
        'mahasiswa_count': mahasiswa_count
    }
    
    return render(request, 'dosen/kehadiran_form.html', context)
