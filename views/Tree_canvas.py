"""
Utilidades compartidas para las vistas de Búsqueda por Residuos
(Árbol Digital, Árbol Trie y Árbol de Residuos Múltiples).

Aquí vive todo lo relacionado con calcular la posición de los nodos y
dibujarlos sobre un tkinter.Canvas, para no repetir esa lógica en cada
vista. No se usa ninguna librería externa de grafos: un Canvas normal
es suficiente para dibujar círculos, líneas y animarlos con colores.
"""
import tkinter as tk
import customtkinter as ctk


def compute_positions(root, get_children, level_height=90, unit_gap=56):
    """Asigna una posición (x, y) a cada nodo del árbol.

    ``get_children(node)`` debe devolver una lista de hijos (puede
    contener ``None`` en las ramas vacías) para que el árbol quede
    centrado visualmente sin importar cuántos hijos tenga cada nodo.

    Devuelve un diccionario {id(nodo): (x, y)}.
    """
    positions = {}
    next_slot = [0]

    def assign(node, depth):
        if node is None:
            x = next_slot[0] * unit_gap
            next_slot[0] += 1
            return x
        children = [c for c in get_children(node)]
        if not children:
            x = next_slot[0] * unit_gap
            next_slot[0] += 1
            positions[id(node)] = (x, depth * level_height)
            return x
        child_xs = [assign(child, depth + 1) for child in children]
        x = sum(child_xs) / len(child_xs)
        positions[id(node)] = (x, depth * level_height)
        return x

    if root is not None:
        assign(root, 0)
    return positions


def draw_tree(canvas, root, get_children, get_label, get_style,
              radius=22, x_offset=50, y_offset=40, unit_gap=56,
              level_height=90):
    """Dibuja el árbol completo en ``canvas``.

    - ``get_children(node)`` -> lista de hijos (con None en huecos vacíos).
    - ``get_label(node)`` -> texto a mostrar dentro del nodo ("" si no
      debe mostrar texto, por ejemplo en nodos internos de un trie).
    - ``get_style(node)`` -> tupla (color_relleno, color_borde).

    Devuelve {id(nodo): {"oval": id_canvas, "text": id_canvas,
    "x": x, "y": y, "node": nodo}} para poder animar cada nodo después
    (por ejemplo con ``canvas.itemconfig(items[...]["oval"], fill=...)``).
    """
    canvas.delete("all")
    items = {}
    if root is None:
        return items

    positions = compute_positions(root, get_children, level_height, unit_gap)

    def draw_edges(node):
        if node is None:
            return
        x, y = positions[id(node)]
        x += x_offset
        y += y_offset
        for child in get_children(node):
            if child is not None:
                cx, cy = positions[id(child)]
                cx += x_offset
                cy += y_offset
                canvas.create_line(x, y, cx, cy, fill="#94A3B8", width=2)
            draw_edges(child)

    def draw_nodes(node):
        if node is None:
            return
        x, y = positions[id(node)]
        x += x_offset
        y += y_offset
        fill, outline = get_style(node)
        oval = canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            fill=fill, outline=outline, width=2,
        )
        label = get_label(node)
        text = canvas.create_text(
            x, y, text=label, font=("Consolas", 12, "bold"), fill="#1E293B",
        )
        items[id(node)] = {"oval": oval, "text": text, "x": x, "y": y, "node": node}
        for child in get_children(node):
            draw_nodes(child)

    draw_edges(root)
    draw_nodes(root)

    bbox = canvas.bbox("all")
    if bbox:
        canvas.configure(scrollregion=(
            bbox[0] - 20, bbox[1] - 20, bbox[2] + 20, bbox[3] + 20
        ))
    return items


def build_scrollable_canvas(parent, bg="#f8fafc"):
    """Crea un contenedor con un Canvas desplazable en ambos ejes.

    Devuelve (contenedor, canvas) donde ``contenedor`` es el widget que
    debe empacarse en el layout, y ``canvas`` es donde se dibuja el árbol.
    """
    container = ctk.CTkFrame(
        parent, corner_radius=12, fg_color=("gray96", "gray14"),
        border_width=2, border_color=("gray78", "gray30"),
    )
    canvas = tk.Canvas(container, bg=bg, highlightthickness=0)
    vbar = ctk.CTkScrollbar(container, orientation="vertical", command=canvas.yview)
    hbar = ctk.CTkScrollbar(container, orientation="horizontal", command=canvas.xview)
    canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

    canvas.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))
    vbar.grid(row=0, column=1, sticky="ns", pady=(10, 0))
    hbar.grid(row=1, column=0, sticky="ew", padx=(10, 0))
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    return container, canvas


def show_placeholder(canvas, text):
    """Muestra un texto centrado cuando todavía no hay árbol que dibujar."""
    canvas.delete("all")
    canvas.configure(scrollregion=(0, 0, 500, 120))
    canvas.create_text(
        250, 55, text=text, font=("Consolas", 13), fill="#94A3B8",
        width=460, justify="center",
    )