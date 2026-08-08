import customtkinter as ctk
from views.base_view import BaseView


class BusquedasView(BaseView):

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Búsquedas",
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self):
        self.add_title("Búsquedas")
        self.add_subtitle("Elige el tipo de búsqueda que deseas explorar")

        btn_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        btn_frame.pack(expand=True)

        self.add_nav_button(
            "Búsquedas Internas", "busquedas_internas", parent=btn_frame
        )
        self.add_nav_button(
            "Búsquedas Externas", "busquedas_externas", parent=btn_frame
        )
