from views.base_view import BaseView


class GrafosView(BaseView):

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
            "Representación y recorrido de estructuras de datos tipo grafo."
        )
        self.workspace = self.add_algorithm_workspace(
            "⚙️  Aquí se implementará el algoritmo de grafos"
        )
