import flet as ft

print("hello")

def main(page: ft.Page):
    page.title = "Мобильное приложение на Flet"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    txt_number = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT, width=100)
    txt_number2 = ft.TextField(value="0", text_align=ft.TextAlign.RIGHT, width=100)
    
    def minus_click(e):
        print("hello")
        txt_number.value = str(int(txt_number.value) - 1)
        page.update()
    def minus_click2(e):
        txt_number2.value = str(int(txt_number.value) - 1)
        page.update()
    
    def plus_click(e):
        txt_number.value = str(int(txt_number.value) + 1)

        page.update()

    def plus_click2(e): 
        txt_number2.value = str(int(txt_number2.value) + 1)
        page.add(
        ft.Row(
            [
                txt_number2,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )
        page.update()


    page.add(
        ft.Row(
            [
                ft.IconButton(ft.Icons.REMOVE, on_click=minus_click),
                txt_number,
                ft.IconButton(ft.Icons.ADD, on_click=plus_click),

                ft.IconButton(ft.Icons.ADD, on_click = plus_click2)
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )

ft.run(main)