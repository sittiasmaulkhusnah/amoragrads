from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import UserAdmin
from .roles import ROLE_ADMIN


def check_useradmin(function):
    """Pastikan profil admin sudah dilengkapi (foto)."""
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        useradmin = UserAdmin.objects.filter(username=request.user).first()
        request.useradmin = useradmin
        if not useradmin or not useradmin.photo:
            messages.error(request, "Lengkapi data anda terlebih dahulu!")
            return redirect('app:profile_admin')
        return function(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.last_name == ROLE_ADMIN:
            return view_func(request, *args, **kwargs)
        return redirect('app:dashboard')
    return _wrapped_view
