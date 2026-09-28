import customtkinter as ctk
from views.base_view import BaseView


class GrafosView(BaseView):
    """Menú principal de la sección de grafos."""

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Grafos",
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self):
        self.add_title("Grafos")
        self.add_subtitle(
            "Selecciona el tipo de operación o análisis que deseas realizar."
        )

        frame = ctk.CTkFrame(
            self.content,
            fg_color="transparent",
        )
        frame.pack(expand=True)

        self.add_nav_button(
            "Operaciones con Grafos",
            "grafos_operaciones",
            parent=frame,
        )

        self.add_nav_button(
            "Productos de Grafos",
            "grafos_productos",
            parent=frame,
        )

        self.add_nav_button(
            "Árboles como Grafos",
            "grafos_arboles",
            parent=frame,
        )
