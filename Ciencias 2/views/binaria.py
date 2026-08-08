import random
import customtkinter as ctk
from views.base_view import BaseView

_MAX_SIZE = 1_000
_DEFAULT_SIZE = 10
_VALUE_MIN = 1
_VALUE_MAX = 9_999


class BinariaView(BaseView):

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Búsqueda Binaria",
            **kwargs,
        )
        self._data: list[int] = []
        self._cell_frames: list[ctk.CTkFrame] = []
        self._mode_var = ctk.StringVar(value="Aleatorio")
        self._build_ui()

    def _build_ui(self):
        self.add_title("Búsqueda Binaria")
        self.add_subtitle(
            "Divide el conjunto ordenado a la mitad en cada paso para "
            "localizar el valor."
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
            row2, text="Generar",
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
            self._row3_manual, text="Valores (separados por coma):",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        self._manual_entry = ctk.CTkEntry(
            self._row3_manual, height=34,
            placeholder_text="Ej: 5, 12, 23, 45, 89",
            font=ctk.CTkFont(size=14),
        )
        self._manual_entry.pack(side="left", fill="x", expand=True)

        self._error_label = ctk.CTkLabel(
            self.content, text="",
            font=ctk.CTkFont(size=13),
            text_color=("#cc0000", "#ff4444"),
        )
        self._error_label.pack(fill="x", padx=20, pady=(0, 4))

        self._scroll_frame = ctk.CTkScrollableFrame(
            self.content,
            corner_radius=12,
            fg_color=("gray96", "gray14"),
            border_width=2,
            border_color=("gray78", "gray30"),
            label_text="Estructura generada (ordenada)",
            label_font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self._placeholder = ctk.CTkLabel(
            self._scroll_frame,
            text="Configura los parámetros y presiona «Generar» para comenzar.",
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
        self._data.clear()
        self._info_label.configure(text="")
        self._clear_error()
        self._manual_entry.delete(0, 'end')
        
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()
        self._cell_frames.clear()
        
        self._placeholder = ctk.CTkLabel(
            self._scroll_frame,
            text="Estructura limpiada. Configura los parámetros y presiona «Generar».",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray55"),
        )
        self._placeholder.pack(pady=40)

    def _validate_inputs(self) -> tuple[list[int] | None, bool]:
        raw_size = self._size_entry.get().strip()
        if not raw_size:
            self._show_error("Ingresa un número para el tamaño (N).")
            return None, False

        try:
            size = int(raw_size)
        except ValueError:
            self._show_error(f"«{raw_size}» no es un tamaño válido.")
            return None, False

        if size <= 0:
            self._show_error("El tamaño debe ser un entero positivo.")
            return None, False
            
        if size > _MAX_SIZE:
            self._show_error(f"El tamaño máximo recomendado es {_MAX_SIZE:,}.")
            return None, False

        mode = self._mode_var.get()
        
        if mode == "Aleatorio":
            self._clear_error()
            data = [random.randint(_VALUE_MIN, _VALUE_MAX) for _ in range(size)]
            return sorted(data), True
            
        raw_manual = self._manual_entry.get().strip()
        if not raw_manual:
            self._show_error("Ingresa los valores separados por coma.")
            return None, False
            
        parts = [p.strip() for p in raw_manual.split(",") if p.strip()]
        
        if len(parts) != size:
            self._show_error(
                f"Ingresaste {len(parts)} valores, pero el tamaño (N) es {size}."
            )
            return None, False
            
        parsed_data = []
        for p in parts:
            try:
                parsed_data.append(int(p))
            except ValueError:
                self._show_error(f"«{p}» no es un valor entero válido.")
                return None, False
                
        self._clear_error()
        
        is_sorted = all(parsed_data[i] <= parsed_data[i+1] for i in range(len(parsed_data)-1))
        
        if not is_sorted:
            return sorted(parsed_data), True
            
        return parsed_data, False

    def _on_generate(self):
        new_data, was_sorted_automatically = self._validate_inputs()
        if new_data is None:
            return

        self._data = new_data
        self._render_structure()
        
        mode = self._mode_var.get()
        msg = f"{len(self._data)} elementos"
        
        if mode == "Aleatorio":
            self._info_label.configure(text=msg + " (Aleatorio, ordenados)")
        else:
            if was_sorted_automatically:
                self._info_label.configure(
                    text=msg + " (Manual. Se ordenaron automáticamente para Búsqueda Binaria)"
                )
            else:
                self._info_label.configure(text=msg + " (Manual, ingresados en orden)")

    def _render_structure(self):
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()
        self._cell_frames.clear()

        if not self._data:
            return

        header = ctk.CTkFrame(self._scroll_frame, fg_color="transparent")
        header.pack(fill="x", padx=6, pady=(8, 4))

        ctk.CTkLabel(
            header, text="Índice", width=80,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("gray30", "gray70"),
        ).pack(side="left", padx=(4, 16))

        ctk.CTkLabel(
            header, text="Valor",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("gray30", "gray70"),
        ).pack(side="left")

        for idx, value in enumerate(self._data):
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

            ctk.CTkLabel(
                row, text=str(value),
                font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
                anchor="w",
            ).pack(side="left", padx=4)

            self._cell_frames.append(row)

    def _show_error(self, msg: str):
        self._error_label.configure(text=msg)

    def _clear_error(self):
        self._error_label.configure(text="")
