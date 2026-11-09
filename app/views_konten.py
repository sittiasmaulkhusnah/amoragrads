from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .decorators_admin import admin_required
from .form_konten import (ArticleForm, CategoryForm, HeroSlideForm, KerjaSamaForm, PageForm,
                          WebSettingForm)
from .models import Article, Category, HeroSlide, KerjaSama, Page, UserAdmin, WebSetting



# KELOLA KONTEN DI PANEL ADMIN (satu pola CRUD untuk lima jenis konten)
# kolom: (judul kolom, atribut atau fungsi, jenis tampilan)
KONTEN = {
    'artikel': {
        'model': Article, 'form': ArticleForm, 'judul': 'Artikel', 'tunggal': 'artikel',
        'info': 'Artikel berstatus Published tampil di halaman Artikel dan beranda.',
        'kolom': [('Judul', 'title', 'teks'), ('Kategori', lambda o: o.category or '-', 'teks'),
                  ('Status', 'status', 'status'), ('Dilihat', 'views_count', 'teks'),
                  ('Dibuat', 'created_at', 'tanggal')],
        'gambar': 'featured_image', 'penulis': True,
    },
    'kategori-artikel': {
        'model': Category, 'form': CategoryForm, 'judul': 'Kategori Artikel', 'tunggal': 'kategori artikel',
        'info': 'Kelompok untuk mengatur artikel, misalnya Tips Wisuda atau Info & Promo. Kategori nonaktif tidak tampil di filter halaman Artikel.',
        'kolom': [('Nama', 'name', 'teks'), ('Slug', 'slug', 'teks'),
                  ('Status', 'status', 'status'),
                  ('Jumlah artikel', lambda o: o.articles.count(), 'teks')],
        'gambar': None, 'penulis': False,
    },
    'halaman': {
        'model': Page, 'form': PageForm, 'judul': 'Halaman', 'tunggal': 'halaman',
        'info': 'Halaman statis (Tentang Kami, Kebijakan Privasi, dan lainnya). Isinya diubah di sini, bukan di kode HTML.',
        'kolom': [('Judul', 'title', 'teks'), ('Alamat halaman', lambda o: f'/halaman/{o.slug}/', 'teks'),
                  ('Diperbarui', 'updated_at', 'tanggal')],
        'gambar': 'featured_image', 'penulis': True,
    },
    'hero-slide': {
        'model': HeroSlide, 'form': HeroSlideForm, 'judul': 'Hero Slide', 'tunggal': 'hero slide',
        'info': 'Slide utama di bagian atas beranda. Slide aktif tampil bergantian sesuai urutan.',
        'kolom': [('Judul', 'judul', 'teks'), ('Urutan', 'urutan', 'teks'), ('Status', 'is_active', 'aktif')],
        'gambar': 'banner', 'penulis': False,
    },
    'mitra': {
        'model': KerjaSama, 'form': KerjaSamaForm, 'judul': 'Mitra / Kerja Sama', 'tunggal': 'mitra',
        'info': 'Daftar mitra (networking) yang tampil di beranda.',
        'kolom': [('Nama', 'nama_kerjasama', 'teks'), ('Website', lambda o: o.link_website or '-', 'teks'),
                  ('Ditambahkan', 'created_at', 'tanggal')],
        'gambar': 'logo', 'penulis': False,
    },
}


def _cfg(jenis):
    cfg = KONTEN.get(jenis)
    if not cfg:
        raise Http404('Jenis konten tidak dikenal.')
    return cfg


def _foto_admin(request):
    ua = UserAdmin.objects.filter(username=request.user).first()
    return ua.photo if ua and ua.photo else None


def _sel(o, getter):
    v = getter(o) if callable(getter) else getattr(o, getter)
    return v


@admin_required
def konten_list(request, jenis):
    cfg = _cfg(jenis)
    baris = []
    for o in cfg['model'].objects.all():
        sel = []
        for judul, getter, jenis_sel in cfg['kolom']:
            v = _sel(o, getter)
            if jenis_sel == 'tanggal':
                v = v.strftime('%d %b %Y')
            elif jenis_sel == 'aktif':
                jenis_sel, v = ('aktif' if v else 'nonaktif'), ('Aktif' if v else 'Nonaktif')
            elif jenis_sel == 'status':
                jenis_sel = 'ok' if v in ('published', 'aktif') else 'off'
            else:
                jenis_sel = 'teks'
            sel.append({'v': v, 'j': jenis_sel})
        foto = getattr(o, cfg['gambar']) if cfg['gambar'] else None
        baris.append({'pk': o.pk, 'sel': sel, 'foto': foto.url if foto else ''})
    return render(request, 'admin_super/konten_list.html', {
        'title': cfg['judul'], 'photo': _foto_admin(request), 'jenis': jenis, 'cfg': cfg,
        'kolom': [k[0] for k in cfg['kolom']], 'baris': baris,
    })


@admin_required
def konten_form(request, jenis, pk=None):
    cfg = _cfg(jenis)
    obj = get_object_or_404(cfg['model'], pk=pk) if pk else None
    form = cfg['form'](request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST':
        if form.is_valid():
            hasil = form.save(commit=False)
            if cfg['penulis'] and not hasil.author:
                hasil.author = request.user
            hasil.save()
            form.save_m2m()
            messages.success(request, f"{cfg['tunggal'].capitalize()} berhasil {'diperbarui' if pk else 'ditambahkan'}!")
            return redirect('app:konten_list', jenis=jenis)
        messages.error(request, 'Gagal menyimpan. Periksa isian form.')
    previews = {}
    if obj:
        for nama, f in form.fields.items():
            if hasattr(f, 'widget') and getattr(f.widget, 'input_type', '') == 'file':
                fl = getattr(obj, nama, None)
                if fl:
                    previews[nama] = fl.url
    return render(request, 'admin_super/konten_form.html', {
        'title': f"{'Edit' if pk else 'Tambah'} {cfg['tunggal'].capitalize()}", 'photo': _foto_admin(request),
        'jenis': jenis, 'cfg': cfg, 'form': form,
        'campos': [{'f': bf, 'preview': previews.get(bf.name)} for bf in form],
    })


@admin_required
@require_POST
def konten_hapus(request, jenis, pk):
    cfg = _cfg(jenis)
    get_object_or_404(cfg['model'], pk=pk).delete()
    messages.success(request, f"{cfg['tunggal'].capitalize()} berhasil dihapus!")
    return redirect('app:konten_list', jenis=jenis)


@admin_required
def pengaturan_web(request):
    obj = WebSetting.objects.first() or WebSetting()
    form = WebSettingForm(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Pengaturan website berhasil disimpan!')
            return redirect('app:pengaturan_web')
        messages.error(request, 'Gagal menyimpan. Periksa isian form.')
    previews = {}
    if obj.pk and obj.logo:
        previews['logo'] = obj.logo.url
    if obj.pk and obj.favicon:
        previews['favicon'] = obj.favicon.url
    return render(request, 'admin_super/konten_form.html', {
        'title': 'Pengaturan Website', 'photo': _foto_admin(request), 'jenis': 'pengaturan',
        'cfg': {'judul': 'Pengaturan Website', 'info': 'Data ini dipakai di footer, kontak, tombol WhatsApp, logo, dan favicon website.'},
        'form': form, 'campos': [{'f': bf, 'preview': previews.get(bf.name)} for bf in form], 'pengaturan': True,
    })


# HALAMAN artikel dan halaman statis

def konteks_publik():
    """Data yang dipakai bersama oleh footer / kontak di halaman publik."""
    return {
        'ws': WebSetting.objects.first(),
        'footer_pages': Page.objects.all().order_by('title')[:6],
    }


def artikel_list(request):
    kategori = request.GET.get('kategori')
    q = (request.GET.get('q') or '').strip()
    artikel = Article.objects.filter(status='published').select_related('category', 'author')
    if kategori:
        artikel = artikel.filter(category__slug=kategori)
    if q:
        artikel = artikel.filter(Q(title__icontains=q) | Q(content__icontains=q))
    ctx = konteks_publik()
    ctx.update({'artikel': artikel, 'kategori_list': Category.objects.filter(status='aktif'),
                'kategori_aktif': kategori, 'q': q, 'judul_halaman': 'Artikel'})
    return render(request, 'publik/artikel_list.html', ctx)


def artikel_detail(request, slug):
    art = get_object_or_404(Article.objects.select_related('category', 'author'), slug=slug, status='published')
    Article.objects.filter(pk=art.pk).update(views_count=art.views_count + 1)
    art.refresh_from_db(fields=['views_count'])
    terkait = Article.objects.filter(status='published').exclude(pk=art.pk)
    if art.category:
        terkait = terkait.filter(category=art.category)
    ctx = konteks_publik()
    ctx.update({'art': art, 'terkait': terkait[:3], 'judul_halaman': art.title})
    return render(request, 'publik/artikel_detail.html', ctx)


def halaman_detail(request, slug):
    hal = get_object_or_404(Page, slug=slug)
    ctx = konteks_publik()
    ctx.update({'hal': hal, 'judul_halaman': hal.title})
    return render(request, 'publik/halaman_detail.html', ctx)