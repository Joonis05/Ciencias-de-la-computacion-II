import random
import customtkinter as ctk
from views.base_view import BaseView
from views.persistence import save_json, load_json

_MAX_ELEMENTS = 1_000
_DEFAULT_KEY_SIZE = 3
_DEFAULT_SIZE = 10
_INITIAL_COLS = 2
_INITIAL_ROW_HEIGHT = 2


class BusquedaDinamicaExternaView(BaseView):
    """Vista de Búsqueda Externa Dinámica basada en Cubetas y función Hash (key % N)."""

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Búsqueda Externa Dinámica",
            **kwargs,
        )
        self._max_records = 0
        self._num_cols = _INITIAL_COLS
        self._structure_created = False
        self._cubetas = {c: [] for c in range(_INITIAL_COLS)}
        self._cubeta_heights = {c: _INITIAL_ROW_HEIGHT for c in range(_INITIAL_COLS)}
        self._cell_widgets = {}  # (r, c) -> dict of widgets
        self._mode_var = ctk.StringVar(value="Aleatorio")
        self._expansion_mode_var = ctk.StringVar(value="Total")
        self._anim_job = None
        self._is_animating = False
        self._pending_action = None
        self._build_ui()

    def _build_ui(self):
        self.add_title("Búsqueda Externa Dinámica")
        self.add_subtitle("Función hash (clave % cubetas). Expansión vertical por cubeta y horizontal al 75% de ocupación.")

        config = ctk.CTkFrame(
            self.content,
            corner_radius=12,
            fg_color=("gray92", "gray17"),
            border_width=2,
            border_color=("gray78", "gray30"),
        )
        config.pack(fill="x", padx=10, pady=(0, 8))
        inner = ctk.CTkFrame(config, fg_color="transparent")
        inner.pack(padx=16, pady=14, fill="x")

        # Row 1: Modo de Carga [Aleatorio | Manual] | Modo de Expansión [Total | Parcial]
        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(row1, text="Modo de Carga:", font=ctk.CTkFont(size=14, weight="bold")).pack(
            side="left", padx=(0, 12)
        )
        self._mode_seg = ctk.CTkSegmentedButton(
            row1,
            values=["Aleatorio", "Manual"],
            variable=self._mode_var,
            command=self._on_mode_change,
            font=ctk.CTkFont(size=13),
        )
        self._mode_seg.pack(side="left", padx=(0, 24))

        ctk.CTkLabel(row1, text="Modo de Expansión:", font=ctk.CTkFont(size=14, weight="bold")).pack(
            side="left", padx=(0, 12)
        )
        self._expansion_mode_seg = ctk.CTkSegmentedButton(
            row1,
            values=["Total", "Parcial"],
            variable=self._expansion_mode_var,
            font=ctk.CTkFont(size=13),
        )
        self._expansion_mode_seg.pack(side="left")

        # Row 2: Cantidad de registros [ ] Tamaño de clave [ ] [Generar Estructura] [Limpiar]
        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 10))
        self._size_entry = self._entry_with_label(row2, "Cantidad de registros:", str(_DEFAULT_SIZE))
        self._key_size_entry = self._entry_with_label(row2, "Tamaño de clave:", str(_DEFAULT_KEY_SIZE))

        self._btn_structure = ctk.CTkButton(
            row2,
            text="Generar Estructura",
            width=140,
            height=34,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_generate_structure,
        )
        self._btn_structure.pack(side="left", padx=(0, 8))
        self._btn_clear = ctk.CTkButton(
            row2,
            text="Limpiar",
            width=90,
            height=34,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            text_color=("black", "white"),
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_clear,
        )
        self._btn_clear.pack(side="left", padx=(0, 8))
        self._info_label = ctk.CTkLabel(row2, text="", font=ctk.CTkFont(size=12), text_color=("gray50", "gray55"))
        self._info_label.pack(side="left", padx=(8, 0))

        # Row 3: Valores [_______________________________________________________]
        row3 = ctk.CTkFrame(inner, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(row3, text="Valores:", font=ctk.CTkFont(size=14, weight="bold")).pack(
            side="left", padx=(0, 12)
        )
        self._val_entry = ctk.CTkEntry(
            row3,
            height=34,
            placeholder_text="Ingrese valores o clave objetivo (ej: 25, 45, 15, 10)",
            font=ctk.CTkFont(size=14),
        )
        self._val_entry.pack(side="left", fill="x", expand=True)
        self._manual_entry = self._val_entry
        self._search_entry = self._val_entry

        # Row 4: [Añadir] [Buscar] [Eliminar] [Reiniciar] | Speed Slider | [Guardar] [Cargar]
        row4 = ctk.CTkFrame(inner, fg_color="transparent")
        row4.pack(fill="x", pady=(0, 10))
        self._btn_generate = ctk.CTkButton(
            row4,
            text="Añadir",
            width=90,
            height=34,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_add,
        )
        self._btn_generate.pack(side="left", padx=(0, 8))
        self._btn_search = ctk.CTkButton(
            row4,
            text="Buscar",
            width=90,
            height=34,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_start_search,
        )
        self._btn_search.pack(side="left", padx=(0, 8))
        self._btn_delete = ctk.CTkButton(
            row4,
            text="Eliminar",
            width=90,
            height=34,
            fg_color="#C62828",
            hover_color="#8E0000",
            text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_delete,
        )
        self._btn_delete.pack(side="left", padx=(0, 8))
        self._btn_reset_search = ctk.CTkButton(
            row4,
            text="Reiniciar",
            width=90,
            height=34,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            text_color=("black", "white"),
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_reset_search,
        )
        self._btn_reset_search.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(row4, text="Velocidad:", font=ctk.CTkFont(size=12, weight="bold")).pack(
            side="left", padx=(0, 4)
        )
        self._speed_slider = ctk.CTkSlider(
            row4, from_=100, to=2000, number_of_steps=19, width=130, command=self._on_speed_change
        )
        self._speed_slider.set(500)
        self._speed_slider.pack(side="left", padx=(0, 4))
        self._speed_label = ctk.CTkLabel(
            row4, text="500 ms", font=ctk.CTkFont(size=12), text_color=("gray40", "gray60"), width=55
        )
        self._speed_label.pack(side="left", padx=(0, 8))

        self._btn_save = ctk.CTkButton(row4, text="Guardar", width=80, height=34, command=self._on_save)
        self._btn_save.pack(side="right", padx=(6, 0))
        self._btn_load = ctk.CTkButton(row4, text="Cargar", width=80, height=34, command=self._on_load)
        self._btn_load.pack(side="right")

        # Row 5: Estado: ...
        row5 = ctk.CTkFrame(
            inner, corner_radius=8, fg_color=("gray85", "gray22"), border_width=1, border_color=("gray75", "gray35")
        )
        row5.pack(fill="x", pady=(4, 0))
        self._status_box = row5
        self._status_label = ctk.CTkLabel(
            self._status_box,
            text="Estado: estructura no generada.",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("gray20", "gray80"),
            anchor="w",
            padx=12,
            pady=10,
        )
        self._status_label.pack(fill="x")

        self._error_box = ctk.CTkFrame(
            self.content,
            corner_radius=8,
            fg_color=("#FEE2E2", "#450A0A"),
            border_width=1,
            border_color=("#FCA5A5", "#7F1D1D"),
        )
        self._error_label = ctk.CTkLabel(
            self._error_box,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#991B1B", "#FCA5A5"),
            anchor="w",
            padx=12,
            pady=6,
        )
        self._error_label.pack(fill="x")
        self._error_box.pack_forget()

        # Canvas/Scroll container for the Matrix Grid Diagram with horizontal scrollbar
        self._scroll_frame = ctk.CTkScrollableFrame(
            self.content,
            corner_radius=12,
            fg_color=("gray96", "gray14"),
            border_width=2,
            border_color=("gray78", "gray30"),
            orientation="horizontal",
            height=280,
        )
        self._scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Estado inicial: mostrar placeholder hasta presionar «Generar Estructura»
        self._show_placeholder()
        self._on_mode_change(self._mode_var.get())

    def _entry_with_label(self, parent, text, default):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(0, 6))
        e = ctk.CTkEntry(
            parent, width=105, height=34, placeholder_text=default, font=ctk.CTkFont(size=14), justify="center"
        )
        e.pack(side="left", padx=(0, 16))
        e.insert(0, default)
        return e

    def _on_mode_change(self, selected):
        self._manual_entry.configure(
            state="disabled" if selected == "Aleatorio" else "normal",
            fg_color=("gray85", "gray25") if selected == "Aleatorio" else ("white", "gray20"),
        )
        self._clear_error()

    def _validate_configuration(self):
        try:
            key_size = int(self._key_size_entry.get().strip())
            size = int(self._size_entry.get().strip())
        except ValueError:
            self._show_error("Tamaño de clave y cantidad de registros deben ser números enteros.")
            return None
        if key_size <= 0 or size <= 0:
            self._show_error("Los parámetros deben ser mayores que cero.")
            return None
        if size > _MAX_ELEMENTS:
            self._show_error(f"La cantidad máxima de registros es {_MAX_ELEMENTS:,}.")
            return None
        min_key = 1 if key_size == 1 else (10 ** (key_size - 1))
        max_key = (10**key_size) - 1
        return key_size, size, min_key, max_key

    def _parse_manual_values(self, min_key, max_key, key_size):
        text = self._manual_entry.get().strip()
        if not text:
            self._show_error("Ingresa al menos un valor.")
            return None
        values = []
        for part in [p.strip() for p in text.split(",") if p.strip()]:
            try:
                value = int(part)
            except ValueError:
                self._show_error(f"«{part}» no es un número entero válido.")
                return None
            if not (min_key <= value <= max_key):
                self._show_error(
                    f"El valor {value} debe tener exactamente {key_size} dígitos (entre {min_key} y {max_key})."
                )
                return None
            values.append(value)
        return values

    def _get_all_inserted_keys(self):
        all_keys = []
        for c in range(self._num_cols):
            all_keys.extend(self._cubetas[c])
        return all_keys

    def _total_slots_capacity(self):
        return self._num_cols * _INITIAL_ROW_HEIGHT

    def _check_and_expand_horizontal(self):
        """Si la ocupación supera el 75% de la capacidad base (num_cols * 2),
        duplica el número de columnas (cubetas) al doble de la actual (2 -> 4 -> 8...)
        y recalcula la posición de todas las claves con (clave % num_cols)."""
        all_keys = self._get_all_inserted_keys()
        total_slots = self._total_slots_capacity()

        needs_expansion = total_slots > 0 and (len(all_keys) / total_slots) > 0.75

        expanded = False
        if needs_expansion:
            if self._expansion_mode_var.get() == "Parcial":
                if (self._num_cols & (self._num_cols - 1)) == 0:
                    self._num_cols += self._num_cols // 2
                else:
                    self._num_cols += self._num_cols // 3
            else:
                self._num_cols *= 2
            expanded = True
            # Reorganizar todas las claves existentes recalculando (clave % num_cols)
            self._cubetas = {c: [] for c in range(self._num_cols)}
            self._cubeta_heights = {c: _INITIAL_ROW_HEIGHT for c in range(self._num_cols)}
            for k in all_keys:
                c = k % self._num_cols
                self._cubetas[c].append(k)
                if len(self._cubetas[c]) > self._cubeta_heights[c]:
                    self._cubeta_heights[c] = len(self._cubetas[c])
        return expanded

    def _on_generate_structure(self):
        if self._is_animating:
            return
        cfg = self._validate_configuration()
        if cfg is None:
            return
        _, size, _, _ = cfg
        self._max_records = size
        self._num_cols = _INITIAL_COLS
        self._cubetas = {c: [] for c in range(_INITIAL_COLS)}
        self._cubeta_heights = {c: _INITIAL_ROW_HEIGHT for c in range(_INITIAL_COLS)}
        self._structure_created = True
        self._expansion_mode_seg.configure(state="disabled")
        self._render_structure()
        self._update_info_and_status("Estructura 2x2 generada (2 cubetas). Función Hash: clave % 2.")
        self._clear_error()

    def _generate_unique_random_keys(self, count, min_key, max_key, existing_set):
        available_range = max_key - min_key + 1
        if available_range < len(existing_set) + count:
            return None
        res = set()
        while len(res) < count:
            k = random.randint(min_key, max_key)
            if k not in existing_set and k not in res:
                res.add(k)
        return list(res)

    def _insert_single_key(self, key):
        """Inserta una clave usando (key % num_cols). Expande verticalmente la cubeta si sobrepasa su altura actual."""
        col = key % self._num_cols
        if key in self._cubetas[col]:
            return False, f"La clave {key} ya existe en la cubeta {col}."
        self._cubetas[col].append(key)
        # Si la cubeta supera la cantidad actual de filas, expande en 1 verticalmente sólo esa columna
        if len(self._cubetas[col]) > self._cubeta_heights[col]:
            self._cubeta_heights[col] = len(self._cubetas[col])
        return True, ""

    def _on_add(self):
        if self._is_animating:
            return
        if not self._structure_created:
            self._show_error("Primero debes generar la estructura.")
            return
        all_keys = self._get_all_inserted_keys()
        if len(all_keys) >= self._max_records:
            self._show_error(f"Se alcanzó el límite máximo de registros configurado ({self._max_records}).")
            return
        cfg = self._validate_configuration()
        if cfg is None:
            return
        key_size, _, min_key, max_key = cfg
        existing_keys = set(all_keys)

        if self._mode_var.get() == "Aleatorio":
            remaining = self._max_records - len(all_keys)
            new_values = self._generate_unique_random_keys(remaining, min_key, max_key, existing_keys)
            if new_values is None:
                self._show_error(f"No hay suficientes claves únicas disponibles en el rango de {key_size} dígitos.")
                return
        else:
            new_values = self._parse_manual_values(min_key, max_key, key_size)
            if new_values is None:
                return
            remaining = self._max_records - len(all_keys)
            if len(new_values) > remaining:
                self._show_error(f"Solo se pueden agregar hasta {remaining} registro(s) más.")
                return
            seen = set()
            for val in new_values:
                if val in seen or val in existing_keys:
                    self._show_error(f"La clave {val} está duplicada. No se permiten claves repetidas.")
                    return
                seen.add(val)

        # Insertar claves aplicando la función Hash (key % num_cols) y recalculando al expandir
        added_count = 0
        expanded_any = False

        for val in new_values:
            success, err = self._insert_single_key(val)
            if not success:
                self._show_error(err)
                return
            added_count += 1
            if self._check_and_expand_horizontal():
                expanded_any = True

        self._val_entry.delete(0, "end")
        self._render_structure()

        total_k = len(self._get_all_inserted_keys())
        total_s = self._total_slots_capacity()
        occ_pct = (total_k / total_s * 100) if total_s > 0 else 0

        if expanded_any:
            msg = (
                f"¡Estructura expandida a {self._num_cols} cubetas! "
                f"Se recalcularon las posiciones de todas las claves con (clave % {self._num_cols})."
            )
        else:
            msg = (
                f"Se añadieron {added_count} clave(s) usando (clave % {self._num_cols}). "
                f"Ocupación: {total_k}/{total_s} ({occ_pct:.1f}%)."
            )
        self._update_info_and_status(msg)
        self._clear_error()

    def _update_info_and_status(self, status_msg):
        total_k = len(self._get_all_inserted_keys())
        total_s = self._total_slots_capacity()
        occ_pct = (total_k / total_s * 100) if total_s > 0 else 0
        self._info_label.configure(
            text=f"{total_k}/{total_s} ({occ_pct:.1f}%) | {self._num_cols} cubetas (mod {self._num_cols})"
        )
        self._status_label.configure(text=f"Estado: {status_msg}")

    def _on_clear(self):
        self._on_reset_search()
        self._max_records = 0
        self._num_cols = _INITIAL_COLS
        self._cubetas = {c: [] for c in range(_INITIAL_COLS)}
        self._cubeta_heights = {c: _INITIAL_ROW_HEIGHT for c in range(_INITIAL_COLS)}
        self._structure_created = False
        self._expansion_mode_seg.configure(state="normal")
        self._manual_entry.delete(0, "end")
        self._info_label.configure(text="")
        self._clear_error()
        self._show_placeholder()
        self._status_label.configure(text="Estado: estructura limpiada.")

    def _render_structure(self):
        """Renderiza la matriz de cubetas (columnas N) con altura dinámica independiente por cubeta."""
        for w in self._scroll_frame.winfo_children():
            w.destroy()
        self._cell_widgets.clear()
        if not self._structure_created:
            return

        matrix_frame = ctk.CTkFrame(
            self._scroll_frame,
            corner_radius=12,
            fg_color="transparent",
        )
        matrix_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        # Encabezados de Columna (Cubetas 0, 1, 2, 3...)
        header_corner = ctk.CTkLabel(matrix_frame, text="", width=40)
        header_corner.grid(row=0, column=0, padx=5, pady=5)

        for col in range(self._num_cols):
            col_lbl = ctk.CTkLabel(
                matrix_frame,
                text=str(col),
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=("gray20", "gray80"),
                width=110,
            )
            col_lbl.grid(row=0, column=col + 1, padx=5, pady=5)

        # Determinar la altura máxima de fila a renderizar entre todas las cubetas
        max_rows = max(max(self._cubeta_heights.values(), default=_INITIAL_ROW_HEIGHT), _INITIAL_ROW_HEIGHT)

        for row in range(max_rows):
            # Etiqueta de Fila a la izquierda
            row_lbl = ctk.CTkLabel(
                matrix_frame,
                text=str(row),
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=("gray20", "gray80"),
                width=40,
            )
            row_lbl.grid(row=row + 1, column=0, padx=5, pady=5)

            for col in range(self._num_cols):
                if row < self._cubeta_heights[col]:
                    keys_list = self._cubetas[col]
                    val = keys_list[row] if row < len(keys_list) else None

                    cell_box = ctk.CTkFrame(
                        matrix_frame,
                        width=110,
                        height=100,
                        corner_radius=8,
                        border_width=2,
                        border_color=("gray70", "gray40"),
                        fg_color=("white", "gray16"),
                    )
                    cell_box.pack_propagate(False)
                    cell_box.grid(row=row + 1, column=col + 1, padx=4, pady=4)
                    cell_box._default_border = ("gray70", "gray40")
                    cell_box._default_fg = ("white", "gray16")

                    key_val_str = str(val) if val is not None else ""
                    val_lbl = ctk.CTkLabel(
                        cell_box,
                        text=key_val_str,
                        font=ctk.CTkFont(size=20, weight="bold" if key_val_str else "normal"),
                        text_color=("black", "white") if key_val_str else ("gray40", "gray60"),
                    )
                    val_lbl.pack(expand=True)

                    self._cell_widgets[(row, col)] = {
                        "box": cell_box,
                        "lbl": val_lbl,
                        "val": val,
                    }

    def _on_speed_change(self, value):
        self._speed_label.configure(text=f"{int(value)} ms")

    def _set_controls_state(self, state):
        disabled = state == "disabled"
        for w in (
            self._mode_seg,
            self._key_size_entry,
            self._size_entry,
            self._manual_entry,
            self._btn_structure,
            self._btn_generate,
            self._btn_clear,
            self._btn_save,
            self._btn_load,
            self._search_entry,
            self._btn_search,
            self._btn_delete,
            self._btn_reset_search,
            self._speed_slider,
        ):
            w.configure(state="disabled" if disabled else "normal")
        exp_state = "disabled" if (disabled or self._structure_created) else "normal"
        self._expansion_mode_seg.configure(state=exp_state)
        if not disabled:
            self._on_mode_change(self._mode_var.get())

    def _reset_search_visuals(self):
        for cell in self._cell_widgets.values():
            cell["box"].configure(
                border_color=cell["box"]._default_border, fg_color=cell["box"]._default_fg
            )

    def _get_target(self):
        raw = self._val_entry.get().strip()
        if not raw:
            self._show_error('Ingresa el valor objetivo en "Valores".')
            return None
        if "," in raw:
            raw = raw.split(",")[0].strip()
        try:
            val = int(raw)
            cfg = self._validate_configuration()
            if cfg is not None:
                key_size, _, min_key, max_key = cfg
                if not (min_key <= val <= max_key):
                    self._show_error(
                        f"El valor a buscar debe tener exactamente {key_size} dígitos (entre {min_key} y {max_key})."
                    )
                    return None
            return val
        except ValueError:
            self._show_error("El valor a buscar debe ser un número entero.")
            return None

    def _on_start_search(self):
        if self._is_animating:
            return
        if not self._structure_created or not self._get_all_inserted_keys():
            self._show_error("Primero genera la estructura y añade claves.")
            return
        target = self._get_target()
        if target is None:
            return
        self._pending_action = "search"
        self._begin_hash_animation(target)

    def _begin_hash_animation(self, target):
        self._reset_search_visuals()
        self._clear_error()
        self._set_controls_state("disabled")
        self._is_animating = True
        target_col = target % self._num_cols
        self._status_label.configure(
            text=f"Calculando hash: {target} % {self._num_cols} = cubeta {target_col}. Revisa la cubeta {target_col}..."
        )
        self._step_hash_search(target, target_col, 0, 1)

    def _step_hash_search(self, target, target_col, row_idx, step):
        if not self._is_animating:
            return
        height = self._cubeta_heights.get(target_col, _INITIAL_ROW_HEIGHT)
        if row_idx >= height:
            for cell in self._cell_widgets.values():
                cell["box"].configure(border_color="#C62828", fg_color=("#FEE2E2", "#450A0A"))
            action = "Eliminación" if self._pending_action == "delete" else "Búsqueda"
            self._status_label.configure(
                text=f"{action}: {target} no fue encontrado en la cubeta {target_col}."
            )
            if self._pending_action == "delete":
                self._show_error(f"La clave {target} no existe; no se eliminó nada.")
            self._is_animating = False
            self._pending_action = None
            self._set_controls_state("normal")
            return

        if row_idx > 0:
            prev_cell = self._cell_widgets.get((row_idx - 1, target_col))
            if prev_cell:
                prev_cell["box"].configure(
                    border_color=prev_cell["box"]._default_border, fg_color=prev_cell["box"]._default_fg
                )

        cell = self._cell_widgets.get((row_idx, target_col))
        if cell:
            cell["box"].configure(border_color="#1F6AA5", fg_color="#1F6AA5")
            val = cell["val"]

            if val == target:
                cell["box"].configure(border_color="#2FA572", fg_color="#2FA572")
                if self._pending_action == "delete":
                    self._cubetas[target_col].remove(target)
                    self._render_structure()
                    self._update_info_and_status(f"Clave {target} eliminada de la cubeta {target_col} (fila {row_idx}).")
                else:
                    self._update_info_and_status(f"Elemento {target} encontrado en cubeta {target_col}, fila {row_idx}. Paso {step}")
                self._is_animating = False
                self._pending_action = None
                self._set_controls_state("normal")
                return

            self._status_label.configure(
                text=f"Paso {step}: cubeta {target_col}, fila {row_idx} [valor: {val or 'vacío'}]. No es {target}."
            )

        self._anim_job = self.after(
            int(self._speed_slider.get()), lambda: self._step_hash_search(target, target_col, row_idx + 1, step + 1)
        )

    def _on_delete(self):
        if self._is_animating:
            return
        if not self._structure_created or not self._get_all_inserted_keys():
            self._show_error("No hay registros para eliminar.")
            return
        target = self._get_target()
        if target is None:
            return
        self._pending_action = "delete"
        self._begin_hash_animation(target)

    def _on_reset_search(self):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
        self._anim_job = None
        self._is_animating = False
        self._pending_action = None
        self._reset_search_visuals()
        self._clear_error()
        if hasattr(self, "_status_label"):
            self._status_label.configure(text="Estado: búsqueda reiniciada. Listo para buscar.")
        if hasattr(self, "_btn_search"):
            self._set_controls_state("normal")

    def _on_save(self):
        if not self._structure_created:
            self._show_error("Primero genera la estructura.")
            return
        payload = {
            "tipo": "ext_dinamicas",
            "key_size": self._key_size_entry.get().strip(),
            "size": self._max_records,
            "num_cols": self._num_cols,
            "cubetas": self._cubetas,
            "cubeta_heights": self._cubeta_heights,
            "mode": self._mode_var.get(),
            "expansion_mode": self._expansion_mode_var.get(),
            "data": self._get_all_inserted_keys(),
        }
        save_json(self, payload, "Guardar búsqueda dinámica externa")

    def _on_load(self):
        payload = load_json(self, "Cargar búsqueda dinámica externa")
        if payload is None:
            return
        if payload.get("tipo") != "ext_dinamicas":
            self._show_error("El archivo no corresponde a una búsqueda dinámica externa válida.")
            return
        try:
            data = payload.get("data", [])
            size = int(payload.get("size", len(data)))
            num_cols = int(payload.get("num_cols", _INITIAL_COLS))
            key_size = int(payload.get("key_size", _DEFAULT_KEY_SIZE))
            expansion_mode = payload.get("expansion_mode", "Total")

            self._max_records = size
            self._num_cols = num_cols
            self._cubetas = {int(k): list(v) for k, v in payload.get("cubetas", {}).items()}
            self._cubeta_heights = {int(k): int(v) for k, v in payload.get("cubeta_heights", {}).items()}
            self._expansion_mode_var.set(expansion_mode)
            self._structure_created = True
            self._expansion_mode_seg.configure(state="disabled")

            self._key_size_entry.delete(0, "end")
            self._key_size_entry.insert(0, str(key_size))
            self._size_entry.delete(0, "end")
            self._size_entry.insert(0, str(size))
            self._render_structure()
            self._update_info_and_status("Estructura dinámica de cubetas cargada correctamente.")
            self._clear_error()
        except (ValueError, TypeError) as exc:
            self._show_error(f"Archivo inválido: {exc}")

    def _show_placeholder(self):
        for w in self._scroll_frame.winfo_children():
            w.destroy()
        self._cell_widgets.clear()
        ctk.CTkLabel(
            self._scroll_frame,
            text="Configura tamaño de clave y cantidad de registros, luego presiona «Generar estructura» para inicializar las cubetas.",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray55"),
        ).pack(pady=60, padx=40)

    def _show_error(self, msg):
        self._error_box.pack(fill="x", padx=20, pady=(0, 4))
        self._error_label.configure(text=msg)

    def _clear_error(self):
        self._error_label.configure(text="")
        self._error_box.pack_forget()

    def destroy(self):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
        self._anim_job = None
        super().destroy()
