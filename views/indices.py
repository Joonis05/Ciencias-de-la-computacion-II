
import random
import math
from bisect import bisect_left
from dataclasses import dataclass

import tkinter as tk
import customtkinter as ctk

from views.base_view import BaseView
from views.persistence import save_json, load_json


# Límites para evitar estructuras que puedan congelar el portátil.
_MAX_RECORDS = 500_000
_MAX_BLOCK_BYTES = 1_048_576
_MAX_RECORD_BYTES = 1_048_576
_MAX_INDEX_RECORD_BYTES = 1_048_576
_MAX_STORAGE_MB = 2_048

_DEFAULT_RECORDS = 100
_DEFAULT_RECORD_BYTES = 120
_DEFAULT_INDEX_RECORD_BYTES = 15
_DEFAULT_BLOCK_BYTES = 4096
_DEFAULT_STORAGE_MB = 128

_INDEX_TYPES = [
    "Índice Primario",
    "Índice Secundario",
    "Multinivel Primario",
    "Multinivel Secundario",
]


@dataclass
class IndexEntry:
    key: int
    pointer: int


@dataclass
class IndexLevel:
    level_number: int
    entries: list[IndexEntry]
    blocks: list[list[IndexEntry]]

    @property
    def entry_count(self):
        return len(self.entries)

    @property
    def block_count(self):
        return len(self.blocks)


class IndicesModel:
    """Cálculo y construcción de índices externos."""

    def __init__(self, records, record_bytes, index_record_bytes, block_bytes, storage_mb):
        self.records = max(0, int(records))
        self.record_bytes = int(record_bytes)
        self.index_record_bytes = int(index_record_bytes)
        self.block_bytes = int(block_bytes)
        self.storage_mb = int(storage_mb)
        self.data = []
        self._recalculate()

    def _recalculate(self):
        self.data_bfr = self.block_bytes // self.record_bytes if self.record_bytes else 0
        self.index_bfr = self.block_bytes // self.index_record_bytes if self.index_record_bytes else 0

        self.data_blocks_count = (
            math.ceil(self.records / self.data_bfr)
            if self.data_bfr > 0 and self.records > 0
            else 0
        )

        self.primary_entries_count = self.data_blocks_count
        self.primary_blocks_count = (
            math.ceil(self.primary_entries_count / self.index_bfr)
            if self.index_bfr > 0 and self.primary_entries_count > 0
            else 0
        )

        self.secondary_entries_count = self.records
        self.secondary_blocks_count = (
            math.ceil(self.secondary_entries_count / self.index_bfr)
            if self.index_bfr > 0 and self.secondary_entries_count > 0
            else 0
        )

    def theoretical_level_block_counts(self, secondary=False):
        """Cantidad de bloques de cada nivel usando todos los registros configurados."""
        first_entries = self.records if secondary else self.data_blocks_count
        counts = []
        if first_entries <= 0 or self.index_bfr <= 0:
            return counts

        blocks = math.ceil(first_entries / self.index_bfr)
        counts.append(blocks)

        while blocks > 1:
            entries = blocks
            blocks = math.ceil(entries / self.index_bfr)
            counts.append(blocks)

        return counts

    def theoretical_total_blocks(self, secondary=False):
        return self.data_blocks_count + sum(
            self.theoretical_level_block_counts(secondary)
        )

    def theoretical_total_bytes(self, secondary=False):
        return self.theoretical_total_blocks(secondary) * self.block_bytes

    def theoretical_within_storage(self):
        required_primary = self.theoretical_total_bytes(False)
        required_secondary = self.theoretical_total_bytes(True)
        capacity = self.storage_mb * 1024 * 1024
        return required_primary <= capacity and required_secondary <= capacity

    def required_data_blocks(self):
        self._recalculate()
        return self.data_blocks_count

    def build_simple_primary(self):
        data = sorted(self.data)
        entries = []

        for block_number in range(self.data_blocks_count):
            start = block_number * self.data_bfr
            if start >= len(data):
                break
            entries.append(IndexEntry(data[start], block_number))

        return [self._build_level(1, entries)] if entries else []

    def build_simple_secondary(self):
        indexed = sorted(
            (IndexEntry(key, position) for position, key in enumerate(self.data)),
            key=lambda entry: entry.key,
        )
        entries = list(indexed)
        return [self._build_level(1, entries)] if entries else []

    def _build_level(self, level_number, entries):
        blocks = [
            entries[i:i + self.index_bfr]
            for i in range(0, len(entries), self.index_bfr)
        ]
        return IndexLevel(level_number, list(entries), blocks)

    def build_multilevel(self, secondary=False):
        if secondary:
            levels = self.build_simple_secondary()
        else:
            levels = self.build_simple_primary()

        if not levels:
            return []

        current_blocks = levels[0].blocks
        next_level_number = 2

        while len(current_blocks) > 1:
            next_entries = [
                IndexEntry(
                    block[0].key,
                    block_number,
                )
                for block_number, block in enumerate(current_blocks)
                if block
            ]

            next_level = self._build_level(
                next_level_number,
                next_entries,
            )

            levels.append(next_level)
            current_blocks = next_level.blocks
            next_level_number += 1

        return levels

    def total_index_blocks(self, levels):
        return sum(level.block_count for level in levels)

    def total_blocks(self, levels):
        return self.data_blocks_count + self.total_index_blocks(levels)

    def total_bytes(self, levels):
        return self.total_blocks(levels) * self.block_bytes

    def within_storage(self, levels):
        return self.total_bytes(levels) <= self.storage_mb * 1024 * 1024

    @staticmethod
    def single_level_accesses(index_blocks):
        if index_blocks <= 0:
            return 1
        return math.ceil(math.log2(index_blocks)) + 1

    @staticmethod
    def multilevel_accesses(levels):
        if not levels:
            return 1
        return len(levels) + 1

    def get_levels(self, index_type):
        if index_type == "Índice Primario":
            return self.build_simple_primary()
        if index_type == "Índice Secundario":
            return self.build_simple_secondary()
        if index_type == "Multinivel Primario":
            return self.build_multilevel(secondary=False)
        return self.build_multilevel(secondary=True)

    def is_secondary(self, index_type):
        return index_type in (
            "Índice Secundario",
            "Multinivel Secundario",
        )

    def get_display_data(self, index_type):
        if self.is_secondary(index_type):
            return list(self.data)
        return sorted(self.data)

    def build_search_path(self, target, index_type):
        """
        Retorna una lista de pasos para animar la búsqueda.
        Cada paso tiene: level, block, kind, key, pointer y text.
        """
        levels = self.get_levels(index_type)
        if not levels:
            return [], None

        found = target in self.data
        data_position = None
        data_block = None

        if found:
            if self.is_secondary(index_type):
                data_position = self.data.index(target)
                data_block = data_position // self.data_bfr
            else:
                ordered = sorted(self.data)
                ordered_position = bisect_left(ordered, target)
                data_position = ordered_position
                data_block = ordered_position // self.data_bfr

        path = []

        if index_type.startswith("Índice"):
            leaf = levels[0]
            if not leaf.blocks:
                return [], found

            if found:
                if self.is_secondary(index_type):
                    leaf_index = bisect_left(
                        [entry.key for entry in leaf.entries],
                        target,
                    )
                    leaf_block = min(
                        leaf_index // self.index_bfr,
                        leaf.block_count - 1,
                    )
                else:
                    leaf_block = min(
                        data_block // self.index_bfr,
                        leaf.block_count - 1,
                    )
            else:
                if self.is_secondary(index_type):
                    leaf_index = bisect_left(
                        [entry.key for entry in leaf.entries],
                        target,
                    )
                    leaf_index = min(
                        max(0, leaf_index),
                        len(leaf.entries) - 1,
                    ) if leaf.entries else 0
                    leaf_block = min(
                        leaf_index // self.index_bfr,
                        leaf.block_count - 1,
                    )
                else:
                    leaf_block = min(
                        max(0, (data_block or 0)) // self.index_bfr,
                        leaf.block_count - 1,
                    )

            # Para los índices de un solo nivel se simula la selección del bloque índice.
            path.append({
                "level": leaf.level_number,
                "block": leaf_block,
                "kind": "index",
                "text": f"Nivel {leaf.level_number}: revisar bloque de índice {leaf_block + 1}.",
            })

            if found:
                entry_index = None
                if self.is_secondary(index_type):
                    keys = [entry.key for entry in leaf.entries]
                    entry_index = bisect_left(keys, target)
                else:
                    entry_index = data_block

                if entry_index is not None and leaf.entries:
                    entry_index = min(entry_index, len(leaf.entries) - 1)
                    entry = leaf.entries[entry_index]
                    path.append({
                        "level": leaf.level_number,
                        "block": leaf_block,
                        "kind": "entry",
                        "key": entry.key,
                        "pointer": entry.pointer,
                        "text": (
                            (
                                f"Clave {entry.key} encontrada en el índice; "
                                f"apunta al registro {entry.pointer + 1:,} (bloque "
                                f"{entry.pointer // self.data_bfr + 1 if self.data_bfr else 1})."
                            )
                            if self.is_secondary(index_type)
                            else (
                                f"Clave {entry.key} encontrada en el índice; "
                                f"apunta al bloque {entry.pointer + 1}."
                            )
                        ),
                    })

                path.append({
                    "level": 0,
                    "block": data_block,
                    "kind": "data",
                    "text": f"Acceso al bloque de datos {data_block + 1}.",
                })
            else:
                path.append({
                    "level": 0,
                    "block": data_block or 0,
                    "kind": "data", 
                    "text": "La clave no está en el archivo de datos.",
                })

            return path, found

        # Multinivel: subir desde la raíz hacia la hoja.
        # levels[0] = hoja, levels[-1] = raíz.
        child_block = data_block if found else 0

        for level_index in range(len(levels) - 1, -1, -1):
            level = levels[level_index]

            if level_index == len(levels) - 1:
                block_number = 0
            else:
                block_number = min(
                    child_block // self.index_bfr,
                    level.block_count - 1,
                )

            path.append({
                "level": level.level_number,
                "block": block_number,
                "kind": "index",
                "text": (
                    f"Nivel {level.level_number}: revisar bloque de índice "
                    f"{block_number + 1}."
                ),
            })

            if level_index > 0:
                child_block = block_number

        if found:
            leaf = levels[0]
            entry_index = (
                data_position
                if self.is_secondary(index_type)
                else data_block
            )
            entry_index = min(
                max(0, entry_index),
                len(leaf.entries) - 1,
            ) if leaf.entries else 0

            if leaf.entries:
                entry = leaf.entries[entry_index]
                path.append({
                    "level": leaf.level_number,
                    "block": min(
                        entry_index // self.index_bfr,
                        leaf.block_count - 1,
                    ),
                    "kind": "entry",
                    "key": entry.key,
                    "pointer": entry.pointer,
                    "text": (
                        f"Clave {entry.key} encontrada en el nivel hoja; "
                        f"apunta al bloque {data_block + 1}."
                    ),
                })

            path.append({
                "level": 0,
                "block": data_block,
                "kind": "data",
                "text": f"Acceso al bloque de datos {data_block + 1}.",
            })
        else:
            path.append({
                "level": 0,
                "block": 0,
                "kind": "data",
                "text": "La clave no está en el archivo de datos.",
            })

        return path, found


def sample_values(count):
    """Genera claves únicas sin crear estructuras de Python innecesariamente grandes."""
    if count <= 0:
        return []
    upper = max(1000, count * 10)
    return random.sample(range(1, upper + 1), count)




class IndicesView(BaseView):
    """Interfaz para índices externos con estructura vertical tipo diagrama."""

    _MAX_REAL_RECORDS = 25_000
    _VISIBLE_TABLE_ROWS = 10
    _COLUMN_WIDTH = 210
    _BLOCK_H = 125
    _BLOCK_GAP = 10

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Índices",
            **kwargs,
        )

        self._model = None
        self._data = []
        self._mode_var = ctk.StringVar(value="Aleatorio")
        self._index_type = _INDEX_TYPES[0]

        self._anim_job = None
        self._is_animating = False
        self._animation_path = []
        self._animation_step = 0
        self._target = None
        self._found = False

        self._canvas_items = {}
        self._data_rows = {}
        self._display_columns = []
        self._block_positions = {}
        self._pointer_items = []

        self._build_ui()

    # ==========================================================
    # UI
    # ==========================================================

    def _build_ui(self):
        self.add_title("Índices")
        self.add_subtitle(
            "Índice primario, secundario y estructuras multinivel "
            "para búsqueda de archivos externos."
        )

        # -------------------- CONFIGURACIÓN --------------------
        config = ctk.CTkFrame(
            self.content,
            corner_radius=12,
            fg_color=("gray92", "gray17"),
            border_width=2,
            border_color=("gray78", "gray30"),
        )
        config.pack(fill="x", padx=10, pady=(0, 8))

        inner = ctk.CTkFrame(config, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)

        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            row1,
            text="Tipo de índice:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        self._index_menu = ctk.CTkOptionMenu(
            row1,
            values=_INDEX_TYPES,
            width=205,
            height=32,
            command=self._on_index_change,
        )
        self._index_menu.set(self._index_type)
        self._index_menu.pack(side="left", padx=(0, 18))

        ctk.CTkLabel(
            row1,
            text="Modo:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        self._mode_seg = ctk.CTkSegmentedButton(
            row1,
            values=["Aleatorio", "Manual"],
            variable=self._mode_var,
            command=self._on_mode_change,
            font=ctk.CTkFont(size=12),
        )
        self._mode_seg.pack(side="left")

        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 8))

        self._records_entry = self._entry_with_label(
            row2, "Registros:", str(_DEFAULT_RECORDS)
        )
        self._record_len_entry = self._entry_with_label(
            row2, "Registro (bytes):", str(_DEFAULT_RECORD_BYTES)
        )
        self._index_len_entry = self._entry_with_label(
            row2, "Índice (bytes):", str(_DEFAULT_INDEX_RECORD_BYTES)
        )
        self._block_size_entry = self._entry_with_label(
            row2, "Bloque (bytes):", str(_DEFAULT_BLOCK_BYTES)
        )
        self._storage_entry = self._entry_with_label(
            row2, "Capacidad (MB):", str(_DEFAULT_STORAGE_MB)
        )

        row3 = ctk.CTkFrame(inner, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 8))

        self._value_entry = ctk.CTkEntry(
            row3,
            height=32,
            placeholder_text="Valores manuales o clave objetivo: 34, 2449, 9282",
            font=ctk.CTkFont(size=13),
        )
        self._value_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._btn_add = self._button(row3, "Añadir", 82, self._on_add)
        self._btn_search = self._button(row3, "Buscar", 82, self._on_search)
        self._btn_delete = self._button(
            row3, "Eliminar", 82, self._on_delete,
            fg_color="#C62828", hover_color="#8E0000", text_color="white"
        )
        self._btn_reset = self._button(
            row3, "Reiniciar", 88, self._reset_search,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            text_color=("black", "white"),
        )

        row4 = ctk.CTkFrame(inner, fg_color="transparent")
        row4.pack(fill="x")

        self._btn_structure = self._button(
            row4, "Construir Índices", 135, self._on_build
        )
        self._btn_clear = self._button(
            row4, "Limpiar", 82, self._on_clear,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            text_color=("black", "white"),
        )

        ctk.CTkLabel(
            row4,
            text="Velocidad:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=(16, 5))

        self._speed_slider = ctk.CTkSlider(
            row4,
            from_=100,
            to=2000,
            number_of_steps=19,
            width=130,
            command=self._on_speed_change,
        )
        self._speed_slider.set(500)
        self._speed_slider.pack(side="left")

        self._speed_label = ctk.CTkLabel(
            row4,
            text="500 ms",
            width=52,
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
        )
        self._speed_label.pack(side="left", padx=(4, 8))

        self._btn_save = self._button(
            row4, "Guardar", 82, self._on_save
        )
        self._btn_load = self._button(
            row4, "Cargar", 82, self._on_load
        )

        # -------------------- ESTADO --------------------
        status_box = ctk.CTkFrame(
            self.content,
            corner_radius=8,
            fg_color=("gray85", "gray22"),
            border_width=1,
            border_color=("gray75", "gray35"),
        )
        status_box.pack(fill="x", padx=10, pady=(0, 6))

        self._status_label = ctk.CTkLabel(
            status_box,
            text="Estado: configura los parámetros y construye la estructura.",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("gray20", "gray80"),
            anchor="w",
            padx=12,
            pady=7,
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
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#991B1B", "#FCA5A5"),
            anchor="w",
            padx=10,
            pady=5,
        )
        self._error_label.pack(fill="x")
        self._error_box.pack_forget()

        # -------------------- ÁREA PRINCIPAL --------------------
        main = ctk.CTkFrame(self.content, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=0)
        main.grid_rowconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=0)

        # Estructura a la izquierda
        structure_box = ctk.CTkFrame(
            main,
            corner_radius=12,
            fg_color=("gray96", "gray14"),
            border_width=2,
            border_color=("gray78", "gray30"),
        )
        structure_box.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        structure_box.grid_rowconfigure(1, weight=1)
        structure_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            structure_box,
            text="Estructura del índice",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 2))

        canvas_frame = ctk.CTkFrame(
            structure_box,
            fg_color=("gray96", "gray14"),
        )
        canvas_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(
            canvas_frame,
            bg="#F7F7F7",
            highlightthickness=0,
            bd=0,
        )
        self._canvas.grid(row=0, column=0, sticky="nsew")

        ybar = ctk.CTkScrollbar(
            canvas_frame,
            orientation="vertical",
            command=self._canvas.yview,
        )
        ybar.grid(row=0, column=1, sticky="ns")

        xbar = ctk.CTkScrollbar(
            canvas_frame,
            orientation="horizontal",
            command=self._canvas.xview,
        )
        xbar.grid(row=1, column=0, sticky="ew")

        self._canvas.configure(
            yscrollcommand=ybar.set,
            xscrollcommand=xbar.set,
        )

        self._canvas.bind(
            "<Configure>",
            lambda event: self._draw_structure()
        )

        # Registros cargados: el panel derecho queda dedicado únicamente a esto.
        side_box = ctk.CTkFrame(
            main,
            width=320,
            corner_radius=12,
            fg_color=("gray94", "gray15"),
            border_width=2,
            border_color=("gray78", "gray30"),
        )
        side_box.grid(row=0, column=1, sticky="nsew")
        side_box.grid_propagate(False)
        side_box.grid_rowconfigure(1, weight=1)
        side_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            side_box,
            text="Registros cargados",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 8))

        table_box = ctk.CTkFrame(side_box, fg_color="transparent")
        table_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        table_box.grid_rowconfigure(1, weight=1)
        table_box.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(
            table_box,
            corner_radius=6,
            fg_color=("gray82", "gray28"),
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=0)
        header.grid_columnconfigure(1, weight=1)
        header.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(
            header, text="#", width=42,
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, padx=4, pady=6)
        ctk.CTkLabel(
            header, text="Clave",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=1, sticky="w", padx=4, pady=6)
        ctk.CTkLabel(
            header, text="Bloque", width=72,
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=2, padx=4, pady=6)

        self._data_table = ctk.CTkScrollableFrame(
            table_box,
            fg_color=("gray97", "gray13"),
            corner_radius=6,
        )
        self._data_table.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self._data_table.grid_columnconfigure(0, weight=0)
        self._data_table.grid_columnconfigure(1, weight=1)
        self._data_table.grid_columnconfigure(2, weight=0)

        # Cálculos: panel pequeño y horizontal en la parte inferior.
        calc_box = ctk.CTkFrame(
            main,
            corner_radius=10,
            fg_color=("gray88", "gray22"),
            border_width=1,
            border_color=("gray75", "gray35"),
        )
        calc_box.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        calc_box.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            calc_box,
            text="Cálculos:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=(10, 6), pady=5)

        self._calc_frame = ctk.CTkFrame(
            calc_box,
            fg_color="transparent",
        )
        self._calc_frame.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=2)

        self._show_placeholder()

    def _button(self, parent, text, width, command, **kwargs):
        btn = ctk.CTkButton(
            parent,
            text=text,
            width=width,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=command,
            **kwargs,
        )
        btn.pack(side="left", padx=(0, 6))
        return btn

    def _entry_with_label(self, parent, text, default):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=(0, 5))

        entry = ctk.CTkEntry(
            parent,
            width=70,
            height=32,
            font=ctk.CTkFont(size=12),
            justify="center",
        )
        entry.insert(0, default)
        entry.pack(side="left", padx=(0, 10))
        return entry

    # ==========================================================
    # CONFIGURACIÓN Y DATOS
    # ==========================================================

    def _on_mode_change(self, selected):
        self._clear_error()

    def _on_index_change(self, selected):
        if self._is_animating:
            return
        self._index_type = selected
        if self._model is not None:
            self._draw_structure()
            self._render_calculations()
            self._render_data_table()

    def _read_configuration(self):
        try:
            records = int(self._records_entry.get().strip())
            record_bytes = int(self._record_len_entry.get().strip())
            index_record_bytes = int(self._index_len_entry.get().strip())
            block_bytes = int(self._block_size_entry.get().strip())
            storage_mb = int(self._storage_entry.get().strip())
        except ValueError:
            self._show_error("Todos los parámetros deben ser números enteros.")
            return None

        if not 1 <= records <= _MAX_RECORDS:
            self._show_error(
                f"La cantidad de registros debe estar entre 1 y {_MAX_RECORDS:,}."
            )
            return None
        if not 1 <= record_bytes <= _MAX_RECORD_BYTES:
            self._show_error("La longitud del registro no es válida.")
            return None
        if not 1 <= index_record_bytes <= _MAX_INDEX_RECORD_BYTES:
            self._show_error("La longitud del registro índice no es válida.")
            return None
        if not 1 <= block_bytes <= _MAX_BLOCK_BYTES:
            self._show_error("El tamaño del bloque no es válido.")
            return None
        if not 1 <= storage_mb <= _MAX_STORAGE_MB:
            self._show_error(
                f"La capacidad configurada debe estar entre 1 y {_MAX_STORAGE_MB:,} MB."
            )
            return None
        if record_bytes > block_bytes:
            self._show_error(
                "La longitud del registro no puede ser mayor que el tamaño del bloque."
            )
            return None
        if index_record_bytes > block_bytes:
            self._show_error(
                "La longitud del registro índice no puede ser mayor que el tamaño del bloque."
            )
            return None

        data_bfr = block_bytes // record_bytes
        index_bfr = block_bytes // index_record_bytes
        if data_bfr < 1 or index_bfr < 1:
            self._show_error("Cada bloque debe poder contener al menos un registro.")
            return None

        return records, record_bytes, index_record_bytes, block_bytes, storage_mb

    def _on_build(self):
        if self._is_animating:
            return

        cfg = self._read_configuration()
        if cfg is None:
            return

        self._model = IndicesModel(*cfg)

        # La estructura teórica siempre se valida. La generación aleatoria
        # se limita para evitar que el portátil tenga que crear cientos de miles
        # de objetos reales solo para mostrar el diagrama.
        if not self._model.theoretical_within_storage():
            required = self._format_bytes(
                self._model.theoretical_total_bytes(True)
            )
            self._model = None
            self._show_error(
                f"La estructura multinivel secundaria requiere aproximadamente "
                f"{required}, pero la capacidad configurada es {cfg[4]} MB."
            )
            return

        if self._mode_var.get() == "Aleatorio":
            if self._model.records <= self._MAX_REAL_RECORDS:
                self._data = sample_values(self._model.records)
                status = (
                    f"Estructura construida con {len(self._data):,} registros reales."
                )
            else:
                self._data = []
                status = (
                    f"Estructura teórica preparada para {self._model.records:,} registros. "
                    f"Para proteger el equipo, la carga automática se limita a "
                    f"{self._MAX_REAL_RECORDS:,} registros."
                )
        else:
            self._data = []
            status = (
                f"Estructura preparada para {self._model.records:,} registros. "
                "Usa Añadir para cargar las claves."
            )

        self._model.data = list(self._data)
        self._render_all()
        self._status_label.configure(text=status)
        self._clear_error()

    def _on_add(self):
        if self._is_animating:
            return
        if self._model is None:
            self._show_error("Primero construye la estructura.")
            return
        if len(self._data) >= min(self._model.records, self._MAX_REAL_RECORDS):
            self._show_error(
                f"La carga real está limitada a {self._MAX_REAL_RECORDS:,} registros "
                "para proteger el rendimiento del equipo."
            )
            return

        text = self._value_entry.get().strip()

        if not text:
            if self._mode_var.get() != "Aleatorio":
                self._show_error("Ingresa al menos una clave.")
                return

            remaining = min(
                self._model.records - len(self._data),
                self._MAX_REAL_RECORDS - len(self._data),
            )
            count = min(remaining, 100)
            existing = set(self._data)
            upper = max(1000, self._model.records * 10)
            values = []
            while len(values) < count:
                value = random.randint(1, upper)
                if value not in existing:
                    existing.add(value)
                    values.append(value)
        else:
            values = []
            for part in [p.strip() for p in text.split(",") if p.strip()]:
                try:
                    value = int(part)
                except ValueError:
                    self._show_error(f"«{part}» no es un número entero válido.")
                    return
                if value <= 0:
                    self._show_error("Las claves deben ser mayores que cero.")
                    return
                if value in self._data or value in values:
                    self._show_error(f"La clave {value} está repetida.")
                    return
                values.append(value)

            remaining = min(
                self._model.records - len(self._data),
                self._MAX_REAL_RECORDS - len(self._data),
            )
            if len(values) > remaining:
                self._show_error(f"Solo quedan {remaining:,} registros disponibles para cargar.")
                return

        self._data.extend(values)
        self._model.data = list(self._data)
        self._value_entry.delete(0, "end")
        self._render_all()
        self._status_label.configure(
            text=f"Se añadieron {len(values):,} registro(s). Total cargado: {len(self._data):,}."
        )
        self._clear_error()

    # ==========================================================
    # BÚSQUEDA / ELIMINACIÓN
    # ==========================================================

    def _get_target(self):
        raw = self._value_entry.get().strip()
        if not raw:
            self._show_error("Ingresa la clave que deseas buscar.")
            return None
        if "," in raw:
            raw = raw.split(",")[0].strip()
        try:
            return int(raw)
        except ValueError:
            self._show_error("La clave debe ser un número entero.")
            return None

    def _on_search(self):
        if self._is_animating:
            return
        if self._model is None or not self._data:
            self._show_error("Primero construye la estructura y añade registros reales.")
            return

        target = self._get_target()
        if target is None:
            return

        self._animation_path, self._found = self._model.build_search_path(
            target,
            self._index_type,
        )
        if not self._animation_path:
            self._show_error("No hay una ruta de búsqueda disponible para esta estructura.")
            return

        self._target = target
        self._animation_step = 0
        self._is_animating = True
        self._reset_visuals()
        self._set_controls_state("disabled")

        levels = self._model.get_levels(self._index_type)
        if self._index_type in ("Índice Primario", "Índice Secundario"):
            accesses = self._model.single_level_accesses(
                levels[0].block_count if levels else 0
            )
        else:
            accesses = self._model.multilevel_accesses(levels)

        self._status_label.configure(
            text=f"Buscando {target} en {self._index_type}. Accesos teóricos: {accesses}."
        )
        self._animate_step()

    def _animate_step(self):
        if not self._is_animating:
            return
        if self._animation_step >= len(self._animation_path):
            self._finish_search()
            return

        step = self._animation_path[self._animation_step]
        self._reset_visuals()
        self._highlight_step(step)
        self._status_label.configure(
            text=f"Paso {self._animation_step + 1}: {step['text']}"
        )

        self._animation_step += 1
        self._anim_job = self.after(
            int(self._speed_slider.get()),
            self._animate_step,
        )

    def _finish_search(self):
        self._cancel_animation_only()

        if self._found:
            self._highlight_found_data(self._target)
            self._status_label.configure(
                text=f"La clave {self._target} fue encontrada correctamente."
            )
        else:
            self._status_label.configure(
                text=f"La clave {self._target} no fue encontrada."
            )

        self._set_controls_state("normal")

    def _highlight_step(self, step):
        kind = step.get("kind")
        block = step.get("block", 0)
        level = step.get("level", 0)

        key = (kind, level, block)
        items = self._canvas_items.get(key, [])

        for item in items:
            self._canvas.itemconfigure(
                item,
                fill="#FEF3C7",
                outline="#D97706",
                width=3,
            )

        if kind == "entry":
            self._show_search_pointer(step)

    def _highlight_found_data(self, target):
        if self._model is None or not self._data:
            return

        try:
            if self._model.is_secondary(self._index_type):
                position = self._data.index(target)
            else:
                ordered = sorted(self._data)
                position = bisect_left(ordered, target)
        except ValueError:
            return

        block = position // self._model.data_bfr
        row_index = self._compressed_record_indexes(len(self._data))
        if block in row_index:
            for row in self._data_rows.get(block, []):
                row.configure(
                    fg_color=("#DCFCE7", "#14532D")
                )

    def _on_delete(self):
        if self._is_animating:
            return
        if self._model is None or not self._data:
            self._show_error("No hay registros para eliminar.")
            return

        target = self._get_target()
        if target is None:
            return
        if target not in self._data:
            self._show_error(f"La clave {target} no existe; no se eliminó nada.")
            return

        self._data.remove(target)
        self._model.data = list(self._data)
        self._render_all()
        self._status_label.configure(
            text=f"La clave {target} fue eliminada y los índices se reconstruyeron."
        )
        self._clear_error()

    def _reset_search(self):
        self._cancel_animation_only()
        self._reset_visuals()
        self._status_label.configure(text="Estado: búsqueda reiniciada.")
        self._clear_error()
        self._set_controls_state("normal")

    def _cancel_animation_only(self):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
        self._anim_job = None
        self._is_animating = False

    # ==========================================================
    # RENDER DE CÁLCULOS Y TABLA
    # ==========================================================

    def _render_all(self):
        self._render_calculations()
        self._render_data_table()
        self._draw_structure()

    def _render_calculations(self):
        for child in self._calc_frame.winfo_children():
            child.destroy()

        if self._model is None:
            return

        levels = self._model.theoretical_level_block_counts(
            self._model.is_secondary(self._index_type)
        )
        index_blocks = sum(levels)
        required = self._model.theoretical_total_bytes(
            self._model.is_secondary(self._index_type)
        )

        if self._index_type in ("Índice Primario", "Índice Secundario"):
            accesses = self._model.single_level_accesses(
                levels[0] if levels else 0
            )
        else:
            accesses = self._model.multilevel_accesses(levels)

        rows = [
            ("R/B", f"{self._model.data_bfr:,}"),
            ("Ri/B", f"{self._model.index_bfr:,}"),
            ("B. datos", f"{self._model.data_blocks_count:,}"),
            ("B. índice", f"{index_blocks:,}"),
            ("Niveles", f"{len(levels):,}"),
            ("Accesos", f"{accesses:,}"),
            ("Almacenamiento", self._format_bytes(required)),
        ]

        for label, value in rows:
            item = ctk.CTkFrame(self._calc_frame, fg_color="transparent")
            item.pack(side="left", padx=7, pady=2)

            ctk.CTkLabel(
                item,
                text=label,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=("gray40", "gray65"),
            ).pack(side="left", padx=(0, 4))

            ctk.CTkLabel(
                item,
                text=value,
                font=ctk.CTkFont(size=10, weight="bold"),
            ).pack(side="left")

    def _render_data_table(self):
        for child in self._data_table.winfo_children():
            child.destroy()
        self._data_rows = {}

        if not self._data or self._model is None:
            ctk.CTkLabel(
                self._data_table,
                text="Sin registros reales cargados",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=("gray50", "gray55"),
            ).grid(row=0, column=0, columnspan=3, pady=15, padx=8)
            return

        # En la tabla lateral se muestran todos los registros cargados.
        # El scrollbar permite recorrerlos uno por uno, sin saltar del primero al último.
        ordered = sorted(self._data) if not self._model.is_secondary(self._index_type) else list(self._data)

        row = 0
        for position, value in enumerate(ordered):
            block = position // self._model.data_bfr

            number_label = ctk.CTkLabel(
                self._data_table,
                text=str(position + 1),
                width=42,
                font=ctk.CTkFont(family="Consolas", size=12),
            )
            number_label.grid(row=row, column=0, padx=4, pady=4)

            value_label = ctk.CTkLabel(
                self._data_table,
                text=str(value),
                font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
                anchor="w",
            )
            value_label.grid(row=row, column=1, sticky="w", padx=4, pady=4)

            block_label = ctk.CTkLabel(
                self._data_table,
                text=f"B{block + 1}",
                width=70,
                font=ctk.CTkFont(family="Consolas", size=12),
            )
            block_label.grid(row=row, column=2, padx=4, pady=4)

            self._data_rows.setdefault(block, []).append(value_label)
            row += 1

    @staticmethod
    def _compressed_record_indexes(total):
        if total <= 10:
            return list(range(total))
        return [0, 1, 2, 3, 4, "...", total - 5, total - 4, total - 3, total - 2, total - 1]

    # ==========================================================
    # DIAGRAMA VERTICAL
    # ==========================================================

    def _draw_structure(self):
        if not hasattr(self, "_canvas"):
            return

        self._canvas.delete("all")
        self._canvas_items = {}
        self._display_columns = []
        self._block_positions = {}
        self._pointer_items = []

        if self._model is None:
            self._show_placeholder()
            return

        secondary = self._model.is_secondary(self._index_type)

        # Antes de cargar datos se muestra la capacidad teórica configurada.
        # Después de cargar datos, el diagrama se construye con la estructura
        # real para que los bloques y las entradas coincidan con lo que se ve.
        if self._data:
            levels = self._model.get_levels(self._index_type)
            level_counts = [level.block_count for level in levels]
            data_blocks_count = math.ceil(len(self._data) / self._model.data_bfr) if self._model.data_bfr else 0
        else:
            levels = []
            level_counts = self._model.theoretical_level_block_counts(secondary)
            data_blocks_count = self._model.data_blocks_count

        columns = []
        if level_counts:
            # El nivel superior queda a la izquierda y el nivel hoja junto a datos.
            for level_number, block_count in reversed(
                list(enumerate(level_counts, start=1))
            ):
                columns.append((f"Nivel {level_number}", block_count, "index", level_number))

        columns.append((
            "Archivo de datos",
            data_blocks_count,
            "data",
            0,
        ))

        canvas_width = max(1050, len(columns) * 235)
        canvas_height = max(620, self._required_column_height(level_counts, data_blocks_count))

        self._canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))

        title = self._index_type
        self._canvas.create_text(
            20,
            18,
            anchor="w",
            text=title,
            font=("Arial", 15, "bold"),
            fill="#252525",
        )

        if self._data:
            structure_note = (
                f"Estructura real: {len(self._data):,} registros cargados"
            )
        else:
            structure_note = (
                f"Estructura teórica para {self._model.records:,} registros"
            )

        self._canvas.create_text(
            20,
            42,
            anchor="w",
            text=structure_note,
            font=("Arial", 10),
            fill="#666666",
        )

        top = 75
        x = 30
        column_centers = []

        for title, block_count, kind, level_number in columns:
            col_x = x
            center = col_x + self._COLUMN_WIDTH / 2
            column_centers.append(center)

            self._draw_column(
                title,
                block_count,
                kind,
                level_number,
                col_x,
                top,
            )

            x += 225

        # No se dibujan punteros permanentes. El puntero concreto aparece
        # durante la búsqueda, cuando se selecciona una entrada del índice.

    def _required_column_height(self, levels, data_blocks):
        max_blocks = max(
            [self._visible_block_count(x) for x in levels]
            + [self._visible_block_count(data_blocks), 1]
        )
        return 100 + max_blocks * (self._BLOCK_H + self._BLOCK_GAP) + 40

    @staticmethod
    def _visible_block_count(total):
        return total if total <= 5 else 5

    def _draw_column(self, title, total_blocks, kind, level_number, x, y):
        self._canvas.create_text(
            x + self._COLUMN_WIDTH / 2,
            y,
            text=title,
            font=("Arial", 12, "bold"),
            fill="#333333",
        )

        self._canvas.create_text(
            x + self._COLUMN_WIDTH / 2,
            y + 20,
            text=f"{total_blocks:,} bloques",
            font=("Arial", 9),
            fill="#777777",
        )

        visible = self._compressed_block_indexes(total_blocks)
        current_y = y + 40

        for marker in visible:
            if marker == "...":
                self._canvas.create_text(
                    x + self._COLUMN_WIDTH / 2,
                    current_y + self._BLOCK_H / 2,
                    text="· · ·",
                    font=("Arial", 20, "bold"),
                    fill="#777777",
                )
                current_y += self._BLOCK_H + self._BLOCK_GAP
                continue

            block_index = marker
            kind_key = "data" if kind == "data" else "index"
            position_key = (kind_key, level_number, block_index)
            self._block_positions[position_key] = (x, current_y)

            rect = self._canvas.create_rectangle(
                x,
                current_y,
                x + self._COLUMN_WIDTH,
                current_y + self._BLOCK_H,
                fill="#FFFFFF",
                outline="#6B7280",
                width=2,
            )

            self._canvas_items.setdefault(position_key, []).append(rect)

            self._canvas.create_text(
                x + 10,
                current_y + 9,
                anchor="nw",
                text=f"B{block_index + 1}",
                font=("Arial", 10, "bold"),
                fill="#374151",
            )

            if kind == "data":
                self._draw_data_block_content(x, current_y, block_index)
            else:
                self._draw_index_block_content(x, current_y, block_index, level_number)

            current_y += self._BLOCK_H + self._BLOCK_GAP

    @staticmethod
    def _compressed_block_indexes(total):
        if total <= 5:
            return list(range(total))
        return [0, 1, "...", total - 2, total - 1]

    @staticmethod
    def _compact_values(values, max_visible=5):
        values = list(values)
        if not values:
            return "—"
        if len(values) <= max_visible:
            return ", ".join(str(value) for value in values)

        left_count = max_visible // 2
        right_count = max_visible - left_count
        left = ", ".join(str(value) for value in values[:left_count])
        right = ", ".join(str(value) for value in values[-right_count:])
        return f"{left}, ..., {right}"

    @staticmethod
    def _list_values(values, max_visible=5):
        values = list(values)
        if len(values) <= max_visible:
            return values

        left_count = max_visible // 2
        right_count = max_visible - left_count
        return values[:left_count] + ["..."] + values[-right_count:]

    def _draw_data_block_content(self, x, y, block_index):
        bfr = self._model.data_bfr
        if bfr <= 0:
            return

        # En primario, los registros del archivo se visualizan ordenados;
        # en secundario se conserva el orden en que fueron cargados.
        secondary = self._model.is_secondary(self._index_type)
        ordered_data = list(self._data) if secondary else sorted(self._data)

        start = block_index * bfr
        block_values = ordered_data[start:start + bfr]

        if not block_values:
            self._canvas.create_text(
                x + 10,
                y + 38,
                anchor="nw",
                text="Sin registros cargados",
                font=("Arial", 9),
                fill="#777777",
            )
            return

        # Los registros se muestran como lista dentro del bloque.
        # Para no desbordar el rectángulo, se muestran 5 elementos como máximo.
        visible_values = self._list_values(block_values, max_visible=5)
        lines = [f"• {value}" if value != "..." else "  ..." for value in visible_values]
        values_text = "\n".join(lines)

        self._canvas.create_text(
            x + 10,
            y + 28,
            anchor="nw",
            text="Registros:",
            font=("Arial", 8, "bold"),
            fill="#333333",
        )

        self._canvas.create_text(
            x + 13,
            y + 44,
            anchor="nw",
            text=values_text,
            font=("Consolas", 8),
            fill="#333333",
            width=self._COLUMN_WIDTH - 24,
        )

    def _draw_index_block_content(self, x, y, block_index, level_number):
        secondary = self._model.is_secondary(self._index_type)
        entry_count = self._model.index_bfr

        actual_entries = []
        if self._data:
            levels = self._model.get_levels(self._index_type)
            if 1 <= level_number <= len(levels):
                level = levels[level_number - 1]
                if 0 <= block_index < len(level.blocks):
                    actual_entries = level.blocks[block_index]

        if actual_entries:
            visible_entries = actual_entries
            label = "Claves:"
        elif not self._data:
            counts = self._model.theoretical_level_block_counts(secondary)
            if 1 <= level_number <= len(counts):
                if level_number == 1:
                    total_entries = (
                        self._model.records
                        if secondary
                        else self._model.data_blocks_count
                    )
                else:
                    total_entries = counts[level_number - 2]

                first_entry = block_index * entry_count + 1
                last_entry = min(
                    (block_index + 1) * entry_count,
                    total_entries,
                )
                theoretical = (
                    list(range(first_entry, min(first_entry + 4, last_entry + 1)))
                    if last_entry >= first_entry
                    else []
                )
                if last_entry - first_entry + 1 > 4:
                    theoretical.append("...")
                    theoretical.extend(
                        range(max(first_entry + 4, last_entry - 1), last_entry + 1)
                    )
                visible_entries = theoretical
                label = "Entradas:"
            else:
                visible_entries = []
                label = "Entradas:"
        else:
            visible_entries = []
            label = "Entradas:"

        # En todos los niveles se usa el mismo formato de lista.
        if actual_entries:
            values = [entry.key for entry in actual_entries]
        else:
            values = visible_entries

        values = self._list_values(values, max_visible=5)
        lines = [f"• {value}" if value != "..." else "  ..." for value in values]
        values_text = "\n".join(lines) if lines else "—"

        self._canvas.create_text(
            x + 10,
            y + 30,
            anchor="nw",
            text=label,
            font=("Arial", 8, "bold"),
            fill="#333333",
        )

        self._canvas.create_text(
            x + 13,
            y + 46,
            anchor="nw",
            text=values_text,
            font=("Consolas", 8),
            fill="#333333",
            width=self._COLUMN_WIDTH - 24,
        )

        if self._data and actual_entries:
            detail = f"{len(actual_entries):,} ent. / {entry_count:,} posibles"
        elif not self._data:
            detail = f"máx. {entry_count:,} ent. / bloque"
        else:
            detail = "Sin entradas cargadas"

        self._canvas.create_text(
            x + 10,
            y + self._BLOCK_H - 18,
            anchor="nw",
            text=detail,
            font=("Arial", 7, "bold"),
            fill="#777777",
        )

    def _show_search_pointer(self, step):
        pointer = step.get("pointer")
        if pointer is None or not self._canvas_items:
            return

        level = step.get("level", 0)
        source_block = step.get("block", 0)
        source_pos = self._block_positions.get(("index", level, source_block))
        if source_pos is None:
            return

        source_x, source_y = source_pos
        source_right = source_x + self._COLUMN_WIDTH
        source_mid_y = source_y + self._BLOCK_H / 2

        # Nivel > 1: el puntero va al bloque del nivel inferior.
        if level > 1:
            target_key = ("index", level - 1, pointer)
            target_pos = self._block_positions.get(target_key)
            label = f"→ B{pointer + 1} del nivel {level - 1}"
        else:
            # En primario el puntero es un bloque de datos. En secundario
            # apunta a la posición del registro, por lo que calculamos su bloque.
            if self._model.is_secondary(self._index_type):
                target_block = pointer // self._model.data_bfr if self._model.data_bfr else 0
                label = f"→ registro {pointer + 1:,} (B{target_block + 1})"
            else:
                target_block = pointer
                label = f"→ B{target_block + 1}"
            target_key = ("data", 0, target_block)
            target_pos = self._block_positions.get(target_key)

        if target_pos is not None:
            target_x, target_y = target_pos
            line = self._canvas.create_line(
                source_right,
                source_mid_y,
                target_x,
                target_y + self._BLOCK_H / 2,
                fill="#D97706",
                width=3,
                arrow=tk.LAST,
            )
            self._pointer_items.append(line)

        text = self._canvas.create_text(
            source_x + self._COLUMN_WIDTH / 2,
            source_y + self._BLOCK_H - 10,
            text=label,
            font=("Arial", 8, "bold"),
            fill="#B45309",
        )
        self._pointer_items.append(text)

    def _reset_visuals(self):
        for items in self._canvas_items.values():
            for item in items:
                self._canvas.itemconfigure(
                    item,
                    fill="#FFFFFF",
                    outline="#6B7280",
                    width=2,
                )

        for row in self._data_rows.values():
            for widget in row:
                widget.configure(
                    fg_color=("gray97", "gray13")
                )

        for item in self._pointer_items:
            try:
                self._canvas.delete(item)
            except Exception:
                pass
        self._pointer_items = []

    # ==========================================================
    # GUARDAR / CARGAR / LIMPIAR
    # ==========================================================

    # ==========================================================

    def _on_save(self):
        if self._model is None:
            self._show_error("No hay una estructura para guardar.")
            return

        payload = {
            "tipo": "indices_externos",
            "index_type": self._index_type,
            "mode": self._mode_var.get(),
            "records": self._model.records,
            "record_bytes": self._model.record_bytes,
            "index_record_bytes": self._model.index_record_bytes,
            "block_bytes": self._model.block_bytes,
            "storage_mb": self._model.storage_mb,
            "data": self._data,
        }

        save_json(self, payload, "Guardar índices externos")

    def _on_load(self):
        payload = load_json(self, "Cargar índices externos")
        if payload is None:
            return

        if payload.get("tipo") != "indices_externos":
            self._show_error("El archivo no corresponde a índices externos.")
            return

        try:
            values = (
                int(payload["records"]),
                int(payload["record_bytes"]),
                int(payload["index_record_bytes"]),
                int(payload["block_bytes"]),
                int(payload["storage_mb"]),
            )

            test_model = IndicesModel(*values)
            if not test_model.theoretical_within_storage():
                raise ValueError(
                    "La estructura guardada supera la capacidad configurada."
                )

            data = [int(x) for x in payload.get("data", [])]
            if len(data) > min(test_model.records, self._MAX_REAL_RECORDS):
                raise ValueError(
                    f"El archivo supera el máximo de {self._MAX_REAL_RECORDS:,} "
                    "registros reales permitidos."
                )

            self._records_entry.delete(0, "end")
            self._records_entry.insert(0, str(values[0]))
            self._record_len_entry.delete(0, "end")
            self._record_len_entry.insert(0, str(values[1]))
            self._index_len_entry.delete(0, "end")
            self._index_len_entry.insert(0, str(values[2]))
            self._block_size_entry.delete(0, "end")
            self._block_size_entry.insert(0, str(values[3]))
            self._storage_entry.delete(0, "end")
            self._storage_entry.insert(0, str(values[4]))

            mode = payload.get("mode")
            if mode in ("Aleatorio", "Manual"):
                self._mode_var.set(mode)
                self._mode_seg.set(mode)

            index_type = payload.get("index_type", "Índice Primario")
            if index_type not in _INDEX_TYPES:
                raise ValueError("Tipo de índice no válido.")

            self._index_type = index_type
            self._index_menu.set(index_type)
            self._model = test_model
            self._data = data
            self._model.data = list(data)

            self._render_all()
            self._status_label.configure(
                text="Estructura, datos y configuración cargados correctamente."
            )
            self._clear_error()

        except (ValueError, TypeError, KeyError) as exc:
            self._show_error(f"Archivo inválido: {exc}")

    def _on_clear(self):
        self._cancel_animation_only()
        self._model = None
        self._data = []
        self._value_entry.delete(0, "end")
        self._clear_error()
        self._status_label.configure(text="Estado: estructura limpiada.")
        self._show_placeholder()

    def _show_placeholder(self):
        if not hasattr(self, "_canvas"):
            return
        self._canvas.delete("all")
        self._canvas_items = {}
        self._canvas.configure(scrollregion=(0, 0, 1000, 600))
        self._canvas.create_text(
            40,
            80,
            anchor="w",
            text="Configura los parámetros y presiona «Construir Índices». ",
            font=("Arial", 14),
            fill="#666666",
        )
        self._canvas.create_text(
            40,
            110,
            anchor="w",
            text="La estructura se dibujará verticalmente, con los niveles de índice a la izquierda y los bloques de datos a la derecha.",
            font=("Arial", 11),
            fill="#888888",
        )

    def _show_error(self, msg):
        self._error_box.pack(fill="x", padx=10, pady=(0, 6))
        self._error_label.configure(text=msg)

    def _clear_error(self):
        self._error_label.configure(text="")
        self._error_box.pack_forget()

    def _on_speed_change(self, value):
        self._speed_label.configure(text=f"{int(value)} ms")

    def _set_controls_state(self, state):
        disabled = state == "disabled"
        widgets = (
            self._index_menu,
            self._mode_seg,
            self._records_entry,
            self._record_len_entry,
            self._index_len_entry,
            self._block_size_entry,
            self._storage_entry,
            self._btn_structure,
            self._btn_clear,
            self._value_entry,
            self._btn_add,
            self._btn_search,
            self._btn_delete,
            self._btn_reset,
            self._speed_slider,
            self._btn_save,
            self._btn_load,
        )
        for widget in widgets:
            widget.configure(state="disabled" if disabled else "normal")

    @staticmethod
    def _format_bytes(value):
        if value < 1024:
            return f"{value} B"
        if value < 1024 * 1024:
            return f"{value / 1024:.2f} KB"
        if value < 1024 * 1024 * 1024:
            return f"{value / (1024 * 1024):.2f} MB"
        return f"{value / (1024 * 1024 * 1024):.2f} GB"

    def destroy(self):
        self._cancel_animation_only()
        super().destroy()
        