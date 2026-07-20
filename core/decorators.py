from functools import wraps
from django.shortcuts import redirect

def redirect_by_role(user):
    role = user.profile.role

    if role == 'purchasing':
        return redirect('dashboard_purchasing')
    elif role == 'produksi':
        return redirect('dashboard_produksi')
    elif role == 'penjualan':
        return redirect('dashboard_penjualan')
    elif role == 'qualitycontrol':
        return redirect('dashboard_qc')

    return redirect('login')


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            if not hasattr(request.user, 'profile'):
                return redirect('login')

            if request.user.profile.role not in roles:
                return redirect_by_role(request.user)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator