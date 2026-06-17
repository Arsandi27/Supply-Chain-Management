from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            role = user.profile.role

            if role == 'purchasing':
                return redirect('dashboard_purchasing')
            elif role == 'produksi':
                return redirect('dashboard_produksi')
            elif role == 'penjualan':
                return redirect('dashboard_penjualan')
            elif role == 'qualitycontrol':
                return redirect('dashboard_qc')
        else:
            messages.error(request, 'Username atau password salah')

    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')
