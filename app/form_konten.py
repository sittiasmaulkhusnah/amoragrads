from django import forms

from .models import Article, Category, HeroSlide, KerjaSama, Page, WebSetting
from django.utils.html import strip_tags

from .sanitasi import sanitasi


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description']
        labels = {'name': 'Nama kategori', 'slug': 'Slug / URL (opsional)', 'description': 'Deskripsi singkat'}
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Contoh: Tips Wisuda'}),
            'slug': forms.TextInput(attrs={'placeholder': 'Otomatis dibuat jika kosong'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class _SanitasiIsi:
    use_required_attribute = False   # textarea disembunyikan editor, validasi dilakukan di server

    def clean_content(self):
        isi = sanitasi(self.cleaned_data.get('content', ''))
        polos = strip_tags(isi).replace('&nbsp;', ' ').strip()
        if not polos and '<img' not in isi:
            raise forms.ValidationError('Isi tidak boleh kosong.')
        return isi


class ArticleForm(_SanitasiIsi, forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False,
                                      empty_label='-- Tanpa kategori --', label='Kategori')

    class Meta:
        model = Article
        fields = ['title', 'slug', 'category', 'status', 'featured_image', 'content']
        labels = {'title': 'Judul artikel', 'slug': 'Slug / URL (opsional)', 'status': 'Status',
                  'featured_image': 'Foto utama (opsional)', 'content': 'Isi artikel'}
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Judul artikel'}),
            'slug': forms.TextInput(attrs={'placeholder': 'Otomatis dibuat jika kosong'}),
            'content': forms.Textarea(attrs={'rows': 14, 'class': 'summernote'}),
            'featured_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class PageForm(_SanitasiIsi, forms.ModelForm):
    class Meta:
        model = Page
        fields = ['title', 'slug', 'featured_image', 'content']
        labels = {'title': 'Judul halaman', 'slug': 'Slug / URL (opsional)',
                  'featured_image': 'Foto utama (opsional)', 'content': 'Isi halaman'}
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Contoh: Tentang Kami'}),
            'slug': forms.TextInput(attrs={'placeholder': 'Otomatis dibuat jika kosong'}),
            'content': forms.Textarea(attrs={'rows': 14, 'class': 'summernote'}),
            'featured_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class HeroSlideForm(forms.ModelForm):
    class Meta:
        model = HeroSlide
        fields = ['judul', 'judul_highlight', 'badge_text', 'deskripsi', 'tombol_teks', 'tombol_url',
                  'banner', 'urutan', 'is_active']
        widgets = {
            'deskripsi': forms.Textarea(attrs={'rows': 3}),
            'banner': forms.FileInput(attrs={'accept': 'image/*'}),
            'urutan': forms.NumberInput(attrs={'min': 0}),
        }


class KerjaSamaForm(forms.ModelForm):
    class Meta:
        model = KerjaSama
        fields = ['nama_kerjasama', 'logo', 'link_website']
        labels = {'nama_kerjasama': 'Nama mitra', 'logo': 'Logo (opsional)', 'link_website': 'Link website (opsional)'}
        widgets = {
            'nama_kerjasama': forms.TextInput(attrs={'placeholder': 'Contoh: Nama kampus, MUA, atau vendor'}),
            'logo': forms.FileInput(attrs={'accept': 'image/*'}),
            'link_website': forms.URLInput(attrs={'placeholder': 'https://...'}),
        }


class WebSettingForm(forms.ModelForm):
    midtrans_server_key = forms.CharField(
        required=False, label='Midtrans Server Key',
        widget=forms.PasswordInput(render_value=False, attrs={'placeholder': '(kosongkan jika tidak diubah)', 'autocomplete': 'off'}),
        help_text='Rahasia. Sandbox: dashboard.sandbox.midtrans.com > Settings > Access Keys.')

    def clean_midtrans_server_key(self):
        baru = (self.cleaned_data.get('midtrans_server_key') or '').strip()
        return baru or (self.instance.midtrans_server_key if self.instance else '')

    class Meta:
        model = WebSetting
        fields = ['nama_web', 'tagline', 'no_telp', 'email', 'alamat', 'jam_operasional', 'logo',
                  'link_instagram', 'link_tiktok', 'link_facebook', 'link_youtube', 'link_maps',
                  'midtrans_client_key', 'midtrans_server_key', 'midtrans_production']
        labels = {
            'nama_web': 'Nama website', 'tagline': 'Tagline singkat', 'no_telp': 'Nomor WhatsApp',
            'email': 'Email', 'alamat': 'Alamat', 'jam_operasional': 'Jam operasional', 'logo': 'Logo (opsional)',
            'link_instagram': 'Link Instagram', 'link_tiktok': 'Link TikTok', 'link_facebook': 'Link Facebook',
            'link_youtube': 'Link YouTube', 'link_maps': 'Link Google Maps',
            'midtrans_client_key': 'Midtrans Client Key', 'midtrans_production': 'Mode Production (uang sungguhan)',
        }
        widgets = {
            'alamat': forms.Textarea(attrs={'rows': 3}),
            'logo': forms.FileInput(attrs={'accept': 'image/*'}),
            'no_telp': forms.TextInput(attrs={'placeholder': '08xxxxxxxxxx'}),
            'jam_operasional': forms.TextInput(attrs={'placeholder': 'Contoh: Setiap hari, 09.00 - 21.00 WITA'}),
        }
