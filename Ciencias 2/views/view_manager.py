import customtkinter as ctk
from views.base_view import BaseView

class ViewManager(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._views: dict[str, type[BaseView]] = {}

        self._history: list[str] = []

        self._current_view: BaseView | None = None

        self._register_views()

    def _register_views(self):
        from views.inicio import InicioView
        from views.busquedas import BusquedasView
        from views.busquedas_internas import BusquedasInternasView
        from views.busquedas_externas import BusquedasExternasView
        from views.secuencial import SecuencialView
        from views.binaria import BinariaView
        from views.transformacion_claves import TransformacionClavesView
        from views.grafos import GrafosView

        self._views = {
            "inicio":                 InicioView,
            "busquedas":              BusquedasView,
            "busquedas_internas":     BusquedasInternasView,
            "busquedas_externas":     BusquedasExternasView,
            "secuencial":             SecuencialView,
            "binaria":                BinariaView,
            "transformacion_claves":  TransformacionClavesView,
            "grafos":                 GrafosView,
        }

    def show_view(self, view_key: str):
        """
        Muestra la vista identificada por *view_key*.
        Añade la vista actual al historial para poder retroceder.
        """
        if view_key not in self._views:
            raise KeyError(f"Vista '{view_key}' no registrada.")

        if self._current_view is not None:
            self._history.append(self._current_view.view_key)
            self._current_view.destroy()

        view_class = self._views[view_key]
        self._current_view = view_class(self, view_manager=self)
        self._current_view.view_key = view_key
        self._current_view.pack(fill="both", expand=True)

    def go_back(self):
        if self._history:
            previous_key = self._history.pop()
            if self._current_view is not None:
                self._current_view.destroy()
                self._current_view = None
            view_class = self._views[previous_key]
            self._current_view = view_class(self, view_manager=self)
            self._current_view.view_key = previous_key
            self._current_view.pack(fill="both", expand=True)

    def go_home(self):
        self._history.clear()
        if self._current_view is not None:
            self._current_view.destroy()
            self._current_view = None
        self.show_view("inicio")

    def get_breadcrumbs(self) -> list[str]:
        LABELS = {
            "inicio":                "Inicio",
            "busquedas":             "Búsquedas",
            "busquedas_internas":    "Búsquedas Internas",
            "busquedas_externas":    "Búsquedas Externas",
            "secuencial":            "Secuencial",
            "binaria":               "Binaria",
            "transformacion_claves": "Transformación de Claves",
            "grafos":                "Grafos",
        }
        crumbs = [LABELS.get(k, k) for k in self._history]
        if self._current_view:
            crumbs.append(LABELS.get(self._current_view.view_key, ""))
        return crumbs
