from views.base_view import BaseView


class BinariaView(BaseView):

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Búsqueda Binaria",
            **kwargs,
        )
        self._build_ui()

    def _build_ui(self):
        self.add_title("Búsqueda Binaria")
        self.add_subtitle(
            "Divide el conjunto ordenado a la mitad en cada paso para localizar el valor."
        )
        self.workspace = self.add_algorithm_workspace(
            "⚙️  Aquí se implementará el algoritmo de búsqueda binaria"
        )
