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

                # 1. Если передана функция/лямбда (для динамического извлечения параметров из view)
                if callable(redirect_after_login):
                    res = redirect_after_login(request, *args, **kwargs)
                    target_url = res if res.startswith('/') else reverse(res)

                # 2. Если передан кортеж/список: ('route_name', kwargs_dict) или ('route_name', args_list, kwargs_dict)
                elif isinstance(redirect_after_login, (tuple, list)):
                    route_name = redirect_after_login[0]
                    url_args = redirect_after_login[1] if len(redirect_after_login) > 1 else None
                    url_kwargs = redirect_after_login[2] if len(redirect_after_login) > 2 else None

                    # Если 2-й элемент — это словарь kwargs: ('item_detail', {'pk': 10})
                    if isinstance(url_args, dict) and url_kwargs is None:
                        url_kwargs = url_args
                        url_args = None

                    target_url = reverse(route_name, args=url_args, kwargs=url_kwargs)

                # 3. Если передано обычное имя маршрута без параметров
                elif redirect_after_login:
                    target_url = reverse(redirect_after_login)

                # 4. По умолчанию редиректим на текущий URL (сохраняя query-параметры `?page=2`)
                else:
                    target_url = request.get_full_path()

                return redirect(f"{login_url}?next={target_url}")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
