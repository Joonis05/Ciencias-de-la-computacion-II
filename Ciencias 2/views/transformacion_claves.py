from views.base_view import BaseView


class TransformacionClavesView(BaseView):

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Transformación de Claves",
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self):
        self.add_title("Transformación de Claves")
        self.add_subtitle(
            "Utiliza una función hash para mapear claves a posiciones en una tabla."
        )
        self.workspace = self.add_algorithm_workspace(
            "⚙️  Aquí se implementará el algoritmo de transformación de claves (hashing)"
        )
