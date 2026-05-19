import flet as ft
import random
import time
import subprocess

def main(page: ft.Page):

    page.title = "Albakryak Messenger"
    # Элементы теперь распределяются по всей ширине, убираем жесткое центрирование корпуса
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.bgcolor = ft.Colors.BLUE_GREY_200  # Сделали приятный темный фон для всего приложения
    
    # Стартовые размеры окна (теперь это просто начальный размер, его можно крутить как угодно)
    page.window_width = 450
    page.window_height = 750
    page.padding = 15

    # ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ ХРАНЕНИЯ ДАННЫХ
    user_status = "Привет, я Иван"
    user_avatar = None
    chat_history = {}

    all_users = ["Алексей", "Мария", "Дмитрий", "Разработчики Flet", "Учеба - Программирование", "Анна", "Виктор"]
    users_db = {f"id_{abs(hash(name)) % 1000000}": name for name in all_users}

    # Главный контейнер теперь автоматически заполняет всё окно благодаря expand=True
    form_container = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        spacing=15,
        expand=True
    )

    # =========================================================================
    # ШАГ 1: ЭКРАН АУТЕНТИФИКАЦИИ (ВХОД / РЕГИСТРАЦИЯ)
    # =========================================================================
    def show_login(e=None):
        form_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # Вместо фиксированной ширины используем max_width, чтобы на ультрашироких мониторах поля не растягивались во всю стену
        login_field = ft.TextField(label="Логин", max_length=400, prefix_icon="person")
        password_field = ft.TextField(label="Пароль", max_length=400, password=True, can_reveal_password=True, prefix_icon="lock")

        def on_login_click(e):
            if not login_field.value or not login_field.value.strip():
                return
            if not password_field.value or not password_field.value.strip():
                return
            show_chats()

        form_container.controls.clear()
        form_container.controls.extend([
            ft.Container(height=40), # Отступ сверху
            ft.Text("Вход в аккаунт", size=26, weight=ft.FontWeight.BOLD, color="white"),
            ft.Container(height=10),
            login_field,
            password_field,
            ft.Container(height=10),
            ft.Button("Войти", width=400, height=45, on_click=on_login_click),
            ft.TextButton("Нет аккаунта? Зарегистрироваться", on_click=show_register, style=ft.ButtonStyle(color="white"))
        ])
        page.update()

    def show_register(e=None):
        form_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        login_field = ft.TextField(label="Логин", max_width=400, prefix_icon="person")
        password_field = ft.TextField(label="Пароль", max_width=400, password=True, can_reveal_password=True, prefix_icon="lock")
        age_field = ft.TextField(label="Возраст", max_width=400, keyboard_type=ft.KeyboardType.NUMBER, prefix_icon="calendar_today")

        def on_register_click(e):
            if not login_field.value or not login_field.value.strip():
                return
            if not password_field.value or not password_field.value.strip():
                return
            if not age_field.value or not age_field.value.strip():
                return
            show_email_binding()

        form_container.controls.clear()
        form_container.controls.extend([
            ft.Container(height=40),
            ft.Text("Регистрация", size=26, weight=ft.FontWeight.BOLD, color="white"),
            ft.Container(height=10),
            login_field,
            password_field,
            age_field,
            ft.Container(height=10),
            ft.Button("Зарегистрироваться", max_width=400, height=45, on_click=on_register_click),
            ft.TextButton("Уже есть аккаунт? Войти", on_click=show_login, style=ft.ButtonStyle(color="white"))
        ])
        page.update()

    def show_email_binding():
        form_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        email_field = ft.TextField(label="Email", max_width=400, keyboard_type=ft.KeyboardType.EMAIL, prefix_icon="mail")

        def on_bind_click(e):
            if not email_field.value or not email_field.value.strip():
                return
            show_chats()

        form_container.controls.clear()
        form_container.controls.extend([
            ft.Container(height=40),
            ft.Text("Привязать почту", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, color="white"),
            ft.Container(height=15),
            email_field,
            ft.Container(height=10),
            ft.Button("Привязать", max_width=400, height=45, on_click=on_bind_click)
        ])
        page.update()

    # =========================================================================
    # ШАГ 3: ГЛАВНЫЙ ЭКРАН (СПИСОК ЧАТОВ)
    # =========================================================================
    def show_chats(e=None):
        form_container.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        
        def on_settings_click(e):
            show_settings()

        def on_chat_click(chat_name):
            show_chat_window(chat_name)

        def on_search_submit(e):
            search_id = search_field.value.strip()
            if not search_id:
                return
            
            if search_id in users_db:
                found_name = users_db[search_id]
                show_user_profile(found_name)  
            else:
                page.snack_bar = ft.SnackBar(content=ft.Text(f"ID '{search_id}' не найден!"), bgcolor="#ef4444")
                page.snack_bar.open = True
                page.update()

        if user_avatar:
            chat_top_avatar = ft.CircleAvatar(background_image_src=user_avatar, radius=14)
        else:
            chat_top_avatar = ft.CircleAvatar(content=ft.Icon("person", color="#1f2937", size=16), radius=14, bgcolor="white")

        top_bar = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text("Настройки", size=12, weight=ft.FontWeight.W_500, color="#1f2937"),
                    padding=10,
                    bgcolor="white", 
                    border_radius=10,
                    on_click=on_settings_click
                ),
                chat_top_avatar,
                ft.VerticalDivider(width=10),
                ft.Text("Чаты", size=22, weight=ft.FontWeight.BOLD, color="white"),
            ],
            alignment=ft.MainAxisAlignment.START
        )

        search_field = ft.TextField(
            label="Поиск по ID", 
            prefix_icon="search", 
            height=45, 
            hint_text="Вставьте ID и нажмите Enter",
            on_submit=on_search_submit
        )

        # Важно: Списку чатов ставим expand=True, чтобы он занимал всё оставшееся вертикальное место окна
        chats_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        
        for name in all_users:  
            chat_item = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.CircleAvatar(content=ft.Text(name[0], color="white", weight=ft.FontWeight.BOLD), bgcolor="#3b82f6"),
                        ft.Text(name, size=16, weight=ft.FontWeight.W_500, color="black")
                    ],
                    spacing=12,
                ),
                padding=12,
                bgcolor="white", 
                border_radius=12,
                on_click=lambda e, chat_name=name: on_chat_click(chat_name)
            )
            chats_column.controls.append(chat_item)

        form_container.controls.clear()
        form_container.controls.extend([top_bar, search_field, ft.Divider(height=1, color="#374151"), chats_column])
        page.update()

    # =========================================================================
    # ШАГ 4: НАСТРОЙКИ ПРОФИЛЯ
    # =========================================================================
    def show_settings():
        nonlocal user_status, user_avatar
        form_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        async def on_avatar_click(e):
            nonlocal user_avatar
            file_path = await ft.FilePicker().pick_files(allow_multiple=True)
            print(file_path[0].path)
            if file_path:
                user_avatar = file_path[0].path
                show_settings()

        def on_save_click(e):
            nonlocal user_status
            user_status = about_field.value.strip()
            show_chats()

        def on_delete_click(e):
            show_login()

        settings_bar = ft.Row(
            controls=[
                ft.TextButton(content=ft.Text("<- Назад", size=16, weight=ft.FontWeight.W_500, color="#3b82f6"), on_click=show_chats),
                ft.VerticalDivider(width=10),
                ft.Text("Настройки", size=22, weight=ft.FontWeight.BOLD, color="white"),
            ],
            alignment=ft.MainAxisAlignment.START
        )

        if user_avatar:
            current_avatar = ft.CircleAvatar(background_image_src=user_avatar, radius=40)
        else:
            current_avatar = ft.CircleAvatar(content=ft.Icon("person", size=40, color="white"), radius=40, bgcolor="#374151")

        about_field = ft.TextField(label="О себе", max_length=400, multiline=True, min_lines=2, max_lines=3, value=user_status)

        form_container.controls.clear()
        form_container.controls.extend([
            settings_bar, 
            ft.Container(height=10),
            ft.TextButton(
                content=ft.Column(
                    controls=[current_avatar, ft.Text("Изменить аватарку", size=14, color="white")], 
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ), 
                on_click=on_avatar_click
            ),
            ft.Container(height=10), about_field, ft.Container(height=20),
            ft.Button("Сохранить", width=400, height=45, on_click=on_save_click),
            ft.TextButton("Удалить профиль", on_click=on_delete_click, style=ft.ButtonStyle(color="red"))
        ])
        page.update()

    # =========================================================================
    # ШАГ 5: ПРОФИЛЬ СОБЕСЕДНИКА
    # =========================================================================
    def show_user_profile(user_name):
        form_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        user_id = None
        for uid, name in users_db.items():
            if name == user_name:
                user_id = uid
                break
        if not user_id:
            user_id = f"id_{abs(hash(user_name)) % 1000000}"

        def copy_id_to_clipboard(e):
            try:
                subprocess.run(f"echo {user_id}| clip", shell=True, check=True)
            except Exception as ex:
                print(f"Ошибка копирования: {ex}")
            
            page.snack_bar = ft.SnackBar(content=ft.Text(f"ID {user_id} скопирован!"), duration=2000)
            page.snack_bar.open = True
            page.update()

        profile_bar = ft.Row(
            controls=[
                ft.TextButton(content=ft.Text("<- Назад", size=16, weight=ft.FontWeight.W_500, color="#3b82f6"), on_click=lambda _: show_chat_window(user_name)),
                ft.VerticalDivider(width=10),
                ft.Text("Профиль", size=22, weight=ft.FontWeight.BOLD, color="white"),
            ],
            alignment=ft.MainAxisAlignment.START
        )

        form_container.controls.clear()
        form_container.controls.extend([
            profile_bar,
            ft.Container(height=20),
            ft.CircleAvatar(content=ft.Text(user_name[0], size=32, color="white", weight=ft.FontWeight.BOLD), radius=50, bgcolor="#3b82f6"),
            ft.Container(height=10),
            ft.Text(user_name, size=24, weight=ft.FontWeight.BOLD, color="white"),
            
            ft.Row(
                controls=[
                    ft.Text(f"ID: {user_id}", size=14, color="lightgrey"),
                    ft.IconButton(icon=ft.Icons.COPY, icon_size=16, icon_color="lightgrey", on_click=copy_id_to_clipboard)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=5
            ),
            ft.Container(height=15),
            ft.Container(
                content=ft.Column([
                    ft.Text("О себе:", size=14, weight=ft.FontWeight.BOLD, color="lightgrey"),
                    ft.Text("Привет! Я пользуюсь Albakryak Messenger.", size=16, color="white")
                ]),
                width=400,
                padding=10,
                border=ft.Border.all(1, "#374151"),  
                border_radius=10
            ),
            ft.Container(height=20),
            ft.Button("Написать сообщение", width=400, height=45, on_click=lambda _: show_chat_window(user_name))
        ])
        page.update()

    # =========================================================================
    # ШАГ 6: ЭКРАН ЧАТА (МАКСИМАЛЬНОЕ АВТО-МАСШТАБИРОВАНИЕ)
    # =========================================================================
    def show_chat_window(chat_name):
        nonlocal chat_history
        form_container.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

        bot_phrases = [
            "Привет! Давно не виделись. Как дела?",
            "О, круто! Расскажи подробнее.",
            "Я сейчас немного занят по учебе, отвечу чуть позже, ладно?",
            "Ха-ха, забавно! Твой Albakryak работает отлично!",
            "Слушай, а ты пробовал запустить это на C++?",
            "Интересная мысль, надо обдумать.",
            "Понял тебя. Ладно, я погнал, скоро спишемся!"
        ]

        if chat_name not in chat_history:
            chat_history[chat_name] = []

        def append_message_to_ui(text, sender):
            if sender == "user":
                chat_messages.controls.append(
                    ft.Row(
                        controls=[ft.Container(content=ft.Text(text, size=15, color="white"), padding=10, bgcolor="#1e3a8a", border_radius=10, width=300)],
                        alignment=ft.MainAxisAlignment.END
                    )
                )
            else:
                chat_messages.controls.append(
                    ft.Row(
                        controls=[ft.Container(content=ft.Text(text, size=15, color="white"), padding=10, bgcolor="#374151", border_radius=10, width=300)],
                        alignment=ft.MainAxisAlignment.START
                    )
                )

        user_clickable_zone = ft.Container(
            content=ft.Row(
                controls=[
                    ft.CircleAvatar(content=ft.Text(chat_name[0], color="white"), radius=15, bgcolor="#3b82f6"),
                    ft.Text(chat_name, size=18, weight=ft.FontWeight.BOLD, color="white"),
                ],
                spacing=8,
            ),
            on_click=lambda _: show_user_profile(chat_name),
            padding=5,
            border_radius=8
        )

        chat_bar = ft.Row(
            controls=[
                ft.TextButton(content=ft.Text("<- Назад", size=16, weight=ft.FontWeight.W_500, color="#3b82f6"), on_click=lambda _: show_chats()),
                user_clickable_zone, 
                ft.Container(width=40) 
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        chat_messages = ft.Column(
            controls=[ft.Row(controls=[ft.Text(f"Переписка с {chat_name}", size=13, color="grey")], alignment=ft.MainAxisAlignment.CENTER)],
            spacing=10, scroll=ft.ScrollMode.AUTO, expand=True
        )

        for msg in chat_history[chat_name]:
            append_message_to_ui(msg["text"], msg["sender"])

        animated_chat_box = ft.Container(
            content=chat_messages, bgcolor="#f3f4f6", padding=10, border_radius=15, expand=True
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

        message_field = ft.TextField(
            hint_text="Введите сообщение...", height=45, color="white",
            hint_style=ft.TextStyle(color="grey"), filled=True, fill_color="#1f2937",
            focused_border_color="#3b82f6", autofocus=True, on_submit=on_send_message,
            expand=True  
        )

        send_button = ft.Container(
            content=ft.Text("Отправить", size=13, weight=ft.FontWeight.BOLD, color="white"),
            padding=12, bgcolor="#3b82f6", border_radius=10, on_click=on_send_message   
        )

        bottom_input_bar = ft.Row(
            controls=[message_field, send_button], 
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        form_container.controls.clear()
        form_container.controls.extend([chat_bar, ft.Divider(height=1, color="#374151"), animated_chat_box, bottom_input_bar])
        page.update()

    show_login()
    page.add(form_container)

if __name__ == "__main__":
    ft.run(main)
