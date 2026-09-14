import random
import customtkinter as ctk
from views.base_view import BaseView
from views.persistence import save_json, load_json

_MAX_ELEMENTS = 1_000
_DEFAULT_KEY_SIZE = 3
_DEFAULT_SIZE = 10


class BusquedaBinariaExternaView(BaseView):
    """Vista de simulación de Búsqueda Binaria Externa representada en bloques de almacenamiento."""

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Búsqueda Binaria Externa",
            **kwargs,
        )
        self._data = []
        self._capacity = 0
        self._structure_created = False
        self._block_widgets = []
        self._mode_var = ctk.StringVar(value="Aleatorio")
        self._anim_job = None
        self._is_animating = False
        self._pending_action = None
        self._build_ui()

    def _build_ui(self):
        self.add_title("Búsqueda Binaria Externa")
        self.add_subtitle("Busca dividiendo el conjunto ordenado de bloques por mitades en cada paso.")

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
            placeholder_text="Ingrese valores o clave objetivo (ej: 12, 45, 78)",
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
        e = ctk.CTkEntry(
            parent, width=110, height=34, placeholder_text=default, font=ctk.CTkFont(size=14), justify="center"
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
            self._show_error("Tamaño de clave y cantidad de registros deben ser mayores que cero.")
            return None
        if size > _MAX_ELEMENTS:
            self._show_error(f"La cantidad máxima de registros es {_MAX_ELEMENTS:,}.")
            return None
        min_key = 1 if key_size == 1 else (10 ** (key_size - 1))
        max_key = (10 ** key_size) - 1
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

    def _on_generate_structure(self):
        if self._is_animating:
            return
        cfg = self._validate_configuration()
        if cfg is None:
            return
        _, size, _, _ = cfg
        if self._structure_created:
            self._show_error("La estructura ya fue generada. Presiona Limpiar para crear una nueva.")
            return
        self._capacity = size
        self._data = []
        self._structure_created = True
        self._render_structure()
        self._info_label.configure(text=f"0/{size} bloques")
        self._status_label.configure(
            text=f"Estructura generada con {size} bloques vacíos. Ahora puedes añadir datos."
        )
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

    def _on_add(self):
        if self._is_animating:
            return
        if not self._structure_created:
            self._show_error("Primero debes generar la estructura.")
            return
        if len(self._data) >= self._capacity:
            self._show_error("La estructura ya está llena.")
            return
        cfg = self._validate_configuration()
        if cfg is None:
            return
        key_size, _, min_key, max_key = cfg
        existing_keys = set(self._data)
        if self._mode_var.get() == "Aleatorio":
            remaining = self._capacity - len(self._data)
            new_values = self._generate_unique_random_keys(remaining, min_key, max_key, existing_keys)
            if new_values is None:
                self._show_error(f"No hay suficientes claves únicas disponibles en el rango de {key_size} dígitos.")
                return
        else:
            new_values = self._parse_manual_values(min_key, max_key, key_size)
            if new_values is None:
                return
            remaining = self._capacity - len(self._data)
            if len(new_values) > remaining:
                self._show_error(f"Solo quedan {remaining} bloques disponibles.")
                return
            seen = set()
            for val in new_values:
                if val in seen:
                    self._show_error(
                        f"La clave {val} está duplicada en la lista ingresada. No se permiten claves repetidas."
                    )
                    return
                seen.add(val)
                if val in existing_keys:
                    self._show_error(f"La clave {val} ya existe en la estructura. No se permiten claves repetidas.")
                    return
        self._data.extend(new_values)
        self._data.sort()
        self._val_entry.delete(0, "end")
        self._render_structure()
        self._info_label.configure(text=f"{len(self._data)}/{self._capacity} bloques ordenados")
        self._status_label.configure(
            text=f"Se añadieron {len(new_values)} bloque(s). La estructura se mantiene ordenada."
        )
        self._clear_error()

    def _on_clear(self):
        self._on_reset_search()
        self._data.clear()
        self._capacity = 0
        self._structure_created = False
        self._manual_entry.delete(0, "end")
        self._info_label.configure(text="")
        self._clear_error()
        self._show_placeholder()
        self._status_label.configure(text="Estado: estructura limpiada.")

    def _render_structure(self):
        """Renderiza los bloques según el boceto de la imagen en un contenedor horizontal."""
        for w in self._scroll_frame.winfo_children():
            w.destroy()
        self._block_widgets.clear()
        if not self._structure_created:
            return

        n_filled = len(self._data)
        total_cap = self._capacity

        blocks_to_render = []
        if n_filled == 0:
            if total_cap <= 5:
                for i in range(total_cap):
                    blocks_to_render.append((i, None, False))
            else:
                blocks_to_render.append((0, None, False))
                blocks_to_render.append((1, None, False))
                blocks_to_render.append(("...", None, False))
                blocks_to_render.append((total_cap - 1, None, False))
        else:
            for i in range(n_filled):
                blocks_to_render.append((i, self._data[i], True))
            remaining = total_cap - n_filled
            if remaining == 1:
                blocks_to_render.append((total_cap - 1, None, False))
            elif remaining > 1:
                blocks_to_render.append(("...", None, False))
                blocks_to_render.append((total_cap - 1, None, False))

        for idx_label, val, is_real in blocks_to_render:
            if idx_label == "...":
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
                text=str(idx_label),
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

            key_val_str = str(val) if val is not None else ""
            key_val_lbl = ctk.CTkLabel(
                inner_box,
                text=key_val_str,
                font=ctk.CTkFont(size=20, weight="bold" if key_val_str else "normal"),
            )
            key_val_lbl.pack(expand=True)

            if is_real and val is not None:
                self._block_widgets.append(
                    {
                        "outer": outer_box,
                        "inner": inner_box,
                        "key_lbl": key_val_lbl,
                        "data_idx": idx_label,
                        "val": val,
                    }
                )

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
        if not disabled:
            self._on_mode_change(self._mode_var.get())

    def _reset_search_visuals(self):
        for bw in self._block_widgets:
            bw["outer"].configure(border_color=bw["outer"]._default_border, fg_color=bw["outer"]._default_fg)
            bw["inner"].configure(fg_color=bw["inner"]._default_fg)

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
        if not self._structure_created or not self._data:
            self._show_error("Primero genera la estructura y añade registros.")
            return
        target = self._get_target()
        if target is None:
            return
        self._pending_action = "search"
        self._begin_binary_animation(target)

    def _begin_binary_animation(self, target):
        self._reset_search_visuals()
        self._clear_error()
        self._set_controls_state("disabled")
        self._is_animating = True
        self._status_label.configure(text=f"Buscando {target} mediante búsqueda binaria en los bloques externos...")
        self._step_binary(0, len(self._data) - 1, target, 1)

    def _step_binary(self, inicio, fin, target, step):
        if not self._is_animating:
            return
        if inicio > fin:
            for bw in self._block_widgets:
                bw["outer"].configure(border_color="#C62828", fg_color=("#FEE2E2", "#450A0A"))
            action = "Eliminación" if self._pending_action == "delete" else "Búsqueda"
            self._status_label.configure(
                text=f"{action}: {target} no fue encontrado en los bloques. Intervalo agotado en {step - 1} paso(s)."
            )
            if self._pending_action == "delete":
                self._show_error(f"El registro {target} no existe; no se eliminó nada.")
            self._is_animating = False
            self._pending_action = None
            self._set_controls_state("normal")
            return

        medio = (inicio + fin) // 2
        self._reset_search_visuals()

        # Desactivar/atenuar bloques fuera del rango activo [inicio, fin]
        for idx, bw in enumerate(self._block_widgets):
            if idx < inicio or idx > fin:
                bw["outer"].configure(border_color=("gray60", "gray40"), fg_color=("gray92", "gray16"))
                bw["inner"].configure(fg_color=("gray95", "gray18"))

        bw_medio = self._block_widgets[medio]
        bw_medio["outer"].configure(border_color="#FB923C", fg_color="#9A3412")
        bw_medio["inner"].configure(fg_color=("gray90", "gray28"))
        val = self._data[medio]
        display_idx = bw_medio["data_idx"]

        self._status_label.configure(
            text=f"Paso {step}: Bloque MEDIO=índice {display_idx}, clave={val}."
        )

        if val == target:
            bw_medio["outer"].configure(border_color="#2FA572", fg_color="#2FA572")
            bw_medio["inner"].configure(fg_color="#1E7145")
            if self._pending_action == "delete":
                del self._data[medio]
                self._render_structure()
                self._info_label.configure(text=f"{len(self._data)}/{self._capacity} bloques ordenados")
                self._status_label.configure(
                    text=f"Clave {target} encontrada en el bloque índice {display_idx} y eliminada correctamente."
                )
            else:
                self._status_label.configure(
                    text=f"Elemento {target} encontrado en el bloque con índice {display_idx}. Paso {step}"
                )
            self._is_animating = False
            self._pending_action = None
            self._set_controls_state("normal")
            return

        if target < val:
            self._status_label.configure(
                text=f"Paso {step}: Bloque MEDIO=índice {display_idx}, clave={val}. {target} < {val} → se descarta la mitad derecha."
            )
            nxt = (inicio, medio - 1)
        else:
            self._status_label.configure(
                text=f"Paso {step}: Bloque MEDIO=índice {display_idx}, clave={val}. {target} > {val} → se descarta la mitad izquierda."
            )
            nxt = (medio + 1, fin)

        self._anim_job = self.after(
            int(self._speed_slider.get()), lambda: self._step_binary(nxt[0], nxt[1], target, step + 1)
        )

    def _on_delete(self):
        if self._is_animating:
            return
        if not self._structure_created or not self._data:
            self._show_error("No hay registros para eliminar.")
            return
        target = self._get_target()
        if target is None:
            return
        self._pending_action = "delete"
        self._begin_binary_animation(target)

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
        save_json(
            self,
            {
                "tipo": "ext_binaria",
                "key_size": self._key_size_entry.get().strip(),
                "size": self._capacity,
                "mode": self._mode_var.get(),
                "data": self._data,
            },
            "Guardar búsqueda binaria externa",
        )

    def _on_load(self):
        payload = load_json(self, "Cargar búsqueda binaria externa")
        if payload is None:
            return
        if payload.get("tipo") not in ("ext_binaria", "binaria") or not isinstance(payload.get("data"), list):
            self._show_error("El archivo no corresponde a una búsqueda binaria externa válida.")
            return
        try:
            data = sorted(int(x) for x in payload["data"])
            capacity = int(payload.get("size", len(data)))
            key_size = int(payload.get("key_size", _DEFAULT_KEY_SIZE))
            max_key = (10**key_size) - 1
            if capacity <= 0 or capacity > _MAX_ELEMENTS or len(data) > capacity or any(x < 1 or x > max_key for x in data):
                raise ValueError("Datos incompatibles con la configuración.")
            self._capacity = capacity
            self._structure_created = True
            self._data = data
            self._key_size_entry.delete(0, "end")
            self._key_size_entry.insert(0, str(key_size))
            self._size_entry.delete(0, "end")
            self._size_entry.insert(0, str(capacity))
            self._render_structure()
            self._info_label.configure(text=f"{len(data)}/{capacity} bloques ordenados")
            self._status_label.configure(text="Estructura de bloques cargada correctamente.")
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
