from functools import wraps
from django.shortcuts import redirect

# Role disimpan di kolom last_name (sesuai arahan dosen)
ROLE_ADMIN = 'super admin'
ROLE_USER = 'pengguna'


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.last_name.lower() == ROLE_ADMIN)


def admin_required(view_func):
    """Hanya super admin yang boleh masuk. Pengguna biasa dikembalikan ke profilnya."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login.html')
        if not is_admin(request.user):
            return redirect('/profil.html')
        return view_func(request, *args, **kwargs)
    return wrapper
