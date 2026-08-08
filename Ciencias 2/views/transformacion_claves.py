import random
import customtkinter as ctk
from views.base_view import BaseView

_MAX_SIZE = 1_000
_DEFAULT_SIZE = 13          
_KEY_MIN = 1
_KEY_MAX = 9_999
_LOAD_FACTOR = 0.75         


class TransformacionClavesView(BaseView):

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Transformación de Claves",
            **kwargs,
        )
        self._table: list[int | None] = []
        self._cell_frames: list[ctk.CTkFrame] = []
        self._mode_var = ctk.StringVar(value="Aleatorio")
        self._build_ui()

    def _build_ui(self):
        self.add_title("Transformación de Claves")
        self.add_subtitle(
            "Utiliza una función hash para mapear claves a posiciones en una tabla. "
        )

        config_frame = ctk.CTkFrame(
            self.content, corner_radius=12,
            fg_color=("gray92", "gray17"),
            border_width=2, border_color=("gray78", "gray30"),
        )
        config_frame.pack(fill="x", padx=10, pady=(0, 8))

        inner = ctk.CTkFrame(config_frame, fg_color="transparent")
        inner.pack(padx=16, pady=14, fill="x")

        # Fila 1: Modo de ingreso
        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            row1, text="Modo de carga:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=(0, 12))

        self._mode_seg = ctk.CTkSegmentedButton(
            row1, values=["Aleatorio", "Manual"],
            variable=self._mode_var,
            command=self._on_mode_change,
            font=ctk.CTkFont(size=13),
        )
        self._mode_seg.pack(side="left")

        # Fila 2: Tamaño y botones
        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            row2, text="Tamaño (N):",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        self._size_entry = ctk.CTkEntry(
            row2, width=80, height=34,
            placeholder_text=str(_DEFAULT_SIZE),
            font=ctk.CTkFont(size=14),
            justify="center",
        )
        self._size_entry.pack(side="left", padx=(0, 16))
        self._size_entry.insert(0, str(_DEFAULT_SIZE))

        self._btn_generate = ctk.CTkButton(
            row2, text="Generar Tabla",
            width=140, height=34,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_generate,
        )
        self._btn_generate.pack(side="left", padx=(0, 8))

        self._btn_clear = ctk.CTkButton(
            row2, text="Limpiar",
            width=120, height=34,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            text_color=("black", "white"),
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_clear,
        )
        self._btn_clear.pack(side="left", padx=(0, 16))
        
        self._info_label = ctk.CTkLabel(
            row2, text="",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray55"),
        )
        self._info_label.pack(side="left")

        # Fila 3: Entrada manual
        self._row3_manual = ctk.CTkFrame(inner, fg_color="transparent")
        self._row3_manual.pack(fill="x")

        ctk.CTkLabel(
            self._row3_manual, text="Claves (separadas por coma):",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        self._manual_entry = ctk.CTkEntry(
            self._row3_manual, height=34,
            placeholder_text="Ej: 42, 15, 87, 34",
            font=ctk.CTkFont(size=14),
        )
        self._manual_entry.pack(side="left", fill="x", expand=True)

        # Error
        self._error_label = ctk.CTkLabel(
            self.content, text="",
            font=ctk.CTkFont(size=13),
            text_color=("#cc0000", "#ff4444"),
        )
        self._error_label.pack(fill="x", padx=20, pady=(0, 4))

        # Estructura
        self._scroll_frame = ctk.CTkScrollableFrame(
            self.content,
            corner_radius=12,
            fg_color=("gray96", "gray14"),
            border_width=2,
            border_color=("gray78", "gray30"),
            label_text="Tabla Hash generada",
            label_font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._placeholder = ctk.CTkLabel(
            self._scroll_frame,
            text="Configura los parámetros y presiona «Generar Tabla» para comenzar.",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray55"),
        )
        self._placeholder.pack(pady=40)
        
        self._on_mode_change(self._mode_var.get())

    def _on_mode_change(self, selected_mode: str):
        if selected_mode == "Aleatorio":
            self._manual_entry.configure(state="disabled", fg_color=("gray85", "gray25"))
            self._clear_error()
        else:
            self._manual_entry.configure(state="normal", fg_color=("white", "gray20"))
            self._clear_error()

    def _on_clear(self):
        self._table.clear()
        self._info_label.configure(text="")
        self._clear_error()
        self._manual_entry.delete(0, 'end')
        
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()
        self._cell_frames.clear()
        
        self._placeholder = ctk.CTkLabel(
            self._scroll_frame,
            text="Tabla limpiada. Configura los parámetros y presiona «Generar Tabla».",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray55"),
        )
        self._placeholder.pack(pady=40)

    def _validate_inputs(self) -> tuple[int, list[int] | None]:

        raw_size = self._size_entry.get().strip()
        if not raw_size:
            self._show_error("Ingresa un número para el tamaño de la tabla (N).")
            return 0, None

        try:
            size = int(raw_size)
        except ValueError:
            self._show_error(f"«{raw_size}» no es un tamaño válido.")
            return 0, None

        if size <= 0:
            self._show_error("El tamaño debe ser un entero positivo.")
            return 0, None

        if size > _MAX_SIZE:
            self._show_error(f"El tamaño máximo recomendado es {_MAX_SIZE:,}.")
            return 0, None

        mode = self._mode_var.get()
        
        if mode == "Aleatorio":
            self._clear_error()
            num_keys = max(1, int(size * _LOAD_FACTOR))
            keys = random.sample(range(_KEY_MIN, _KEY_MAX + 1), min(num_keys, _KEY_MAX))
            return size, keys
            
        # Modo Manual
        raw_manual = self._manual_entry.get().strip()
        if not raw_manual:
            self._show_error("Ingresa las claves separadas por coma.")
            return 0, None
            
        parts = [p.strip() for p in raw_manual.split(",") if p.strip()]
        
        if len(parts) > size:
            self._show_error(
                f"Ingresaste {len(parts)} claves, pero el tamaño de la tabla es {size}. "
                "No hay suficiente espacio."
            )
            return 0, None
            
        parsed_data = []
        for p in parts:
            try:
                parsed_data.append(int(p))
            except ValueError:
                self._show_error(f"«{p}» no es una clave entera válida.")
                return 0, None
                
        self._clear_error()
        return size, parsed_data

    def _on_generate(self):
        size, keys = self._validate_inputs()
        if keys is None:
            return

        self._table = [None] * size

        inserted = 0
        for key in keys:
            if self._hash_insert(key):
                inserted += 1

        self._render_structure()

        occupied = sum(1 for slot in self._table if slot is not None)
        mode = self._mode_var.get()
        self._info_label.configure(
            text=f"{occupied}/{size} slots ocupados ({mode})"
        )

    def _hash_insert(self, key: int) -> bool:
        size = len(self._table)
        idx = key % size

        for _ in range(size):
            if self._table[idx] is None:
                self._table[idx] = key
                return True
            idx = (idx + 1) % size

        return False

    def _render_structure(self):
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()
        self._cell_frames.clear()

        if not self._table:
            return

        header = ctk.CTkFrame(self._scroll_frame, fg_color="transparent")
        header.pack(fill="x", padx=6, pady=(8, 4))

        ctk.CTkLabel(
            header, text="Índice", width=80,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("gray30", "gray70"),
        ).pack(side="left", padx=(4, 16))

        ctk.CTkLabel(
            header, text="Clave", width=120,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("gray30", "gray70"),
        ).pack(side="left", padx=(0, 16))

        ctk.CTkLabel(
            header, text="Estado",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("gray30", "gray70"),
        ).pack(side="left")

        for idx, slot in enumerate(self._table):
            is_empty = slot is None

            if is_empty:
                bg = ("gray94", "gray17")
            else:
                bg = ("gray88", "gray22") if idx % 2 == 0 else ("gray94", "gray17")

            row = ctk.CTkFrame(
                self._scroll_frame, height=36,
                corner_radius=8, fg_color=bg,
            )
            row.pack(fill="x", padx=6, pady=2)
            row.pack_propagate(False)

            ctk.CTkLabel(
                row, text=str(idx), width=80,
                font=ctk.CTkFont(family="Consolas", size=14),
                anchor="center",
            ).pack(side="left", padx=(8, 16))

            key_text = str(slot) if slot is not None else "—"
            key_color = ("gray10", "gray90") if slot is not None else ("gray60", "gray45")
            ctk.CTkLabel(
                row, text=key_text, width=120,
                font=ctk.CTkFont(family="Consolas", size=14,
                                 weight="bold" if slot is not None else "normal"),
                text_color=key_color,
                anchor="center",
            ).pack(side="left", padx=(0, 16))

            status_text = "Ocupado" if slot is not None else "Vacío"
            status_color = ("#2e7d32", "#66bb6a") if slot is not None else ("gray55", "gray50")
            ctk.CTkLabel(
                row, text=status_text,
                font=ctk.CTkFont(size=13),
                text_color=status_color,
                anchor="w",
            ).pack(side="left", padx=4)

            self._cell_frames.append(row)

    def _show_error(self, msg: str):
        self._error_label.configure(text=msg)

    def _clear_error(self):
        self._error_label.configure(text="")
