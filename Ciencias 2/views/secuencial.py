from views.base_view import BaseView


class SecuencialView(BaseView):

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Búsqueda Secuencial",
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self):
        self.add_title("Búsqueda Secuencial")
        self.add_subtitle(
            "Recorre los elementos uno a uno hasta encontrar el valor buscado."
        )
        self.workspace = self.add_algorithm_workspace(
            "⚙️  Aquí se implementará el algoritmo de búsqueda secuencial"
        )
