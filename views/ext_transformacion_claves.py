import random
import customtkinter as ctk
from views.base_view import BaseView
from views.persistence import save_json, load_json

_MAX_SIZE = 1000
_DEFAULT_KEY_SIZE = 3
_DEFAULT_SIZE = 10
_COLLISION_METHODS = ["Lineal", "Cuadrática", "Doble función hash", "Anidado", "Encadenado"]


class BusquedaTransformacionClavesExternaView(BaseView):
    """Vista de simulación de Transformación de Claves Externa representada en bloques de almacenamiento."""

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Transformación de Claves Externa",
            **kwargs,
        )
        self._data = []
        self._table = []
        self._collision_method = None
        self._pending_key = None
        self._table_created = False
        self._anim_job = None
        self._is_animating = False
        self._pending_action = None
        self._block_widgets = {}
        self._mode_var = ctk.StringVar(value="Aleatorio")
        self._build_ui()

    def _build_ui(self):
        self.add_title("Transformación de Claves Externa")
        self.add_subtitle("Construcción de una tabla hash externa en bloques con solución de colisiones.")

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

        # Row 1: Modo de Carga [Aleatorio | Manual]
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
        self._mode_seg.pack(side="left")

        # Row 2: Cantidad de registros [ ] Tamaño de clave [ ] Solución de colisiones [ ] [Generar Estructura] [Limpiar]
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

        ctk.CTkLabel(row2, text="Solución de colisiones:", font=ctk.CTkFont(size=13, weight="bold")).pack(
            side="left", padx=(8, 4)
        )
        self._collision_menu = ctk.CTkOptionMenu(
            row2, values=_COLLISION_METHODS, width=170, height=34, command=self._on_collision_selected
        )
        self._collision_menu.pack(side="left")
        self._collision_menu.set("Seleccione una opción")
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
            placeholder_text="Ingrese valores o clave objetivo (ej: 25, 35, 45, 15)",
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
            command=self._on_generate,
        )
        self._btn_generate.pack(side="left", padx=(0, 8))
        self._btn_search = ctk.CTkButton(
            row4,
            text="Buscar",
            width=90,
            height=34,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_search,
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
            text="Estado: listo para búsqueda por transformación de claves.",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("gray20", "gray80"),
            anchor="w",
            padx=12,
            pady=10,
        )
        self._status_label.pack(fill="x")
        self._collision_status = self._status_label

        self._error_box = ctk.CTkFrame(
            self.content,
            corner_radius=8,
            fg_color=("#FEE2E2", "#450A0A"),
            border_width=1,
            border_color=("#FCA5A5", "#7F1D1D"),
        )
        self._error_box.pack(fill="x", padx=20, pady=(0, 4))
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

        # Canvas/Scroll container for the Block Diagram
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
        self._show_placeholder()
        self._on_mode_change(self._mode_var.get())

    def _entry_with_label(self, parent, text, default):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(0, 8))
        e = ctk.CTkEntry(parent, width=80, height=34, font=ctk.CTkFont(size=14), justify="center")
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
            ks = int(self._key_size_entry.get().strip())
            size = int(self._size_entry.get().strip())
        except ValueError:
            self._show_error("Tamaño de clave y cantidad de registros deben ser números enteros.")
            return None
        if ks <= 0 or size <= 0:
            self._show_error("Tamaño de clave y cantidad de registros deben ser mayores que cero.")
            return None
        if size > _MAX_SIZE:
            self._show_error(f"El tamaño máximo de la tabla es {_MAX_SIZE}.")
            return None
        min_key = 1 if ks == 1 else (10 ** (ks - 1))
        max_key = (10**ks) - 1
        return ks, size, min_key, max_key

    def _parse_manual_values(self, min_key, max_key, key_size):
        text = self._manual_entry.get().strip()
        if not text:
            self._show_error("Ingresa al menos un valor.")
            return None
        vals = []
        for p in [x.strip() for x in text.split(",") if x.strip()]:
            try:
                v = int(p)
            except ValueError:
                self._show_error(f"«{p}» no es un número válido.")
                return None
            if not (min_key <= v <= max_key):
                self._show_error(
                    f"El valor {v} debe tener exactamente {key_size} dígitos (entre {min_key} y {max_key})."
                )
                return None
            vals.append(v)
        return vals

    def _hash(self, key):
        return key % len(self._table)

    def _second_hash(self, key):
        size = len(self._table)
        return 1 if size <= 1 else 1 + (key % (size - 1))

    def _probe_indices(self, key):
        size = len(self._table)
        if size == 0:
            return
        initial = self._hash(key)
        yield initial
        method = self._collision_method
        if method == "Lineal":
            for i in range(1, size):
                yield (initial + i) % size
        elif method == "Cuadrática":
            for i in range(1, size):
                yield (initial + i * i) % size
        elif method == "Doble función hash":
            step = self._second_hash(key)
            for i in range(1, size):
                yield (initial + i * step) % size
        elif method == "Anidado":
            nested = ((key // size) + key) % size
            if nested != initial:
                yield nested
            for i in range(1, size):
                idx = (nested + i) % size
                if idx != initial:
                    yield idx

    def _insert_key(self, key):
        if not self._table:
            return False, None, False
        initial = self._hash(key)
        if self._collision_method == "Encadenado":
            if self._table[initial] is None:
                self._table[initial] = []
            collision = bool(self._table[initial])
            self._table[initial].append(key)
            return True, initial, collision
        if self._table[initial] is None:
            self._table[initial] = key
            return True, initial, False
        if self._collision_method is None:
            return False, initial, True
        for idx in list(self._probe_indices(key))[1:]:
            if self._table[idx] is None:
                self._table[idx] = key
                return True, idx, True
        return False, None, True

    def _insert_keys(self, keys):
        for key in keys:
            inserted, index, collision = self._insert_key(key)
            if not inserted:
                self._pending_key = key
                self._collision_status.configure(text=f"Colisión en la clave {key}. Selecciona una estrategia.")
                self._show_error(
                    f"Se produjo una colisión al insertar la clave {key}. Debes seleccionar una solución de colisiones para continuar."
                )
                self._render_table()
                return
            self._data.append(key)
        self._manual_entry.delete(0, "end")
        self._clear_error()
        self._update_info()
        self._render_table()

    def _on_generate_structure(self):
        cfg = self._validate_configuration()
        if cfg is None:
            return
        _, size, _, _ = cfg
        if self._table_created:
            self._show_error("La estructura ya fue generada. Presiona Limpiar para crear una nueva.")
            return
        self._table = [None for _ in range(size)]
        self._data = []
        self._table_created = True
        self._collision_method = None
        self._pending_key = None
        self._collision_menu.set("Seleccione una opción")
        self._collision_status.configure(text="La estrategia se solicitará solo si aparece una colisión.")
        self._update_info()
        self._render_table()
        self._clear_error()
        self._status_label.configure(
            text=f"Estructura generada con {size} bloques hash vacíos. Ahora puedes añadir claves."
        )

    def _get_existing_keys(self):
        existing = set()
        for slot in self._table:
            if slot is None:
                continue
            if isinstance(slot, list):
                existing.update(slot)
            else:
                existing.add(slot)
        if self._pending_key is not None:
            existing.add(self._pending_key)
        return existing

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

    def _on_generate(self):
        if not self._table_created:
            self._show_error("Primero debes generar la estructura.")
            return
        cfg = self._validate_configuration()
        if cfg is None:
            return
        ks, size, min_key, max_key = cfg
        if len(self._table) != size:
            self._show_error(
                f"La tabla ya fue creada con tamaño {len(self._table)}. Presiona Limpiar para crear una nueva tabla."
            )
            return
        if self._pending_key is not None:
            self._show_error("Debes seleccionar una solución de colisiones antes de continuar.")
            return
        remaining = size - self._count_elements()
        if remaining <= 0:
            self._show_error("La tabla ya está llena. Presiona Limpiar para comenzar una nueva tabla.")
            return
        existing_keys = self._get_existing_keys()
        if self._mode_var.get() == "Aleatorio":
            new_keys = self._generate_unique_random_keys(remaining, min_key, max_key, existing_keys)
            if new_keys is None:
                self._show_error(f"No hay suficientes claves únicas disponibles en el rango de {ks} dígitos.")
                return
        else:
            new_keys = self._parse_manual_values(min_key, max_key, ks)
            if new_keys is None:
                return
            if len(new_keys) > remaining:
                self._show_error(f"Solo quedan {remaining} bloques disponibles en la tabla hash.")
                return
            seen = set()
            for val in new_keys:
                if val in seen:
                    self._show_error(
                        f"La clave {val} está duplicada en la lista ingresada. No se permiten claves repetidas."
                    )
                    return
                seen.add(val)
                if val in existing_keys:
                    self._show_error(f"La clave {val} ya existe en la tabla. No se permiten claves repetidas.")
                    return
        self._insert_keys(new_keys)

    def _on_collision_selected(self, method):
        if self._collision_method is not None:
            self._collision_menu.set(self._collision_method)
            self._show_error(
                f"La solución de colisiones ya está definida como «{self._collision_method}». Solo puede cambiarse después de presionar Limpiar."
            )
            return
        self._collision_method = method
        if method == "Encadenado":
            self._table = [
                ([] if slot is None else ([slot] if isinstance(slot, int) else slot)) for slot in self._table
            ]
        self._collision_status.configure(text=f"Estrategia seleccionada: {method}")
        self._clear_error()
        if self._pending_key is None:
            return
        key = self._pending_key
        self._pending_key = None
        inserted, index, collision = self._insert_key(key)
        if not inserted:
            self._pending_key = key
            self._show_error(f"No fue posible insertar la clave {key} utilizando {method}. La tabla puede estar llena.")
            return
        self._data.append(key)
        self._manual_entry.delete(0, "end")
        self._update_info()
        self._render_table()

    def _count_elements(self):
        if self._collision_method == "Encadenado":
            return sum(len(bucket) for bucket in self._table if isinstance(bucket, list))
        return sum(1 for value in self._table if value is not None)

    def _update_info(self):
        self._info_label.configure(
            text=f"{self._count_elements()}/{len(self._table)} elementos | Método: {self._collision_method or 'todavía no requerido'}"
        )

    def _render_table(self, active_probe=None):
        """Renderiza los bloques hash siguiendo el boceto en un contenedor horizontal."""
        for w in self._scroll_frame.winfo_children():
            w.destroy()
        self._block_widgets.clear()
        if not self._table:
            return

        total_size = len(self._table)

        req_indices = set()
        req_indices.add(0)
        req_indices.add(total_size - 1)

        for i, slot in enumerate(self._table):
            occupied = slot is not None and (slot != [] if isinstance(slot, list) else True)
            if occupied:
                req_indices.add(i)

        if active_probe is not None and 0 <= active_probe < total_size:
            req_indices.add(active_probe)

        sorted_indices = sorted(req_indices)

        blocks_to_render = []
        for i, slot_idx in enumerate(sorted_indices):
            if i > 0:
                prev_idx = sorted_indices[i - 1]
                diff = slot_idx - prev_idx
                if diff == 2:
                    blocks_to_render.append((prev_idx + 1, self._table[prev_idx + 1]))
                elif diff > 2:
                    blocks_to_render.append(("...", None))

            blocks_to_render.append((slot_idx, self._table[slot_idx]))

        for slot_idx, slot_val in blocks_to_render:
            if slot_idx == "...":
                dots_frame = ctk.CTkFrame(self._scroll_frame, fg_color="transparent")
                dots_frame.pack(side="left", padx=15, pady=60)
                ctk.CTkLabel(
                    dots_frame,
                    text=". . .",
                    font=ctk.CTkFont(size=28, weight="bold"),
                    text_color=("gray40", "gray60"),
                ).pack()
                continue

            # --- Caja Exterior (Representa el Bloque) ---
            outer_box = ctk.CTkFrame(
                self._scroll_frame,
                width=140,
                height=160,
                corner_radius=12,
                border_width=2,
                border_color=("gray75", "gray35"),
                fg_color=("gray90", "gray22"),
            )
            outer_box.pack_propagate(False)
            outer_box.pack(side="left", padx=10, pady=15)
            outer_box._default_border = ("gray75", "gray35")
            outer_box._default_fg = ("gray90", "gray22")

            # Índice únicamente en la esquina superior izquierda
            idx_num_lbl = ctk.CTkLabel(
                outer_box,
                text=str(slot_idx),
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=("gray30", "gray70"),
            )
            idx_num_lbl.place(x=12, y=8)

            # --- Caja Interior (Representa la Clave) ---
            inner_box = ctk.CTkFrame(
                outer_box,
                width=100,
                height=80,
                corner_radius=8,
                border_width=1,
                border_color=("gray70", "gray45"),
                fg_color=("white", "gray16"),
            )
            inner_box.place(relx=0.5, rely=0.56, anchor="center")
            inner_box.pack_propagate(False)
            inner_box._default_fg = ("white", "gray16")

            occupied = slot_val is not None and (slot_val != [] if isinstance(slot_val, list) else True)
            if self._collision_method == "Encadenado":
                bucket = slot_val if isinstance(slot_val, list) else []
                key_text = ", ".join(map(str, bucket)) if bucket else ""
            elif occupied:
                key_text = str(slot_val)
            else:
                key_text = ""

            key_val_lbl = ctk.CTkLabel(
                inner_box,
                text=key_text,
                font=ctk.CTkFont(size=16 if len(key_text) > 4 else 20, weight="bold" if occupied else "normal"),
            )
            key_val_lbl.pack(expand=True)

            self._block_widgets[slot_idx] = {
                "outer": outer_box,
                "inner": inner_box,
                "key_lbl": key_val_lbl,
                "slot_val": slot_val,
            }

        if self._pending_key is not None:
            ctk.CTkLabel(
                self._scroll_frame,
                text=f"La clave {self._pending_key} espera solución de colisión.",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=("#cc7700", "#ffaa33"),
            ).pack(side="left", padx=10)

    def _on_search(self):
        if self._is_animating:
            return
        if not self._table_created or not self._table:
            self._show_error("Primero añade o carga una tabla hash.")
            return
        target = self._get_target()
        if target is None:
            return
        self._pending_action = "search"
        self._start_hash_animation(target)

    def _on_delete(self):
        if self._is_animating:
            return
        if not self._table_created or not self._table:
            self._show_error("No hay una tabla hash para eliminar.")
            return
        target = self._get_target()
        if target is None:
            return
        self._pending_action = "delete"
        self._start_hash_animation(target)

    def _get_target(self):
        raw = self._val_entry.get().strip()
        if not raw:
            self._show_error('Ingresa la clave objetivo en "Valores".')
            return None
        if "," in raw:
            raw = raw.split(",")[0].strip()
        try:
            val = int(raw)
            cfg = self._validate_configuration()
            if cfg is not None:
                ks, _, min_key, max_key = cfg
                if not (min_key <= val <= max_key):
                    self._show_error(f"La clave debe tener exactamente {ks} dígitos (entre {min_key} y {max_key}).")
                    return None
            return val
        except ValueError:
            self._show_error("La clave debe ser un número entero.")
            return None

    def _start_hash_animation(self, target):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
        self._anim_job = None
        self._is_animating = False
        self._reset_search_visuals()
        self._clear_error()
        self._set_hash_controls_state("disabled")
        self._is_animating = True
        self._status_label.configure(text=f"Calculando hash de {target}...")
        self._anim_job = self.after(
            150, lambda: self._step_hash_animation(target, 0, list(self._probe_indices(target)))
        )

    def _on_speed_change(self, value):
        val = int(value)
        self._speed_label.configure(text=f"{val} ms")

    def _set_hash_controls_state(self, state):
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
            self._collision_menu,
            self._speed_slider,
        ):
            try:
                w.configure(state="disabled" if disabled else "normal")
            except Exception:
                pass
        if not disabled:
            self._on_mode_change(self._mode_var.get())

    def _cancel_animation(self):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
        self._anim_job = None
        self._is_animating = False
        self._pending_action = None

    def _set_probe_block(self, index, border_color, fg_color, inner_fg):
        if index not in self._block_widgets:
            self._render_table(active_probe=index)
        bw = self._block_widgets.get(index)
        if bw is not None:
            bw["outer"].configure(border_color=border_color, fg_color=fg_color)
            bw["inner"].configure(fg_color=inner_fg)

    def _step_hash_animation(self, target, step, probes):
        if not self._is_animating:
            return
        if step >= len(probes):
            for bw in self._block_widgets.values():
                bw["outer"].configure(border_color="#C62828", fg_color=("#FEE2E2", "#450A0A"))
            action = "Eliminación" if self._pending_action == "delete" else "Búsqueda"
            self._status_label.configure(text=f"{action}: {target} no fue encontrada en la tabla hash de bloques.")
            if self._pending_action == "delete":
                self._show_error(f"La clave {target} no fue encontrada; no se eliminó nada.")
            self._is_animating = False
            self._pending_action = None
            self._set_hash_controls_state("normal")
            return

        idx = probes[step]
        self._reset_search_visuals()
        self._set_probe_block(idx, "#FB923C", "#9A3412", ("gray90", "gray28"))
        initial = self._hash(target)
        slot = self._table[idx]

        if self._collision_method == "Encadenado":
            bucket = slot or []
            if target in bucket:
                self._set_probe_block(idx, "#2FA572", "#2FA572", "#1E7145")
                if self._pending_action == "delete":
                    self._status_label.configure(
                        text=f"{target} encontrada en el bloque con índice {idx} dentro de la cadena. Eliminando... | Hash inicial={initial}"
                    )
                    self._is_animating = True
                    self._anim_job = self.after(
                        int(self._speed_slider.get()),
                        lambda target=target, idx=idx: self._delete_found_hash_key(target, idx, True),
                    )
                    return
                else:
                    self._status_label.configure(
                        text=f"{target} encontrada en el bloque con índice {idx} dentro de la cadena. | Paso {step + 1}"
                    )
                self._is_animating = False
                self._pending_action = None
                self._set_hash_controls_state("normal")
                return
            self._status_label.configure(
                text=f"Paso {step + 1}: hash({target})={initial} → revisando bloque índice {idx}. La clave no está aquí."
            )
        else:
            if slot == target:
                self._set_probe_block(idx, "#2FA572", "#2FA572", "#1E7145")
                if self._pending_action == "delete":
                    self._status_label.configure(
                        text=f"{target} encontrada en el bloque índice {idx}. Eliminando... | Hash inicial={initial}"
                    )
                    self._is_animating = True
                    self._anim_job = self.after(
                        int(self._speed_slider.get()),
                        lambda target=target, idx=idx: self._delete_found_hash_key(target, idx, False),
                    )
                    return
                else:
                    self._status_label.configure(
                        text=f"{target} encontrada en el bloque índice {idx}. | Hash inicial={initial} | Paso {step + 1}"
                    )
                self._is_animating = False
                self._pending_action = None
                self._set_hash_controls_state("normal")
                return
            if slot is None:
                self._set_probe_block(idx, "#C62828", ("#FEE2E2", "#450A0A"), ("#FEE2E2", "#450A0A"))
                self._status_label.configure(
                    text=f"Paso {step + 1}: bloque índice {idx} está vacío → {target} no está en la tabla hash."
                )
                was_delete = self._pending_action == "delete"
                self._is_animating = False
                self._pending_action = None
                if was_delete:
                    self._show_error(f"La clave {target} no fue encontrada; no se eliminó nada.")
                self._set_hash_controls_state("normal")
                return
            self._status_label.configure(
                text=f"Paso {step + 1}: bloque índice {idx} contiene {slot} ≠ {target}. Método {self._collision_method or 'sin colisión'}, continuando."
            )

        self._anim_job = self.after(
            int(self._speed_slider.get()), lambda: self._step_hash_animation(target, step + 1, probes)
        )

    def _reset_search_visuals(self):
        for bw in self._block_widgets.values():
            bw["outer"].configure(border_color=bw["outer"]._default_border, fg_color=bw["outer"]._default_fg)
            bw["inner"].configure(fg_color=bw["inner"]._default_fg)

    def _delete_found_hash_key(self, target, index, is_chain):
        """Elimina directamente la clave que ya fue localizada por la búsqueda."""
        self._anim_job = None
        try:
            if is_chain:
                if not (0 <= index < len(self._table)):
                    raise ValueError("Índice fuera de rango.")
                bucket = self._table[index]
                if not isinstance(bucket, list) or target not in bucket:
                    raise ValueError("La clave ya no se encuentra en la cadena.")
                bucket.remove(target)
                if not bucket:
                    self._table[index] = None
            else:
                if not (0 <= index < len(self._table)) or self._table[index] != target:
                    raise ValueError("La clave ya no se encuentra en la posición localizada.")

                remaining = list(self._data)
                if target not in remaining:
                    raise ValueError("La clave no se encuentra en los registros.")
                remaining.remove(target)

                table_size = len(self._table)
                self._table = [None] * table_size
                for value in remaining:
                    inserted, _, _ = self._insert_key(value)
                    if not inserted:
                        raise ValueError("No fue posible reconstruir la tabla después de eliminar.")

            if target in self._data:
                self._data.remove(target)

            self._update_info()
            self._render_table()
            self._reset_search_visuals()
            self._status_label.configure(
                text=f"Clave {target} eliminada correctamente. La tabla de bloques fue actualizada."
            )
            self._clear_error()
        except (ValueError, TypeError) as exc:
            self._show_error(f"No fue posible eliminar la clave {target}: {exc}")
        finally:
            self._is_animating = False
            self._pending_action = None
            self._set_hash_controls_state("normal")

    def _on_reset_search(self):
        self._cancel_animation()
        self._reset_search_visuals()
        self._status_label.configure(text="Estado: Búsqueda reiniciada. Listo para buscar.")
        self._clear_error()
        self._set_hash_controls_state("normal")

    def _on_clear(self):
        self._data.clear()
        self._table.clear()
        self._collision_method = None
        self._pending_key = None
        self._table_created = False
        self._collision_menu.set("Seleccione una opción")
        self._collision_status.configure(text="No se necesita una estrategia todavía.")
        self._info_label.configure(text="")
        self._manual_entry.delete(0, "end")
        self._clear_error()
        self._show_placeholder()
        self._status_label.configure(text="Estado: Tabla de bloques limpiada.")

    def _on_save(self):
        if not self._table_created:
            self._show_error("No hay una tabla para guardar.")
            return
        payload = {
            "tipo": "ext_transformacion_claves",
            "key_size": self._key_size_entry.get().strip(),
            "size": len(self._table),
            "mode": self._mode_var.get(),
            "data": self._data,
            "table": self._table,
            "collision_method": self._collision_method,
        }
        save_json(self, payload, "Guardar tabla hash externa")

    def _on_load(self):
        payload = load_json(self, "Cargar tabla hash externa")
        if payload is None:
            return
        if payload.get("tipo") not in ("ext_transformacion_claves", "transformacion_claves") or not isinstance(
            payload.get("table"), list
        ):
            self._show_error("El archivo no corresponde a una tabla de transformación de claves externa válida.")
            return
        try:
            table = payload["table"]
            data = [int(x) for x in payload.get("data", [])]
            method = payload.get("collision_method")
            if len(table) > _MAX_SIZE:
                raise ValueError("El tamaño de la tabla supera el máximo permitido.")
            if method not in [None] + _COLLISION_METHODS:
                raise ValueError("Método de colisión no válido.")
            if method == "Encadenado":
                table = [([] if x is None else ([x] if isinstance(x, int) else [int(v) for v in x])) for x in table]
            else:
                table = [None if x is None else int(x) for x in table]
            self._key_size_entry.delete(0, "end")
            self._key_size_entry.insert(0, str(payload.get("key_size", "3")))
            self._size_entry.delete(0, "end")
            self._size_entry.insert(0, str(len(table)))
            self._table = table
            self._data = data
            self._collision_method = method
            self._pending_key = None
            self._table_created = bool(table)
            self._collision_menu.set(method if method else "Seleccione una opción")
            self._collision_status.configure(
                text=f"Estrategia seleccionada: {method}" if method else "No se necesita una estrategia todavía."
            )
            self._update_info()
            self._render_table()
            self._status_label.configure(text="Tabla de bloques cargada correctamente.")
            self._clear_error()
        except (ValueError, TypeError) as exc:
            self._show_error(f"Archivo inválido: {exc}")

    def _show_placeholder(self):
        for w in self._scroll_frame.winfo_children():
            w.destroy()
        self._block_widgets.clear()
        ctk.CTkLabel(
            self._scroll_frame,
            text="Configura tamaño de clave y cantidad de registros, luego presiona «Generar estructura».",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray55"),
        ).pack(pady=60, padx=40)

    def _show_error(self, msg):
        self._error_box.pack(fill="x", padx=20, pady=(0, 4))
        self._error_label.configure(text=f"{msg}")

    def _clear_error(self):
        self._error_label.configure(text="")
        self._error_box.pack_forget()

    def destroy(self):
        self._cancel_animation()
        super().destroy()
