import json
from tkinter import filedialog, messagebox


def save_json(parent, data, title):
    path = filedialog.asksaveasfilename(
        parent=parent,
        title=title,
        defaultextension='.json',
        filetypes=[('Archivo de búsqueda', '*.json'), ('Todos los archivos', '*.*')],
    )
    if not path:
        return False
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        messagebox.showinfo('Guardar', 'La información se guardó correctamente.', parent=parent)
        return True
    except OSError as exc:
        messagebox.showerror('Guardar', f'No fue posible guardar el archivo:\n{exc}', parent=parent)
        return False


def load_json(parent, title):
    path = filedialog.askopenfilename(
        parent=parent,
        title=title,
        filetypes=[('Archivo de búsqueda', '*.json'), ('Todos los archivos', '*.*')],
    )
    if not path:
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except (OSError, json.JSONDecodeError) as exc:
        messagebox.showerror('Cargar', f'No fue posible cargar el archivo:\n{exc}', parent=parent)
        return None