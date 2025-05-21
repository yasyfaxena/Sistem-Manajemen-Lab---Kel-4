from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Praktikum, Jadwal, Mahasiswa, Kehadiran, LaporanKerusakan

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Role', {'fields': ('role',)}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

class JadwalAdmin(admin.ModelAdmin):
    list_display = ('praktikum', 'hari', 'waktu_mulai', 'waktu_selesai', 'ruangan', 'dosen')
    list_filter = ('hari', 'dosen')
    search_fields = ('praktikum__nama', 'ruangan', 'dosen__username')

class KehadiranAdmin(admin.ModelAdmin):
    list_display = ('mahasiswa', 'jadwal', 'tanggal', 'hadir')
    list_filter = ('hadir', 'tanggal', 'jadwal')
    search_fields = ('mahasiswa__nama', 'mahasiswa__nim', 'jadwal__praktikum__nama')
    date_hierarchy = 'tanggal'

class LaporanKerusakanAdmin(admin.ModelAdmin):
    list_display = ('perangkat', 'ruangan', 'tanggal_laporan', 'pelapor', 'status')
    list_filter = ('status', 'ruangan')
    search_fields = ('perangkat', 'ruangan', 'deskripsi', 'pelapor__username')
    date_hierarchy = 'tanggal_laporan'

admin.site.register(User, CustomUserAdmin)
admin.site.register(Praktikum)
admin.site.register(Jadwal, JadwalAdmin)
admin.site.register(Mahasiswa)
admin.site.register(Kehadiran, KehadiranAdmin)
admin.site.register(LaporanKerusakan, LaporanKerusakanAdmin)