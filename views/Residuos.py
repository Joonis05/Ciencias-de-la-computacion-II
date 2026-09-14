import customtkinter as ctk
from views.base_view import BaseView


class ResiduosView(BaseView):

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Búsqueda por Residuos",
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self):
        self.add_title("Búsqueda por Residuos")
        self.add_subtitle("Selecciona el tipo de árbol de residuos que deseas explorar")

        btn_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        btn_frame.pack(expand=True)

        self.add_nav_button("Árbol Digital", "arbol_digital", parent=btn_frame)
        self.add_nav_button("Árbol Trie", "arbol_trie", parent=btn_frame)
        self.add_nav_button("Residuos Múltiples", "arbol_multiple", parent=btn_frame)

