from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.conf import settings

from .forms import CustomUserCreationForm, CustomAuthenticationForm, TelegramVerifyCodeForm, UserProfileForm
from .models import TelegramVerificationCode
from .services import send_telegram_verification_code  # Если вынесли в services.py


@login_required
def profile_view(request):
    user = request.user
    old_tg_username = user.telegram_username

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            new_tg_username = form.cleaned_data.get('telegram_username')
            updated_user = form.save(commit=False)

            # Если пользователь изменил или впервые добавил Telegram username
            if new_tg_username and (new_tg_username != old_tg_username or not user.is_telegram_verified):
                updated_user.is_telegram_verified = False
                updated_user.save()

                # Создаем или обновляем код подтверждения
                tg_code_obj, _ = TelegramVerificationCode.objects.get_or_create(user=user)
                tg_code_obj.generate_code()

                # Отправляем код через API бота
                api_success = send_telegram_verification_code(new_tg_username, tg_code_obj.code)

                if api_success:
                    messages.info(
                        request,
                        'Код подтверждения отправлен в Telegram бота. Введите его для завершения привязки.'
                    )
                else:
                    messages.error(
                        request,
                        'Не удалось отправить код в Telegram. Убедитесь, что вы запустили бота и верно указали username.'
                    )

                return redirect('users:verify_telegram')

            # Если Telegram удалили из формы
            if not new_tg_username:
                updated_user.is_telegram_verified = False
                updated_user.telegram_id = None

            updated_user.save()
            messages.success(request, 'Данные профиля успешно обновлены.')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=user)

    context = {
        'form': form,
        'bot_username': settings.TG_BOT_USERNAME  # Берем из settings вместо хардкода
    }
    return render(request, 'users/profile.html', context)


@login_required
def verify_telegram_view(request):
    # Если Telegram уже подтвержден или не указан никнейм
    if not request.user.telegram_username or request.user.is_telegram_verified:
        return redirect('users:profile')

    try:
        tg_code_obj = request.user.tg_code
    except TelegramVerificationCode.DoesNotExist:
        tg_code_obj = TelegramVerificationCode.objects.create(user=request.user)
        tg_code_obj.generate_code()
        # Если код создался заново, сразу отправляем его
        send_telegram_verification_code(request.user.telegram_username, tg_code_obj.code)

    if request.method == 'POST':
        form = TelegramVerifyCodeForm(request.POST)
        if form.is_valid():
            input_code = form.cleaned_data.get('code')
            if input_code == tg_code_obj.code:
                user = request.user
                user.is_telegram_verified = True
                user.save()
                tg_code_obj.delete()

                messages.success(request, 'Ваш Telegram успешно привязан!')
                return redirect('users:profile')
            else:
                messages.error(request, 'Неверный код подтверждения. Попробуйте еще раз.')
    else:
        form = TelegramVerifyCodeForm()

    context = {
        'form': form,
        'bot_username': settings.TG_BOT_USERNAME,
        'user_tg': request.user.telegram_username
    }
    return render(request, 'users/verify_telegram.html', context)


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home:index')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}! Регистрация прошла успешно.')
            return redirect('home:index')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {'form': form})


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f'С возвращением, {form.get_user().username}!')
        return super().form_valid(form)


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из аккаунта.')
    return redirect('home:index')
