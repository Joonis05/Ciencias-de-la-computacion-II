import customtkinter as ctk
from views.base_view import BaseView


class BusquedasInternasView(BaseView):

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Búsquedas Internas",
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self):
        self.add_title("Búsquedas Internas")
        self.add_subtitle("Selecciona un algoritmo de búsqueda interna")

        btn_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        btn_frame.pack(expand=True)

        self.add_nav_button("Secuencial", "secuencial", parent=btn_frame)
        self.add_nav_button("Binaria", "binaria", parent=btn_frame)
        self.add_nav_button("Transformación de Claves", "transformacion_claves", parent=btn_frame)
        self.add_nav_button("Búsqueda por Residuos", "residuos", parent=btn_frame)
        self.add_nav_button("Árboles de Huffman", "huffman", parent=btn_frame)
