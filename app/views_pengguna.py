from django.contrib import messages
from django.shortcuts import redirect, render

from .decorators_pengguna import pengguna_required
from .form_pengguna import formProfile
from .models import UserPengguna


@pengguna_required
def profile_pengguna(request):
    userpengguna, _ = UserPengguna.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = formProfile(request.POST, request.FILES, instance=userpengguna)
        if form.is_valid():
            pengguna = form.save(commit=False)
            pengguna.user = request.user
            pengguna.save()
            request.user.first_name = form.cleaned_data['nama_lengkap']
            request.user.save()
            messages.success(request, 'Data pengguna berhasil disimpan!')
            return redirect('app:profile_pengguna')
        messages.error(request, 'Data profil belum lengkap atau terjadi kesalahan pengisian. Silakan periksa kembali.')
    else:
        form = formProfile(instance=userpengguna)

    context = {
        'title': 'Profil Pengguna',
        'nama': request.user.first_name or request.user.username,
        'userpengguna': userpengguna,
        'photo': userpengguna.photo if userpengguna and userpengguna.photo else None,
        'form': form,
    }
    return render(request, 'pengguna/profil_pengguna.html', context)
