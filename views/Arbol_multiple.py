import customtkinter as ctk
from views.base_view import BaseView
from views.persistence import save_json, load_json
from views.Tree_canvas import build_scrollable_canvas, draw_tree, show_placeholder

_MAX_PHRASE = 200
_BITS_OPTIONS = {"Base 4 (2 bits)": 2, "Base 8 (3 bits)": 3}
_COLOR_LEAF = ("#DDD6FE", "#5B21B6")
_COLOR_INTERNAL = ("#E2E8F0", "#64748B")
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


class _Leaf:
    __slots__ = ("key",)
    def __init__(self, key):
        self.key = key


class _Internal:
    __slots__ = ("children",)
    def __init__(self, arity):
        self.children = [None] * arity


class ArbolMultipleView(BaseView):
    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(master, view_manager=view_manager,
                         title="Residuos Múltiples", **kwargs)
        self._phrase = ""
        self._data = []
        self._tree_root = None
        self._bits_per_level = 2
        self._padded_bit_length = 6
        self._num_levels = 3
        self._tree_items = {}
        self._anim_job = None
        self._is_animating = False
        self._insert_queue = []
        self._insert_index = 0
        self._bits_var = ctk.StringVar(value="Base 4 (2 bits)")
        self._build_ui()

    def _build_ui(self):
        self.add_title("Árbol de Residuos Múltiples")
        self.add_subtitle(
            "Cada carácter de la frase se transforma a un código de 5 bits "
            "y los bits se agrupan según la base seleccionada."
        )

        config = ctk.CTkFrame(
            self.content, corner_radius=12,
            fg_color=("gray92","gray17"),
            border_width=2, border_color=("gray78","gray30")
        )
        config.pack(fill="x", padx=10, pady=(0,8))
        inner = ctk.CTkFrame(config, fg_color="transparent")
        inner.pack(padx=16, pady=14, fill="x")

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(0,10))
        ctk.CTkLabel(
            row, text="Palabra o frase:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(0,8))
        self._manual_entry = ctk.CTkEntry(
            row, height=34, placeholder_text="Ej: hola mundo",
            font=ctk.CTkFont(size=14)
        )
        self._manual_entry.pack(side="left", fill="x", expand=True, padx=(0,8))

        ctk.CTkLabel(
            row, text="Base:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(4,8))
        self._bits_seg = ctk.CTkSegmentedButton(
            row, values=list(_BITS_OPTIONS.keys()),
            variable=self._bits_var, font=ctk.CTkFont(size=12)
        )
        self._bits_seg.pack(side="left", padx=(0,8))

        self._btn_generate = ctk.CTkButton(
            row, text="Añadir", width=110, height=34,
            command=self._on_generate
        )
        self._btn_generate.pack(side="left", padx=(0,8))
        self._btn_clear = ctk.CTkButton(
            row, text="Limpiar", width=100, height=34,
            fg_color=("gray70","gray30"),
            hover_color=("gray60","gray40"),
            text_color=("black","white"),
            command=self._on_clear
        )
        self._btn_clear.pack(side="left")
        self._btn_save = ctk.CTkButton(
            row, text="Guardar", width=100, height=34,
            command=self._on_save
        )
        self._btn_save.pack(side="right", padx=(8,0))
        self._btn_load = ctk.CTkButton(
            row, text="Cargar", width=100, height=34,
            command=self._on_load
        )
        self._btn_load.pack(side="right")

        search = ctk.CTkFrame(
            self.content, corner_radius=12,
            fg_color=("gray92","gray17"),
            border_width=2, border_color=("gray78","gray30")
        )
        search.pack(fill="x", padx=10, pady=(0,8))
        si = ctk.CTkFrame(search, fg_color="transparent")
        si.pack(padx=16, pady=12, fill="x")
        sr = ctk.CTkFrame(si, fg_color="transparent")
        sr.pack(fill="x", pady=(0,8))
        ctk.CTkLabel(
            sr, text="Carácter a buscar:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=(0,8))
        self._search_entry = ctk.CTkEntry(
            sr, width=120, height=34,
            placeholder_text="Ej: h",
            font=ctk.CTkFont(size=14), justify="center"
        )
        self._search_entry.pack(side="left", padx=(0,10))
        self._btn_search = ctk.CTkButton(
            sr, text="Buscar", width=100, height=34,
            command=self._on_search
        )
        self._btn_search.pack(side="left", padx=(0,8))
        self._btn_reset = ctk.CTkButton(
            sr, text="Reiniciar", width=110, height=34,
            fg_color=("gray70","gray30"),
            hover_color=("gray60","gray40"),
            text_color=("black","white"),
            command=self._on_reset_search
        )
        self._btn_reset.pack(side="left")

        sr2 = ctk.CTkFrame(si, fg_color="transparent")
        sr2.pack(fill="x", pady=(0,8))
        ctk.CTkLabel(
            sr2, text="Velocidad (ms):",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=(0,8))
        self._speed_slider = ctk.CTkSlider(
            sr2, from_=100, to=2000, number_of_steps=19,
            width=180, command=self._on_speed_change
        )
        self._speed_slider.set(500)
        self._speed_slider.pack(side="left", padx=(0,8))
        self._speed_label = ctk.CTkLabel(sr2, text="500 ms", width=65)
        self._speed_label.pack(side="left")

        box = ctk.CTkFrame(
            si, corner_radius=8,
            fg_color=("gray85","gray22"),
            border_width=1, border_color=("gray75","gray35")
        )
        box.pack(fill="x", pady=(4,0))
        self._status_label = ctk.CTkLabel(
            box, text="Estado: listo.",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w", padx=12, pady=8
        )
        self._status_label.pack(fill="x")
        self._error_box = ctk.CTkFrame(
            self.content, corner_radius=8,
            fg_color=("#FEE2E2","#450A0A"),
            border_width=1, border_color=("#FCA5A5","#7F1D1D")
        )
        self._error_label = ctk.CTkLabel(
            self._error_box, text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w", padx=12, pady=6
        )
        self._error_label.pack(fill="x")
        self._error_box.pack_forget()

        container, self._canvas = build_scrollable_canvas(self.content)
        container.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self._show_placeholder()

    def _show_error(self, msg):
        self._error_box.pack(fill="x", padx=20, pady=(0,4))
        self._error_label.configure(text=msg)

    def _clear_error(self):
        self._error_label.configure(text="")
        self._error_box.pack_forget()

    def _on_speed_change(self, value):
        self._speed_label.configure(text=f"{int(value)} ms")

    def _set_controls(self, disabled):
        state = "disabled" if disabled else "normal"
        for w in (
            self._manual_entry, self._btn_generate, self._btn_clear,
            self._btn_save, self._btn_load, self._bits_seg,
            self._search_entry, self._btn_search, self._btn_reset
        ):
            w.configure(state=state)

    def _arity(self):
        return 2 ** self._bits_per_level

    def _prepare_bits(self):
        raw_length = 5
        k = self._bits_per_level
        self._padded_bit_length = ((raw_length + k - 1) // k) * k
        self._num_levels = self._padded_bit_length // k

    def _digits(self, ch):
        raw = bits(" " if ch == "_" else ch)
        padded = raw.ljust(self._padded_bit_length, "0")
        k = self._bits_per_level
        return [
            int(padded[i:i+k], 2)
            for i in range(0, self._padded_bit_length, k)
        ]

    def _group_text(self, ch):
        raw = bits(" " if ch == "_" else ch)
        k = self._bits_per_level
        padded = raw.ljust(self._padded_bit_length, "0")
        return " ".join(
            padded[i:i+k]
            for i in range(0, self._padded_bit_length, k)
        )

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

        self._bits_per_level = _BITS_OPTIONS[self._bits_var.get()]
        self._prepare_bits()
        self._phrase = phrase
        self._data = [simbolo(ch) for ch in phrase]
        self._tree_root = None
        self._insert_queue = list(self._data)
        self._insert_index = 0
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
        inserted = self._insert_character(ch)
        self._render_tree()
        self._status_label.configure(
            text=(
                f"Paso {self._insert_index + 1}/{len(self._insert_queue)}: "
                f"carácter «{ch}» | código {codigo(' ' if ch == '_' else ch)} | "
                f"binario {bits(' ' if ch == '_' else ch)} | "
                f"grupos: {self._group_text(ch)} | "
                f"{'insertado' if inserted else 'ya estaba en el árbol'}"
            )
        )
        self._insert_index += 1
        self._anim_job = self.after(
            int(self._speed_slider.get()), self._animate_insert
        )

    def _insert_character(self, ch):
        if self._tree_root is None:
            self._tree_root = _Leaf(ch)
            return True
        try:
            self._tree_root = self._insert_rec(
                self._tree_root, ch, self._digits(ch), 0
            )
            return True
        except ValueError:
            return False

    def _insert_rec(self, node, key, digits, depth):
        if isinstance(node, _Leaf):
            if node.key == key:
                raise ValueError("duplicada")
            return self._split(
                node.key, key, digits, depth
            )

        slot = digits[depth]
        child = node.children[slot]
        if child is None:
            node.children[slot] = _Leaf(key)
        else:
            node.children[slot] = self._insert_rec(
                child, key, digits, depth + 1
            )
        return node

    def _split(self, old_key, new_key, new_digits, depth):
        old_digits = self._digits(old_key)
        root = _Internal(self._arity())
        node = root
        d = depth

        while (
            d < len(new_digits)
            and old_digits[d] == new_digits[d]
        ):
            branch = _Internal(self._arity())
            node.children[old_digits[d]] = branch
            node = branch
            d += 1

        if d >= len(new_digits):
            raise ValueError("No fue posible separar los caracteres.")

        node.children[old_digits[d]] = _Leaf(old_key)
        node.children[new_digits[d]] = _Leaf(new_key)
        return root

    def _get_children(self, node):
        if isinstance(node, _Leaf):
            return []
        return list(node.children)

    def _get_label(self, node):
        if not isinstance(node, _Leaf):
            return ""
        return " " if node.key == "_" else node.key

    def _get_style(self, node):
        return _COLOR_LEAF if isinstance(node, _Leaf) else _COLOR_INTERNAL

    def _render_tree(self):
        self._tree_items = draw_tree(
            self._canvas, self._tree_root,
            self._get_children, self._get_label,
            self._get_style, radius=28, unit_gap=48
        )
        self._draw_branch_labels()

    def _draw_branch_labels(self):
        self._canvas.delete("branch_bits")
        for node in self._walk_nodes(self._tree_root):
            items = self._tree_items.get(id(node))
            if not items or isinstance(node, _Leaf):
                continue
            k = self._bits_per_level
            for index, child in enumerate(node.children):
                if child is None:
                    continue
                citems = self._tree_items.get(id(child))
                if not citems:
                    continue
                label = format(index, f"0{k}b")
                self._canvas.create_text(
                    (items["x"] + citems["x"]) / 2,
                    (items["y"] + citems["y"]) / 2 - 10,
                    text=label,
                    font=("Consolas", 11, "bold"),
                    fill="#334155",
                    tags="branch_bits"
                )

    def _walk_nodes(self, node):
        if node is None:
            return
        yield node
        for child in self._get_children(node):
            yield from self._walk_nodes(child)

    def _show_placeholder(self):
        self._tree_items = {}
        show_placeholder(
            self._canvas,
            "Escribe una palabra o frase y presiona «Añadir»."
        )

    def _get_target(self):
        raw = self._search_entry.get().lower()
        if raw == " ":
            return "_"
        raw = raw.strip()
        if len(raw) != 1 or not ("a" <= raw <= "z"):
            self._show_error("La búsqueda admite una sola letra o un espacio.")
            return None
        return raw

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
        self._render_tree()
        self._clear_error()
        self._set_controls(True)
        self._is_animating = True
        self._search_recursive(
            self._tree_root, target, self._digits(target), 0
        )

    def _search_recursive(self, node, target, digits, depth):
        if node is None:
            self._finish_not_found(target)
            return
        items = self._tree_items.get(id(node))
        if items:
            self._canvas.itemconfig(
                items["oval"],
                fill=_COLOR_VISITING[0],
                outline=_COLOR_VISITING[1]
            )

        if isinstance(node, _Leaf):
            if node.key == target:
                if items:
                    self._canvas.itemconfig(
                        items["oval"],
                        fill=_COLOR_FOUND[0],
                        outline=_COLOR_FOUND[1]
                    )
                self._is_animating = False
                self._set_controls(False)
                self._status_label.configure(
                    text=(
                        f"Encontrado: «{target}» | "
                        f"código {codigo(' ' if target == '_' else target)} | "
                        f"binario {bits(' ' if target == '_' else target)}"
                    )
                )
                return
            self._finish_not_found(target)
            return

        slot = digits[depth]
        group = format(slot, f"0{self._bits_per_level}b")
        self._status_label.configure(
            text=(
                f"Paso {depth + 1}: grupo {group} | "
                f"rama {slot} de {self._arity()}"
            )
        )
        next_node = node.children[slot]
        self._anim_job = self.after(
            int(self._speed_slider.get()),
            lambda: self._search_recursive(
                next_node, target, digits, depth + 1
            )
        )

    def _finish_not_found(self, target):
        self._is_animating = False
        self._set_controls(False)
        self._status_label.configure(
            text=(
                f"«{target}» no fue encontrado | "
                f"código {codigo(' ' if target == '_' else target)} | "
                f"binario {bits(' ' if target == '_' else target)}"
            )
        )

    def _on_reset_search(self):
        self._cancel_animation()
        if self._tree_root:
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
        self._manual_entry.delete(0, "end")
        self._clear_error()
        self._show_placeholder()
        self._status_label.configure(text="Estado: árbol limpiado.")
        self._set_controls(False)

    def _on_save(self):
        if not self._phrase:
            self._show_error("No hay una frase para guardar.")
            return
        save_json(
            self,
            {
                "tipo": "arbol_multiple_frase",
                "frase": self._phrase,
                "bits_per_level": self._bits_per_level,
                "bits_option": self._bits_var.get()
            },
            "Guardar árbol de residuos múltiples"
        )

    def _on_load(self):
        payload = load_json(
            self, "Cargar árbol de residuos múltiples"
        )
        if payload is None:
            return
        if payload.get("tipo") != "arbol_multiple_frase":
            self._show_error(
                "El archivo no corresponde a un árbol de residuos múltiples válido."
            )
            return
        self._on_clear()
        option = payload.get("bits_option")
        if option in _BITS_OPTIONS:
            self._bits_var.set(option)
            self._bits_seg.set(option)
        self._manual_entry.insert(0, payload.get("frase", ""))
        self._on_generate()

    def destroy(self):
        self._cancel_animation()
        super().destroy()