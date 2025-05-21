from django.urls import path
from . import views

app_name = 'labApp'

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Jadwal
    path('jadwal/', views.jadwal_list, name='jadwal_list'),
    path('jadwal/tambah/', views.jadwal_create, name='jadwal_create'),
    path('jadwal/<int:pk>/edit/', views.jadwal_update, name='jadwal_update'),
    path('jadwal/<int:pk>/hapus/', views.jadwal_delete, name='jadwal_delete'),
    
    # Kehadiran
    path('kehadiran/', views.kehadiran_list, name='kehadiran_list'),
    path('kehadiran/tambah/', views.kehadiran_bulk_create, name='kehadiran_create'),
    path('kehadiran/form/', views.kehadiran_form, name='kehadiran_form'),
    
    # Laporan Kerusakan (Asisten)
    path('laporan/', views.laporan_list, name='laporan_list'),
    path('laporan/tambah/', views.laporan_create, name='laporan_create'),
    path('laporan/<int:pk>/edit/', views.laporan_update, name='laporan_update'),
    path('laporan/<int:pk>/hapus/', views.laporan_delete, name='laporan_delete'),
    
    # Praktikum dan Mahasiswa (Admin)
    path('praktikum/', views.praktikum_list, name='praktikum_list'),
    path('praktikum/tambah/', views.praktikum_create, name='praktikum_create'),
    path('praktikum/<int:pk>/edit/', views.praktikum_update, name='praktikum_update'),
    path('praktikum/<int:pk>/hapus/', views.praktikum_delete, name='praktikum_delete'),
    path('mahasiswa/', views.mahasiswa_list, name='mahasiswa_list'),
    path('mahasiswa/tambah/', views.mahasiswa_create, name='mahasiswa_create'),
    path('mahasiswa/<int:pk>/edit/', views.mahasiswa_update, name='mahasiswa_update'),
    path('mahasiswa/<int:pk>/detail/', views.mahasiswa_detail, name='mahasiswa_detail'),
    path('mahasiswa/<int:pk>/hapus/', views.mahasiswa_delete, name='mahasiswa_delete'),
]