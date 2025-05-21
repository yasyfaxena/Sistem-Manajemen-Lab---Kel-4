from django import forms
from .models import DataPraktikum, PerangkatInventaris
from django.contrib.auth.forms import UserCreationForm

class PraktikumForm(forms.ModelForm):
    class Meta:
        model = DataPraktikum
        fields = ['nama', 'kode', 'deskripsi']

class PerangkatInventarisForm(forms.ModelForm):
    class Meta:
        model = PerangkatInventaris
        fields = ['nama', 'kondisi', 'lokasi']

class AdminRegistrationForm(UserCreationForm):
    pass
