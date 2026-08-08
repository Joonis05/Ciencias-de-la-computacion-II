import customtkinter as ctk


class BaseView(ctk.CTkFrame):
    """
    Plantilla base de vista.  Todas las pantallas heredan de esta clase.
    """

    view_key: str = ""

    def __init__(
        self,
        master,
        *,
        view_manager,
        title: str = "",
        show_nav: bool = True,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._vm = view_manager
        self._title = title

        if show_nav:
            self._build_navbar()

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        
    def _build_navbar(self):
        """Construye la barra superior con breadcrumbs y botón de regresar."""
        navbar = ctk.CTkFrame(self, height=45, corner_radius=0,
                              fg_color=("gray86", "gray20"))
        navbar.pack(fill="x", padx=0, pady=(0, 5))
        navbar.pack_propagate(False)

        btn_back = ctk.CTkButton(
            navbar,
            text="← Regresar",
            width=110,
            height=32,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            hover_color=("gray78", "gray30"),
            text_color=("gray20", "gray80"),
            command=self._vm.go_back,
        )
        btn_back.pack(side="left", padx=(10, 5), pady=6)

        crumbs = self._vm.get_breadcrumbs()
        breadcrumb_text = "  ›  ".join(crumbs) if crumbs else ""
        lbl = ctk.CTkLabel(
            navbar,
            text=breadcrumb_text,
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray60"),
        )
        lbl.pack(side="left", padx=10, pady=6)

        btn_home = ctk.CTkButton(
            navbar,
            text="🏠 Inicio",
            width=90,
            height=32,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            hover_color=("gray78", "gray30"),
            text_color=("gray20", "gray80"),
            command=self._vm.go_home,
        )
        btn_home.pack(side="right", padx=(5, 10), pady=6)

    def add_title(self, text: str | None = None):
        label = ctk.CTkLabel(
            self.content,
            text=text or self._title,
            font=ctk.CTkFont(size=26, weight="bold"),
        )
        label.pack(pady=(30, 10))

    def add_subtitle(self, text: str):
        label = ctk.CTkLabel(
            self.content,
            text=text,
            font=ctk.CTkFont(size=14),
            text_color=("gray40", "gray60"),
        )
        label.pack(pady=(0, 20))

    def add_nav_button(self, text: str, view_key: str, *, parent=None):
        container = parent or self.content
        btn = ctk.CTkButton(
            container,
            text=text,
            width=280,
            height=48,
            font=ctk.CTkFont(size=15, weight="bold"),
            corner_radius=12,
            command=lambda: self._vm.show_view(view_key),
        )
        btn.pack(pady=8)
        return btn

    def add_algorithm_workspace(self, description: str = ""):
        workspace = ctk.CTkFrame(
            self.content,
            corner_radius=12,
            fg_color=("gray92", "gray17"),
            border_width=2,
            border_color=("gray78", "gray30"),
        )
        workspace.pack(fill="both", expand=True, padx=10, pady=10)

        lbl = ctk.CTkLabel(
            workspace,
            text=description or "⚙️  Espacio reservado para el algoritmo",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray55"),
        )
        lbl.place(relx=0.5, rely=0.5, anchor="center")

        return workspace
