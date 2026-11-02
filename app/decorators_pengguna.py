from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import UserPengguna
from .roles import ROLE_PENGGUNA


def check_userpengguna(function):
    """Pastikan profil pengguna sudah dilengkapi."""
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        userpengguna = UserPengguna.objects.filter(user=request.user).first()
        request.userpengguna = userpengguna
        if not userpengguna or not userpengguna.telp or not userpengguna.universitas:
            messages.error(request, "Lengkapi data anda terlebih dahulu!")
            return redirect('app:profile_pengguna')
        return function(request, *args, **kwargs)
    return wrapper


def pengguna_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.last_name != ROLE_PENGGUNA:
            return redirect('app:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
