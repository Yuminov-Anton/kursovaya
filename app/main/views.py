import re
import logging
import json
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, logout
from django.contrib import messages
from django.utils.translation import gettext as _
from .forms import CustomUserCreationForm
from .models import UserProfile
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth import login, authenticate
from .forms import CustomAuthenticationForm
from .forms import UserChangeForm
from django.views.decorators.csrf import csrf_exempt
from .models import UserProfile, Service, ServiceVariant, Order, SupportMessage

logger = logging.getLogger(__name__)

def main(request):
    show_register_modal = False
    show_login_modal = False
    
    services = Service.objects.filter(is_active=True)
    
    # Инициализируем обе формы
    registration_form = CustomUserCreationForm()
    login_form = CustomAuthenticationForm()

    if request.method == 'POST':
        # Определяем, какая форма была отправлена
        if 'login-submit' in request.POST:  # Обработка входа
            logger.info('Получен POST-запрос для входа')
            login_form = CustomAuthenticationForm(request, data=request.POST)
            show_login_modal = True

            if login_form.is_valid():
                username = login_form.cleaned_data.get('username')
                password = login_form.cleaned_data.get('password')
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    messages.success(request, f'Добро пожаловать, {username}!')
                    return redirect('main')
                else:
                    messages.error(request, 'Неверное имя пользователя или пароль.')

        elif 'register-submit' in request.POST:  # Обработка регистрации
            logger.info('Получен POST-запрос для регистрации')
            registration_form = CustomUserCreationForm(request.POST)
            show_register_modal = True

            if registration_form.is_valid():
                logger.info('Форма прошла валидацию')
                try:
                    with transaction.atomic():
                        phone_number = registration_form.cleaned_data.get('phone_number')
                        username = registration_form.cleaned_data.get('username')
                        email = registration_form.cleaned_data.get('email')

                        # Проверяем уникальность телефона
                        if UserProfile.objects.filter(phone_number=phone_number).exists():
                            registration_form.add_error('phone_number', 'Пользователь с таким номером телефона уже существует.')
                            return render(request, 'home.html', {
                                'form': registration_form,
                                'login_form': login_form,
                                'show_register_modal': True,
                                'services': services
                            })

                        # Проверяем уникальность username/email
                        UserModel = get_user_model()
                        if UserModel.objects.filter(username=username).exists() or UserModel.objects.filter(email=email).exists():
                            messages.error(
                                request,
                                "Пользователь с таким именем или email уже зарегистрирован. "
                                "Если это вы — попробуйте <a href='#' onclick=\"showLoginModal();return false;\">войти в аккаунт</a>.",
                                extra_tags='safe'
                            )
                            registration_form.add_error('username', 'Пользователь с таким именем уже существует.')
                            registration_form.add_error('email', 'Пользователь с таким email уже существует.')
                            return render(request, 'home.html', {
                                'form': registration_form,
                                'login_form': login_form,
                                'show_register_modal': True,
                                'services': services
                            })

                        # Создаём пользователя
                        user = registration_form.save()

                        # Создаём профиль вручную с номером телефона
                        try:
                            UserProfile.objects.create(
                                user=user,
                                phone_number=phone_number
                            )
                        except ValidationError as e:
                            error_dict = e.message_dict
                            if 'phone_number' in error_dict:
                                registration_form.add_error('phone_number', error_dict['phone_number'][0])
                            if 'user' in error_dict:
                                registration_form.add_error('username', error_dict['user'][0])
                            return render(request, 'home.html', {
                                'form': registration_form,
                                'login_form': login_form,
                                'show_register_modal': True,
                                'services': services
                            })

                        login(request, user)
                        logger.info(f"User id in session: {request.session.get('_auth_user_id')}")
                        logger.info(f"User is_active: {user.is_active}")
                        messages.success(request, 'Регистрация прошла успешно!')
                        return redirect('main')

                except IntegrityError as e:
                    logger.error(f'Ошибка уникальности данных: {str(e)}')
                    if 'phone_number' in str(e):
                        registration_form.add_error('phone_number', 'Пользователь с таким номером телефона уже существует.')
                    if 'username' in str(e):
                        registration_form.add_error('username', 'Пользователь с таким именем уже существует.')
                except Exception as e:
                    logger.error(f'Ошибка при регистрации: {str(e)}')
                    if isinstance(e, ValidationError):
                        error_dict = getattr(e, 'message_dict', {})
                        if 'phone_number' in error_dict:
                            registration_form.add_error('phone_number', error_dict['phone_number'][0])
                        if 'user' in error_dict:
                            registration_form.add_error('username', error_dict['user'][0])
                    else:
                        registration_form.add_error(None, 'Произошла ошибка при регистрации. Попробуйте еще раз.')
            else:
                logger.error(f'Ошибки формы: {registration_form.errors}')

        # После обработки POST-запроса, если не было redirect, возвращаем страницу с формами и модальными окнами
        return render(request, 'home.html', {
            'form': registration_form,
            'login_form': login_form,
            'show_register_modal': show_register_modal,
            'show_login_modal': show_login_modal,
            'services': services
        })

    # Для GET-запроса и всех остальных случаев возвращаем страницу с формами
    return render(request, 'home.html', {
        'form': registration_form,
        'login_form': login_form,
        'show_register_modal': show_register_modal,
        'show_login_modal': show_login_modal,
        'services': services
    })

def LogoutView(request):
    logout(request)
    messages.success(request, _('Вы успешно вышли из системы.'))
    return redirect('main')

@login_required
def PasswordChangeView(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Ваш пароль был успешно обновлён!')
            return redirect('account')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки ниже.')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'change_password.html', {'form': form})

@login_required
def account_view(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        orders = Order.objects.filter(client=user_profile).order_by('-date', '-time')
    except UserProfile.DoesNotExist:
        orders = []

    return render(request, 'account.html', {
        'orders': orders,
    })

@login_required
def edit_profile_view(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
        is_google_user = getattr(user_profile, 'auth_provider', 'local') == 'google'
    except UserProfile.DoesNotExist:
        is_google_user = False

    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user)
        if is_google_user:
            form.data = form.data.copy()
            form.data['email'] = request.user.email

        try:
            if form.is_valid():
                form.save()
                messages.success(request, 'Профиль успешно обновлён!')
                return redirect('account')
            else:
                messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
        except ValidationError as e:
            # Добавляем ошибки формы вручную, чтобы они отобразились в шаблоне
            for field, errors in e.message_dict.items():
                for error in errors:
                    form.add_error(field, error)
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = UserChangeForm(instance=request.user)

    return render(request, 'edit_profile.html', {
        'form': form,
        'is_google_user': is_google_user,
    })
    
PHONE_REGEX = r'^\+?1?\d{9,15}$'

def parse_duration(duration_str):
    """
    Преобразует строку длительности ('1:30', '2 ч', '2.5 ч', '90 мин', '2.5') в минуты (int).
    """
    duration_str = duration_str.strip().lower().replace(',', '.')
    # 1.5 ч или 2.5
    if 'ч' in duration_str:
        # Пример: '2 ч', '1 ч 30 мин', '2.5 ч'
        hours = 0
        minutes = 0
        # ищем дробные часы
        import re
        match = re.search(r'(\d+(\.\d+)?)\s*ч', duration_str)
        if match:
            hours = float(match.group(1))
        # ищем минуты
        match_min = re.search(r'(\d+)\s*мин', duration_str)
        if match_min:
            minutes = int(match_min.group(1))
        return int(hours * 60 + minutes)
    elif ':' in duration_str:
        # Пример: '1:30'
        h, m = duration_str.split(':')
        return int(h) * 60 + int(m)
    elif 'мин' in duration_str:
        return int(''.join(filter(str.isdigit, duration_str)))
    else:
        # Просто число, возможно дробное
        try:
            return int(float(duration_str) * 60)
        except Exception:
            return 60  # fallback: 1 час

def generate_time_slots(start_hour, end_hour, duration_minutes):
    """
    Генерирует список строк времени с шагом duration_minutes между start_hour и end_hour.
    """
    slots = []
    current = datetime(2000, 1, 1, start_hour, 0)
    end = datetime(2000, 1, 1, end_hour, 0)
    while current + timedelta(minutes=duration_minutes) <= end + timedelta(minutes=1):
        slots.append(current.strftime('%H:%M'))
        current += timedelta(minutes=duration_minutes)
    return slots

def order(request, pk):
    service = get_object_or_404(Service, pk=pk)
    errors = {}
    form_data = {}

    # Получаем variant_id из GET или POST
    variant_id = request.GET.get('variant') or request.POST.get('variant')
    variant_obj = None
    if variant_id:
        variant_obj = ServiceVariant.objects.filter(id=variant_id).first()

    # --- Динамические слоты времени ---
    start_hour = 8
    end_hour = 21
    duration_minutes = parse_duration(service.duration)
    all_time_slots = generate_time_slots(start_hour, end_hour, duration_minutes)

    # Завтрашняя дата для ограничения выбора
    tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()

    # Определяем выбранную дату (для фильтрации слотов)
    selected_date = request.POST.get('date') or request.GET.get('date') or tomorrow

    # Получаем занятые слоты на выбранную дату
    busy_times = set(
        Order.objects.filter(
            service=service,
            date=selected_date,
            service__master=service.master
        ).values_list('time', flat=True)
    )
    # Преобразуем в строки для сравнения с time_slots
    busy_time_strs = {t.strftime('%H:%M') for t in busy_times}
    # Оставляем только свободные слоты
    time_slots = [slot for slot in all_time_slots if slot not in busy_time_strs]

    # no_slots_message = None # Заккоментировал так как сделал AJAX-запрос(JS)
    # if not time_slots:
    #     no_slots_message = "К сожалению, на выбранную дату нет свободных времён для записи."

    if request.method == 'POST':
        form_data = request.POST
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        date = request.POST.get('date')
        time = request.POST.get('time')

        # Проверка номера телефона
        if not re.match(PHONE_REGEX, phone):
            errors['phone'] = "Номер телефона должен быть в формате: '+999999999'. До 15 цифр."

        # Проверка занятости слота (по услуге, дате, времени и мастеру)
        if not errors:
            try:
                time_obj = datetime.strptime(time, "%H:%M").time()
            except Exception:
                errors['time'] = "Некорректный формат времени."
                return render(request, 'order.html', {
                    'service': service,
                    'variant_obj': variant_obj,
                    'errors': errors,
                    'form_data': form_data,
                    'time_slots': time_slots,
                    'tomorrow': tomorrow,
                    # 'no_slots_message': no_slots_message,
                })

            is_busy = Order.objects.filter(
                service=service,
                date=date,
                time=time_obj,
                service__master=service.master
            ).exists()
            if is_busy:
                errors['time'] = "Это время уже занято для выбранной услуги и мастера. Пожалуйста, выберите другое время."

        if not errors:
            client, created = UserProfile.objects.get_or_create(phone_number=phone)
            try:
                with transaction.atomic():
                    Order.objects.create(
                        client=client,
                        service=service,
                        variant=variant_obj,
                        date=date,
                        time=time_obj
                    )
                messages.success(request, 'Спасибо за вашу запись! Мы свяжемся с вами для подтверждения.')
                return redirect('order', pk=pk)
            except IntegrityError:
                errors['time'] = "Это время уже занято для выбранной услуги и мастера. Пожалуйста, выберите другое время."

        return render(request, 'order.html', {
            'service': service,
            'variant_obj': variant_obj,
            'errors': errors,
            'form_data': form_data,
            'time_slots': time_slots,
            'tomorrow': tomorrow,
            # 'no_slots_message': no_slots_message,
        })

    # GET-запрос
    return render(request, 'order.html', {
        'service': service,
        'variant_obj': variant_obj,
        'errors': errors,
        'form_data': form_data,
        'time_slots': time_slots,
        'tomorrow': tomorrow,
        # 'no_slots_message': no_slots_message,
    })
    
def service_detail(request, pk):
    service = get_object_or_404(Service, pk=pk)
    variants = service.variants.all()
    examples = service.examples.all() if hasattr(service, 'examples') else []
    variant_id = request.GET.get('variant')
    variant_obj = None
    if variant_id:
        variant_obj = variants.filter(id=variant_id).first()
    # Примеры работ можно хранить в отдельной модели или как изображения, связанные с услугой
    examples = service.examples.all() if hasattr(service, 'examples') else []
    return render(request, 'service_detail.html', {
        'service': service,
        'variants': variants,
        'examples': examples,
        'variant_obj': variant_obj,
    })

def ajax_get_time_slots(request):
    service_id = request.GET.get('service_id')
    date = request.GET.get('date')
    variant_id = request.GET.get('variant_id')
    from .models import Service, ServiceVariant, Order

    service = Service.objects.get(id=service_id)
    variant_obj = None
    if variant_id:
        try:
            variant_obj = ServiceVariant.objects.get(id=variant_id)
        except ServiceVariant.DoesNotExist:
            variant_obj = None

    # Генерация всех возможных слотов
    start_hour = 8
    end_hour = 21
    duration_minutes = parse_duration(service.duration)
    all_time_slots = generate_time_slots(start_hour, end_hour, duration_minutes)

    # Получаем занятые слоты на выбранную дату
    busy_times = set(
        Order.objects.filter(
            service=service,
            date=date,
            service__master=service.master
        ).values_list('time', flat=True)
    )
    busy_time_strs = {t.strftime('%H:%M') for t in busy_times}
    time_slots = [slot for slot in all_time_slots if slot not in busy_time_strs]

    no_slots_message = None
    if not time_slots:
        no_slots_message = "К сожалению, на выбранную дату нет свободных времён для записи."

    return JsonResponse({
        "time_slots": time_slots,
        "no_slots_message": no_slots_message,
    })
    
# ПРИМЕР ОТПРАВКИ ПИСЬМА НА ПОЧТУ   
# from django.views.decorators.csrf import csrf_exempt
# from django.http import JsonResponse
# import json
# from django.core.mail import send_mail

# @csrf_exempt
# def support_chat(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             email = data.get('email')
#             message = data.get('message')
#             if not email or not message:
#                 return JsonResponse({'success': False, 'error': 'Заполните все поля.'})
#             # Отправка письма на почту поддержки
#             send_mail(
#                 subject='Вопрос с сайта',
#                 message=f'От: {email}\n\n{message}',
#                 from_email=None,
#                 recipient_list=['support@yourdomain.ru'],
#             )
#             return JsonResponse({'success': True})
#         except Exception as e:
#             return JsonResponse({'success': False, 'error': str(e)})
#     return JsonResponse({'success': False, 'error': 'Только POST'})

@csrf_exempt
def support_chat_send(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('message')
            email = data.get('email')
            user = request.user if request.user.is_authenticated else None
            if not text or not email:
                return JsonResponse({'success': False, 'error': 'Заполните все поля.'})
            msg = SupportMessage.objects.create(
                user=user,
                email=email,
                text=text,
                is_from_support=False
            )
            return JsonResponse({'success': True, 'message': {
                "id": msg.id,
                "text": msg.text,
                "is_from_support": msg.is_from_support,
                "created_at": msg.created_at.strftime("%d.%m.%Y %H:%M"),
            }})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Только POST'})

def support_chat_history(request):
    email = request.GET.get('email')
    user = request.user if request.user.is_authenticated else None
    if user:
        messages = SupportMessage.objects.filter(user=user).order_by('created_at')
    elif email:
        messages = SupportMessage.objects.filter(email=email).order_by('created_at')
    else:
        messages = []
    data = [
        {
            "id": m.id,
            "text": m.text,
            "is_from_support": m.is_from_support,
            "created_at": m.created_at.strftime("%d.%m.%Y %H:%M"),
        }
        for m in messages
    ]
    return JsonResponse({"messages": data})

@staff_member_required
def support_operator_dashboard(request):
    # Группируем чаты по email (или user)
    # Показываем только уникальные email/user, последние сообщения
    chats = {}
    for msg in SupportMessage.objects.order_by('-created_at'):
        key = msg.user_id or msg.email
        if key not in chats:
            chats[key] = msg
    # Сортируем по времени последнего сообщения
    chat_list = sorted(chats.values(), key=lambda m: m.created_at, reverse=True)
    return render(request, "support_operator_dashboard.html", {"chats": chat_list})

@staff_member_required
def support_operator_chat(request, chat_id):
    user = None
    messages = []
    chat_name = chat_id
    chat_email = chat_id

    # Попробуем найти пользователя по id (если chat_id — число)
    try:
        user = User.objects.get(pk=int(chat_id))
        messages = SupportMessage.objects.filter(user=user).order_by('created_at')
        chat_name = user.username
        chat_email = user.email
    except (User.DoesNotExist, ValueError):
        # Если не получилось — считаем chat_id email'ом
        messages = SupportMessage.objects.filter(email=chat_id).order_by('created_at')
        chat_name = chat_id
        chat_email = chat_id

    if request.method == "POST":
        text = request.POST.get("reply")
        if text:
            SupportMessage.objects.create(
                user=user,
                email=chat_email,
                text=text,
                is_from_support=True
            )
            return redirect(request.path)

    return render(request, "support_operator_chat.html", {
        "messages": messages,
        "chat_name": chat_name,
        "chat_email": chat_email,
    })