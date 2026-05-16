import flet as ft

def main(page: ft.Page):
    # Настройки страницы (Единый стиль окна)
    page.title = "Albakryak Messenger"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_width = 400
    page.window_height = 650
    page.padding = 25

    # Основной контейнер, в котором плавно меняются все экраны
    form_container = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15
    )

    # =========================================================================
    # ШАГ 1: ЭКРАН АУТЕНТИФИКАЦИИ (ВХОД / РЕГИСТРАЦИЯ)
    # =========================================================================

    # --- РЕЖИМ ВХОДА ---
    def show_login(e=None):
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        form_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER # ВОТ ЭТА СТРОКА (возвращает центр для экрана входа)
        
        login_field = ft.TextField(label="Логин", width=320, prefix_icon="person")
        password_field = ft.TextField(label="Пароль", width=320, password=True, can_reveal_password=True, prefix_icon="lock")

        def on_login_click(e):
            print(f"Вход: Логин={login_field.value}, Пароль={password_field.value}")
            show_chats()

        form_container.controls.clear()
        form_container.controls.extend([
            ft.Text("Вход в аккаунт", size=26, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            login_field,
            password_field,
            ft.Container(height=10),
            ft.ElevatedButton("Войти", width=320, height=45, on_click=on_login_click),
            ft.TextButton("Нет аккаунта? Зарегистрироваться", on_click=show_register)
        ])
        page.update()

    # --- РЕЖИМ РЕГИСТРАЦИИ ---
    def show_register(e=None):
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        form_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        login_field = ft.TextField(label="Логин", width=320, prefix_icon="person")
        password_field = ft.TextField(label="Пароль", width=320, password=True, can_reveal_password=True, prefix_icon="lock")
        age_field = ft.TextField(label="Возраст", width=320, keyboard_type=ft.KeyboardType.NUMBER, prefix_icon="calendar_today")

        def on_register_click(e):
            print(f"Регистрация: Логин={login_field.value}, Пароль={password_field.value}, Возраст={age_field.value}")
            show_email_binding()

        form_container.controls.clear()
        form_container.controls.extend([
            ft.Text("Регистрация", size=26, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            login_field,
            password_field,
            age_field,
            ft.Container(height=10),
            ft.ElevatedButton("Зарегистрироваться", width=320, height=45, on_click=on_register_click),
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
            print(f"Привязка почты: Email={email_field.value}")
            show_chats()

        form_container.controls.clear()
        form_container.controls.extend([
            ft.Text("Привяжите почту для восстановления аккаунта", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Container(height=15),
            email_field,
            ft.Container(height=10),
            ft.ElevatedButton("Привязать", width=320, height=45, on_click=on_bind_click)
        ])
        page.update()


    # =========================================================================
    # ШАГ 3: ГЛАВНЫЙ ЭКРАН (СПИСОК ЧАТОВ) — ТЕПЕРЬ СЛЕВА
    # =========================================================================
    def show_chats(e=None):
        page.vertical_alignment = ft.MainAxisAlignment.START
        form_container.horizontal_alignment = ft.CrossAxisAlignment.START # ИСПРАВЛЕНО: Теперь этот экран жмётся влево
        
        def on_settings_click(e):
            show_settings()

        def on_chat_click(e, chat_name):
            show_chat_window(chat_name)

        # --- ВЕРХНЯЯ ПАНЕЛЬ С КНОПКОЙ НАСТРОЕК С ФОНОМ ---
        top_bar = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text("Настройки", size=12, weight=ft.FontWeight.W_500),
                    padding=8,
                    bgcolor="surfacevariant", 
                    border_radius=10,
                    on_click=on_settings_click
                ),
                ft.CircleAvatar(content=ft.Icon("person"), radius=14),
                ft.VerticalDivider(width=10),
                ft.Text("Чаты", size=22, weight=ft.FontWeight.BOLD),
            ],
            alignment=ft.MainAxisAlignment.START
        )

        # Поиск по ID
        search_field = ft.TextField(
            label="Поиск по ID", 
            width=340, 
            prefix_icon="search",
            height=45,
            hint_text="Введите ID..."
        )

        # --- ВЕРТИКАЛЬНЫЙ СПИСОК ЧАТОВ ---
        chats_column = ft.Column(
            spacing=8, 
            scroll=ft.ScrollMode.AUTO, 
            height=430,
            horizontal_alignment=ft.CrossAxisAlignment.START
        )
        
        demo_chats = ["Алексей", "Мария", "Дмитрий", "Разработчики Flet", "Учеба - Программирование"]
        
        for name in demo_chats:
            chat_item = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.CircleAvatar(content=ft.Text(name[0])),
                        ft.Text(name, size=16, weight=ft.FontWeight.W_500)
                    ],
                    spacing=12,
                    alignment=ft.MainAxisAlignment.START
                ),
                padding=10,
                width=340,
                border_radius=8,
                on_click=lambda e, chat_name=name: on_chat_click(e, chat_name)
            )
            chats_column.controls.append(chat_item)

        form_container.controls.clear()
        form_container.controls.extend([
            top_bar,
            search_field,
            ft.Divider(height=1), 
            chats_column
        ])
        page.update()


    # =========================================================================
    # ШАГ 4: НАСТРОЙКИ ПРОФИЛЯ
    # =========================================================================
    def show_settings():
        page.vertical_alignment = ft.MainAxisAlignment.START
        form_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        def on_avatar_click(e):
            print("Действие: Изменить аватарку")

        def on_save_click(e):
            print(f"Сохранение настроек. Статус 'О себе': {about_field.value}")
            show_chats()

        def on_delete_click(e):
            print("Профиль удален!")
            show_login()

        # --- ВЕРХНЯЯ ПАНЕЛЬ НАСТРОЕК ---
        settings_bar = ft.Row(
            controls=[
                ft.TextButton(content=ft.Text("<- Назад", size=16, weight=ft.FontWeight.W_500), on_click=show_chats),
                ft.VerticalDivider(width=10),
                ft.Text("Настройки", size=22, weight=ft.FontWeight.BOLD),
            ],
            alignment=ft.MainAxisAlignment.START
        )

        about_field = ft.TextField(
            label="О себе", 
            width=320, 
            multiline=True, 
            min_lines=2, 
            max_lines=3,
            hint_text="Расскажите о себе или укажите статус..."
        )

        form_container.controls.clear()
        form_container.controls.extend([
            settings_bar,
            ft.Container(height=10),
            ft.TextButton(
                content=ft.Column(
                    controls=[
                        ft.CircleAvatar(content=ft.Icon("person", size=40), radius=40),
                        ft.Text("Изменить аватарку", size=14)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                on_click=on_avatar_click
            ),
            ft.Container(height=10),
            about_field,
            ft.Container(height=20),
            ft.ElevatedButton("Сохранить", width=320, height=45, on_click=on_save_click),
            ft.TextButton("Удалить профиль", on_click=on_delete_click)
        ])
        page.update()


    # =========================================================================
    # ШАГ 5: ОКНО ДИАЛОГА (ОТКРЫТЫЙ ЧАТ)
    # =========================================================================
    def show_chat_window(chat_name):
        page.vertical_alignment = ft.MainAxisAlignment.START
        form_container.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        # Обработчик отправки сообщения
        def on_send_message(e):
            if message_field.value:
                print(f"Отправлено в чат '{chat_name}': {message_field.value}")
                chat_messages.controls.append(
                    ft.Container(
                        content=ft.Text(message_field.value, size=15),
                        padding=10,
                        bgcolor="surfacevariant",
                        border_radius=10,
                        alignment="center_right"
                    )
                )
                message_field.value = ""
                page.update()

        # Верхняя панель диалога
        chat_bar = ft.Row(
            controls=[
                ft.TextButton(content=ft.Text("<- Назад", size=16, weight=ft.FontWeight.W_500), on_click=show_chats),
                ft.VerticalDivider(width=10),
                ft.CircleAvatar(content=ft.Text(chat_name[0]), radius=16),
                ft.Text(chat_name, size=18, weight=ft.FontWeight.BOLD),
            ],
            alignment=ft.MainAxisAlignment.START
        )

        # Контейнер для отображения сообщений
        chat_messages = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Text(f"Это начало вашей переписки с пользователем {chat_name}", size=13, color="grey"),
                    padding=10,
                    alignment="center"
                )
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            height=400,
            alignment=ft.MainAxisAlignment.END
        )

        # Поле ввода текста сообщения
        message_field = ft.TextField(
            hint_text="Напишите сообщение...",
            width=230,
            height=45
        )

        # Кнопка «Отправить»
        send_button = ft.Container(
            content=ft.Text("Отправить", size=12, weight=ft.FontWeight.BOLD),
            padding=10,
            bgcolor="surfacevariant",
            border_radius=10,
            on_click=on_send_message
        )

        # Нижняя панель с вводом и отправкой
        bottom_input_bar = ft.Row(
            controls=[message_field, send_button],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )

        # Сборка экрана открытого диалога
        form_container.controls.clear()
        form_container.controls.extend([
            chat_bar,
            ft.Divider(height=1),
            chat_messages,
            bottom_input_bar
        ])
        page.update()


    # Запуск приложения
    show_login()
    page.add(form_container)

if __name__ == "__main__":
    ft.app(target=main)