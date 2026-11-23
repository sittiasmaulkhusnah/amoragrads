"""Membersihkan HTML dari editor Summernote supaya aman ditampilkan.

Memakai library `bleach` (pip install "bleach[css]"). Kalau belum terpasang,
semua tag dibuang (aman, tapi format teks hilang) sampai bleach dipasang.
"""
import re

from django.utils.html import strip_tags

TAG = ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'strike', 'h1', 'h2', 'h3', 'h4', 'blockquote',
       'ul', 'ol', 'li', 'a', 'img', 'span', 'div', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
       'pre', 'code', 'sub', 'sup']
ATRIBUT = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'width', 'height', 'style'],
    '*': ['style', 'class'],
}
GAYA = ['color', 'background-color', 'font-size', 'font-weight', 'font-style', 'text-decoration',
        'text-align', 'width', 'height', 'max-width', 'float', 'margin', 'margin-left', 'margin-right']
PROTOKOL = ['http', 'https', 'mailto', 'tel']

try:  # pragma: no cover
    import bleach
    from bleach.css_sanitizer import CSSSanitizer
    _CSS = CSSSanitizer(allowed_css_properties=GAYA)
    BLEACH_ADA = True
except Exception:  # bleach / tinycss2 belum terpasang
    BLEACH_ADA = False

_ADA_HTML = re.compile(r'<\s*(p|br|div|span|strong|b|em|i|u|h[1-6]|ul|ol|li|a|img|table|blockquote)[\s>/]', re.I)


def punya_html(teks):
    return bool(_ADA_HTML.search(teks or ''))


def sanitasi(html):
    html = html or ''
    if not BLEACH_ADA:
        return strip_tags(html)
    bersih = bleach.clean(html, tags=TAG, attributes=ATRIBUT, protocols=PROTOKOL,
                          css_sanitizer=_CSS, strip=True, strip_comments=True)
    # gambar hanya dari situs sendiri (/media/...) atau https; buang data: dan lainnya
    bersih = re.sub(r'<img\b[^>]*\bsrc="(?!/|https?://)[^"]*"[^>]*>', '', bersih, flags=re.I)
    return bersih
