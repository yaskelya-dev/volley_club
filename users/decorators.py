from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


def login_required_message(message="Для доступа к этой странице необходимо войти в систему", redirect_after_login=None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, message)

                login_url = reverse('users:login')
                if redirect_after_login:
                    target_url = reverse(redirect_after_login)
                else:
                    target_url = request.path

                return redirect(f"{login_url}?next={target_url}")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
