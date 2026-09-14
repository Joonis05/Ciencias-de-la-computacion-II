import customtkinter as ctk
from views.base_view import BaseView


class BusquedasExternasView(BaseView):

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Búsquedas Externas",
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self):
        self.add_title("Búsquedas Externas")
        self.add_subtitle("Selecciona un algoritmo de búsqueda externa")

        btn_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        btn_frame.pack(expand=True)

        self.add_nav_button("Secuencial", "ext_secuencial", parent=btn_frame)
        self.add_nav_button("Binaria", "ext_binaria", parent=btn_frame)
        self.add_nav_button("Transformación de Claves", "ext_transformacion_claves", parent=btn_frame)
        self.add_nav_button("Dinámicas", "ext_dinamicas", parent=btn_frame)
