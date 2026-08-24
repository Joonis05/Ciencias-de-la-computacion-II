import customtkinter as ctk
from views.base_view import BaseView


class InicioView(BaseView):

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Inicio",
            show_nav=False,
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self):

        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(pady=(50, 10))

        ctk.CTkLabel(
            header,
            text="Ciencias de la Computación II",
            font=ctk.CTkFont(size=30, weight="bold"),
        ).pack()

        ctk.CTkLabel(
            header,
            text="Selecciona una categoría para explorar los algoritmos",
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60"),
        ).pack(pady=(8, 0))

        btn_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        btn_frame.pack(expand=True)

        self.add_nav_button("Búsquedas", "busquedas", parent=btn_frame)
        self.add_nav_button("Grafos",     "grafos",     parent=btn_frame)
