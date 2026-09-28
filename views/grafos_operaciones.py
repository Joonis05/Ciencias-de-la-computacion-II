from __future__ import annotations

import math

import customtkinter as ctk

from views.base_view import BaseView
from views.persistence import save_json, load_json
from views.grafo_modelo import Arista, Grafo


MAX_VERTICES = 30


class GrafosOperacionesView(BaseView):
    """Operaciones básicas entre dos grafos y edición del resultado."""

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Operaciones con Grafos",
            **kwargs,
        )

        self._grafos = {
            "A": Grafo(),
            "B": Grafo(),
        }
        self._resultado: Grafo | None = None
        self._grafo_activo = "A"
        self._pasos: list[str] = []
        self._canvas_nodes: dict[str, dict[str, tuple[float, float]]] = {}

        self._build_ui()
        self._redraw_all()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def _build_ui(self):
        self.add_title("Operaciones con Grafos")
        self.add_subtitle(
            "Crea los grafos A y B y aplica operaciones sobre sus vértices y aristas."
        )

        # =====================================================
        # CONFIGURACIÓN COMPACTA
        # =====================================================
        config = ctk.CTkFrame(
            self.content,
            corner_radius=12,
            fg_color=("gray92", "gray17"),
            border_width=2,
            border_color=("gray78", "gray30"),
        )
        config.pack(fill="x", padx=10, pady=(0, 8))

        inner = ctk.CTkFrame(config, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)

        # -------- Fila 1: grafo activo --------
        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 7))

        ctk.CTkLabel(
            row1,
            text="Grafo activo:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left", padx=(0, 8))

        self._graph_menu = ctk.CTkSegmentedButton(
            row1,
            values=["A", "B"],
            command=self._on_graph_change,
            width=100,
        )
        self._graph_menu.set("A")
        self._graph_menu.pack(side="left")

        self._active_info = ctk.CTkLabel(
            row1,
            text="Editando Grafo A",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("gray40", "gray65"),
        )
        self._active_info.pack(side="left", padx=(10, 0))

        # -------- Fila 2: vértices --------
        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 7))

        ctk.CTkLabel(
            row2,
            text="Vértice:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=(0, 6))

        self._vertex_entry = ctk.CTkEntry(
            row2,
            width=100,
            height=32,
            placeholder_text="Ej: A",
        )
        self._vertex_entry.pack(side="left", padx=(0, 6))

        self._btn_add_vertex = ctk.CTkButton(
            row2,
            text="Añadir vértice",
            width=110,
            height=32,
            command=self._add_vertex,
        )
        self._btn_add_vertex.pack(side="left", padx=(0, 6))

        self._btn_remove_vertex = ctk.CTkButton(
            row2,
            text="Eliminar vértice",
            width=115,
            height=32,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            text_color=("black", "white"),
            command=self._remove_vertex,
        )
        self._btn_remove_vertex.pack(side="left")

        # -------- Fila 3: aristas --------
        row3 = ctk.CTkFrame(inner, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 7))

        ctk.CTkLabel(
            row3,
            text="Arista:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(side="left", padx=(0, 6))

        self._from_entry = ctk.CTkEntry(
            row3, width=80, height=32, placeholder_text="Desde"
        )
        self._from_entry.pack(side="left", padx=(0, 5))

        self._to_entry = ctk.CTkEntry(
            row3, width=80, height=32, placeholder_text="Hasta"
        )
        self._to_entry.pack(side="left", padx=(0, 5))

        self._weight_entry = ctk.CTkEntry(
            row3, width=72, height=32, placeholder_text="Peso"
        )
        self._weight_entry.pack(side="left", padx=(0, 5))

        self._directed_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            row3,
            text="Dirigida",
            variable=self._directed_var,
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=(0, 5))

        self._btn_add_edge = ctk.CTkButton(
            row3,
            text="Añadir arista",
            width=105,
            height=32,
            command=self._add_edge,
        )
        self._btn_add_edge.pack(side="left", padx=(0, 5))

        self._btn_remove_edge = ctk.CTkButton(
            row3,
            text="Eliminar arista",
            width=110,
            height=32,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            text_color=("black", "white"),
            command=self._remove_edge,
        )
        self._btn_remove_edge.pack(side="left")

        # -------- Fila 4: operaciones + cargar/guardar --------
        row4 = ctk.CTkFrame(inner, fg_color="transparent")
        row4.pack(fill="x")

        operation_buttons = [
            ("Unión", self._union, 68),
            ("Intersección", self._intersection, 92),
            ("Suma", self._sum_graphs, 68),
            ("Suma anillo", self._ring_sum, 88),
        ]

        for text, command, width in operation_buttons:
            ctk.CTkButton(
                row4,
                text=text,
                width=width,
                height=32,
                command=command,
            ).pack(side="left", padx=(0, 5))

        self._btn_clear_graph = ctk.CTkButton(
            row4,
            text="Limpiar activo",
            width=100,
            height=32,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            text_color=("black", "white"),
            command=self._clear_active_graph,
        )
        self._btn_clear_graph.pack(side="left", padx=(0, 5))

        self._btn_save = ctk.CTkButton(
            row4,
            text="Guardar",
            width=82,
            height=32,
            command=self._on_save,
        )
        self._btn_save.pack(side="right", padx=(5, 0))

        self._btn_load = ctk.CTkButton(
            row4,
            text="Cargar",
            width=82,
            height=32,
            command=self._on_load,
        )
        self._btn_load.pack(side="right")

        # -------- Estado y registro compacto --------
        info_row = ctk.CTkFrame(inner, fg_color="transparent")
        info_row.pack(fill="x", pady=(7, 0))

        self._status_label = ctk.CTkLabel(
            info_row,
            text="Listo para trabajar con los grafos.",
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray65"),
            anchor="w",
        )
        self._status_label.pack(side="left", fill="x", expand=True)

        self._steps_box = ctk.CTkTextbox(
            info_row,
            width=360,
            height=54,
            font=ctk.CTkFont(size=11),
        )
        self._steps_box.pack(side="right", padx=(10, 0))
        self._steps_box.configure(state="disabled")

        # =====================================================
        # ÁREA DE GRAFOS CON SCROLL EXCLUSIVO
        # =====================================================
        graphs = ctk.CTkFrame(
            self.content,
            corner_radius=12,
            fg_color=("gray96", "gray14"),
            border_width=2,
            border_color=("gray78", "gray30"),
        )
        graphs.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 10),
        )

        ctk.CTkLabel(
            graphs,
            text="Visualización de grafos",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=(8, 4))

        # Solo esta zona se desplaza.
        self._graphs_scroll = ctk.CTkScrollableFrame(
            graphs,
            fg_color="transparent",
            scrollbar_button_hover_color=("gray55", "gray45"),
        )
        self._graphs_scroll.pack(
            fill="both",
            expand=True,
            padx=7,
            pady=(0, 7),
        )

        self._canvas_a = self._make_canvas(
            self._graphs_scroll,
            "Grafo A",
            height=300,
        )
        self._canvas_a.pack(
            fill="x",
            padx=2,
            pady=(0, 8),
        )

        self._canvas_b = self._make_canvas(
            self._graphs_scroll,
            "Grafo B",
            height=300,
        )
        self._canvas_b.pack(
            fill="x",
            padx=2,
            pady=(0, 8),
        )

        self._canvas_result = self._make_canvas(
            self._graphs_scroll,
            "Resultado",
            height=360,
        )
        self._canvas_result.pack(
            fill="x",
            padx=2,
            pady=(0, 2),
        )

        self._canvas_a.bind(
            "<Configure>", lambda _e: self._redraw_all()
        )
        self._canvas_b.bind(
            "<Configure>", lambda _e: self._redraw_all()
        )
        self._canvas_result.bind(
            "<Configure>", lambda _e: self._redraw_all()
        )

        # Mouse wheel sobre los grafos.
        self._bind_graph_scroll(self._canvas_a)
        self._bind_graph_scroll(self._canvas_b)
        self._bind_graph_scroll(self._canvas_result)

    def _bind_graph_scroll(self, widget):
        widget.bind(
            "<MouseWheel>",
            lambda event: self._graphs_scroll._parent_canvas.yview_scroll(
                -int(event.delta / 120),
                "units",
            ),
        )

    def _make_canvas(self, parent, title, height=300):
        frame = ctk.CTkFrame(
            parent,
            height=height,
            corner_radius=10,
            fg_color=("white", "gray13"),
            border_width=1,
            border_color=("gray78", "gray30"),
        )
        frame.pack_propagate(False)

        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(pady=(7, 3))

        canvas = ctk.CTkCanvas(
            frame,
            highlightthickness=0,
            bg="#F7F7F7",
        )
        canvas.pack(
            fill="both",
            expand=True,
            padx=6,
            pady=(0, 6),
        )
        frame._canvas = canvas
        return frame

    # ---------------------------------------------------------
    # Edición
    # ---------------------------------------------------------

    def _on_graph_change(self, selected):
        self._grafo_activo = selected
        self._active_info.configure(text=f"Editando Grafo {selected}")
        self._clear_error()

    def _add_vertex(self):
        grafo = self._grafos[self._grafo_activo]
        nombre = self._vertex_entry.get().strip()

        if not nombre:
            return self._show_error("Ingresa un nombre de vértice.")
        if len(grafo.vertices) >= MAX_VERTICES:
            return self._show_error(f"El máximo es de {MAX_VERTICES} vértices por grafo.")
        if not grafo.agregar_vertice(nombre):
            return self._show_error("Ese vértice ya existe en el grafo activo.")

        self._vertex_entry.delete(0, "end")
        self._log(f"Grafo {self._grafo_activo}: añadido vértice {nombre}.")
        self._set_status("Vértice añadido correctamente.")
        self._redraw_all()

    def _remove_vertex(self):
        nombre = self._vertex_entry.get().strip()
        if not nombre:
            return self._show_error("Ingresa el vértice que deseas eliminar.")

        if not self._grafos[self._grafo_activo].eliminar_vertice(nombre):
            return self._show_error("El vértice no existe en el grafo activo.")

        self._vertex_entry.delete(0, "end")
        self._log(f"Grafo {self._grafo_activo}: eliminado vértice {nombre}.")
        self._set_status("Vértice eliminado correctamente.")
        self._redraw_all()

    def _add_edge(self):
        desde = self._from_entry.get().strip()
        hasta = self._to_entry.get().strip()
        peso = self._weight_entry.get().strip()
        dirigida = self._directed_var.get()

        if not desde or not hasta:
            return self._show_error("Ingresa los dos extremos de la arista.")
        if len(self._grafos[self._grafo_activo].vertices) >= MAX_VERTICES:
            return self._show_error(f"El máximo es de {MAX_VERTICES} vértices por grafo.")

        grafo = self._grafos[self._grafo_activo]
        nuevos_vertices = sum(
            1
            for nombre in (desde, hasta)
            if nombre not in grafo.vertices
        )

        if len(grafo.vertices) + nuevos_vertices > MAX_VERTICES:
            return self._show_error(f"El máximo es de {MAX_VERTICES} vértices por grafo.")

        if not grafo.agregar_arista(desde, hasta, peso, dirigida):
            return self._show_error("La arista ya existe o los datos no son válidos.")

        self._from_entry.delete(0, "end")
        self._to_entry.delete(0, "end")
        self._weight_entry.delete(0, "end")
        self._directed_var.set(False)
        self._log(
            f"Grafo {self._grafo_activo}: añadida arista "
            f"{desde}{'→' if dirigida else '—'}{hasta}."
        )
        self._set_status("Arista añadida correctamente.")
        self._redraw_all()

    def _remove_edge(self):
        desde = self._from_entry.get().strip()
        hasta = self._to_entry.get().strip()

        if not desde or not hasta:
            return self._show_error("Ingresa los extremos de la arista.")

        if not self._grafos[self._grafo_activo].eliminar_arista(desde, hasta):
            return self._show_error("La arista no existe en el grafo activo.")

        self._from_entry.delete(0, "end")
        self._to_entry.delete(0, "end")
        self._log(f"Grafo {self._grafo_activo}: eliminada arista {desde}—{hasta}.")
        self._set_status("Arista eliminada correctamente.")
        self._redraw_all()

    def _clear_active_graph(self):
        self._grafos[self._grafo_activo].limpiar()
        self._log(f"Grafo {self._grafo_activo}: limpiado.")
        self._set_status(f"Grafo {self._grafo_activo} limpiado.")
        self._redraw_all()

    # ---------------------------------------------------------
    # Operaciones
    # ---------------------------------------------------------

    def _union(self):
        a = self._grafos["A"]
        b = self._grafos["B"]
        result = Grafo(a.vertices)

        for vertice in b.vertices:
            result.agregar_vertice(vertice)

        for arista in [*a.aristas, *b.aristas]:
            result.agregar_arista(
                arista.desde,
                arista.hasta,
                arista.peso,
                arista.dirigida,
            )

        self._resultado = result
        self._log("Unión: A ∪ B.")
        self._set_status("Se generó la unión de A y B.")
        self._redraw_all()

    def _intersection(self):
        a = self._grafos["A"]
        b = self._grafos["B"]
        result = Grafo(v for v in a.vertices if v in b.vertices)

        for arista in a.aristas:
            if any(
                Grafo.aristas_equivalentes(arista, candidata)
                for candidata in b.aristas
            ):
                if arista.desde in result.vertices and arista.hasta in result.vertices:
                    result.aristas.append(arista)

        self._resultado = result
        self._log("Intersección: A ∩ B.")
        self._set_status("Se generó la intersección de A y B.")
        self._redraw_all()

    def _sum_graphs(self):
        a = self._grafos["A"]
        b = self._grafos["B"]
        result = Grafo(a.vertices)

        for vertice in b.vertices:
            result.agregar_vertice(vertice)
        for arista in [*a.aristas, *b.aristas]:
            result.agregar_arista(
                arista.desde,
                arista.hasta,
                arista.peso,
                arista.dirigida,
            )

        for va in a.vertices:
            for vb in b.vertices:
                if va == vb:
                    continue
                if not result.contiene_arista(
                    Arista(va, vb, "", False)
                ):
                    result.agregar_arista(va, vb)

        self._resultado = result
        self._log("Suma: se añadieron las conexiones entre A y B.")
        self._set_status("Se generó la suma de A y B.")
        self._redraw_all()

    def _ring_sum(self):
        a = self._grafos["A"]
        b = self._grafos["B"]
        result = Grafo(list(dict.fromkeys([*a.vertices, *b.vertices])))

        for arista in a.aristas:
            if not any(
                Grafo.aristas_equivalentes(arista, otra)
                for otra in b.aristas
            ):
                result.aristas.append(arista)

        for arista in b.aristas:
            if not any(
                Grafo.aristas_equivalentes(arista, otra)
                for otra in a.aristas
            ):
                result.aristas.append(arista)

        self._resultado = result
        self._log("Suma anillo: diferencia simétrica A ⊕ B.")
        self._set_status("Se generó la suma anillo de A y B.")
        self._redraw_all()

    # ---------------------------------------------------------
    # Resultado
    # ---------------------------------------------------------

    def _add_result_vertex(self):
        if self._resultado is None:
            return self._show_error("Primero genera un resultado.")

        nombre = self._vertex_entry.get().strip()
        if not nombre:
            return self._show_error("Ingresa un nombre de vértice.")

        if len(self._resultado.vertices) >= MAX_VERTICES:
            return self._show_error(f"El máximo es de {MAX_VERTICES} vértices en el resultado.")

        if not self._resultado.agregar_vertice(nombre):
            return self._show_error("Ese vértice ya existe en el resultado.")

        self._log(f"Resultado: insertado vértice {nombre}.")
        self._set_status("Vértice insertado en el resultado.")
        self._redraw_all()

    def _remove_result_vertex(self):
        if self._resultado is None:
            return self._show_error("Primero genera un resultado.")

        nombre = self._vertex_entry.get().strip()
        if not nombre:
            return self._show_error("Ingresa el vértice que deseas eliminar.")

        if not self._resultado.eliminar_vertice(nombre):
            return self._show_error("Ese vértice no existe en el resultado.")

        self._log(f"Resultado: eliminado vértice {nombre}.")
        self._set_status("Vértice eliminado del resultado.")
        self._redraw_all()

    # ---------------------------------------------------------
    # Persistencia
    # ---------------------------------------------------------

    def _on_save(self):
        payload = {
            "tipo": "grafos_operaciones",
            "grafos": {
                "A": self._grafos["A"].a_dict(),
                "B": self._grafos["B"].a_dict(),
            },
            "resultado": self._resultado.a_dict() if self._resultado else None,
            "pasos": self._pasos,
        }
        save_json(self, payload, "Guardar grafos")

    def _on_load(self):
        payload = load_json(self, "Cargar grafos")
        if payload is None:
            return

        try:
            if payload.get("tipo") != "grafos_operaciones":
                raise ValueError("El archivo no corresponde a operaciones con grafos.")

            grafos = payload.get("grafos", {})
            self._grafos["A"] = Grafo.from_dict(grafos.get("A", {}))
            self._grafos["B"] = Grafo.from_dict(grafos.get("B", {}))

            resultado = payload.get("resultado")
            self._resultado = Grafo.from_dict(resultado) if resultado else None
            self._pasos = list(payload.get("pasos", []))
            self._refresh_log()
            self._set_status("Grafos cargados correctamente.")
            self._redraw_all()
        except (ValueError, TypeError, KeyError) as exc:
            self._show_error(f"Archivo inválido: {exc}")

    # ---------------------------------------------------------
    # Dibujo
    # ---------------------------------------------------------

    def _redraw_all(self):
        self._draw_graph(self._canvas_a, self._grafos["A"], "A")
        self._draw_graph(self._canvas_b, self._grafos["B"], "B")
        self._draw_graph(self._canvas_result, self._resultado, "Resultado")

    def _canvas_from_frame(self, frame):
        return frame._canvas

    def _draw_graph(self, frame, graph, key):
        canvas = self._canvas_from_frame(frame)
        canvas.delete("all")

        if graph is None or not graph.vertices:
            canvas.create_text(
                max(120, canvas.winfo_width() / 2),
                max(80, canvas.winfo_height() / 2),
                text="Sin datos",
                font=("Arial", 13),
                fill="#777777",
            )
            return

        positions = self._layout_vertices(graph.vertices, canvas.winfo_width(), canvas.winfo_height())
        self._canvas_nodes[key] = positions

        radius = 20

        for arista in graph.aristas:
            p1 = positions.get(arista.desde)
            p2 = positions.get(arista.hasta)
            if not p1 or not p2:
                continue

            color = "#596579"
            width = 2
            self._draw_edge(canvas, p1, p2, arista, radius, color, width)

        for vertice, (x, y) in positions.items():
            fill = "#647cff"
            if key == "B":
                fill = "#4cc9f0"
            elif key == "Resultado":
                fill = "#7c5cff"

            canvas.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                fill=fill,
                outline="#1f2937",
                width=2,
            )
            canvas.create_text(
                x,
                y,
                text=vertice,
                font=("Arial", 10, "bold"),
                fill="white",
            )

    def _draw_edge(self, canvas, p1, p2, arista, radius, color, width):
        x1, y1 = p1
        x2, y2 = p2

        dx = x2 - x1
        dy = y2 - y1
        distancia = max(1.0, math.hypot(dx, dy))

        ux = dx / distancia
        uy = dy / distancia

        start_x = x1 + ux * radius
        start_y = y1 + uy * radius
        end_x = x2 - ux * radius
        end_y = y2 - uy * radius

        # Lazo: la arista comienza y termina en el mismo vértice.
        if arista.desde == arista.hasta:
            loop_radius = radius * 1.5
            canvas.create_arc(
                x1 - loop_radius,
                y1 - loop_radius * 2.25,
                x1 + loop_radius,
                y1 + radius * 0.15,
                start=25,
                extent=310,
                style="arc",
                outline=color,
                width=width,
            )

            # create_arc no admite arrow; para un lazo dirigido
            # dibujamos una pequeña flecha tangente en el extremo del arco.
            if arista.dirigida:
                arrow_x = x1 + loop_radius * 0.91
                arrow_y = y1 - loop_radius * 0.65
                prev_x = arrow_x - 13
                prev_y = arrow_y - 5
                canvas.create_line(
                    prev_x,
                    prev_y,
                    arrow_x,
                    arrow_y,
                    fill=color,
                    width=width,
                    arrow="last",
                )

            if arista.peso:
                canvas.create_text(
                    x1,
                    y1 - loop_radius * 1.55,
                    text=str(arista.peso),
                    font=("Arial", 9, "bold"),
                    fill="#374151",
                )
            return

        if arista.dirigida:
            canvas.create_line(
                start_x,
                start_y,
                end_x,
                end_y,
                fill=color,
                width=width,
                arrow="last",
            )
        else:
            canvas.create_line(
                start_x,
                start_y,
                end_x,
                end_y,
                fill=color,
                width=width,
            )

        if arista.peso:
            mid_x = (start_x + end_x) / 2
            mid_y = (start_y + end_y) / 2
            canvas.create_text(
                mid_x,
                mid_y - 8,
                text=str(arista.peso),
                font=("Arial", 9, "bold"),
                fill="#374151",
            )

    @staticmethod
    def _layout_vertices(vertices, width, height):
        width = max(320, width)
        height = max(220, height)
        n = len(vertices)

        if n <= 8:
            center_x = width / 2
            center_y = height / 2
            radius = max(60, min(width, height) * 0.32)
            step = 2 * math.pi / n
            return {
                vertice: (
                    center_x + radius * math.cos(i * step - math.pi / 2),
                    center_y + radius * math.sin(i * step - math.pi / 2),
                )
                for i, vertice in enumerate(vertices)
            }

        columns = math.ceil(math.sqrt(n))
        rows = math.ceil(n / columns)
        margin_x = 45
        margin_y = 35
        cell_w = (width - 2 * margin_x) / max(1, columns - 1)
        cell_h = (height - 2 * margin_y) / max(1, rows - 1)

        positions = {}
        for i, vertice in enumerate(vertices):
            row = i // columns
            column = i % columns
            x = margin_x + column * cell_w
            y = margin_y + row * cell_h
            positions[vertice] = (x, y)
        return positions

    # ---------------------------------------------------------
    # Mensajes
    # ---------------------------------------------------------

    def _log(self, text):
        self._pasos.append(text)
        self._refresh_log()

    def _refresh_log(self):
        self._steps_box.configure(state="normal")
        self._steps_box.delete("1.0", "end")
        for i, paso in enumerate(self._pasos, start=1):
            self._steps_box.insert("end", f"{i}. {paso}\n")
        self._steps_box.configure(state="disabled")

    def _set_status(self, text):
        self._status_label.configure(text=text)
        self._clear_error()

    def _show_error(self, text):
        self._status_label.configure(text=text)

    def _clear_error(self):
        pass

    def destroy(self):
        super().destroy()
