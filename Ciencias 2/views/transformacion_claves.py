import random
import customtkinter as ctk

from views.base_view import BaseView


_MAX_SIZE = 1000

_COLLISION_METHODS = [
    "Lineal",
    "Cuadrática",
    "Doble función hash",
    "Anidado",
    "Encadenado",
]


class TransformacionClavesView(BaseView):

    def __init__(self, master, *, view_manager, **kwargs):

        super().__init__(
            master,
            view_manager=view_manager,
            title="Transformación de Claves",
            **kwargs,
        )

        # =========================================================
        # DATOS DE LA TABLA
        # =========================================================

        # Todas las claves que ya fueron agregadas.
        self._data: list[int] = []

        # Tabla hash.
        # Para direccionamiento abierto contiene int | None.
        # Para encadenamiento contiene listas.
        self._table = []

        # Método de colisión seleccionado para ESTA tabla.
        # None = todavía no se ha necesitado.
        self._collision_method = None

        # Clave que provocó una colisión y está esperando
        # que el usuario seleccione una estrategia.
        self._pending_key = None

        # Indica si ya existe una tabla.
        self._table_created = False

        self._mode_var = ctk.StringVar(
            value="Aleatorio"
        )

        self._build_ui()

    # =========================================================
    # INTERFAZ
    # =========================================================

    def _build_ui(self):

        self.add_title(
            "Transformación de Claves"
        )

        self.add_subtitle(
            "Construcción de una tabla hash mediante "
            "transformación de claves y resolución de colisiones."
        )

        # =========================================================
        # CONFIGURACIÓN
        # =========================================================

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

        # =========================================================
        # MODO
        # =========================================================

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
            values=[
                "Aleatorio",
                "Manual"
            ],
            variable=self._mode_var,
            command=self._on_mode_change,
            font=ctk.CTkFont(size=13),
        )

        self._mode_seg.pack(
            side="left"
        )

        # =========================================================
        # RANGO / TAMAÑO DE CLAVE / TAMAÑO TABLA
        # =========================================================

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
            justify="center",
            font=ctk.CTkFont(size=14),
        )

        self._range_entry.pack(
            side="left",
            padx=(0, 16)
        )

        self._range_entry.insert(
            0,
            "100"
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
            justify="center",
            font=ctk.CTkFont(size=14),
        )

        self._key_size_entry.pack(
            side="left",
            padx=(0, 16)
        )

        self._key_size_entry.insert(
            0,
            "2"
        )

        # Tamaño de tabla
        ctk.CTkLabel(
            row2,
            text="Tamaño (N):",
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
            justify="center",
            font=ctk.CTkFont(size=14),
        )

        self._size_entry.pack(
            side="left",
            padx=(0, 16)
        )

        self._size_entry.insert(
            0,
            "10"
        )

        # Generar / Agregar
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
            padx=(0, 12)
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

        # =========================================================
        # ENTRADA MANUAL
        # =========================================================

        row3 = ctk.CTkFrame(
            inner,
            fg_color="transparent"
        )

        row3.pack(
            fill="x",
            pady=(0, 10)
        )

        ctk.CTkLabel(
            row3,
            text="Valores:",
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
            placeholder_text="Ej: 25, 35, 45, 15",
            font=ctk.CTkFont(size=14),
        )

        self._manual_entry.pack(
            side="left",
            fill="x",
            expand=True
        )

        # =========================================================
        # COLISIONES
        # =========================================================

        row4 = ctk.CTkFrame(
            inner,
            fg_color="transparent"
        )

        row4.pack(
            fill="x"
        )

        ctk.CTkLabel(
            row4,
            text="Solución de colisiones:",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            ),
        ).pack(
            side="left",
            padx=(0, 12)
        )

        self._collision_menu = ctk.CTkOptionMenu(
            row4,
            values=_COLLISION_METHODS,
            width=190,
            height=34,
            command=self._on_collision_selected,
        )

        self._collision_menu.pack(
            side="left"
        )

        self._collision_menu.set(
            "Seleccione una opción"
        )

        self._collision_status = ctk.CTkLabel(
            row4,
            text="No se necesita una estrategia todavía.",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray55"),
        )

        self._collision_status.pack(
            side="left",
            padx=(15, 0)
        )

        # =========================================================
        # ERROR
        # =========================================================

        self._error_label = ctk.CTkLabel(
            self.content,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=(
                "#cc0000",
                "#ff4444"
            ),
        )

        self._error_label.pack(
            fill="x",
            padx=20,
            pady=(0, 4)
        )

        # =========================================================
        # TABLA
        # =========================================================

        self._scroll_frame = ctk.CTkScrollableFrame(
            self.content,
            corner_radius=12,
            fg_color=("gray96", "gray14"),
            border_width=2,
            border_color=("gray78", "gray30"),
            label_text="Tabla Hash generada",
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

        self._show_placeholder()

        self._on_mode_change(
            self._mode_var.get()
        )

    # =========================================================
    # CAMBIO DE MODO
    # =========================================================

    def _on_mode_change(self, selected_mode):

        if selected_mode == "Aleatorio":

            self._manual_entry.configure(
                state="disabled",
                fg_color=(
                    "gray85",
                    "gray25"
                )
            )

        else:

            self._manual_entry.configure(
                state="normal",
                fg_color=(
                    "white",
                    "gray20"
                )
            )

        self._clear_error()

    # =========================================================
    # VALIDAR CONFIGURACIÓN
    # =========================================================

    def _validate_configuration(self):

        raw_range = self._range_entry.get().strip()

        raw_key_size = self._key_size_entry.get().strip()

        raw_size = self._size_entry.get().strip()

        if not raw_range:
            self._show_error(
                "Ingresa el rango."
            )
            return None

        if not raw_key_size:
            self._show_error(
                "Ingresa el tamaño de la clave."
            )
            return None

        if not raw_size:
            self._show_error(
                "Ingresa el tamaño de la tabla."
            )
            return None

        try:
            value_range = int(raw_range)
            key_size = int(raw_key_size)
            size = int(raw_size)

        except ValueError:

            self._show_error(
                "Rango, tamaño de clave y tamaño de tabla "
                "deben ser números enteros."
            )

            return None

        if value_range <= 0:

            self._show_error(
                "El rango debe ser mayor que cero."
            )

            return None

        if key_size <= 0:

            self._show_error(
                "El tamaño de clave debe ser mayor que cero."
            )

            return None

        if size <= 0:

            self._show_error(
                "El tamaño de la tabla debe ser mayor que cero."
            )

            return None

        if size > _MAX_SIZE:

            self._show_error(
                f"El tamaño máximo de la tabla es {_MAX_SIZE}."
            )

            return None

        # El rango no puede necesitar más dígitos
        # que el tamaño de clave permitido.
        max_key = (10 ** key_size) - 1

        if value_range > max_key:

            self._show_error(
                f"El rango no puede superar {max_key} "
                f"porque la clave tiene {key_size} dígitos."
            )

            return None

        return value_range, key_size, size

    # =========================================================
    # VALIDAR VALORES MANUALES
    # =========================================================

    def _parse_manual_values(
        self,
        value_range,
        key_size
    ):

        text = self._manual_entry.get().strip()

        if not text:

            self._show_error(
                "Ingresa al menos un valor."
            )

            return None

        parts = [
            x.strip()
            for x in text.split(",")
            if x.strip()
        ]

        values = []

        for part in parts:

            try:
                value = int(part)

            except ValueError:

                self._show_error(
                    f"«{part}» no es un número válido."
                )

                return None

            if value < 1 or value > value_range:

                self._show_error(
                    f"El valor {value} está fuera del rango "
                    f"1 - {value_range}."
                )

                return None

            if len(str(value)) > key_size:

                self._show_error(
                    f"El valor {value} supera el tamaño "
                    f"de clave de {key_size} dígitos."
                )

                return None

            values.append(value)

        return values

    # =========================================================
    # HASH
    # =========================================================

    def _hash(self, key):

        return key % len(self._table)

    # =========================================================
    # SEGUNDA FUNCIÓN HASH
    # =========================================================

    def _second_hash(self, key):

        size = len(self._table)

        if size <= 1:
            return 1

        return 1 + (
            key % (size - 1)
        )

    # =========================================================
    # INSERTAR UNA CLAVE
    # =========================================================

    def _insert_key(self, key):

        size = len(self._table)

        if size == 0:

            return False, None, False

        initial_index = self._hash(key)

        # =====================================================
        # ENCADENADO
        # =====================================================

        if self._collision_method == "Encadenado":

            if self._table[initial_index]:

                self._table[
                    initial_index
                ].append(key)

                return (
                    True,
                    initial_index,
                    True
                )

            self._table[
                initial_index
            ].append(key)

            return (
                True,
                initial_index,
                False
            )

        # =====================================================
        # SIN COLISIÓN
        # =====================================================

        if self._table[initial_index] is None:

            self._table[
                initial_index
            ] = key

            return (
                True,
                initial_index,
                False
            )

        # Aquí sí hubo una colisión.
        collision = True

        # =====================================================
        # SI NO HAY MÉTODO TODAVÍA
        # =====================================================

        if self._collision_method is None:

            return (
                False,
                initial_index,
                collision
            )

        # =====================================================
        # LINEAL
        # =====================================================

        if self._collision_method == "Lineal":

            for i in range(1, size):

                index = (
                    initial_index + i
                ) % size

                if self._table[index] is None:

                    self._table[index] = key

                    return (
                        True,
                        index,
                        True
                    )

            return False, None, True

        # =====================================================
        # CUADRÁTICA
        # =====================================================

        if self._collision_method == "Cuadrática":

            for i in range(1, size):

                index = (
                    initial_index + i * i
                ) % size

                if self._table[index] is None:

                    self._table[index] = key

                    return (
                        True,
                        index,
                        True
                    )

            return False, None, True

        # =====================================================
        # DOBLE FUNCIÓN HASH
        # =====================================================

        if self._collision_method == "Doble función hash":

            step = self._second_hash(key)

            for i in range(1, size):

                index = (
                    initial_index + i * step
                ) % size

                if self._table[index] is None:

                    self._table[index] = key

                    return (
                        True,
                        index,
                        True
                    )

            return False, None, True

        # =====================================================
        # ANIDADO
        # =====================================================

        if self._collision_method == "Anidado":

            nested_index = (
                (key // size) + key
            ) % size

            if self._table[nested_index] is None:

                self._table[
                    nested_index
                ] = key

                return (
                    True,
                    nested_index,
                    True
                )

            # Segundo intento a partir
            # de la posición anidada.
            for i in range(1, size):

                index = (
                    nested_index + i
                ) % size

                if self._table[index] is None:

                    self._table[index] = key

                    return (
                        True,
                        index,
                        True
                    )

            return False, None, True

        return False, None, True

    # =========================================================
    # GENERAR / AGREGAR
    # =========================================================

    def _on_generate(self):

        configuration = self._validate_configuration()

        if configuration is None:
            return

        value_range, key_size, size = configuration

        # -----------------------------------------------------
        # SI HAY UNA COLISIÓN PENDIENTE
        # -----------------------------------------------------

        if self._pending_key is not None:

            self._show_error(
                "Debes seleccionar una solución de colisiones "
                "antes de continuar."
            )

            return

        # -----------------------------------------------------
        # SI LA TABLA TODAVÍA NO EXISTE
        # -----------------------------------------------------

        if not self._table_created:

            self._table = [
                None
                for _ in range(size)
            ]

            self._table_created = True

            self._collision_method = None

            self._collision_menu.set(
                "Seleccione una opción"
            )

            self._collision_status.configure(
                text=(
                    "La estrategia se solicitará "
                    "solo si aparece una colisión."
                )
            )

        else:

            # No permitimos cambiar el tamaño de una tabla
            # que ya está creada.
            if len(self._table) != size:

                self._show_error(
                    "La tabla ya fue creada con tamaño "
                    f"{len(self._table)}. Presiona Limpiar "
                    "para crear una nueva tabla."
                )

                return

        # -----------------------------------------------------
        # OBTENER NUEVAS CLAVES
        # -----------------------------------------------------

        remaining = size - self._count_elements()

        if remaining <= 0:

            self._show_error(
                "La tabla ya está llena. Presiona Limpiar "
                "para comenzar una nueva tabla."
            )

            return

        if self._mode_var.get() == "Aleatorio":

            new_keys = [
                random.randint(
                    1,
                    value_range
                )
                for _ in range(remaining)
            ]

        else:

            new_keys = self._parse_manual_values(
                value_range,
                key_size
            )

            if new_keys is None:
                return

            if len(new_keys) > remaining:

                self._show_error(
                    f"Solo quedan {remaining} posiciones "
                    "disponibles en la tabla."
                )

                return

        # -----------------------------------------------------
        # INSERTAR
        # -----------------------------------------------------

        self._insert_keys(new_keys)

    # =========================================================
    # INSERTAR VARIAS CLAVES
    # =========================================================

    def _insert_keys(self, keys):

        for key in keys:

            inserted, index, collision = (
                self._insert_key(key)
            )

            # -------------------------------------------------
            # NO SE PUDO INSERTAR PORQUE HAY COLISIÓN
            # -------------------------------------------------

            if not inserted:

                self._pending_key = key

                self._collision_status.configure(
                    text=(
                        f"⚠ Colisión en la clave {key}. "
                        "Selecciona una estrategia."
                    )
                )

                self._show_error(
                    f"Se produjo una colisión al insertar "
                    f"la clave {key}. Debes seleccionar una "
                    "solución de colisiones para continuar."
                )

                self._render_table()

                return

            # La clave ya fue insertada.
            self._data.append(key)

        # -----------------------------------------------------
        # TODAS LAS CLAVES SE INSERTARON
        # -----------------------------------------------------

        self._manual_entry.delete(
            0,
            "end"
        )

        self._clear_error()

        self._update_info()

        self._render_table()

    # =========================================================
    # SELECCIONAR SOLUCIÓN DE COLISIÓN
    # =========================================================

    def _on_collision_selected(self, method):

        # -----------------------------------------------------
        # NO PERMITIR CAMBIAR MÉTODO DURANTE LA MISMA TABLA
        # -----------------------------------------------------

        if self._collision_method is not None:

            self._collision_menu.set(
                self._collision_method
            )

            self._show_error(
                "La solución de colisiones ya está definida "
                f"como «{self._collision_method}». "
                "Solo puede cambiarse después de presionar "
                "Limpiar."
            )

            return

        # -----------------------------------------------------
        # GUARDAR MÉTODO
        # -----------------------------------------------------

        self._collision_method = method

        self._collision_status.configure(
            text=(
                f"Estrategia seleccionada: {method}"
            )
        )

        self._clear_error()

        # -----------------------------------------------------
        # SI NO HAY COLISIÓN PENDIENTE
        # -----------------------------------------------------

        if self._pending_key is None:

            return

        # -----------------------------------------------------
        # INTENTAR INSERTAR NUEVAMENTE
        # -----------------------------------------------------

        key = self._pending_key

        self._pending_key = None

        inserted, index, collision = (
            self._insert_key(key)
        )

        if not inserted:

            # La estrategia elegida no pudo resolver
            # la colisión.
            self._pending_key = key

            self._show_error(
                f"No fue posible insertar la clave {key} "
                f"utilizando {method}. "
                "La tabla puede estar llena."
            )

            return

        self._data.append(key)

        self._manual_entry.delete(
            0,
            "end"
        )

        self._update_info()

        self._render_table()

    # =========================================================
    # CONTAR ELEMENTOS
    # =========================================================

    def _count_elements(self):

        if self._collision_method == "Encadenado":

            return sum(
                len(bucket)
                for bucket in self._table
            )

        return sum(
            1
            for value in self._table
            if value is not None
        )

    # =========================================================
    # INFORMACIÓN
    # =========================================================

    def _update_info(self):

        total = len(
            self._table
        )

        used = self._count_elements()

        if self._collision_method is None:

            method_text = (
                "Método: todavía no requerido"
            )

        else:

            method_text = (
                f"Método: {self._collision_method}"
            )

        self._info_label.configure(
            text=(
                f"{used}/{total} elementos | "
                f"{method_text}"
            )
        )

    # =========================================================
    # RENDER TABLA
    # =========================================================

    def _render_table(self):

        for widget in (
            self._scroll_frame.winfo_children()
        ):

            widget.destroy()

        # -----------------------------------------------------
        # ENCABEZADO
        # -----------------------------------------------------

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
        ).pack(
            side="left",
            padx=(8, 12)
        )

        ctk.CTkLabel(
            header,
            text="Clave",
            width=130,
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
        ).pack(
            side="left",
            padx=(0, 12)
        )

        ctk.CTkLabel(
            header,
            text="Hash",
            width=80,
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
        ).pack(
            side="left",
            padx=(0, 12)
        )

        ctk.CTkLabel(
            header,
            text="Estado",
            font=ctk.CTkFont(
                size=13,
                weight="bold"
            ),
        ).pack(
            side="left"
        )

        # -----------------------------------------------------
        # FILAS
        # -----------------------------------------------------

        for index, slot in enumerate(
            self._table
        ):

            if self._collision_method == "Encadenado":

                occupied = bool(slot)

                if occupied:

                    key_text = " → ".join(
                        str(key)
                        for key in slot
                    )

                    hash_text = str(index)

                    status_text = (
                        "Encadenado"
                        if len(slot) > 1
                        else "Ocupado"
                    )

                else:

                    key_text = "—"
                    hash_text = "—"
                    status_text = "Vacío"

            else:

                occupied = (
                    slot is not None
                )

                if occupied:

                    key_text = str(slot)

                    hash_text = str(
                        self._hash(slot)
                    )

                    if self._hash(slot) == index:

                        status_text = "Ocupado"

                    else:

                        status_text = (
                            "Colisión resuelta"
                        )

                else:

                    key_text = "—"
                    hash_text = "—"
                    status_text = "Vacío"

            # -------------------------------------------------
            # COLOR DE FILA
            # -------------------------------------------------

            if not occupied:

                bg = (
                    "gray94",
                    "gray17"
                )

            elif index % 2 == 0:

                bg = (
                    "gray88",
                    "gray22"
                )

            else:

                bg = (
                    "gray94",
                    "gray17"
                )

            row = ctk.CTkFrame(
                self._scroll_frame,
                height=40,
                corner_radius=8,
                fg_color=bg,
            )

            row.pack(
                fill="x",
                padx=6,
                pady=2
            )

            row.pack_propagate(False)

            # Índice
            ctk.CTkLabel(
                row,
                text=str(index),
                width=80,
                font=ctk.CTkFont(
                    family="Consolas",
                    size=14
                ),
                anchor="center",
            ).pack(
                side="left",
                padx=(8, 12)
            )

            # Clave
            ctk.CTkLabel(
                row,
                text=key_text,
                width=130,
                font=ctk.CTkFont(
                    family="Consolas",
                    size=14,
                    weight=(
                        "bold"
                        if occupied
                        else "normal"
                    )
                ),
                anchor="w",
            ).pack(
                side="left",
                padx=(0, 12)
            )

            # Hash
            ctk.CTkLabel(
                row,
                text=hash_text,
                width=80,
                font=ctk.CTkFont(
                    family="Consolas",
                    size=14
                ),
                anchor="center",
            ).pack(
                side="left",
                padx=(0, 12)
            )

            # Estado
            ctk.CTkLabel(
                row,
                text=status_text,
                font=ctk.CTkFont(
                    size=13
                ),
                anchor="w",
            ).pack(
                side="left",
                padx=4
            )

        # -----------------------------------------------------
        # COLISIÓN PENDIENTE
        # -----------------------------------------------------

        if self._pending_key is not None:

            warning = ctk.CTkLabel(
                self._scroll_frame,
                text=(
                    f"⚠ La clave {self._pending_key} "
                    "está esperando una solución de colisión."
                ),
                font=ctk.CTkFont(
                    size=13,
                    weight="bold"
                ),
                text_color=(
                    "#cc7700",
                    "#ffaa33"
                ),
            )

            warning.pack(
                pady=12
            )

    # =========================================================
    # LIMPIAR TODO
    # =========================================================

    def _on_clear(self):

        # Borra las claves.
        self._data.clear()

        # Borra la tabla.
        self._table.clear()

        # Borra método de colisión.
        self._collision_method = None

        # Borra colisión pendiente.
        self._pending_key = None

        # Indica que todavía no existe tabla.
        self._table_created = False

        # Restablecer selector.
        self._collision_menu.set(
            "Seleccione una opción"
        )

        self._collision_status.configure(
            text=(
                "No se necesita una estrategia todavía."
            )
        )

        self._info_label.configure(
            text=""
        )

        self._manual_entry.delete(
            0,
            "end"
        )

        self._clear_error()

        self._show_placeholder()

    # =========================================================
    # PLACEHOLDER
    # =========================================================

    def _show_placeholder(self):

        for widget in (
            self._scroll_frame.winfo_children()
        ):

            widget.destroy()

        placeholder = ctk.CTkLabel(
            self._scroll_frame,
            text=(
                "Configura los parámetros y presiona "
                "«Generar» para comenzar."
            ),
            font=ctk.CTkFont(
                size=14
            ),
            text_color=(
                "gray50",
                "gray55"
            ),
        )

        placeholder.pack(
            pady=40
        )

    # =========================================================
    # MENSAJES
    # =========================================================

    def _show_error(self, message):

        self._error_label.configure(
            text=message
        )

    def _clear_error(self):

        self._error_label.configure(
            text=""
        )