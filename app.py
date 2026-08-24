"""
==========================================================
  Ciencias de la computación 2 — Aplicación de Algoritmos de Búsqueda y Grafos
==========================================================
  Ejecutar:  python app.py
  Requisitos: pip install customtkinter
==========================================================
"""

import customtkinter as ctk
from views.view_manager import ViewManager


def main():
    """Inicializa la aplicación y arranca el loop principal."""

    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue") 

    root = ctk.CTk()
    root.title("Ciencias 2 — Búsquedas y Grafos")
    root.geometry("900x600")
    root.minsize(700, 450)

    view_manager = ViewManager(root)
    view_manager.pack(fill="both", expand=True)

    view_manager.show_view("inicio")

    root.mainloop()


if __name__ == "__main__":
    main()
