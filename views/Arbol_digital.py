import customtkinter as ctk
from views.base_view import BaseView
from views.persistence import save_json, load_json
from views.Tree_canvas import build_scrollable_canvas, draw_tree, show_placeholder

_MAX_PHRASE = 200
_COLOR_DEFAULT = ("#BFDBFE", "#1D4ED8")
_COLOR_VISITING = ("#FB923C", "#9A3412")
_COLOR_FOUND = ("#4ADE80", "#166534")


def normalizar_frase(texto):
    texto = texto.strip().lower()
    if not texto:
        raise ValueError("Ingresa una palabra o frase.")
    for ch in texto:
        if ch != " " and not ("a" <= ch <= "z"):
            raise ValueError("Solo se permiten letras de la A a la Z y espacios.")
    return texto


def simbolo(ch):
    return "_" if ch == " " else ch


def codigo(ch):
    s = simbolo(ch)
    return 27 if s == "_" else ord(s) - ord("a") + 1


def bits(ch):
    return format(codigo(ch), "05b")


class _Node:
    __slots__ = ("key", "left", "right")

    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None


class ArbolDigitalView(BaseView):
    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(master, view_manager=view_manager,
                         title="Árbol Digital", **kwargs)
        self._phrase = ""
        self._data = []
        self._tree_root = None
        self._tree_items = {}
        self._anim_job = None
        self._is_animating = False
        self._insert_queue = []
        self._insert_index = 0
<<<<<<< HEAD
=======
        self._pending_action = None
        self._history_lines = []
>>>>>>> origin/2
        self._build_ui()

    def _build_ui(self):
        self.add_title("Árbol Digital")
        self.add_subtitle(
            "Una frase se separa carácter por carácter y cada carácter "
            "se representa con su código y 5 bits."
        )

        config = ctk.CTkFrame(
            self.content, corner_radius=12,
            fg_color=("gray92", "gray17"),
            border_width=2, border_color=("gray78", "gray30")
        )
        config.pack(fill="x", padx=10, pady=(0, 8))
        inner = ctk.CTkFrame(config, fg_color="transparent")
        inner.pack(padx=16, pady=14, fill="x")

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            row, text="Palabra o frase:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(0, 8))
        self._manual_entry = ctk.CTkEntry(
            row, height=34, placeholder_text="Ej: hola mundo",
            font=ctk.CTkFont(size=14)
        )
        self._manual_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._btn_generate = ctk.CTkButton(
            row, text="Añadir", width=110, height=34,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_generate
        )
        self._btn_generate.pack(side="left", padx=(0, 8))

        self._btn_clear = ctk.CTkButton(
            row, text="Limpiar", width=100, height=34,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            text_color=("black", "white"),
            command=self._on_clear
        )
        self._btn_clear.pack(side="left")

        self._btn_save = ctk.CTkButton(
            row, text="Guardar", width=100, height=34,
            command=self._on_save
        )
        self._btn_save.pack(side="right", padx=(8, 0))

        self._btn_load = ctk.CTkButton(
            row, text="Cargar", width=100, height=34,
            command=self._on_load
        )
        self._btn_load.pack(side="right")

        search = ctk.CTkFrame(
            self.content, corner_radius=12,
            fg_color=("gray92", "gray17"),
            border_width=2, border_color=("gray78", "gray30")
        )
        search.pack(fill="x", padx=10, pady=(0, 8))
        si = ctk.CTkFrame(search, fg_color="transparent")
        si.pack(padx=16, pady=12, fill="x")

        sr = ctk.CTkFrame(si, fg_color="transparent")
        sr.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            sr, text="Carácter a buscar:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(0, 8))

        self._search_entry = ctk.CTkEntry(
            sr, width=120, height=34,
            placeholder_text="Ej: h",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        self._search_entry.pack(side="left", padx=(0, 10))

        self._btn_search = ctk.CTkButton(
            sr, text="Buscar", width=100, height=34,
            command=self._on_search
        )
        self._btn_search.pack(side="left", padx=(0, 8))

<<<<<<< HEAD
=======
        self._btn_delete = ctk.CTkButton(
            sr, text="Eliminar", width=100, height=34,
            fg_color="#C62828", hover_color="#8E0000",
            text_color="white", command=self._on_delete
        )
        self._btn_delete.pack(side="left", padx=(0, 8))

>>>>>>> origin/2
        self._btn_reset = ctk.CTkButton(
            sr, text="Reiniciar", width=110, height=34,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            text_color=("black", "white"),
            command=self._on_reset_search
        )
        self._btn_reset.pack(side="left")

        sr2 = ctk.CTkFrame(si, fg_color="transparent")
        sr2.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            sr2, text="Velocidad (ms):",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=(0, 8))
        self._speed_slider = ctk.CTkSlider(
            sr2, from_=100, to=2000,
            number_of_steps=19, width=180,
            command=self._on_speed_change
        )
        self._speed_slider.set(500)
        self._speed_slider.pack(side="left", padx=(0, 8))
        self._speed_label = ctk.CTkLabel(
            sr2, text="500 ms", width=65
        )
        self._speed_label.pack(side="left")

        box = ctk.CTkFrame(
            si, corner_radius=8,
            fg_color=("gray85", "gray22"),
            border_width=1, border_color=("gray75", "gray35")
        )
        box.pack(fill="x", pady=(4, 0))
        self._status_label = ctk.CTkLabel(
            box, text="Estado: listo.",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w", padx=12, pady=8
        )
        self._status_label.pack(fill="x")

        self._error_box = ctk.CTkFrame(
            self.content, corner_radius=8,
            fg_color=("#FEE2E2", "#450A0A"),
            border_width=1, border_color=("#FCA5A5", "#7F1D1D")
        )
        self._error_label = ctk.CTkLabel(
            self._error_box, text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w", padx=12, pady=6
        )
        self._error_label.pack(fill="x")
        self._error_box.pack_forget()

<<<<<<< HEAD
        container, self._canvas = build_scrollable_canvas(self.content)
        container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
=======
        workspace = ctk.CTkFrame(self.content, fg_color="transparent")
        workspace.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        tree_container, self._canvas = build_scrollable_canvas(workspace)
        tree_container.pack(side="left", fill="both", expand=True, padx=(0, 8))

        sidebar = ctk.CTkFrame(
            workspace, width=300, corner_radius=12,
            fg_color=("gray92", "gray17"),
            border_width=2, border_color=("gray78", "gray30")
        )
        sidebar.pack(side="right", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(
            sidebar, text="Tabla de caracteres",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
        ).pack(fill="x", padx=10, pady=(10, 6))
        self._table_frame = ctk.CTkScrollableFrame(
            sidebar, height=210, fg_color="transparent"
        )
        self._table_frame.pack(fill="x", padx=8, pady=(0, 8))

        ctk.CTkLabel(
            sidebar, text="Historial de construcción y búsqueda",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w"
        ).pack(fill="x", padx=10, pady=(4, 6))
        self._history_box = ctk.CTkTextbox(
            sidebar, height=220, font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self._history_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._history_box.configure(state="disabled")

>>>>>>> origin/2
        self._show_placeholder()

    def _show_error(self, msg):
        self._error_box.pack(fill="x", padx=20, pady=(0, 4))
        self._error_label.configure(text=msg)

    def _clear_error(self):
        self._error_label.configure(text="")
        self._error_box.pack_forget()

    def _on_speed_change(self, value):
        self._speed_label.configure(text=f"{int(value)} ms")

    def _set_controls(self, disabled):
        state = "disabled" if disabled else "normal"
        for widget in (
            self._manual_entry, self._btn_generate, self._btn_clear,
            self._btn_save, self._btn_load, self._search_entry,
<<<<<<< HEAD
            self._btn_search, self._btn_reset
=======
            self._btn_search, self._btn_delete, self._btn_reset
>>>>>>> origin/2
        ):
            widget.configure(state=state)

    def _on_generate(self):
        if self._is_animating:
            return
        if self._phrase:
            self._show_error(
                "Ya existe una frase en este árbol. Presiona Limpiar para ingresar otra."
            )
            return

        try:
            phrase = normalizar_frase(self._manual_entry.get())
        except ValueError as exc:
            self._show_error(str(exc))
            return

        if len(phrase) > _MAX_PHRASE:
            self._show_error(
                f"La frase no puede superar {_MAX_PHRASE} caracteres."
            )
            return

        self._phrase = phrase
        self._data = [simbolo(ch) for ch in phrase]
        self._tree_root = None
        self._insert_queue = list(self._data)
        self._insert_index = 0
<<<<<<< HEAD
=======
        self._clear_history()
>>>>>>> origin/2
        self._manual_entry.delete(0, "end")
        self._clear_error()
        self._set_controls(True)
        self._is_animating = True
        self._animate_insert()

    def _animate_insert(self):
        if not self._is_animating:
            return

        if self._insert_index >= len(self._insert_queue):
            self._is_animating = False
            self._set_controls(False)
            self._status_label.configure(
                text=f"Árbol construido. Frase: {self._phrase}"
            )
            return

        ch = self._insert_queue[self._insert_index]
        self._insert_character(ch)
        self._render_tree()
<<<<<<< HEAD

        code = codigo(" " if ch == "_" else ch)
        binary = bits(" " if ch == "_" else ch)
        self._status_label.configure(
            text=(
                f"Paso {self._insert_index + 1}/{len(self._insert_queue)}: "
                f"carácter «{ch}» | código {code} | binario {binary}"
            )
        )
=======
        self._refresh_character_table(self._insert_index + 1)

        code = codigo(" " if ch == "_" else ch)
        binary = bits(" " if ch == "_" else ch)
        message = (
            f"Paso {self._insert_index + 1}/{len(self._insert_queue)}: "
            f"carácter «{ch}» | código {code} | binario {binary}"
        )
        self._status_label.configure(text=message)
        self._add_history(message)
>>>>>>> origin/2

        self._insert_index += 1
        self._anim_job = self.after(
            int(self._speed_slider.get()), self._animate_insert
        )

    def _insert_character(self, ch):
        if self._tree_root is None:
            self._tree_root = _Node(ch)
            return

        # Árbol Digital: se toma el bit según la profundidad actual.
        node = self._tree_root
        if node.key == ch:
            return

        binary = bits(" " if ch == "_" else ch)
        depth = 0
        while depth < len(binary):
            bit = binary[depth]
            if bit == "0":
                if node.left is None:
                    node.left = _Node(ch)
                    return
                node = node.left
            else:
                if node.right is None:
                    node.right = _Node(ch)
                    return
                node = node.right

            if node.key == ch:
                return
            depth += 1

        raise ValueError("No fue posible ubicar el carácter en el árbol.")

    def _get_children(self, node):
        return [node.left, node.right]

    def _get_label(self, node):
        return " " if node.key == "_" else node.key

    def _get_style(self, node):
        return _COLOR_DEFAULT

    def _iter_children_with_label(self, node):
        return [("0", node.left), ("1", node.right)]

    def _render_tree(self):
        self._tree_items = draw_tree(
            self._canvas, self._tree_root,
            self._get_children, self._get_label,
            self._get_style, radius=28
        )
        self._draw_branch_labels()
<<<<<<< HEAD
=======
        self._draw_level_labels()


    def _draw_level_labels(self):
        self._canvas.delete("level_labels")
        seen = set()
        def walk(node, depth):
            if node is None:
                return
            items = self._tree_items.get(id(node))
            if items and depth not in seen:
                self._canvas.create_text(
                    18, items["y"], text=f"Nivel {depth}",
                    font=("Consolas", 10, "bold"), fill="#64748B",
                    anchor="w", tags="level_labels"
                )
                seen.add(depth)
            walk(node.left, depth + 1)
            walk(node.right, depth + 1)
        walk(self._tree_root, 0)
>>>>>>> origin/2

    def _draw_branch_labels(self):
        self._canvas.delete("branch_bits")
        for node in self._walk_nodes(self._tree_root):
            items = self._tree_items.get(id(node))
            if not items:
                continue
            for label, child in self._iter_children_with_label(node):
                if child is None:
                    continue
                citems = self._tree_items.get(id(child))
                if not citems:
                    continue
                x = (items["x"] + citems["x"]) / 2
                y = (items["y"] + citems["y"]) / 2 - 10
                self._canvas.create_text(
                    x, y, text=label,
                    font=("Consolas", 12, "bold"),
                    fill="#334155", tags="branch_bits"
                )

    def _walk_nodes(self, node):
        if node is None:
            return
        yield node
        yield from self._walk_nodes(node.left)
        yield from self._walk_nodes(node.right)

    def _show_placeholder(self):
        self._tree_items = {}
        show_placeholder(
            self._canvas,
            "Escribe una palabra o frase y presiona «Añadir»."
        )

<<<<<<< HEAD
=======
    def _clear_history(self):
        self._history_lines = []
        self._history_box.configure(state="normal")
        self._history_box.delete("1.0", "end")
        self._history_box.configure(state="disabled")

    def _add_history(self, text):
        self._history_lines.append(text)
        self._history_box.configure(state="normal")
        self._history_box.insert("end", text + "\n")
        self._history_box.see("end")
        self._history_box.configure(state="disabled")

    def _refresh_character_table(self, upto=None):
        for w in self._table_frame.winfo_children():
            w.destroy()
        chars = self._data if upto is None else self._data[:upto]
        for idx, ch in enumerate(chars, 1):
            disp = "espacio" if ch == "_" else ch
            code = codigo(" " if ch == "_" else ch)
            binary = bits(" " if ch == "_" else ch)
            row = ctk.CTkFrame(self._table_frame, height=28, corner_radius=5,
                               fg_color=("gray88", "gray22") if idx % 2 else ("gray94", "gray17"))
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=str(idx), width=28, font=ctk.CTkFont(size=11), anchor="center").pack(side="left")
            ctk.CTkLabel(row, text=disp, width=58, font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=str(code), width=42, font=ctk.CTkFont(family="Consolas", size=11), anchor="center").pack(side="left")
            ctk.CTkLabel(row, text=binary, font=ctk.CTkFont(family="Consolas", size=11), anchor="w").pack(side="left")

>>>>>>> origin/2
    def _get_target(self):
        raw = self._search_entry.get().lower()
        if raw == " ":
            return "_"
        raw = raw.strip()
        if not raw:
            self._show_error("Ingresa un carácter.")
            return None
        if len(raw) != 1 or not ("a" <= raw <= "z"):
            self._show_error(
                "La búsqueda admite una sola letra o un espacio."
            )
            return None
        return raw

<<<<<<< HEAD
=======
    def _on_delete(self):
        if self._is_animating or self._tree_root is None:
            return
        target = self._get_target()
        if target is None:
            return
        self._pending_action = "delete"
        self._begin_search(target)

>>>>>>> origin/2
    def _on_search(self):
        if self._is_animating:
            return
        if self._tree_root is None:
            self._show_error("Primero construye el árbol.")
            return
        target = self._get_target()
        if target is None:
            return

        self._cancel_animation()
<<<<<<< HEAD
=======
        self._pending_action = "search"
>>>>>>> origin/2
        self._render_tree()
        self._clear_error()
        self._set_controls(True)
        self._is_animating = True

        target_bits = bits(" " if target == "_" else target)
        self._search_recursive(
            self._tree_root, target, target_bits, 0
        )

    def _search_recursive(self, node, target, target_bits, depth):
        if not self._is_animating:
            return
        if node is None:
            self._is_animating = False
            self._set_controls(False)
            self._status_label.configure(
                text=(
                    f"El carácter «{target}» no fue encontrado. "
                    f"Código: {codigo(' ' if target == '_' else target)} | "
                    f"Binario: {target_bits}"
                )
            )
            return

        items = self._tree_items.get(id(node))
        if items:
            self._canvas.itemconfig(
                items["oval"],
                fill=_COLOR_VISITING[0],
                outline=_COLOR_VISITING[1]
            )

        if node.key == target:
            if items:
                self._canvas.itemconfig(
                    items["oval"],
                    fill=_COLOR_FOUND[0],
                    outline=_COLOR_FOUND[1]
                )
<<<<<<< HEAD
            self._is_animating = False
            self._set_controls(False)
            self._status_label.configure(
                text=(
                    f"Encontrado: «{target}» | "
                    f"Código: {codigo(' ' if target == '_' else target)} | "
                    f"Binario: {target_bits}"
                )
            )
=======
            code = codigo(" " if target == "_" else target)
            if self._pending_action == "delete":
                self._status_label.configure(
                    text=f"Encontrado: «{target}» | Código: {code} | Binario: {target_bits} | Eliminando..."
                )
                self._add_history(f"Eliminación: encontrado «{target}» en nivel {depth}.")
                self._anim_job = self.after(int(self._speed_slider.get()), lambda: self._finish_delete(target))
                return
            self._is_animating = False
            self._set_controls(False)
            self._status_label.configure(
                text=f"Encontrado: «{target}» | Código: {code} | Binario: {target_bits} | Nivel {depth}"
            )
            self._add_history(f"Búsqueda: «{target}» encontrado en nivel {depth}.")
            self._pending_action = None
>>>>>>> origin/2
            return

        if depth >= len(target_bits):
            self._is_animating = False
            self._set_controls(False)
            self._status_label.configure(
                text=f"El carácter «{target}» no fue encontrado."
            )
            return

        bit = target_bits[depth]
        direction = "izquierda" if bit == "0" else "derecha"
        self._status_label.configure(
            text=(
<<<<<<< HEAD
                f"Paso {depth + 1}: nodo «{node.key}» | bit {bit} | "
=======
                f"Paso {depth + 1}: nodo «{node.key}» | nivel {depth} | bit {bit} | "
>>>>>>> origin/2
                f"avanzo a {direction}"
            )
        )
        next_node = node.left if bit == "0" else node.right
        self._anim_job = self.after(
            int(self._speed_slider.get()),
            lambda: self._search_recursive(
                next_node, target, target_bits, depth + 1
            )
        )

<<<<<<< HEAD
=======
    def _finish_delete(self, target):
        self._phrase = "".join(ch for ch in self._phrase if simbolo(ch) != target)
        self._data = [simbolo(ch) for ch in self._phrase]
        self._tree_root = None
        for ch in self._data:
            self._insert_character(ch)
        self._render_tree()
        self._refresh_character_table()
        self._history_box.configure(state="normal")
        self._history_box.insert("end", f"Eliminado: «{target}».\n")
        self._history_box.see("end")
        self._history_box.configure(state="disabled")
        self._status_label.configure(text=f"El carácter «{target}» fue eliminado correctamente. Nivel actualizado en el árbol.")
        self._is_animating = False
        self._pending_action = None
        self._set_controls(False)

>>>>>>> origin/2
    def _on_reset_search(self):
        self._cancel_animation()
        if self._tree_root is not None:
            self._render_tree()
        self._set_controls(False)
        self._clear_error()
        self._status_label.configure(
            text="Estado: búsqueda reiniciada. Listo para buscar."
        )

    def _cancel_animation(self):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
        self._anim_job = None
        self._is_animating = False

    def _on_clear(self):
        self._cancel_animation()
        self._phrase = ""
        self._data.clear()
        self._tree_root = None
        self._insert_queue = []
        self._insert_index = 0
<<<<<<< HEAD
=======
        self._clear_history()
>>>>>>> origin/2
        self._manual_entry.delete(0, "end")
        self._clear_error()
        self._status_label.configure(text="Estado: árbol limpiado.")
        self._show_placeholder()
        self._set_controls(False)

    def _on_save(self):
        if not self._phrase:
            self._show_error("No hay una frase para guardar.")
            return
        save_json(
            self,
            {"tipo": "arbol_digital_frase", "frase": self._phrase},
            "Guardar árbol digital"
        )

    def _on_load(self):
        payload = load_json(self, "Cargar árbol digital")
        if payload is None:
            return
        if (
            payload.get("tipo") != "arbol_digital_frase"
            or not isinstance(payload.get("frase"), str)
        ):
            self._show_error(
                "El archivo no corresponde a un árbol digital de frases válido."
            )
            return
        self._on_clear()
        self._manual_entry.insert(0, payload["frase"])
        self._on_generate()

    def destroy(self):
        self._cancel_animation()
<<<<<<< HEAD
        super().destroy()
=======
        super().destroy()
>>>>>>> origin/2
