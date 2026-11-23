import re

from django import template
from django.utils.html import escape, strip_tags
from django.utils.safestring import mark_safe

from app.models import rp
from app.sanitasi import punya_html, sanitasi

register = template.Library()

_BOLD2 = re.compile(r'\*\*(?=\S)(.+?)(?<=\S)\*\*')
_BOLD1 = re.compile(r'\*(?=\S)(.+?)(?<=\S)\*')
_ITALIC = re.compile(r'(?<![\w/])_(?=\S)(.+?)(?<=\S)_(?![\w/])')


def _inline(teks):
    """Tebal dan miring di dalam satu baris. Teks sudah di-escape lebih dulu."""
    teks = _BOLD2.sub(r'<strong>\1</strong>', teks)
    teks = _BOLD1.sub(r'<strong>\1</strong>', teks)
    return _ITALIC.sub(r'<em>\1</em>', teks)


@register.filter(name='format_konten')
def format_konten(value):
    """Mengubah teks isi artikel/halaman menjadi HTML sederhana.

    *tebal* atau **tebal**   -> tebal
    _miring_                 -> miring
    ## Subjudul              -> subjudul
    - poin                   -> daftar poin
    Baris kosong memisahkan paragraf. HTML dari pengguna selalu di-escape.
    """
    if not value:
        return ''
    if punya_html(value):   # isi dari editor Summernote
        return mark_safe(sanitasi(value))
    html, paragraf, daftar = [], [], []

    def tutup_paragraf():
        if paragraf:
            html.append('<p>' + '<br>'.join(paragraf) + '</p>')
            paragraf.clear()

    def tutup_daftar():
        if daftar:
            html.append('<ul>' + ''.join(f'<li>{x}</li>' for x in daftar) + '</ul>')
            daftar.clear()

    for baris in str(value).replace('\r\n', '\n').split('\n'):
        b = baris.strip()
        if not b:
            tutup_paragraf(); tutup_daftar()
        elif b.startswith('## '):
            tutup_paragraf(); tutup_daftar()
            html.append('<h2>' + _inline(escape(b[3:].strip())) + '</h2>')
        elif b.startswith('- '):
            tutup_paragraf()
            daftar.append(_inline(escape(b[2:].strip())))
        else:
            tutup_daftar()
            paragraf.append(_inline(escape(b)))
    tutup_paragraf(); tutup_daftar()
    return mark_safe(''.join(html))


@register.filter(name='ringkas')
def ringkas(value, jumlah_kata=18):
    """Ringkasan polos untuk kartu artikel (tanpa tanda format)."""
    teks = strip_tags(str(value or '')).replace('&nbsp;', ' ')
    teks = re.sub(r'(?m)^\s*(##\s+|-\s+)', '', teks)
    teks = teks.replace('*', '')
    teks = re.sub(r'(?<![\w/])_|_(?![\w/])', '', teks)
    kata = teks.split()
    n = int(jumlah_kata)
    return ' '.join(kata[:n]) + ('…' if len(kata) > n else '')


@register.filter(name='rupiah')
def rupiah(value):
    return rp(value)
