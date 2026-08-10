import random
from bisect import insort

import customtkinter as ctk
from views.base_view import BaseView


_MAX_ELEMENTS = 1_000
_DEFAULT_RANGE = 100
_DEFAULT_KEY_SIZE = 3
_DEFAULT_SIZE = 10


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

        self._anim_job = None
        self._is_animating = False

        self._build_ui()

    def _build_ui(self):
        """Construye la interfaz de la búsqueda binaria."""

        self.add_title("Búsqueda Binaria")

        self.add_subtitle(
            "Divide el conjunto ordenado a la mitad en cada paso "
            "para localizar el valor."
        )

        config_frame = ctk.CTkFrame(
            self.content,
            corner_radius=12,
            fg_color=("gray92", "gray17"),
            border_width=2,
            border_color=("gray78", "gray30"),
        )
        config_frame.pack(
            fill="x",
            padx=10,
            pady=(0, 8)
        )

        inner = ctk.CTkFrame(
            config_frame,
            fg_color="transparent"
        )
        inner.pack(
            padx=16,
            pady=14,
            fill="x"
        )

        row1 = ctk.CTkFrame(
            inner,
            fg_color="transparent"
        )
        row1.pack(
            fill="x",
            pady=(0, 10)
        )

        ctk.CTkLabel(
            row1,
            text="Modo de carga:",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            ),
        ).pack(
            side="left",
            padx=(0, 12)
        )

        self._mode_seg = ctk.CTkSegmentedButton(
            row1,
            values=["Aleatorio", "Manual"],
            variable=self._mode_var,
            command=self._on_mode_change,
            font=ctk.CTkFont(size=13),
        )
        self._mode_seg.pack(
            side="left"
        )

        row2 = ctk.CTkFrame(
            inner,
            fg_color="transparent"
        )
        row2.pack(
            fill="x",
            pady=(0, 10)
        )

        # Rango
        ctk.CTkLabel(
            row2,
            text="Rango:",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            ),
        ).pack(
            side="left",
            padx=(0, 8)
        )

        self._range_entry = ctk.CTkEntry(
            row2,
            width=80,
            height=34,
            placeholder_text=str(_DEFAULT_RANGE),
            font=ctk.CTkFont(size=14),
            justify="center",
        )
        self._range_entry.pack(
            side="left",
            padx=(0, 16)
        )
        self._range_entry.insert(
            0,
            str(_DEFAULT_RANGE)
        )

        # Tamaño de clave
        ctk.CTkLabel(
            row2,
            text="Tamaño de clave:",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            ),
        ).pack(
            side="left",
            padx=(0, 8)
        )

        self._key_size_entry = ctk.CTkEntry(
            row2,
            width=80,
            height=34,
            placeholder_text=str(_DEFAULT_KEY_SIZE),
            font=ctk.CTkFont(size=14),
            justify="center",
        )
        self._key_size_entry.pack(
            side="left",
            padx=(0, 16)
        )
        self._key_size_entry.insert(
            0,
            str(_DEFAULT_KEY_SIZE)
        )

        # Cantidad
        ctk.CTkLabel(
            row2,
            text="Cantidad:",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            ),
        ).pack(
            side="left",
            padx=(0, 8)
        )

        self._size_entry = ctk.CTkEntry(
            row2,
            width=80,
            height=34,
            placeholder_text=str(_DEFAULT_SIZE),
            font=ctk.CTkFont(size=14),
            justify="center",
        )
        self._size_entry.pack(
            side="left",
            padx=(0, 16)
        )
        self._size_entry.insert(
            0,
            str(_DEFAULT_SIZE)
        )

        # Generar
        self._btn_generate = ctk.CTkButton(
            row2,
            text="Generar",
            width=120,
            height=34,
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            command=self._on_generate,
        )
        self._btn_generate.pack(
            side="left",
            padx=(0, 8)
        )

        # Limpiar
        self._btn_clear = ctk.CTkButton(
            row2,
            text="Limpiar",
            width=100,
            height=34,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            text_color=("black", "white"),
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            command=self._on_clear,
        )
        self._btn_clear.pack(
            side="left",
            padx=(0, 16)
        )

        self._info_label = ctk.CTkLabel(
            row2,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray55"),
        )
        self._info_label.pack(
            side="left"
        )

        row3 = ctk.CTkFrame(
            inner,
            fg_color="transparent"
        )
        row3.pack(
            fill="x"
        )

        ctk.CTkLabel(
            row3,
            text="Agregar valores:",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            ),
        ).pack(
            side="left",
            padx=(0, 8)
        )

        self._manual_entry = ctk.CTkEntry(
            row3,
            height=34,
            placeholder_text="Ej: 12, 45, 7, 89, 23",
            font=ctk.CTkFont(size=14),
        )
        self._manual_entry.pack(
            side="left",
            fill="x",
            expand=True
        )

        search_frame = ctk.CTkFrame(
            self.content,
            corner_radius=12,
            fg_color=("gray92", "gray17"),
            border_width=2,
            border_color=("gray78", "gray30"),
        )
        search_frame.pack(
            fill="x",
            padx=10,
            pady=(0, 8)
        )

        search_inner = ctk.CTkFrame(
            search_frame,
            fg_color="transparent"
        )
        search_inner.pack(
            padx=16,
            pady=12,
            fill="x"
        )

        s_row1 = ctk.CTkFrame(search_inner, fg_color="transparent")
        s_row1.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            s_row1,
            text="Valor objetivo:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        self._search_entry = ctk.CTkEntry(
            s_row1,
            width=110,
            height=34,
            placeholder_text="Ej: 45",
            font=ctk.CTkFont(size=14),
            justify="center",
        )
        self._search_entry.pack(side="left", padx=(0, 12))

        self._btn_search = ctk.CTkButton(
            s_row1,
            text="🔍 Buscar",
            width=110,
            height=34,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_start_search,
        )
        self._btn_search.pack(side="left", padx=(0, 10))

        self._btn_reset_search = ctk.CTkButton(
            s_row1,
            text="Reiniciar Búsqueda",
            width=160,
            height=34,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            text_color=("black", "white"),
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_reset_search,
        )
        self._btn_reset_search.pack(side="left")

        s_row2 = ctk.CTkFrame(search_inner, fg_color="transparent")
        s_row2.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            s_row2,
            text="Velocidad (ms):",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        self._speed_slider = ctk.CTkSlider(
            s_row2,
            from_=100,
            to=2000,
            number_of_steps=19,
            width=180,
            command=self._on_speed_change,
        )
        self._speed_slider.set(500)
        self._speed_slider.pack(side="left", padx=(0, 8))

        self._speed_label = ctk.CTkLabel(
            s_row2,
            text="500 ms",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray60"),
            width=65,
        )
        self._speed_label.pack(side="left")

        self._status_box = ctk.CTkFrame(
            search_inner,
            corner_radius=8,
            fg_color=("gray85", "gray22"),
            border_width=1,
            border_color=("gray75", "gray35"),
        )
        self._status_box.pack(fill="x", pady=(4, 0))

        self._status_label = ctk.CTkLabel(
            self._status_box,
            text="Estado: Listo para realizar una búsqueda binaria.",
            font=ctk.CTkFont(size=13),
            text_color=("gray20", "gray80"),
            anchor="w",
            padx=12,
            pady=8,
        )
        self._status_label.pack(fill="x")

        # ERROR
        self._error_label = ctk.CTkLabel(
            self.content,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=("#cc0000", "#ff4444"),
        )
        self._error_label.pack(
            fill="x",
            padx=20,
            pady=(0, 4)
        )

        self._scroll_frame = ctk.CTkScrollableFrame(
            self.content,
            corner_radius=12,
            fg_color=("gray96", "gray14"),
            border_width=2,
            border_color=("gray78", "gray30"),
            label_text="Estructura generada (ordenada)",
            label_font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
        )
        self._scroll_frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 10)
        )

        self._placeholder = ctk.CTkLabel(
            self._scroll_frame,
            text=(
                "Configura los parámetros y presiona «Generar» "
                "para comenzar."
            ),
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray55"),
        )
        self._placeholder.pack(
            pady=40
        )

        self._on_mode_change(
            self._mode_var.get()
        )

    def _on_mode_change(self, selected_mode: str):

        if selected_mode == "Aleatorio":

            self._manual_entry.configure(
                state="disabled",
                fg_color=("gray85", "gray25")
            )

        else:

            self._manual_entry.configure(
                state="normal",
                fg_color=("white", "gray20")
            )

        self._clear_error()

    def _validate_configuration(self):

        # Rango
        raw_range = self._range_entry.get().strip()

        if not raw_range:
            self._show_error(
                "Ingresa el rango."
            )
            return None

        try:
            value_range = int(raw_range)
        except ValueError:
            self._show_error(
                "El rango debe ser un número entero."
            )
            return None

        if value_range <= 0:
            self._show_error(
                "El rango debe ser mayor que cero."
            )
            return None

        # Tamaño de clave
        raw_key_size = self._key_size_entry.get().strip()

        if not raw_key_size:
            self._show_error(
                "Ingresa el tamaño de la clave."
            )
            return None

        try:
            key_size = int(raw_key_size)
        except ValueError:
            self._show_error(
                "El tamaño de la clave debe ser un número entero."
            )
            return None

        if key_size <= 0:
            self._show_error(
                "El tamaño de la clave debe ser mayor que cero."
            )
            return None

        # Cantidad
        raw_size = self._size_entry.get().strip()

        if not raw_size:
            self._show_error(
                "Ingresa la cantidad de elementos."
            )
            return None

        try:
            size = int(raw_size)
        except ValueError:
            self._show_error(
                "La cantidad debe ser un número entero."
            )
            return None

        if size <= 0:
            self._show_error(
                "La cantidad debe ser mayor que cero."
            )
            return None

        if size > _MAX_ELEMENTS:
            self._show_error(
                f"La cantidad máxima es {_MAX_ELEMENTS:,} elementos."
            )
            return None

        max_by_key_size = (10 ** key_size) - 1

        if value_range > max_by_key_size:
            self._show_error(
                f"El rango {value_range} supera el máximo "
                f"permitido para una clave de {key_size} "
                f"dígitos ({max_by_key_size})."
            )
            return None

        return value_range, key_size, size

    def _validate_manual_values(
        self,
        value_range: int,
        key_size: int,
        values_text: str
    ):

        if not values_text:
            self._show_error(
                "Ingresa al menos un valor."
            )
            return None

        parts = [
            p.strip()
            for p in values_text.split(",")
            if p.strip()
        ]

        if not parts:
            self._show_error(
                "Ingresa valores separados por coma."
            )
            return None

        parsed_values = []

        for part in parts:

            try:
                value = int(part)
            except ValueError:
                self._show_error(
                    f"«{part}» no es un número entero válido."
                )
                return None

            if value < 1 or value > value_range:
                self._show_error(
                    f"El valor {value} está fuera del rango "
                    f"permitido: 1 - {value_range}."
                )
                return None

            if len(str(abs(value))) > key_size:
                self._show_error(
                    f"El valor {value} supera el tamaño de clave "
                    f"de {key_size} dígitos."
                )
                return None

            parsed_values.append(value)

        return parsed_values

    def _on_generate(self):

        self._on_reset_search()

        configuration = self._validate_configuration()

        if configuration is None:
            return

        value_range, key_size, size = configuration

        mode = self._mode_var.get()

        # ALEATORIO
        if mode == "Aleatorio":

            self._data = [
                random.randint(1, value_range)
                for _ in range(size)
            ]

            self._data.sort()

            self._clear_error()
            self._render_structure()

            self._info_label.configure(
                text=f"{len(self._data)} elementos generados y ordenados"
            )

            return

        values = self._validate_manual_values(
            value_range,
            key_size,
            self._manual_entry.get().strip()
        )

        if values is None:
            return

        remaining = size - len(self._data)

        if len(values) > remaining:
            self._show_error(
                f"Intentas agregar {len(values)} valores, "
                f"pero solo quedan {remaining} espacios disponibles "
                f"de los {size} indicados."
            )
            return

        for value in values:
            insort(self._data, value)

        self._manual_entry.delete(
            0,
            "end"
        )

        self._clear_error()
        self._render_structure()

        self._info_label.configure(
            text=f"{len(self._data)}/{size} elementos ordenados"
        )

    # LIMPIAR
    def _on_clear(self):

        self._on_reset_search()

        self._data.clear()

        self._manual_entry.delete(
            0,
            "end"
        )

        self._info_label.configure(
            text=""
        )

        self._clear_error()

        for widget in self._scroll_frame.winfo_children():
            widget.destroy()

        self._cell_frames.clear()

        self._placeholder = ctk.CTkLabel(
            self._scroll_frame,
            text=(
                "Estructura limpiada. Configura los parámetros "
                "y presiona «Generar»."
            ),
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray55"),
        )
        self._placeholder.pack(
            pady=40
        )

    def _render_structure(self):

        for widget in self._scroll_frame.winfo_children():
            widget.destroy()

        self._cell_frames.clear()

        if not self._data:
            return

        header = ctk.CTkFrame(
            self._scroll_frame,
            fg_color="transparent"
        )
        header.pack(
            fill="x",
            padx=6,
            pady=(8, 4)
        )

        ctk.CTkLabel(
            header,
            text="Índice",
            width=80,
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            text_color=("gray30", "gray70"),
        ).pack(
            side="left",
            padx=(4, 16)
        )

        ctk.CTkLabel(
            header,
            text="Valor",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            text_color=("gray30", "gray70"),
        ).pack(
            side="left"
        )

        ctk.CTkLabel(
            header,
            text="Punteros",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
            text_color=("gray30", "gray70"),
        ).pack(
            side="right",
            padx=16
        )

        for idx, value in enumerate(self._data):

            bg = (
                ("gray88", "gray22")
                if idx % 2 == 0
                else ("gray94", "gray17")
            )

            row = ctk.CTkFrame(
                self._scroll_frame,
                height=36,
                corner_radius=8,
                fg_color=bg,
            )
            row._default_bg = bg

            row.pack(
                fill="x",
                padx=6,
                pady=2
            )

            row.pack_propagate(False)

            ctk.CTkLabel(
                row,
                text=str(idx),
                width=80,
                font=ctk.CTkFont(
                    family="Consolas",
                    size=14
                ),
                anchor="center",
            ).pack(
                side="left",
                padx=(8, 16)
            )

            ctk.CTkLabel(
                row,
                text=str(value),
                font=ctk.CTkFont(
                    family="Consolas",
                    size=14,
                    weight="bold"
                ),
                anchor="w",
            ).pack(
                side="left",
                padx=4
            )

            ptr_lbl = ctk.CTkLabel(
                row,
                text="",
                font=ctk.CTkFont(
                    family="Consolas",
                    size=12,
                    weight="bold"
                ),
                text_color=("gray40", "gray60"),
                anchor="e",
            )
            ptr_lbl.pack(side="right", padx=12)
            row._ptr_lbl = ptr_lbl

            self._cell_frames.append(row)

    # MENSAJES

    def _show_error(self, msg: str):
        self._error_label.configure(
            text=msg
        )

    def _clear_error(self):
        self._error_label.configure(
            text=""
        )


    # BÚSQUEDA Y ANIMACIÓN
    def _on_speed_change(self, value):
        val = int(value)
        self._speed_label.configure(text=f"{val} ms")

    def _set_controls_state(self, state: str):
        if state == "disabled":
            self._mode_seg.configure(state="disabled")
            self._range_entry.configure(state="disabled")
            self._key_size_entry.configure(state="disabled")
            self._size_entry.configure(state="disabled")
            self._manual_entry.configure(state="disabled")
            self._btn_generate.configure(state="disabled")
            self._btn_clear.configure(state="disabled")
            self._search_entry.configure(state="disabled")
            self._btn_search.configure(state="disabled")
        else:
            self._mode_seg.configure(state="normal")
            self._range_entry.configure(state="normal")
            self._key_size_entry.configure(state="normal")
            self._size_entry.configure(state="normal")
            self._btn_generate.configure(state="normal")
            self._btn_clear.configure(state="normal")
            self._search_entry.configure(state="normal")
            self._btn_search.configure(state="normal")
            self._on_mode_change(self._mode_var.get())

    def _reset_search_visuals(self):
        for row in self._cell_frames:
            if hasattr(row, "_default_bg"):
                row.configure(fg_color=row._default_bg)
            if hasattr(row, "_ptr_lbl"):
                row._ptr_lbl.configure(text="", text_color=("gray40", "gray60"))

    def _on_start_search(self):
        if self._is_animating:
            return

        if not self._data:
            self._show_error("Primero genera o agrega datos a la estructura para buscar.")
            return

        raw_target = self._search_entry.get().strip()
        if not raw_target:
            self._show_error("Ingresa el valor objetivo a buscar.")
            return

        try:
            target = int(raw_target)
        except ValueError:
            self._show_error("El valor a buscar debe ser un número entero.")
            return

        self._clear_error()
        self._reset_search_visuals()
        self._set_controls_state("disabled")
        self._is_animating = True

        self._step_binary(inicio=0, fin=len(self._data) - 1, target=target, step=1)

    def _step_binary(self, inicio: int, fin: int, target: int, step: int):
        if not self._is_animating:
            return

        if inicio > fin:
            for row in self._cell_frames:
                row.configure(fg_color=("#FEE2E2", "#450A0A"))
                if hasattr(row, "_ptr_lbl"):
                    row._ptr_lbl.configure(text="", text_color=("gray40", "gray60"))

            self._status_label.configure(
                text=f"Elemento {target} no existe en el arreglo (inicio={inicio} > fin={fin}). Pasos evaluados: {step - 1}."
            )
            self._is_animating = False
            self._anim_job = None
            self._set_controls_state("normal")
            return

        medio = (inicio + fin) // 2

        for idx, row in enumerate(self._cell_frames):
            ptr_tags = []

            if idx < inicio or idx > fin:
                row.configure(fg_color=("gray90", "gray20"))
            else:
                row.configure(fg_color=("gray82", "gray28"))

            if idx == inicio:
                ptr_tags.append("INICIO")
            if idx == fin:
                ptr_tags.append("FIN")
            if idx == medio:
                ptr_tags.append("MEDIO")

            if hasattr(row, "_ptr_lbl"):
                if ptr_tags:
                    tag_str = " | ".join(ptr_tags)
                    color = ("#2563EB", "#60A5FA") if idx == medio else ("#374151", "#9CA3AF")
                    row._ptr_lbl.configure(
                        text=f" [{tag_str}]",
                        text_color=color
                    )
                else:
                    row._ptr_lbl.configure(text="")

        # Resaltar la posición MEDIO
        medio_row = self._cell_frames[medio]
        medio_row.configure(fg_color=("#FB923C", "#9A3412"))

        self._scroll_to_index(medio)

        medio_val = self._data[medio]

        if medio_val == target:
            medio_row.configure(fg_color=("#4ADE80", "#166534"))
            if hasattr(medio_row, "_ptr_lbl"):
                medio_row._ptr_lbl.configure(
                    text="[ENCONTRADO]",
                    text_color=("#166534", "#86EFAC")
                )
            self._status_label.configure(
                text=f"¡Elemento {target} encontrado en el índice {medio}! (Paso {step}: inicio={inicio}, fin={fin}, medio={medio})"
            )
            self._is_animating = False
            self._anim_job = None
            self._set_controls_state("normal")
            return

        speed = int(self._speed_slider.get())

        if target < medio_val:
            self._status_label.configure(
                text=f"Paso {step}: inicio={inicio}, fin={fin}, medio={medio}. Como {target} < {medio_val}, el valor buscado es menor -> Descartando mitad derecha (fin pasa a {medio - 1})."
            )
            self._anim_job = self.after(
                speed, lambda: self._step_binary(inicio, medio - 1, target, step + 1)
            )
        else: 
            self._status_label.configure(
                text=f"Paso {step}: inicio={inicio}, fin={fin}, medio={medio}. Como {target} > {medio_val}, el valor buscado es mayor -> Descartando mitad izquierda (inicio pasa a {medio + 1})."
            )
            self._anim_job = self.after(
                speed, lambda: self._step_binary(medio + 1, fin, target, step + 1)
            )

    def _on_reset_search(self):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None

        self._is_animating = False
        self._reset_search_visuals()
        self._set_controls_state("normal")
        self._status_label.configure(text="Estado: Búsqueda reiniciada. Listo para buscar.")
        self._clear_error()

    def _scroll_to_index(self, index: int):
        if not self._data:
            return
        try:
            fraction = max(0.0, min(1.0, index / len(self._data)))
            self._scroll_frame._parent_canvas.yview_moveto(fraction)
        except Exception:
            pass

    def destroy(self):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None
        super().destroy()

