from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.forms import BaseFormSet
from .models import User, Jadwal, Kehadiran, LaporanKerusakan, Praktikum, Mahasiswa

# Add imports for filtering choices
from django.db.models import Q

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            user = User.objects.filter(username=username).first()
            if user and user.check_password(password):
                self.user_cache = user
            else:
                raise forms.ValidationError('Username atau password salah.')
        return cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)

class UserRegisterForm(UserCreationForm):
    role = forms.ChoiceField(choices=User.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}), label="Role")
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'role', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Nama Depan'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Nama Belakang'})
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Email'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Konfirmasi Password'})

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password1'] != cd['password2']:
            raise forms.ValidationError('Passwords tidak cocok.')
        return cd['password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class PraktikumForm(forms.ModelForm):
    class Meta:
        model = Praktikum
        fields = ['kode', 'nama', 'deskripsi']
        widgets = {
            'kode': forms.TextInput(attrs={'class': 'form-control'}),
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'deskripsi': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        nama = cleaned_data.get('nama')
        kode = cleaned_data.get('kode')
        
        if not nama:
            raise forms.ValidationError("Nama praktikum harus diisi")
        if not kode:
            raise forms.ValidationError("Kode praktikum harus diisi")
            
        return cleaned_data

class JadwalForm(forms.ModelForm):
    class Meta:
        model = Jadwal
        exclude = ['dosen']  # Sembunyikan field dosen dari form
        fields = ['praktikum', 'hari', 'waktu_mulai', 'waktu_selesai', 'ruangan', 'asisten']
        widgets = {
            'praktikum': forms.Select(attrs={'class': 'form-control'}),
            'hari': forms.Select(attrs={'class': 'form-control'}),
            'waktu_mulai': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'waktu_selesai': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'ruangan': forms.Select(attrs={'class': 'form-control'}),
            'asisten': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and self.user.is_dosen():
            # Filter praktikum hanya untuk dosen yang login
            self.fields['praktikum'].queryset = Praktikum.objects.filter(dosen=self.user)
            
            # Filter asisten berdasarkan role 'asisten'
            self.fields['asisten'].queryset = User.objects.filter(role='asisten')
    
    def clean(self):
        cleaned_data = super().clean()
        praktikum = cleaned_data.get('praktikum')
        
        # Validasi bahwa praktikum milik dosen yang login
        if self.user and self.user.is_dosen() and praktikum:
            if praktikum.dosen != self.user:
                raise forms.ValidationError("Anda tidak memiliki akses ke praktikum ini")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user and self.user.is_dosen():
            instance.dosen = self.user
        if commit:
            instance.save()
            self.save_m2m()
        return instance

class KehadiranBulkForm(forms.Form):
    jadwal = forms.ModelChoiceField(
        queryset=Jadwal.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Jadwal Praktikum"
    )
    tanggal = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Tanggal Kehadiran"
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            if user.is_dosen():
                self.fields['jadwal'].queryset = Jadwal.objects.filter(dosen=user)
            elif user.is_asisten():
                self.fields['jadwal'].queryset = Jadwal.objects.filter(asisten=user)

class LaporanKerusakanForm(forms.ModelForm):
    class Meta:
        model = LaporanKerusakan
        fields = ['perangkat', 'ruangan', 'deskripsi']
        widgets = {
            'perangkat': forms.TextInput(attrs={'class': 'form-control'}),
            'ruangan': forms.TextInput(attrs={'class': 'form-control'}),
            'deskripsi': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        perangkat = cleaned_data.get('perangkat')
        deskripsi = cleaned_data.get('deskripsi')
        ruangan = cleaned_data.get('ruangan')
        
        if not perangkat:
            raise forms.ValidationError("Perangkat harus diisi")
        if not deskripsi:
            raise forms.ValidationError("Deskripsi kerusakan harus diisi")
        if not ruangan:
            raise forms.ValidationError("Ruangan harus diisi")
            
        return cleaned_data

class MahasiswaForm(forms.ModelForm):
    praktikum_filter = forms.ModelChoiceField(
        queryset=Praktikum.objects.all(),
        required=False,
        empty_label="-- Semua Praktikum --",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'praktikum-filter'}),
        help_text="Filter jadwal berdasarkan praktikum"
    )
    
    hari_filter = forms.ChoiceField(
        choices=[('', '-- Semua Hari --')] + list(Jadwal.HARI_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'hari-filter'}),
        help_text="Filter jadwal berdasarkan hari"
    )
    
    jadwal = forms.ModelMultipleChoiceField(
        queryset=Jadwal.objects.all().select_related('praktikum', 'dosen'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Pilih jadwal praktikum yang diikuti mahasiswa ini"
    )
    
    class Meta:
        model = Mahasiswa
        exclude = ['dosen', 'angkatan']  # Sembunyikan field dosen dan angkatan
        fields = ['nim', 'nama', 'jadwal']
        widgets = {
            'nim': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan NIM'}),
            'nama': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masukkan Nama Lengkap'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter jadwal dan praktikum berdasarkan dosen yang login
        if self.user and self.user.is_dosen():
            jadwal_queryset = Jadwal.objects.filter(dosen=self.user).select_related('praktikum', 'dosen').order_by('praktikum__nama', 'hari', 'waktu_mulai')
            self.fields['jadwal'].queryset = jadwal_queryset
            self.fields['praktikum_filter'].queryset = Praktikum.objects.filter(dosen=self.user)
        
        self.fields['jadwal'].widget.attrs.update({'class': 'jadwal-checkbox-list'})
    
    def clean_nim(self):
        nim = self.cleaned_data.get('nim')
        if not nim:
            raise forms.ValidationError("NIM harus diisi")
        if not nim.isdigit():
            raise forms.ValidationError("NIM harus berupa angka")
        if len(nim) < 8:
            raise forms.ValidationError("NIM harus minimal 8 digit")
        
        # Cek duplikasi NIM hanya untuk dosen yang sama
        if self.user and self.user.is_dosen():
            existing = Mahasiswa.objects.filter(nim=nim, dosen=self.user)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError("NIM sudah terdaftar untuk dosen Anda")
        
        return nim
    
    def clean_nama(self):
        nama = self.cleaned_data.get('nama')
        if not nama:
            raise forms.ValidationError("Nama harus diisi")
        if len(nama) < 3:
            raise forms.ValidationError("Nama harus minimal 3 karakter")
        return nama
    
    def clean_jadwal(self):
        jadwal = self.cleaned_data.get('jadwal')
        if self.user and self.user.is_dosen():
            # Pastikan semua jadwal yang dipilih milik dosen yang login
            invalid_jadwal = jadwal.exclude(dosen=self.user)
            if invalid_jadwal.exists():
                raise forms.ValidationError("Anda tidak memiliki akses ke beberapa jadwal yang dipilih")
        return jadwal
    
    def save(self, commit=True):
        print("=== DEBUG: Saving MahasiswaForm ===")
        print("User:", self.user)
        print("Instance:", self.instance)
        
        instance = super().save(commit=False)
        if self.user and self.user.is_dosen():
            instance.dosen = self.user
            print("Set dosen to:", self.user)
        
        if commit:
            try:
                instance.save()
                self.save_m2m()
                print("Successfully saved instance")
            except Exception as e:
                print(f"Error saving instance: {str(e)}")
                raise
        
        return instance

class KehadiranForm(forms.ModelForm):
    mahasiswa_id = forms.IntegerField(widget=forms.HiddenInput())
    nama_mahasiswa = forms.CharField(max_length=255, required=False)
    nim_mahasiswa = forms.CharField(max_length=20, required=False)
    hadir = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    keterangan = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Kehadiran
        fields = ['mahasiswa_id', 'hadir', 'keterangan']  # sesuaikan sesuai field model yang ingin diedit

    def __init__(self, *args, **kwargs):
        self.jadwal = kwargs.pop('jadwal', None)
        self.tanggal = kwargs.pop('tanggal', None)
        super().__init__(*args, **kwargs)
        
        self.fields['hadir'].label = ''
        self.fields['keterangan'].label = ''
    
    def clean(self):
        cleaned_data = super().clean()
        if not self.jadwal or not self.tanggal:
            raise forms.ValidationError("Jadwal dan tanggal harus diisi")
        return cleaned_data
    
    def save(self, commit=True):
        if not self.is_valid():
            print("KehadiranForm is invalid:", self.errors)
            raise forms.ValidationError("Form kehadiran tidak valid.")

        if not self.jadwal or not self.tanggal:
            print("Jadwal or tanggal is missing")
            print(f"Jadwal: {self.jadwal}")
            print(f"Tanggal: {self.tanggal}")
            return None
        
        try:
            mahasiswa_id = self.cleaned_data['mahasiswa_id']
            hadir = self.cleaned_data['hadir']
            keterangan = self.cleaned_data['keterangan']
            
            print(f"Saving attendance for mahasiswa_id: {mahasiswa_id}")
            print(f"Hadir: {hadir}")
            print(f"Keterangan: {keterangan}")
            
            mahasiswa = Mahasiswa.objects.get(id=mahasiswa_id)
            
            kehadiran, created = Kehadiran.objects.update_or_create(
                jadwal=self.jadwal,
                mahasiswa=mahasiswa,
                tanggal=self.tanggal,
                defaults={
                    'hadir': hadir,
                    'keterangan': keterangan
                }
            )
            
            print(f"Attendance {'created' if created else 'updated'}")
            return kehadiran
            
        except Mahasiswa.DoesNotExist:
            print(f"Mahasiswa with id {mahasiswa_id} does not exist")
            return None
        except Exception as e:
            print(f"Error saving kehadiran: {str(e)}")
            return None

class KehadiranFilterForm(forms.Form):
    jadwal = forms.ModelChoiceField(
        queryset=Jadwal.objects.all().select_related('praktikum'),
        empty_label="-- Pilih Jadwal Praktikum --",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label="Jadwal Praktikum"
    )
    
    tanggal = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=True,
        label="Tanggal Kehadiran"
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            if hasattr(user, 'is_dosen') and user.is_dosen():
                self.fields['jadwal'].queryset = Jadwal.objects.filter(dosen=user).select_related('praktikum')
            elif hasattr(user, 'is_asisten') and user.is_asisten():
                self.fields['jadwal'].queryset = Jadwal.objects.filter(asisten=user).select_related('praktikum')

class KehadiranFormSet(BaseFormSet):
    def __init__(self, *args, **kwargs):
        self.jadwal = kwargs.pop('jadwal', None)
        self.tanggal = kwargs.pop('tanggal', None)
        super().__init__(*args, **kwargs)
        
        for form in self.forms:
            form.jadwal = self.jadwal
            form.tanggal = self.tanggal
    
    def clean(self):
        if any(self.errors):
            return
        
        for form in self.forms:
            if not form.is_valid():
                return
            
            if not form.cleaned_data.get('mahasiswa_id'):
                raise forms.ValidationError('Data mahasiswa tidak valid.')