from __future__ import annotations

import math

import customtkinter as ctk

from views.base_view import BaseView
from views.persistence import save_json, load_json
from views.grafo_modelo import Arista, Grafo


MAX_VERTICES = 16


class GrafosProductosView(BaseView):
    """Productos de grafos tomados del proyecto de referencia."""

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title="Productos de Grafos",
            **kwargs,
        )
        self._grafos = {"A": Grafo(), "B": Grafo()}
        self._resultado: Grafo | None = None
        self._active = "A"
        self._steps: list[str] = []
        self._build_ui()
        self._redraw()

    def _build_ui(self):
        self.add_title("Conectividad y Separabilidad")
        self.add_subtitle(
            "Construye los grafos A y B y aplica productos y composición."
        )

        config = ctk.CTkFrame(
            self.content, corner_radius=12,
            fg_color=("gray92", "gray17"),
            border_width=2, border_color=("gray78", "gray30"),
        )
        config.pack(fill="x", padx=10, pady=(0, 8))
        inner = ctk.CTkFrame(config, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=14)

        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(row1, text="Grafo activo:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0, 8))
        self._graph_menu = ctk.CTkSegmentedButton(row1, values=["A", "B"], command=self._change_graph)
        self._graph_menu.set("A")
        self._graph_menu.pack(side="left")

        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(row2, text="Vértice:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0, 6))
        self._vertex = ctk.CTkEntry(row2, width=100, height=34, placeholder_text="A")
        self._vertex.pack(side="left", padx=(0, 6))
        ctk.CTkButton(row2, text="Añadir", width=90, command=self._add_vertex).pack(side="left", padx=(0, 6))
        ctk.CTkButton(row2, text="Eliminar", width=90, fg_color=("gray70", "gray30"), text_color=("black", "white"), command=self._remove_vertex).pack(side="left")

        row3 = ctk.CTkFrame(inner, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(row3, text="Arista:", font=ctk.CTkFont(size=13, weight="bold")).pack(side="left", padx=(0, 6))
        self._from = ctk.CTkEntry(row3, width=80, height=34, placeholder_text="Desde")
        self._from.pack(side="left", padx=(0, 5))
        self._to = ctk.CTkEntry(row3, width=80, height=34, placeholder_text="Hasta")
        self._to.pack(side="left", padx=(0, 5))
        self._weight = ctk.CTkEntry(row3, width=75, height=34, placeholder_text="Peso")
        self._weight.pack(side="left", padx=(0, 5))
        self._directed = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(row3, text="Dirigida", variable=self._directed).pack(side="left", padx=(0, 5))
        ctk.CTkButton(row3, text="Añadir arista", width=100, command=self._add_edge).pack(side="left", padx=(0, 5))
        ctk.CTkButton(row3, text="Eliminar arista", width=105, fg_color=("gray70", "gray30"), text_color=("black", "white"), command=self._remove_edge).pack(side="left")

        row4 = ctk.CTkFrame(inner, fg_color="transparent")
        row4.pack(fill="x")
        ctk.CTkButton(row4, text="Limpiar", width=100, fg_color=("gray70", "gray30"), text_color=("black", "white"), command=self._clear).pack(side="left")
        ctk.CTkButton(row4, text="Guardar", width=90, command=self._save).pack(side="right", padx=(6, 0))
        ctk.CTkButton(row4, text="Cargar", width=90, command=self._load).pack(side="right")

        body = ctk.CTkFrame(self.content, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        control = ctk.CTkFrame(body, corner_radius=12, fg_color=("gray92", "gray17"), border_width=2, border_color=("gray78", "gray30"))
        control.pack(side="left", fill="y", padx=(0, 5))
        ctk.CTkLabel(control, text="Operaciones", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 8))
        for label, command in [
            ("Producto cartesiano", self._cartesian),
            ("Producto tensorial", self._tensorial),
            ("Composición", self._composition),
        ]:
            ctk.CTkButton(control, text=label, width=180, command=command).pack(padx=12, pady=5)

        log = ctk.CTkFrame(body, corner_radius=12, fg_color=("gray92", "gray17"), border_width=2, border_color=("gray78", "gray30"))
        log.pack(side="left", fill="both", expand=True, padx=(5, 0))
        ctk.CTkLabel(log, text="Registro de pasos", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(12, 8))
        self._steps_box = ctk.CTkTextbox(log, height=120)
        self._steps_box.pack(fill="both", expand=True, padx=12, pady=12)
        self._steps_box.configure(state="disabled")

        graphs = ctk.CTkFrame(self.content, corner_radius=12, fg_color=("gray96", "gray14"), border_width=2, border_color=("gray78", "gray30"))
        graphs.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        top = ctk.CTkFrame(graphs, fg_color="transparent")
        top.pack(fill="both", expand=True, padx=8, pady=8)
        self._frame_a, self._canvas_a = self._make_graph_panel(top, "Grafo A")
        self._frame_a.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self._frame_b, self._canvas_b = self._make_graph_panel(top, "Grafo B")
        self._frame_b.pack(side="left", fill="both", expand=True, padx=(4, 0))
        self._frame_r, self._canvas_r = self._make_graph_panel(graphs, "Resultado")
        self._frame_r.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        for canvas in (self._canvas_a, self._canvas_b, self._canvas_r):
            canvas.bind("<Configure>", lambda _e: self._redraw())

    def _make_graph_panel(self, parent, title):
        frame = ctk.CTkFrame(
            parent,
            corner_radius=10,
            fg_color=("white", "gray13"),
            border_width=1,
            border_color=("gray78", "gray30"),
        )
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
        return frame, canvas

    def _change_graph(self, value):
        self._active = value
        self._clear_status()

    def _add_vertex(self):
        name = self._vertex.get().strip()
        if not name:
            return self._set_status("Ingresa un nombre de vértice.")
        graph = self._grafos[self._active]
        if len(graph.vertices) >= MAX_VERTICES:
            return self._set_status(f"Máximo {MAX_VERTICES} vértices por grafo.")
        if not graph.agregar_vertice(name):
            return self._set_status("Ese vértice ya existe.")
        self._vertex.delete(0, "end")
        self._log(f"{self._active}: añadido vértice {name}.")
        self._redraw()

    def _remove_vertex(self):
        name = self._vertex.get().strip()
        if not self._grafos[self._active].eliminar_vertice(name):
            return self._set_status("El vértice no existe.")
        self._log(f"{self._active}: eliminado vértice {name}.")
        self._redraw()

    def _add_edge(self):
        d, h = self._from.get().strip(), self._to.get().strip()
        if not d or not h:
            return self._set_status("Ingresa los dos extremos de la arista.")
        g = self._grafos[self._active]
        if not g.agregar_arista(d, h, self._weight.get().strip(), self._directed.get()):
            return self._set_status("La arista ya existe o no es válida.")
        self._from.delete(0, "end"); self._to.delete(0, "end"); self._weight.delete(0, "end")
        self._directed.set(False)
        self._log(f"{self._active}: añadida arista {d}{'→' if self._directed.get() else '—'}{h}.")
        self._redraw()

    def _remove_edge(self):
        d, h = self._from.get().strip(), self._to.get().strip()
        if not d or not h:
            return self._set_status("Ingresa los extremos de la arista.")
        if not self._grafos[self._active].eliminar_arista(d, h):
            return self._set_status("La arista no existe.")
        self._log(f"{self._active}: eliminada arista {d}—{h}.")
        self._redraw()

    def _cartesian(self):
        a, b = self._grafos["A"], self._grafos["B"]
        result = Grafo()
        for va in a.vertices:
            for vb in b.vertices:
                result.agregar_vertice(f"({va},{vb})")
        for ea in a.aristas:
            for vb in b.vertices:
                result.agregar_arista(f"({ea.desde},{vb})", f"({ea.hasta},{vb})")
        for eb in b.aristas:
            for va in a.vertices:
                result.agregar_arista(f"({va},{eb.desde})", f"({va},{eb.hasta})")
        self._resultado = result
        self._log("Producto cartesiano A × B.")
        self._redraw()

    def _tensorial(self):
        a, b = self._grafos["A"], self._grafos["B"]
        result = Grafo()
        for va in a.vertices:
            for vb in b.vertices:
                result.agregar_vertice(f"({va},{vb})")
        for ea in a.aristas:
            for eb in b.aristas:
                result.agregar_arista(f"({ea.desde},{eb.desde})", f"({ea.hasta},{eb.hasta})")
                result.agregar_arista(f"({ea.desde},{eb.hasta})", f"({ea.hasta},{eb.desde})")
        self._resultado = result
        self._log("Producto tensorial A ⊗ B.")
        self._redraw()

    def _composition(self):
        a, b = self._grafos["A"], self._grafos["B"]
        result = Grafo()
        for va in a.vertices:
            for vb in b.vertices:
                result.agregar_vertice(f"({va},{vb})")
        for va1 in a.vertices:
            for va2 in a.vertices:
                for vb1 in b.vertices:
                    for vb2 in b.vertices:
                        same_a = va1 == va2
                        b_connected = self._has_connection(b, vb1, vb2)
                        a_connected = self._has_connection(a, va1, va2)
                        if (same_a and b_connected) or a_connected:
                            result.agregar_arista(f"({va1},{vb1})", f"({va2},{vb2})")
        self._resultado = result
        self._log("Composición lexicográfica A ∘ B.")
        self._redraw()

    @staticmethod
    def _has_connection(graph, v1, v2):
        return any(
            (e.desde == v1 and e.hasta == v2)
            or (not e.dirigida and e.desde == v2 and e.hasta == v1)
            for e in graph.aristas
        )

    def _clear(self):
        self._grafos["A"].limpiar(); self._grafos["B"].limpiar(); self._resultado = None; self._steps.clear(); self._refresh_log(); self._redraw()

    def _save(self):
        payload = {
            "tipo": "grafos_productos",
            "A": self._grafos["A"].a_dict(),
            "B": self._grafos["B"].a_dict(),
            "resultado": self._resultado.a_dict() if self._resultado else None,
            "pasos": self._steps,
        }
        save_json(self, payload, "Guardar productos de grafos")

    def _load(self):
        payload = load_json(self, "Cargar productos de grafos")
        if payload is None:
            return
        try:
            if payload.get("tipo") != "grafos_productos":
                raise ValueError("Archivo incompatible con Productos de Grafos.")
            self._grafos["A"] = Grafo.from_dict(payload.get("A", {}))
            self._grafos["B"] = Grafo.from_dict(payload.get("B", {}))
            r = payload.get("resultado")
            self._resultado = Grafo.from_dict(r) if r else None
            self._steps = list(payload.get("pasos", []))
            self._refresh_log(); self._redraw()
        except (ValueError, TypeError, KeyError) as exc:
            self._set_status(f"Archivo inválido: {exc}")

    def _redraw(self):
        self._draw_graph(self._canvas_a, self._grafos["A"], "#647cff")
        self._draw_graph(self._canvas_b, self._grafos["B"], "#4cc9f0")
        self._draw_graph(self._canvas_r, self._resultado, "#7c5cff")

    def _draw_graph(self, canvas, graph, node_color):
        canvas.delete("all")
        if graph is None or not graph.vertices:
            canvas.create_text(max(140, canvas.winfo_width()/2), max(70, canvas.winfo_height()/2), text="Sin datos", font=("Arial", 12), fill="#777777")
            return
        positions = self._layout(graph.vertices, canvas.winfo_width(), canvas.winfo_height())
        radius = 18
        for edge in graph.aristas:
            p1, p2 = positions.get(edge.desde), positions.get(edge.hasta)
            if not p1 or not p2: continue
            x1, y1 = p1; x2, y2 = p2
            # Lazo: la arista sale y regresa al mismo vértice.
            if edge.desde == edge.hasta:
                loop_r = radius * 1.45
                x1_loop = x1 - loop_r
                y1_loop = y1 - loop_r * 2.2
                x2_loop = x1 + loop_r
                y2_loop = y1 + radius * 0.15
                canvas.create_arc(
                    x1_loop, y1_loop, x2_loop, y2_loop,
                    start=25, extent=310, style="arc",
                    outline="#596579", width=2,
                )
                if edge.dirigida:
                    arrow_x = x1 + loop_r * 0.91
                    arrow_y = y1 - loop_r * 0.65
                    canvas.create_line(
                        arrow_x - 12,
                        arrow_y - 5,
                        arrow_x,
                        arrow_y,
                        fill="#596579",
                        width=2,
                        arrow="last",
                    )
                if edge.peso:
                    canvas.create_text(
                        x1, y1 - loop_r * 1.55,
                        text=str(edge.peso),
                        font=("Arial", 8, "bold"),
                        fill="#374151",
                    )
                continue

            dx, dy = x2-x1, y2-y1; dist=max(1.0, math.hypot(dx,dy)); ux,uy=dx/dist,dy/dist
            sx,sy=x1+ux*radius,y1+uy*radius; ex,ey=x2-ux*radius,y2-uy*radius
            canvas.create_line(sx,sy,ex,ey,fill="#596579",width=2,arrow="last" if edge.dirigida else "none")
            if edge.peso:
                canvas.create_text((sx+ex)/2,(sy+ey)/2-8,text=str(edge.peso),font=("Arial",8,"bold"),fill="#374151")
        for name,(x,y) in positions.items():
            canvas.create_oval(x-radius,y-radius,x+radius,y+radius,fill=node_color,outline="#1f2937",width=2)
            canvas.create_text(x,y,text=name,font=("Arial",8,"bold"),fill="white")

    @staticmethod
    def _layout(vertices, width, height):
        n=len(vertices); width=max(300,width); height=max(220,height)
        if n <= 8:
            cx,cy=width/2,height/2; r=min(width,height)*0.30; step=2*math.pi/n
            return {v:(cx+r*math.cos(i*step-math.pi/2), cy+r*math.sin(i*step-math.pi/2)) for i,v in enumerate(vertices)}
        cols=math.ceil(math.sqrt(n)); rows=math.ceil(n/cols); mx,my=40,35
        cw=(width-2*mx)/max(1,cols-1); ch=(height-2*my)/max(1,rows-1)
        return {v:(mx+(i%cols)*cw, my+(i//cols)*ch) for i,v in enumerate(vertices)}

    def _log(self, text):
        self._steps.append(text); self._refresh_log()

    def _refresh_log(self):
        self._steps_box.configure(state="normal"); self._steps_box.delete("1.0", "end")
        for i, step in enumerate(self._steps, start=1): self._steps_box.insert("end", f"{i}. {step}\n")
        self._steps_box.configure(state="disabled")

    def _set_status(self, text):
        # Reutilizamos el primer label de pasos como mensaje visible.
        self._log(text)

    def _clear_status(self):
        pass

    def destroy(self):
        super().destroy()
