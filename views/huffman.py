import heapq
from collections import Counter
import tkinter as tk
import customtkinter as ctk

from views.base_view import BaseView
from views.persistence import save_json, load_json
from views.Tree_canvas import build_scrollable_canvas, draw_tree, show_placeholder

_COLOR_LEAF = ("#DCFCE7", "#15803D")
_COLOR_INTERNAL = ("#F1F5F9", "#475569")

def format_char(ch: str) -> str:
    """Devuelve una representación legible para caracteres especiales como espacios."""
    if ch == " ":
        return "␣ (Espacio)"
    elif ch == "\n":
        return "\\n (Enter)"
    elif ch == "\t":
        return "\\t (Tab)"
    return ch

def format_char_short(ch: str) -> str:
    """Devuelve un formato muy corto para mostrar dentro del círculo del nodo."""
    if ch == " ":
        return "␣"
    elif ch == "\n":
        return "\\n"
    elif ch == "\t":
        return "\\t"
    return ch

class HuffmanNode:
    """Nodo para el Árbol de Huffman."""
    __slots__ = ("char", "freq", "left", "right")

    def __init__(self, char: str | None, freq: int, left=None, right=None):
        self.char = char  # None si es un nodo interno
        self.freq = freq  # Frecuencia acumulada
        self.left = left
        self.right = right

class HuffmanView(BaseView):
    """Vista interactiva para construcción y visualización de Árboles de Huffman."""

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Árboles de Huffman",
            **kwargs,
        )
        self._message = ""
        self._tree_root: HuffmanNode | None = None
        self._codes: dict[str, str] = {}
        self._frequencies: dict[str, int] = {}
        self._tree_items = {}

        self._build_ui()

    def _build_ui(self):
        self.add_title("Árboles de Huffman")
        self.add_subtitle(
            "Algoritmo de compresión basado en frecuencia de caracteres. "
            "Construye un árbol binario óptimo asignando códigos de prefijo de longitud variable."
        )

        config = ctk.CTkFrame(
            self.content,
            corner_radius=12,
            fg_color=("gray92", "gray17"),
            border_width=2,
            border_color=("gray78", "gray30"),
        )
        config.pack(fill="x", padx=10, pady=(0, 8))

        inner = ctk.CTkFrame(config, fg_color="transparent")
        inner.pack(padx=16, pady=12, fill="x")

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x")

        ctk.CTkLabel(
            row,
            text="Mensaje:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        self._manual_entry = ctk.CTkEntry(
            row,
            height=36,
            placeholder_text="Ingresa un mensaje o cadena de texto...",
            font=ctk.CTkFont(size=14),
        )
        self._manual_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._manual_entry.bind("<Return>", lambda e: self._on_build())

        self._btn_build = ctk.CTkButton(
            row,
            text="Construir Árbol de Huffman",
            height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_build,
        )
        self._btn_build.pack(side="left", padx=(0, 8))
        self._delete_entry = ctk.CTkEntry(row, width=80, height=36, placeholder_text="Carácter", font=ctk.CTkFont(size=13))
        self._delete_entry.pack(side="left", padx=(0, 6))
        self._btn_delete = ctk.CTkButton(row, text="Eliminar", width=90, height=36, fg_color="#C62828", hover_color="#8E0000", text_color="white", command=self._on_delete)
        self._btn_delete.pack(side="left", padx=(0, 8))

        self._btn_clear = ctk.CTkButton(
            row,
            text="Limpiar",
            width=90,
            height=36,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            text_color=("black", "white"),
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_clear,
        )
        self._btn_clear.pack(side="left", padx=(0, 8))

        self._btn_save = ctk.CTkButton(
            row,
            text="Guardar",
            width=90,
            height=36,
            command=self._on_save,
        )
        self._btn_save.pack(side="right", padx=(6, 0))

        self._btn_load = ctk.CTkButton(
            row,
            text="Cargar",
            width=90,
            height=36,
            command=self._on_load,
        )
        self._btn_load.pack(side="right")

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

        main_container = ctk.CTkFrame(self.content, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        main_container.grid_columnconfigure(0, weight=3)
        main_container.grid_columnconfigure(1, weight=2)
        main_container.grid_rowconfigure(0, weight=1)

        # Izquierda: Lienzo desplazable del árbol
        tree_frame, self._canvas = build_scrollable_canvas(main_container)
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        # Derecha: Sidebar con Frecuencias, Códigos y Estadísticas
        sidebar = ctk.CTkScrollableFrame(
            main_container,
            corner_radius=12,
            fg_color=("gray96", "gray14"),
            border_width=2,
            border_color=("gray78", "gray30"),
            label_text="Panel de Codificación de Huffman",
            label_font=ctk.CTkFont(size=14, weight="bold"),
        )
        sidebar.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        # --- Sub-sección 1: Tabla de Frecuencias y Códigos ---
        ctk.CTkLabel(
            sidebar,
            text="Tabla de Caracteres y Códigos Binarios",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=10, pady=(10, 6))

        self._table_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        self._table_frame.pack(fill="x", padx=10, pady=(0, 12))

        # --- Sub-sección 2: Mensaje Codificado ---
        ctk.CTkLabel(
            sidebar,
            text="Mensaje Codificado en Bits:",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=10, pady=(6, 4))

        self._encoded_textbox = ctk.CTkTextbox(
            sidebar,
            height=85,
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=8,
            wrap="word",
        )
        self._encoded_textbox.pack(fill="x", padx=10, pady=(0, 6))

        encoded_btn_row = ctk.CTkFrame(sidebar, fg_color="transparent")
        encoded_btn_row.pack(fill="x", padx=10, pady=(0, 12))

        self._btn_copy = ctk.CTkButton(
            encoded_btn_row,
            text="Copiar Bits",
            width=110,
            height=28,
            font=ctk.CTkFont(size=12),
            command=self._on_copy_bits,
        )
        self._btn_copy.pack(side="right")

        # --- Sub-sección 3: Estadísticas de Compresión ---
        ctk.CTkLabel(
            sidebar,
            text="Estadísticas de Compresión",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=10, pady=(6, 6))

        self._stats_card = ctk.CTkFrame(
            sidebar,
            corner_radius=8,
            fg_color=("gray90", "gray20"),
            border_width=1,
            border_color=("gray80", "gray30"),
        )
        self._stats_card.pack(fill="x", padx=10, pady=(0, 10))

        self._stats_label = ctk.CTkLabel(
            self._stats_card,
            text="Ingresa un mensaje para ver las estadísticas.",
            font=ctk.CTkFont(size=12),
            justify="left",
            anchor="w",
            padx=12,
            pady=10,
        )
        self._stats_label.pack(fill="x")

        self._show_placeholder()

    def _show_error(self, msg: str):
        self._error_box.pack(fill="x", padx=20, pady=(0, 4))
        self._error_label.configure(text=f"{msg}")

    def _clear_error(self):
        self._error_label.configure(text="")
        self._error_box.pack_forget()

    def _show_placeholder(self):
        self._tree_items = {}
        show_placeholder(
            self._canvas,
            "Ingresa una cadena o mensaje arriba y presiona «Construir Árbol de Huffman»."
        )
        self._render_empty_sidebar()

    def _render_empty_sidebar(self):
        for child in self._table_frame.winfo_children():
            child.destroy()

        ctk.CTkLabel(
            self._table_frame,
            text="Sin datos generados.",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray55"),
        ).pack(pady=10)

        self._encoded_textbox.configure(state="normal")
        self._encoded_textbox.delete("1.0", "end")
        self._encoded_textbox.configure(state="disabled")

        self._stats_label.configure(
            text="Sin estadísticas disponibles.",
            text_color=("gray50", "gray55"),
        )

    def _build_huffman_tree(self, text: str) -> tuple[HuffmanNode | None, dict[str, str], dict[str, int]]:
        if not text:
            return None, {}, {}

        freqs = Counter(text)

        # Caso especial: solo un carácter único en todo el mensaje
        if len(freqs) == 1:
            char, freq = next(iter(freqs.items()))
            leaf = HuffmanNode(char, freq)
            root = HuffmanNode(None, freq, left=leaf, right=None)
            codes = {char: "0"}
            return root, codes, dict(freqs)

        # Min-heap para construir el árbol
        heap = []
        count = 0
        for char, freq in freqs.items():
            node = HuffmanNode(char, freq)
            heapq.heappush(heap, (freq, count, node))
            count += 1

        while len(heap) > 1:
            freq1, _, left = heapq.heappop(heap)
            freq2, _, right = heapq.heappop(heap)

            parent = HuffmanNode(None, freq1 + freq2, left=left, right=right)
            heapq.heappush(heap, (parent.freq, count, parent))
            count += 1

        root = heap[0][2]
        codes = {}

        def generate_codes(node: HuffmanNode | None, current_code: str = ""):
            if node is None:
                return
            if node.char is not None:
                codes[node.char] = current_code or "0"
                return
            generate_codes(node.left, current_code + "0")
            generate_codes(node.right, current_code + "1")

        generate_codes(root)
        return root, codes, dict(freqs)

    def _on_build(self):
        self._clear_error()
        raw_text = self._manual_entry.get()

        if not raw_text:
            self._show_error("El campo de mensaje está vacío. Ingresa algún texto.")
            return

        self._message = raw_text
        self._tree_root, self._codes, self._frequencies = self._build_huffman_tree(self._message)

        # Renderizar Árbol en el Canvas
        self._render_tree()

        # Renderizar Sidebar (Tabla, Bits, Stats)
        self._render_sidebar()

    def _on_delete(self):
        if not self._message:
            self._show_error("Primero construye un árbol de Huffman.")
            return
        target=self._delete_entry.get()
        if len(target)!=1:
            self._show_error("Ingresa un solo carácter para eliminar.")
            return
        if target not in self._message:
            self._show_error(f"El carácter «{target}» no existe en el mensaje.")
            return
        self._message=self._message.replace(target, "")
        if not self._message:
            self._on_clear(); return
        self._tree_root, self._codes, self._frequencies = self._build_huffman_tree(self._message)
        self._render_tree(); self._render_sidebar()
        self._delete_entry.delete(0, "end")
        self._clear_error()

    def _on_clear(self):
        self._message = ""
        self._tree_root = None
        self._codes = {}
        self._frequencies = {}
        self._manual_entry.delete(0, "end")
        self._clear_error()
        self._show_placeholder()

    def _on_copy_bits(self):
        bits_text = self._encoded_textbox.get("1.0", "end-1c").strip()
        if bits_text:
            self.clipboard_clear()
            self.clipboard_append(bits_text)

    def _get_children(self, node: HuffmanNode):
        if node is None or (node.left is None and node.right is None):
            return []
        return [node.left, node.right]

    def _get_label(self, node: HuffmanNode) -> str:
        if node.char is not None:
            # Nodo Hoja: mostrar carácter y frecuencia
            ch_str = format_char_short(node.char)
            return f"'{ch_str}'\n{node.freq}"
        # Nodo Interno: mostrar solo la frecuencia acumulada
        return str(node.freq)

    def _get_style(self, node: HuffmanNode) -> tuple[str, str]:
        if node.char is not None:
            return _COLOR_LEAF
        return _COLOR_INTERNAL

    def _render_tree(self):
        self._tree_items = draw_tree(
            self._canvas,
            self._tree_root,
            self._get_children,
            self._get_label,
            self._get_style,
            radius=26,
            unit_gap=64,
            level_height=85,
        )
        self._draw_branch_labels()
        self._draw_level_labels()

    def _draw_level_labels(self):
        self._canvas.delete("level_labels")
        seen=set()
        def walk(node, depth):
            if node is None:return
            items=self._tree_items.get(id(node))
            if items and depth not in seen:
                self._canvas.create_text(18, items["y"], text=f"Nivel {depth}", font=("Consolas",10,"bold"), fill="#64748B", anchor="w", tags="level_labels")
                seen.add(depth)
            walk(node.left, depth+1); walk(node.right, depth+1)
        walk(self._tree_root,0)

    def _draw_branch_labels(self):
        self._canvas.delete("branch_bits")
        for node in self._walk_nodes(self._tree_root):
            items = self._tree_items.get(id(node))
            if not items:
                continue
            if node.left is not None:
                citems = self._tree_items.get(id(node.left))
                if citems:
                    x = (items["x"] + citems["x"]) / 2 - 9
                    y = (items["y"] + citems["y"]) / 2 - 2
                    self._canvas.create_text(
                        x,
                        y,
                        text="0",
                        font=("Consolas", 12, "bold"),
                        fill="#2563EB",
                        tags="branch_bits",
                    )
            if node.right is not None:
                citems = self._tree_items.get(id(node.right))
                if citems:
                    x = (items["x"] + citems["x"]) / 2 + 9
                    y = (items["y"] + citems["y"]) / 2 - 2
                    self._canvas.create_text(
                        x,
                        y,
                        text="1",
                        font=("Consolas", 12, "bold"),
                        fill="#DC2626",
                        tags="branch_bits",
                    )

    def _walk_nodes(self, node: HuffmanNode | None):
        if node is None:
            return
        yield node
        yield from self._walk_nodes(node.left)
        yield from self._walk_nodes(node.right)

    def _render_sidebar(self):
        for child in self._table_frame.winfo_children():
            child.destroy()

        if not self._codes:
            return

        # 1. Cabecera de la Tabla
        header = ctk.CTkFrame(self._table_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(header, text="Carácter", width=90, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(side="left", padx=4)
        ctk.CTkLabel(header, text="Freq.", width=50, font=ctk.CTkFont(size=12, weight="bold"), anchor="center").pack(side="left", padx=4)
        ctk.CTkLabel(header, text="Código", width=90, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(side="left", padx=4)

        # Ordenar por frecuencia descendente
        sorted_chars = sorted(self._frequencies.keys(), key=lambda c: self._frequencies[c], reverse=True)

        for idx, char in enumerate(sorted_chars):
            freq = self._frequencies[char]
            code = self._codes.get(char, "")

            bg = ("gray88", "gray22") if idx % 2 == 0 else ("gray94", "gray17")
            row = ctk.CTkFrame(self._table_frame, height=32, corner_radius=6, fg_color=bg)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            char_disp = format_char(char)
            ctk.CTkLabel(row, text=char_disp, width=90, font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), anchor="w").pack(side="left", padx=8)
            ctk.CTkLabel(row, text=str(freq), width=50, font=ctk.CTkFont(family="Consolas", size=12), anchor="center").pack(side="left", padx=4)
            ctk.CTkLabel(row, text=code, width=90, font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color=("#2563EB", "#60A5FA"), anchor="w").pack(side="left", padx=4)

        # 2. Cadena Codificada
        encoded_bits = "".join(self._codes[ch] for ch in self._message)
        self._encoded_textbox.configure(state="normal")
        self._encoded_textbox.delete("1.0", "end")
        self._encoded_textbox.insert("1.0", encoded_bits)
        self._encoded_textbox.configure(state="disabled")

        # 3. Estadísticas de Compresión
        orig_bits = len(self._message) * 8
        huffman_bits = len(encoded_bits)
        saving_pct = (1.0 - (huffman_bits / max(1, orig_bits))) * 100.0

        stats_text = (
            f"• Longitud del texto: {len(self._message)} caracteres\n"
            f"• Tamaño ASCII (8 bits/char): {orig_bits} bits\n"
            f"• Tamaño Huffman: {huffman_bits} bits\n"
            f"• Ahorro de espacio: {saving_pct:.1f}%"
        )
        self._stats_label.configure(
            text=stats_text,
            text_color=("gray10", "gray90"),
        )

    def _on_save(self):
        if not self._message:
            self._show_error("No hay ningún mensaje para guardar.")
            return

        payload = {
            "tipo": "arbol_huffman",
            "mensaje": self._message,
        }
        save_json(self, payload, "Guardar Árbol de Huffman")

    def _on_load(self):
        payload = load_json(self, "Cargar Árbol de Huffman")
        if payload is None:
            return

        if payload.get("tipo") != "arbol_huffman" or not isinstance(payload.get("mensaje"), str):
            self._show_error("El archivo cargado no corresponde a un árbol de Huffman válido.")
            return

        self._on_clear()
        self._manual_entry.insert(0, payload["mensaje"])
        self._on_build()

