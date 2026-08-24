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
        self.add_subtitle(
            "Algoritmos de búsqueda que operan sobre datos almacenados en disco."
        )
        self.workspace = self.add_algorithm_workspace(
            "⚙️  Aquí se implementará el algoritmo de búsquedas externas"
        )
