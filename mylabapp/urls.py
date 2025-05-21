from django.urls import path
from . import views

app_name = 'mylabapp'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('data-praktikum/', views.data_praktikum, name='data_praktikum'),
    path('tambah-praktikum/', views.tambah_praktikum, name='tambah_praktikum'),
    path('edit-praktikum/<int:pk>/', views.edit_praktikum, name='edit_praktikum'),
    path('hapus-praktikum/<int:pk>/', views.hapus_praktikum, name='hapus_praktikum'),
    path('inventaris/', views.inventaris, name='inventaris'),
    path('inventaris/tambah/', views.tambah_inventaris, name='tambah_inventaris'),
    path('inventaris/edit/<int:id>/', views.edit_inventaris, name='edit_inventaris'),
    path('inventaris/hapus/<int:id>/', views.hapus_inventaris, name='hapus_inventaris'),
    path('laporan/', views.laporan_view, name='laporan'),
    path('penanganan-kerusakan/', views.penanganan_kerusakan, name='penanganan_kerusakan'),
    path('kerusakan/selesai/<int:pk>/', views.set_kerusakan_selesai, name='kerusakan_selesai'),
    path('kerusakan/batal/<int:pk>/', views.set_kerusakan_batal, name='kerusakan_batal'),
    path('logout/', views.logout_view, name='logout'),
    path('notifikasi/read_and_redirect/<int:pk>/', views.mark_notification_read_and_redirect, name='mark_notification_read_and_redirect'),
]   