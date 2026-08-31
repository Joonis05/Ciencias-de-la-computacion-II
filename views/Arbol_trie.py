import customtkinter as ctk
from views.base_view import BaseView
from views.persistence import save_json, load_json
from views.Tree_canvas import build_scrollable_canvas, draw_tree, show_placeholder

_MAX_PHRASE = 200
_COLOR_LEAF = ("#BFDBFE", "#1D4ED8")
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
    __slots__ = ("left", "right")
    def __init__(self):
        self.left = None
        self.right = None


class ArbolTrieView(BaseView):
    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(master, view_manager=view_manager,
                         title="Árbol Trie", **kwargs)
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
>>>>>>> origin/2
        self._build_ui()

    def _build_ui(self):
        self.add_title("Árbol Trie")
        self.add_subtitle(
            "La frase se separa en caracteres; cada carácter usa su código "
            "y sus 5 bits para construir el trie."
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
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        self._search_entry.pack(side="left", padx=(0,10))
        self._btn_search = ctk.CTkButton(
            sr, text="Buscar", width=100, height=34,
            command=self._on_search
        )
        self._btn_search.pack(side="left", padx=(0,8))
        self._btn_delete = ctk.CTkButton(sr, text="Eliminar", width=100, height=34, fg_color="#C62828", hover_color="#8E0000", text_color="white", command=self._on_delete)
        self._btn_delete.pack(side="left", padx=(0,8))
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
            sr2, from_=100, to=2000,
            number_of_steps=19, width=180,
            command=self._on_speed_change
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

        workspace = ctk.CTkFrame(self.content, fg_color="transparent")
        workspace.pack(fill="both", expand=True, padx=10, pady=(0,10))
        tree_container, self._canvas = build_scrollable_canvas(workspace)
        tree_container.pack(side="left", fill="both", expand=True, padx=(0,8))
        sidebar = ctk.CTkFrame(workspace, width=300, corner_radius=12, fg_color=("gray92","gray17"), border_width=2, border_color=("gray78","gray30"))
        sidebar.pack(side="right", fill="y")
        sidebar.pack_propagate(False)
        ctk.CTkLabel(sidebar, text="Tabla de caracteres", font=ctk.CTkFont(size=13, weight="bold"), anchor="w").pack(fill="x", padx=10, pady=(10,6))
        self._table_frame = ctk.CTkScrollableFrame(sidebar, height=210, fg_color="transparent")
        self._table_frame.pack(fill="x", padx=8, pady=(0,8))
        ctk.CTkLabel(sidebar, text="Historial de construcción y búsqueda", font=ctk.CTkFont(size=13, weight="bold"), anchor="w").pack(fill="x", padx=10, pady=(4,6))
        self._history_box = ctk.CTkTextbox(sidebar, height=220, font=ctk.CTkFont(family="Consolas", size=11), wrap="word")
        self._history_box.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self._history_box.configure(state="disabled")
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
            self._btn_save, self._btn_load, self._search_entry,
            self._btn_search, self._btn_delete, self._btn_reset
        ):
            w.configure(state=state)

    def _draw_level_labels(self):
        self._canvas.delete("level_labels")
        seen=set()
        def walk(node, depth):
            if node is None: return
            items=self._tree_items.get(id(node))
            if items and depth not in seen:
                self._canvas.create_text(18, items["y"], text=f"Nivel {depth}", font=("Consolas",10,"bold"), fill="#64748B", anchor="w", tags="level_labels")
                seen.add(depth)
            for child in self._get_children(node): walk(child, depth+1)
        walk(self._tree_root,0)

    def _refresh_character_table(self):
        for w in self._table_frame.winfo_children(): w.destroy()
        for idx,ch in enumerate(self._data,1):
            disp="espacio" if ch=="_" else ch
            row=ctk.CTkFrame(self._table_frame,height=28,corner_radius=5,fg_color=("gray88","gray22") if idx%2 else ("gray94","gray17"))
            row.pack(fill="x",pady=1); row.pack_propagate(False)
            ctk.CTkLabel(row,text=str(idx),width=28,font=ctk.CTkFont(size=11),anchor="center").pack(side="left")
            ctk.CTkLabel(row,text=disp,width=58,font=ctk.CTkFont(family="Consolas",size=11,weight="bold"),anchor="w").pack(side="left")
            ctk.CTkLabel(row,text=str(codigo(" " if ch=="_" else ch)),width=42,font=ctk.CTkFont(family="Consolas",size=11),anchor="center").pack(side="left")
            ctk.CTkLabel(row,text=bits(" " if ch=="_" else ch),font=ctk.CTkFont(family="Consolas",size=11),anchor="w").pack(side="left")

    def _add_history(self,text):
        self._history_box.configure(state="normal"); self._history_box.insert("end",text+"\n"); self._history_box.see("end"); self._history_box.configure(state="disabled")

    def _show_placeholder(self):
        self._tree_items = {}
        show_placeholder(
            self._canvas,
            "Escribe una palabra o frase y presiona «Añadir»."
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

        self._phrase = phrase
        self._data = [simbolo(ch) for ch in phrase]
        self._tree_root = None
        self._insert_queue = list(self._data)
        self._insert_index = 0
        self._history_box.configure(state="normal")
        self._history_box.delete("1.0", "end")
        self._history_box.configure(state="disabled")
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
        self._refresh_character_table()
        code = codigo(" " if ch == "_" else ch)
        binary = bits(" " if ch == "_" else ch)

        action = "insertado" if inserted else "ya estaba en el árbol"
        message=(
            f"Paso {self._insert_index + 1}/{len(self._insert_queue)}: "
            f"carácter «{ch}» | código {code} | binario {binary} | {action}"
        )
        self._status_label.configure(text=message)
        self._add_history(message)
        self._insert_index += 1
        self._anim_job = self.after(
            int(self._speed_slider.get()), self._animate_insert
        )

    def _insert_character(self, ch):
        key_bits = bits(" " if ch == "_" else ch)
        if self._tree_root is None:
            self._tree_root = _Leaf(ch)
            return True
        try:
            self._tree_root = self._insert_rec(
                self._tree_root, ch, key_bits, 0
            )
            return True
        except ValueError:
            return False

    def _insert_rec(self, node, key, key_bits, depth):
        if isinstance(node, _Leaf):
            if node.key == key:
                raise ValueError("duplicada")
            return self._split(node.key, key, key_bits, depth)

        bit = key_bits[depth]
        if bit == "0":
            if node.left is None:
                node.left = _Leaf(key)
            else:
                node.left = self._insert_rec(
                    node.left, key, key_bits, depth + 1
                )
        else:
            if node.right is None:
                node.right = _Leaf(key)
            else:
                node.right = self._insert_rec(
                    node.right, key, key_bits, depth + 1
                )
        return node

    def _split(self, old_key, new_key, new_bits, depth):
        old_bits = bits(" " if old_key == "_" else old_key)
        root = _Internal()
        node = root
        d = depth
        while d < len(new_bits) and old_bits[d] == new_bits[d]:
            branch = _Internal()
            if old_bits[d] == "0":
                node.left = branch
            else:
                node.right = branch
            node = branch
            d += 1
        if d >= len(new_bits):
            raise ValueError("No fue posible separar los caracteres.")
        if old_bits[d] == "0":
            node.left = _Leaf(old_key)
            node.right = _Leaf(new_key)
        else:
            node.right = _Leaf(old_key)
            node.left = _Leaf(new_key)
        return root

    def _get_children(self, node):
        if isinstance(node, _Leaf):
            return []
        return [node.left, node.right]

    def _get_label(self, node):
        if not isinstance(node, _Leaf):
            return ""
        return " " if node.key == "_" else node.key

    def _get_style(self, node):
        return _COLOR_LEAF if isinstance(node, _Leaf) else _COLOR_INTERNAL

    def _iter_children_with_bits(self, node):
        if isinstance(node, _Leaf):
            return []
        return [("0", node.left), ("1", node.right)]

    def _render_tree(self):
        self._tree_items = draw_tree(
            self._canvas, self._tree_root,
            self._get_children, self._get_label,
            self._get_style, radius=28
        )
        self._draw_branch_labels()
        self._draw_level_labels()

    def _draw_branch_labels(self):
        self._canvas.delete("branch_bits")
        for node in self._walk_nodes(self._tree_root):
            items = self._tree_items.get(id(node))
            if not items:
                continue
            for label, child in self._iter_children_with_bits(node):
                if child is None:
                    continue
                citems = self._tree_items.get(id(child))
                if not citems:
                    continue
                self._canvas.create_text(
                    (items["x"] + citems["x"]) / 2,
                    (items["y"] + citems["y"]) / 2 - 10,
                    text=label, font=("Consolas", 12, "bold"),
                    fill="#334155", tags="branch_bits"
                )

    def _walk_nodes(self, node):
        if node is None:
            return
        yield node
        for child in self._get_children(node):
            yield from self._walk_nodes(child)

    def _get_target(self):
        raw = self._search_entry.get().lower()
        if raw == " ":
            return "_"
        raw = raw.strip()
        if not raw:
            self._show_error("Ingresa un carácter.")
            return None
        if len(raw) != 1 or not ("a" <= raw <= "z"):
            self._show_error("La búsqueda admite una sola letra o un espacio.")
            return None
        return simbolo(raw)

    def _on_delete(self):
        if self._is_animating or self._tree_root is None: return
        target=self._get_target()
        if target is None: return
        self._pending_action="delete"
        self._begin_search(target)

    def _on_search(self):
        if self._is_animating or self._tree_root is None:
            if self._tree_root is None:
                self._show_error("Primero construye el árbol.")
            return
        target = self._get_target()
        if target is None:
            return

        self._cancel_animation()
        self._pending_action="search"
        self._render_tree()
        self._set_controls(True)
        self._clear_error()
        self._is_animating = True
        target_bits = bits(" " if target == "_" else target)
        self._search_recursive(self._tree_root, target, target_bits, 0)

    def _search_recursive(self, node, target, target_bits, depth):
        if not self._is_animating:
            return
        if node is None:
            self._finish_not_found(target, target_bits)
            return

        items=self._tree_items.get(id(node))
        if items:
            self._canvas.itemconfig(items["oval"], fill=_COLOR_VISITING[0], outline=_COLOR_VISITING[1])

        if isinstance(node, _Leaf):
            if node.key == target:
                if items:
                    self._canvas.itemconfig(items["oval"], fill=_COLOR_FOUND[0], outline=_COLOR_FOUND[1])
                code=codigo(" " if target=="_" else target)
                if self._pending_action == "delete":
                    self._status_label.configure(text=f"Encontrado: «{target}» | código {code} | binario {target_bits} | nivel {depth} | Eliminando...")
                    self._add_history(f"Eliminación: «{target}» encontrado en nivel {depth}.")
                    self._anim_job=self.after(int(self._speed_slider.get()), lambda:self._finish_delete(target))
                    return
                self._status_label.configure(text=f"Encontrado: «{target}» | código {code} | binario {target_bits} | nivel {depth}")
                self._add_history(f"Búsqueda: «{target}» encontrado en nivel {depth}.")
                self._is_animating=False; self._pending_action=None; self._set_controls(False)
                return
            self._finish_not_found(target, target_bits)
            return

        if depth >= len(target_bits):
            self._finish_not_found(target, target_bits)
            return

        bit=target_bits[depth]
        direction="izquierda" if bit=="0" else "derecha"
        message=f"Paso {depth+1}: nivel {depth} | nodo interno | bit {bit} | avanzo a {direction}"
        self._status_label.configure(text=message)
        self._add_history(message)
        next_node=node.left if bit=="0" else node.right
        self._anim_job=self.after(int(self._speed_slider.get()), lambda:self._search_recursive(next_node,target,target_bits,depth+1))

    def _finish_not_found(self, target, target_bits):
        self._is_animating = False
        self._set_controls(False)
        self._status_label.configure(
            text=f"«{target}» no fue encontrado | binario {target_bits}"
        )

    def _finish_delete(self,target):
        self._phrase="".join(ch for ch in self._phrase if simbolo(ch)!=target)
        self._data=[simbolo(ch) for ch in self._phrase]
        self._tree_root=None
        for ch in self._data: self._insert_character(ch)
        self._render_tree(); self._refresh_character_table()
        self._add_history(f"Eliminado: «{target}». Árbol actualizado.")
        self._status_label.configure(text=f"El carácter «{target}» fue eliminado correctamente.")
        self._is_animating=False; self._pending_action=None; self._set_controls(False)

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
            {"tipo": "arbol_trie_frase", "frase": self._phrase},
            "Guardar árbol trie"
        )

    def _on_load(self):
        payload = load_json(self, "Cargar árbol trie")
        if payload is None:
            return
        if payload.get("tipo") != "arbol_trie_frase":
            self._show_error("El archivo no corresponde a un árbol trie de frases válido.")
            return
        self._on_clear()
        self._manual_entry.insert(0, payload.get("frase", ""))
        self._on_generate()

    def destroy(self):
        self._cancel_animation()
        super().destroy()
