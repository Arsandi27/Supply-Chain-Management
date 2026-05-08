from django.http import HttpResponseForbidden

def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                if hasattr(request.user, 'profile'):
                    if request.user.profile.role in allowed_roles:
                        return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("Anda tidak memiliki akses")
        return wrapper
    return decorator
