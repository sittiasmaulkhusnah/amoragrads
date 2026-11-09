from django import forms

from .models import Article, Category, HeroSlide, KerjaSama, Page, WebSetting


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'status']
        labels = {'name': 'Nama kategori', 'slug': 'Slug / URL (opsional)', 'description': 'Deskripsi singkat',
                  'status': 'Status'}
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Contoh: Tips Wisuda'}),
            'slug': forms.TextInput(attrs={'placeholder': 'Otomatis dibuat jika kosong'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ArticleForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False,
                                      empty_label='-- Tanpa kategori --', label='Kategori')

    class Meta:
        model = Article
        fields = ['title', 'slug', 'category', 'status', 'deskripsi_seo', 'featured_image', 'content']
        labels = {'title': 'Judul artikel', 'slug': 'Slug / URL (opsional)', 'status': 'Status',
                  'deskripsi_seo': 'Deskripsi SEO / GEO (opsional)',
                  'featured_image': 'Foto utama (opsional)', 'content': 'Isi artikel'}
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Judul artikel'}),
            'slug': forms.TextInput(attrs={'placeholder': 'Otomatis dibuat jika kosong'}),
            'deskripsi_seo': forms.Textarea(attrs={'rows': 2, 'maxlength': 300,
                                                   'placeholder': 'Ringkasan 1-2 kalimat untuk mesin pencari (maks. 300 karakter)'}),
            'content': forms.Textarea(attrs={'rows': 14}),
            'featured_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = ['title', 'slug', 'deskripsi', 'featured_image', 'content']
        labels = {'title': 'Judul halaman', 'slug': 'Slug / URL (opsional)',
                  'deskripsi': 'Deskripsi SEO (opsional)',
                  'featured_image': 'Foto utama (opsional)', 'content': 'Isi halaman'}
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Contoh: Tentang Kami'}),
            'slug': forms.TextInput(attrs={'placeholder': 'Otomatis dibuat jika kosong'}),
            'deskripsi': forms.Textarea(attrs={'rows': 2, 'maxlength': 300,
                                               'placeholder': 'Ringkasan singkat halaman (maks. 300 karakter)'}),
            'content': forms.Textarea(attrs={'rows': 14}),
            'featured_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }


class HeroSlideForm(forms.ModelForm):
    class Meta:
        model = HeroSlide
        fields = ['judul', 'judul_highlight', 'badge_text', 'badge_icon', 'deskripsi', 'tombol_teks',
                  'tombol_url', 'banner', 'urutan', 'is_active']
        widgets = {
            'deskripsi': forms.Textarea(attrs={'rows': 3}),
            'banner': forms.FileInput(attrs={'accept': 'image/*'}),
            'badge_icon': forms.FileInput(attrs={'accept': 'image/*'}),
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
    class Meta:
        model = WebSetting
        fields = ['nama_web', 'tagline', 'no_telp', 'email', 'alamat', 'jam_operasional', 'logo', 'favicon',
                  'link_instagram', 'link_tiktok', 'link_twitter', 'link_facebook', 'link_youtube', 'link_maps']
        labels = {
            'nama_web': 'Nama website', 'tagline': 'Tagline singkat', 'no_telp': 'Nomor WhatsApp',
            'email': 'Email', 'alamat': 'Alamat', 'jam_operasional': 'Jam operasional', 'logo': 'Logo (opsional)',
            'favicon': 'Favicon (ikon tab browser, opsional)',
            'link_instagram': 'Link Instagram', 'link_tiktok': 'Link TikTok', 'link_twitter': 'Link Twitter / X',
            'link_facebook': 'Link Facebook', 'link_youtube': 'Link YouTube', 'link_maps': 'Link Google Maps',
        }
        widgets = {
            'alamat': forms.Textarea(attrs={'rows': 3}),
            'logo': forms.FileInput(attrs={'accept': 'image/*'}),
            'favicon': forms.FileInput(attrs={'accept': 'image/*'}),
            'no_telp': forms.TextInput(attrs={'placeholder': '08xxxxxxxxxx'}),
            'jam_operasional': forms.TextInput(attrs={'placeholder': 'Contoh: Setiap hari, 09.00 - 21.00 WITA'}),
        }