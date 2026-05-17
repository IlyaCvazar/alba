import flet as ft
import random
import time
import subprocess

def main(page: ft.Page):
    # Настройки страницы (Единый стиль окна)
    page.title = "Albakryak Messenger"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_width = 400
    page.window_height = 650
    page.padding = 25

    # ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ ХРАНЕНИЯ ДАННЫХ
    user_status = "Привет, я Иван"
    
    # Словарь для хранения истории сообщений
    chat_history = {}

    # Имитация базы данных пользователей для работы поиска по ID
    all_users = ["Алексей", "Мария", "Дмитрий", "Разработчики Flet", "Учеба - Программирование", "Анна", "Виктор"]
    users_db = {f"id_{abs(hash(name)) % 1000000}": name for name in all_users}

    # Основной контейнер, в котором плавно меняются все экраны
    form_container = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15,
        expand=True
    )

    # =========================================================================
    # ШАГ 1: ЭКРАН АУТЕНТИФИКАЦИИ (ВХОД / РЕГИСТРАЦИЯ)
    # =========================================================================
    def show_login(e=None):
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        form_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        login_field = ft.TextField(label="Логин", width=320, prefix_icon="person")
        password_field = ft.TextField(label="Пароль", width=320, password=True, can_reveal_password=True, prefix_icon="lock")

        def on_login_click(e):
            login_field.error_text = None
            password_field.error_text = None
            has_error = False

            if not login_field.value or not login_field.value.strip():
                login_field.error_text = "Введите логин"
                has_error = True
            if not password_field.value or not password_field.value.strip():
                password_field.error_text = "Введите пароль"
                has_error = True

            if has_error:
                page.update()
            else:
                print(f"Вход: Логин={login_field.value.strip()}, Пароль={password_field.value.strip()}")
                show_chats()

        form_container.controls.clear()
        form_container.controls.extend([
            ft.Text("Вход в аккаунт", size=26, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            login_field,
            password_field,
            ft.Container(height=10),
            ft.Button("Войти", width=320, height=45, on_click=on_login_click),
            ft.TextButton("Нет аккаунта? Зарегистрироваться", on_click=show_register)
        ])
        page.update()

    def show_register(e=None):
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        form_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        login_field = ft.TextField(label="Логин", width=320, prefix_icon="person")
        password_field = ft.TextField(label="Пароль", width=320, password=True, can_reveal_password=True, prefix_icon="lock")
        age_field = ft.TextField(label="Возраст", width=320, keyboard_type=ft.KeyboardType.NUMBER, prefix_icon="calendar_today")

        def on_register_click(e):
            login_field.error_text = None
            password_field.error_text = None
            age_field.error_text = None
            has_error = False

            if not login_field.value or not login_field.value.strip():
                login_field.error_text = "Придумайте логин"
                has_error = True
            if not password_field.value or not password_field.value.strip():
                password_field.error_text = "Придумайте пароль"
                has_error = True
            if not age_field.value or not age_field.value.strip():
                age_field.error_text = "Укажите возраст"
                has_error = True

            if has_error:
                page.update()
            else:
                print(f"Регистрация: Логин={login_field.value.strip()}, Пароль={password_field.value.strip()}, Возраст={age_field.value.strip()}")
                show_email_binding()

        form_container.controls.clear()
        form_container.controls.extend([
            ft.Text("Регистрация", size=26, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            login_field,
            password_field,
            age_field,
            ft.Container(height=10),
            ft.Button("Зарегистрироваться", width=320, height=45, on_click=on_register_click),
            ft.TextButton("Уже есть аккаунт? Войти", on_click=show_login)
        ])
        page.update()

    # =========================================================================
    # ШАГ 2: ПРИВЯЗКА ПОЧТЫ (ТОЛЬКО ПОСЛЕ РЕГИСТРАЦИИ)
    # =========================================================================
    def show_email_binding():
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        form_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        email_field = ft.TextField(label="Email", width=320, keyboard_type=ft.KeyboardType.EMAIL, prefix_icon="mail")

        def on_bind_click(e):
            email_field.error_text = None
            if not email_field.value or not email_field.value.strip():
                email_field.error_text = "Введите корректный Email"
                page.update()
            else:
                print(f"Привязка почты: Email={email_field.value.strip()}")
                show_chats()

        form_container.controls.clear()
        form_container.controls.extend([
            ft.Text("Привязать почту", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Container(height=15),
            email_field,
            ft.Container(height=10),
            ft.Button("Привязать", width=320, height=45, on_click=on_bind_click)
        ])
        page.update()

    # =========================================================================
    # ШАГ 3: ГЛАВНЫЙ ЭКРАН (СПИСОК ЧАТОВ + ПОИСК ПО ID)
    # =========================================================================
    def show_chats(e=None):
        page.vertical_alignment = ft.MainAxisAlignment.START
        form_container.horizontal_alignment = ft.CrossAxisAlignment.START
        
        def on_settings_click(e):
            show_settings()

        def on_chat_click(chat_name):
            show_chat_window(chat_name)

        # Обработчик отправки ID в строку поиска
        def on_search_submit(e):
            search_id = search_field.value.strip()
            if not search_id:
                return
            
            # Проверяем наличие ID в нашей базе данных
            if search_id in users_db:
                found_name = users_db[search_id]
                show_user_profile(found_name)  # Открываем профиль найденного человека
            else:
                # Если не нашли, выводим красное уведомление
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Пользователь с ID '{search_id}' не найден!"),
                    bgcolor="#ef4444"
                )
                page.snack_bar.open = True
                page.update()

        top_bar = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text("Настройки", size=12, weight=ft.FontWeight.W_500, color="white"),
                    padding=10,
                    bgcolor="#1f2937", 
                    border_radius=10,
                    on_click=on_settings_click
                ),
                ft.CircleAvatar(content=ft.Icon("person", color="white"), radius=14, bgcolor="#1e3a8a"),
                ft.VerticalDivider(width=10),
                ft.Text("Чаты", size=22, weight=ft.FontWeight.BOLD, color="#1f2937"),
            ],
            alignment=ft.MainAxisAlignment.START
        )

        # Поле поиска с привязанным событием on_submit
        search_field = ft.TextField(
            label="Поиск по ID", 
            width=340, 
            prefix_icon="search", 
            height=45, 
            hint_text="Вставьте ID и нажмите Enter",
            on_submit=on_search_submit
        )

        chats_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=430, horizontal_alignment=ft.CrossAxisAlignment.START)
        
        for name in all_users[:5]:  # Выводим первые 5 пользователей как чаты по умолчанию
            chat_item = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.CircleAvatar(content=ft.Text(name[0], color="white", weight=ft.FontWeight.BOLD), bgcolor="#1e3a8a"),
                        ft.Text(name, size=16, weight=ft.FontWeight.W_500, color="white")
                    ],
                    spacing=12,
                    alignment=ft.MainAxisAlignment.START
                ),
                padding=12,
                width=340,
                bgcolor="#1f2937", 
                border_radius=12,
                on_click=lambda e, chat_name=name: on_chat_click(chat_name)
            )
            chats_column.controls.append(chat_item)

        form_container.controls.clear()
        form_container.controls.extend([top_bar, search_field, ft.Divider(height=1), chats_column])
        page.update()

    # =========================================================================
    # ШАГ 4: НАСТРОЙКИ СОБСТВЕННОГО ПРОФИЛЯ
    # =========================================================================
    def show_settings():
        nonlocal user_status
        page.vertical_alignment = ft.MainAxisAlignment.START
        form_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        def on_avatar_click(e):
            print("Действие: Изменить аватарку")

        def on_save_click(e):
            nonlocal user_status
            user_status = about_field.value.strip()
            print(f"Статус 'О себе' сохранён: {user_status}")
            show_chats()

        def on_delete_click(e):
            print("Профиль удален!")
            show_login()

        settings_bar = ft.Row(
            controls=[
                ft.TextButton(content=ft.Text("<- Назад", size=16, weight=ft.FontWeight.W_500, color="#1e3a8a"), on_click=show_chats),
                ft.VerticalDivider(width=10),
                ft.Text("Настройки", size=22, weight=ft.FontWeight.BOLD),
            ],
            alignment=ft.MainAxisAlignment.START
        )

        about_field = ft.TextField(label="О себе", width=320, multiline=True, min_lines=2, max_lines=3, value=user_status, hint_text="Расскажите о себе...")

        form_container.controls.clear()
        form_container.controls.extend([
            settings_bar, ft.Container(height=10),
            ft.TextButton(content=ft.Column(controls=[ft.CircleAvatar(content=ft.Icon("person", size=40), radius=40), ft.Text("Изменить аватарку", size=14)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), on_click=on_avatar_click),
            ft.Container(height=10), about_field, ft.Container(height=20),
            ft.Button("Сохранить", width=320, height=45, on_click=on_save_click),
            ft.TextButton("Удалить профиль", on_click=on_delete_click)
        ])
        page.update()

    # =========================================================================
    # ШАГ 5: ЭКРАН ПРОФИЛЯ СОБЕСЕДНИКА (МГНОВЕННОЕ КОПИРОВАНИЕ ID)
    # =========================================================================
    def show_user_profile(user_name):
        page.vertical_alignment = ft.MainAxisAlignment.START
        form_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        # 1. Ищем существующий ID или генерируем его, если пользователя не было в базе
        user_id = None
        for uid, name in users_db.items():
            if name == user_name:
                user_id = uid
                break
        if not user_id:
            user_id = f"id_{abs(hash(user_name)) % 1000000}"

        # 2. Функция безопасного копирования через утилиту ОС Windows
        def copy_id_to_clipboard(e):
            try:
                subprocess.run(f"echo {user_id}| clip", shell=True, check=True)
            except Exception as ex:
                print(f"Ошибка системного копирования: {ex}")
            
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"ID {user_id} успешно скопирован в буфер обмена!"),
                action="Отлично",
                duration=2000
            )
            page.snack_bar.open = True
            page.update()

        # 3. Верхняя панель навигации
        profile_bar = ft.Row(
            controls=[
                ft.TextButton(
                    content=ft.Text("<- Назад", size=16, weight=ft.FontWeight.W_500, color="#1e3a8a"), 
                    on_click=lambda _: show_chat_window(user_name)
                ),
                ft.VerticalDivider(width=10),
                ft.Text("Профиль", size=22, weight=ft.FontWeight.BOLD),
            ],
            alignment=ft.MainAxisAlignment.START
        )

        # 4. Сборка интерфейса
        form_container.controls.clear()
        form_container.controls.extend([
            profile_bar,
            ft.Container(height=20),
            ft.CircleAvatar(
                content=ft.Text(user_name[0], size=32, color="white", weight=ft.FontWeight.BOLD), 
                radius=50, 
                bgcolor="#1e3a8a"
            ),
            ft.Container(height=10),
            ft.Text(user_name, size=24, weight=ft.FontWeight.BOLD, color="#1f2937"),
            
            # Текст ID + Кнопка копирования
            ft.Row(
                controls=[
                    ft.Text(f"ID: {user_id}", size=14, color="grey"),
                    ft.IconButton(
                        icon=ft.Icons.COPY,        
                        icon_size=16, 
                        icon_color="grey",
                        tooltip="Скопировать ID",
                        on_click=copy_id_to_clipboard  
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=5
            ),
            
            ft.Container(height=15),
            ft.Divider(height=1),
            ft.Container(height=15),
            
            # Контейнер "О себе"
            ft.Container(
                content=ft.Column([
                    ft.Text("О себе:", size=14, weight=ft.FontWeight.BOLD, color="grey"),
                    ft.Text("Привет! Я пользуюсь Albakryak Messenger. Рад общению!", size=16, color="#1f2937")
                ]),
                width=320,
                padding=10,
                border=ft.Border.all(1, "lightgrey"),  
                border_radius=10
            ),
            ft.Container(height=20),
            ft.Button(
                "Написать сообщение", 
                width=320, 
                height=45, 
                on_click=lambda _: show_chat_window(user_name)
            )
        ])
        page.update()

    # =========================================================================
    # ШАГ 6: ЭКРАН ЧАТА
    # =========================================================================
    def show_chat_window(chat_name):
        nonlocal chat_history
        page.vertical_alignment = ft.MainAxisAlignment.START
        form_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        bot_phrases = [
            "Привет! Давно не виделись. Как дела?",
            "О, круто! Расскажи подробнее.",
            "Я сейчас немного занят по учебе, отвечу чуть позже, ладно?",
            "Ха-ха, забавно! Твой Albakryak работает отлично!",
            "Слушай, а ты пробовал запустить это на C++?",
            "Интересная мысль, надо обдумать.",
            "Понял тебя. Ладно, я погнал, скоро спишемся!",
            "Абсолютно согласен с тобой."
        ]

        if chat_name not in chat_history:
            chat_history[chat_name] = []

        def append_message_to_ui(text, sender):
            if sender == "user":
                chat_messages.controls.append(
                    ft.Row(
                        controls=[ft.Container(content=ft.Text(text, size=15, color="white"), padding=10, bgcolor="#1e3a8a", border_radius=10, width=240)],
                        alignment=ft.MainAxisAlignment.END
                    )
                )
            else:
                chat_messages.controls.append(
                    ft.Row(
                        controls=[ft.Container(content=ft.Text(text, size=15, color="white"), padding=10, bgcolor="#374151", border_radius=10, width=240)],
                        alignment=ft.MainAxisAlignment.START
                    )
                )

        def on_send_message(e):
            if message_field.value and message_field.value.strip():
                user_text = message_field.value.strip()
                
                chat_history[chat_name].append({"sender": "user", "text": user_text})
                append_message_to_ui(user_text, "user")
                
                message_field.value = ""
                page.update()

                time.sleep(0.1)

                random_reply = random.choice(bot_phrases)
                chat_history[chat_name].append({"sender": "bot", "text": random_reply})
                append_message_to_ui(random_reply, "bot")
                
                page.update()

        # Кликабельная область профиля в шапке чата
        user_clickable_zone = ft.Container(
            content=ft.Row(
                controls=[
                    ft.CircleAvatar(content=ft.Text(chat_name[0], color="white"), radius=15, bgcolor="#1f2937"),
                    ft.Text(chat_name, size=18, weight=ft.FontWeight.BOLD, color="#1f2937"),
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            on_click=lambda _: show_user_profile(chat_name),
            padding=5,
            border_radius=8
        )

        chat_bar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.TextButton(content=ft.Text("<- Назад", size=16, weight=ft.FontWeight.W_500, color="#1e3a8a"), on_click=lambda _: show_chats()),
                    user_clickable_zone, 
                    ft.Container(width=40) 
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            width=340, padding=5
        )

        chat_messages = ft.Column(
            controls=[ft.Row(controls=[ft.Text(f"Переписка с {chat_name}", size=13, color="grey")], alignment=ft.MainAxisAlignment.CENTER)],
            spacing=10, scroll=ft.ScrollMode.AUTO, height=400, width=340
        )

        for msg in chat_history[chat_name]:
            append_message_to_ui(msg["text"], msg["sender"])

        animated_chat_box = ft.Container(
            content=chat_messages, bgcolor="#111827", padding=10, border_radius=15, opacity=0, 
            animate_opacity=ft.Animation(600, ft.AnimationCurve.EASE_OUT)
        )

        message_field = ft.TextField(
            hint_text="Введите сообщение...", width=230, height=45, color="white",
            hint_style=ft.TextStyle(color="grey"), filled=True, fill_color="#1f2937",
            focused_border_color="#3b82f6", autofocus=True, on_submit=on_send_message  
        )

        send_button = ft.Container(
            content=ft.Text("Отправить", size=11, weight=ft.FontWeight.BOLD, color="white"),
            padding=12, bgcolor="#1f2937", border_radius=10, on_click=on_send_message   
        )

        bottom_input_bar = ft.Container(
            content=ft.Row(controls=[message_field, send_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            width=340
        )

        form_container.controls.clear()
        form_container.controls.extend([chat_bar, ft.Divider(height=1, color="#374151"), animated_chat_box, bottom_input_bar])
        
        page.update()
        animated_chat_box.opacity = 1
        page.update()

    # Запуск стартового экрана
    show_login()
    page.add(form_container)

if __name__ == "__main__":
    ft.run(main)