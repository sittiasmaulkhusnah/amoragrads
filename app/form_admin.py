from django import forms

from .models import KategoriPaket, Package, UserAdmin


class formProfile(forms.ModelForm):
    nama_lengkap = forms.CharField(max_length=100, label='Nama lengkap')

    class Meta:
        model = UserAdmin
        fields = ['photo', 'telp', 'gender']
        labels = {'photo': 'Foto profil', 'telp': 'No. telepon', 'gender': 'Jenis kelamin'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['nama_lengkap'].initial = self.instance.username.first_name


class KategoriPaketForm(forms.ModelForm):
    class Meta:
        model = KategoriPaket
        fields = ['nama_kategori', 'slug', 'deskripsi_kategori', 'aktif']
        labels = {'nama_kategori': 'Nama kategori', 'slug': 'Slug / URL (opsional)',
                  'deskripsi_kategori': 'Deskripsi', 'aktif': 'Aktif (tampil di website)'}
        widgets = {
            'nama_kategori': forms.TextInput(attrs={'placeholder': 'Contoh: Wisuda Solo'}),
            'slug': forms.TextInput(attrs={'placeholder': 'Otomatis dibuat jika kosong'}),
            'deskripsi_kategori': forms.Textarea(attrs={'rows': 3}),
        }


class PaketForm(forms.ModelForm):
    kategori = forms.ModelChoiceField(
        queryset=KategoriPaket.objects.filter(aktif=True), required=False,
        empty_label='-- Pilih kategori --', label='Kategori')

    class Meta:
        model = Package
        fields = ['name', 'slug', 'kategori', 'badge', 'peserta', 'duration_minutes', 'price',
                  'harga_potongan', 'hasil', 'deskripsi', 'subtitle', 'kicker', 'deskripsi_lengkap',
                  'featured_image', 'status']
        labels = {
            'name': 'Nama paket', 'slug': 'Slug / URL (opsional)', 'badge': 'Label (opsional)',
            'peserta': 'Jumlah orang', 'duration_minutes': 'Durasi (menit)', 'price': 'Harga (Rp)',
            'harga_potongan': 'Harga potongan (Rp, opsional)', 'hasil': 'Hasil yang didapat',
            'deskripsi': 'Deskripsi singkat', 'subtitle': 'Subjudul', 'kicker': 'Kicker (teks kecil di atas judul)',
            'deskripsi_lengkap': 'Deskripsi lengkap', 'featured_image': 'Foto utama (cover)', 'status': 'Status',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Contoh: Grads 1'}),
            'slug': forms.TextInput(attrs={'placeholder': 'Otomatis dibuat jika kosong'}),
            'badge': forms.TextInput(attrs={'placeholder': 'Contoh: By Owner'}),
            'peserta': forms.TextInput(attrs={'placeholder': 'Contoh: 1 Orang'}),
            'price': forms.NumberInput(attrs={'min': 0, 'step': 1000, 'placeholder': '400000'}),
            'harga_potongan': forms.NumberInput(attrs={'min': 0, 'step': 1000, 'placeholder': 'Kosongkan jika tidak diskon'}),
            'duration_minutes': forms.NumberInput(attrs={'min': 1, 'placeholder': '60'}),
            'hasil': forms.TextInput(attrs={'placeholder': 'Contoh: 25 Foto Edit'}),
            'deskripsi': forms.Textarea(attrs={'rows': 3}),
            'deskripsi_lengkap': forms.Textarea(attrs={'rows': 5}),
            'featured_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def clean(self):
        data = super().clean()
        harga, potongan = data.get('price'), data.get('harga_potongan')
        if harga and potongan and potongan >= harga:
            self.add_error('harga_potongan', 'Harga potongan harus lebih kecil dari harga awal.')
        return data
