from django import forms
from django.contrib.auth.models import User

from .models import GENDER_CHOICES, Universitas, UserPengguna
from .roles import ROLE_PENGGUNA


class RegisterForm(forms.Form):
    nama = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(min_length=6)
    konfirmasi = forms.CharField()

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(username=email).exists() or User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Email sudah terdaftar. Silakan masuk.')
        return email

    def clean(self):
        data = super().clean()
        if data.get('password') and data.get('password') != data.get('konfirmasi'):
            self.add_error('konfirmasi', 'Konfirmasi kata sandi tidak sama.')
        return data

    def save(self):
        d = self.cleaned_data
        user = User.objects.create_user(
            username=d['email'], email=d['email'], password=d['password'],
            first_name=d['nama'], last_name=ROLE_PENGGUNA,
        )
        UserPengguna.objects.create(user=user)
        return user


class LoginForm(forms.Form):
    email = forms.CharField()
    password = forms.CharField()


class formProfile(forms.ModelForm):
    nama_lengkap = forms.CharField(max_length=100, label='Nama lengkap')

    class Meta:
        model = UserPengguna
        fields = ['photo', 'telp', 'gender', 'tanggal_lahir', 'universitas', 'jurusan']
        widgets = {
            'tanggal_lahir': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'telp': forms.TextInput(attrs={'type': 'tel', 'placeholder': '08xxxxxxxxxx'}),
            'jurusan': forms.TextInput(attrs={'placeholder': 'Contoh: Ilmu Komunikasi'}),
        }
        labels = {
            'photo': 'Foto profil', 'telp': 'Nomor WhatsApp', 'gender': 'Jenis kelamin',
            'tanggal_lahir': 'Tanggal lahir', 'universitas': 'Universitas / kampus',
            'jurusan': 'Jurusan (opsional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['universitas'].queryset = Universitas.objects.filter(aktif=True)
        self.fields['universitas'].empty_label = 'Pilih kampus'
        self.fields['gender'].choices = [('', 'Pilih jenis kelamin')] + GENDER_CHOICES
        self.fields['telp'].required = True
        self.fields['gender'].required = True
        self.fields['universitas'].required = True
        if self.instance and self.instance.pk:
            self.fields['nama_lengkap'].initial = self.instance.user.first_name
