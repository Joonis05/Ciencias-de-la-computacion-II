import random
import customtkinter as ctk
from views.base_view import BaseView
from views.persistence import save_json, load_json

_MAX_ELEMENTS = 1_000
_DEFAULT_KEY_SIZE = 3
_DEFAULT_SIZE = 10


class SecuencialView(BaseView):

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(master, view_manager=view_manager, title='Búsqueda Secuencial', **kwargs)
        self._data = []
        self._capacity = 0
        self._structure_created = False
        self._cell_frames = []
        self._mode_var = ctk.StringVar(value='Aleatorio')
        self._anim_job = None
        self._is_animating = False
        self._last_found_index = None
        self._pending_action = None
        self._build_ui()

    def _build_ui(self):
        self.add_title('Búsqueda Secuencial')
        self.add_subtitle('Recorre los registros uno a uno hasta encontrar el valor buscado.')

        config_frame = ctk.CTkFrame(self.content, corner_radius=12, fg_color=('gray92', 'gray17'), border_width=2, border_color=('gray78', 'gray30'))
        config_frame.pack(fill='x', padx=10, pady=(0, 8))
        inner = ctk.CTkFrame(config_frame, fg_color='transparent')
        inner.pack(padx=16, pady=14, fill='x')

        row1 = ctk.CTkFrame(inner, fg_color='transparent')
        row1.pack(fill='x', pady=(0, 10))
        ctk.CTkLabel(row1, text='Modo de carga:', font=ctk.CTkFont(size=14, weight='bold')).pack(side='left', padx=(0, 12))
        self._mode_seg = ctk.CTkSegmentedButton(row1, values=['Aleatorio', 'Manual'], variable=self._mode_var, command=self._on_mode_change, font=ctk.CTkFont(size=13))
        self._mode_seg.pack(side='left')

        row2 = ctk.CTkFrame(inner, fg_color='transparent')
        row2.pack(fill='x', pady=(0, 10))
        self._key_size_entry = self._entry_with_label(row2, 'Tamaño de clave:', str(_DEFAULT_KEY_SIZE))
        self._size_entry = self._entry_with_label(row2, 'Cantidad de registros:', str(_DEFAULT_SIZE))
        self._btn_structure = ctk.CTkButton(row2, text='Generar estructura', width=150, height=34, font=ctk.CTkFont(size=13, weight='bold'), command=self._on_generate_structure)
        self._btn_structure.pack(side='left', padx=(0, 8))
        self._btn_generate = ctk.CTkButton(row2, text='Añadir', width=100, height=34, font=ctk.CTkFont(size=13, weight='bold'), command=self._on_add)
        self._btn_generate.pack(side='left', padx=(0, 8))
        self._btn_clear = ctk.CTkButton(row2, text='Limpiar', width=100, height=34, fg_color=('gray70', 'gray30'), hover_color=('gray60', 'gray40'), text_color=('black', 'white'), font=ctk.CTkFont(size=13, weight='bold'), command=self._on_clear)
        self._btn_clear.pack(side='left', padx=(0, 8))
        self._btn_save = ctk.CTkButton(row2, text='Guardar', width=100, height=34, command=self._on_save)
        self._btn_save.pack(side='right', padx=(8, 0))
        self._btn_load = ctk.CTkButton(row2, text='Cargar', width=100, height=34, command=self._on_load)
        self._btn_load.pack(side='right')
        self._info_label = ctk.CTkLabel(row2, text='', font=ctk.CTkFont(size=12), text_color=('gray50', 'gray55'))
        self._info_label.pack(side='left', padx=(0, 10))

        row3 = ctk.CTkFrame(inner, fg_color='transparent')
        row3.pack(fill='x')
        ctk.CTkLabel(row3, text='Agregar valores:', font=ctk.CTkFont(size=14, weight='bold')).pack(side='left', padx=(0, 8))
        self._manual_entry = ctk.CTkEntry(row3, height=34, placeholder_text='Ej: 12, 45, 7, 89, 23', font=ctk.CTkFont(size=14))
        self._manual_entry.pack(side='left', fill='x', expand=True)

        search_frame = ctk.CTkFrame(self.content, corner_radius=12, fg_color=('gray92', 'gray17'), border_width=2, border_color=('gray78', 'gray30'))
        search_frame.pack(fill='x', padx=10, pady=(0, 8))
        search_inner = ctk.CTkFrame(search_frame, fg_color='transparent')
        search_inner.pack(padx=16, pady=12, fill='x')
        s_row1 = ctk.CTkFrame(search_inner, fg_color='transparent')
        s_row1.pack(fill='x', pady=(0, 8))
        ctk.CTkLabel(s_row1, text='Valor objetivo:', font=ctk.CTkFont(size=14, weight='bold')).pack(side='left', padx=(0, 8))
        self._search_entry = ctk.CTkEntry(s_row1, width=110, height=34, placeholder_text='Ej: 45', font=ctk.CTkFont(size=14), justify='center')
        self._search_entry.pack(side='left', padx=(0, 12))
        self._btn_search = ctk.CTkButton(s_row1, text='Buscar', width=110, height=34, font=ctk.CTkFont(size=13, weight='bold'), command=self._on_start_search)
        self._btn_search.pack(side='left', padx=(0, 8))
        self._btn_delete = ctk.CTkButton(s_row1, text='Eliminar', width=110, height=34, fg_color='#C62828', hover_color='#8E0000', text_color='white', font=ctk.CTkFont(size=13, weight='bold'), command=self._on_delete)
        self._btn_delete.pack(side='left', padx=(0, 8))
        self._btn_reset_search = ctk.CTkButton(s_row1, text='Reiniciar Búsqueda', width=160, height=34, fg_color=('gray70', 'gray30'), hover_color=('gray60', 'gray40'), text_color=('black', 'white'), font=ctk.CTkFont(size=13, weight='bold'), command=self._on_reset_search)
        self._btn_reset_search.pack(side='left')

        s_row2 = ctk.CTkFrame(search_inner, fg_color='transparent')
        s_row2.pack(fill='x', pady=(0, 8))
        ctk.CTkLabel(s_row2, text='Velocidad (ms):', font=ctk.CTkFont(size=13, weight='bold')).pack(side='left', padx=(0, 8))
        self._speed_slider = ctk.CTkSlider(s_row2, from_=100, to=2000, number_of_steps=19, width=180, command=self._on_speed_change)
        self._speed_slider.set(500)
        self._speed_slider.pack(side='left', padx=(0, 8))
        self._speed_label = ctk.CTkLabel(s_row2, text='500 ms', font=ctk.CTkFont(size=13), text_color=('gray40', 'gray60'), width=65)
        self._speed_label.pack(side='left')
        self._status_box = ctk.CTkFrame(search_inner, corner_radius=8, fg_color=('gray85', 'gray22'), border_width=1, border_color=('gray75', 'gray35'))
        self._status_box.pack(fill='x', pady=(4, 0))
        self._status_label = ctk.CTkLabel(self._status_box, text='Estado: estructura no generada.', font=ctk.CTkFont(size=14, weight='bold'), text_color=('gray20', 'gray80'), anchor='w', padx=12, pady=10)
        self._status_label.pack(fill='x')

        self._error_box = ctk.CTkFrame(self.content, corner_radius=8, fg_color=('#FEE2E2', '#450A0A'), border_width=1, border_color=('#FCA5A5', '#7F1D1D'))
        self._error_label = ctk.CTkLabel(self._error_box, text='', font=ctk.CTkFont(size=13, weight='bold'), text_color=('#991B1B', '#FCA5A5'), anchor='w', padx=12, pady=6)
        self._error_label.pack(fill='x')
        self._error_box.pack_forget()
        self._scroll_frame = ctk.CTkScrollableFrame(self.content, corner_radius=12, fg_color=('gray96', 'gray14'), border_width=2, border_color=('gray78', 'gray30'))
        self._scroll_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        self._show_placeholder()
        self._on_mode_change(self._mode_var.get())

    def _entry_with_label(self, parent, text, default):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=14, weight='bold')).pack(side='left', padx=(0, 8))
        entry = ctk.CTkEntry(parent, width=105, height=34, placeholder_text=default, font=ctk.CTkFont(size=14), justify='center')
        entry.pack(side='left', padx=(0, 16))
        entry.insert(0, default)
        return entry

    def _on_mode_change(self, selected_mode):
        self._manual_entry.configure(state='disabled' if selected_mode == 'Aleatorio' else 'normal', fg_color=('gray85', 'gray25') if selected_mode == 'Aleatorio' else ('white', 'gray20'))
        self._clear_error()

    def _validate_configuration(self):
        try:
            key_size = int(self._key_size_entry.get().strip())
            size = int(self._size_entry.get().strip())
        except ValueError:
            self._show_error('Tamaño de clave y cantidad de registros deben ser números enteros.')
            return None
        if key_size <= 0 or size <= 0:
            self._show_error('Tamaño de clave y cantidad de registros deben ser mayores que cero.')
            return None
        if size > _MAX_ELEMENTS:
            self._show_error(f'La cantidad máxima de registros es {_MAX_ELEMENTS:,}.')
            return None
        min_key = 1 if key_size == 1 else (10 ** (key_size - 1))
        max_key = (10 ** key_size) - 1
        return key_size, size, min_key, max_key

    def _parse_manual_values(self, min_key, max_key, key_size):
        text = self._manual_entry.get().strip()
        if not text:
            self._show_error('Ingresa al menos un valor.')
            return None
        values = []
        for part in [p.strip() for p in text.split(',') if p.strip()]:
            try:
                value = int(part)
            except ValueError:
                self._show_error(f'«{part}» no es un número entero válido.')
                return None
            if not (min_key <= value <= max_key):
                self._show_error(f'El valor {value} debe tener exactamente {key_size} dígitos (entre {min_key} y {max_key}).')
                return None
            values.append(value)
        return values

    def _on_generate_structure(self):
        if self._is_animating:
            return
        cfg = self._validate_configuration()
        if cfg is None:
            return
        _, size, _, _ = cfg
        if self._structure_created:
            self._show_error('La estructura ya fue generada. Presiona Limpiar para crear una nueva.')
            return
        self._capacity = size
        self._data = []
        self._structure_created = True
        self._render_structure()
        self._info_label.configure(text=f'0/{size} registros')
        self._status_label.configure(text=f'Estructura generada con {size} registros vacíos. Ahora puedes añadir datos.')
        self._clear_error()

    def _on_add(self):
        if self._is_animating:
            return
        if not self._structure_created:
            self._show_error('Primero debes generar la estructura.')
            return
        if len(self._data) >= self._capacity:
            self._show_error('La estructura ya está llena.')
            return
        cfg = self._validate_configuration()
        if cfg is None:
            return
        key_size, _, min_key, max_key = cfg
        if self._mode_var.get() == 'Aleatorio':
            remaining = self._capacity - len(self._data)
            new_values = [random.randint(min_key, max_key) for _ in range(remaining)]
        else:
            new_values = self._parse_manual_values(min_key, max_key, key_size)
            if new_values is None:
                return
            remaining = self._capacity - len(self._data)
            if len(new_values) > remaining:
                self._show_error(f'Solo quedan {remaining} registros disponibles.')
                return
        self._data.extend(new_values)
        self._data.sort()
        self._manual_entry.delete(0, 'end')
        self._render_structure()
        self._info_label.configure(text=f'{len(self._data)}/{self._capacity} registros ordenados')
        self._status_label.configure(text=f'Se añadieron {len(new_values)} registro(s). La estructura se mantiene ordenada.')
        self._clear_error()

    def _on_clear(self):
        self._on_reset_search()
        self._data.clear()
        self._capacity = 0
        self._structure_created = False
        self._manual_entry.delete(0, 'end')
        self._info_label.configure(text='')
        self._clear_error()
        self._show_placeholder()
        self._status_label.configure(text='Estado: estructura limpiada.')

    def _render_structure(self):
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()
        self._cell_frames.clear()
        if not self._structure_created:
            return

        table_box = ctk.CTkFrame(
            self._scroll_frame,
            corner_radius=10,
            fg_color=('gray95', 'gray16'),
            border_width=2,
            border_color=('gray75', 'gray30')
        )
        table_box.pack(fill='x', padx=30, pady=15)

        header = ctk.CTkFrame(table_box, corner_radius=0, fg_color=('gray85', 'gray24'), height=40)
        header.pack(fill='x')
        header.pack_propagate(False)

        ctk.CTkLabel(header, text='Indice', font=ctk.CTkFont(size=14, weight='bold'), text_color=('black', 'white'), width=140, anchor='center').pack(side='left')
        ctk.CTkFrame(header, width=2, fg_color=('gray75', 'gray35')).pack(side='left', fill='y')
        ctk.CTkLabel(header, text='Clave', font=ctk.CTkFont(size=14, weight='bold'), text_color=('black', 'white'), anchor='center').pack(side='left', fill='x', expand=True)

        ctk.CTkFrame(table_box, height=2, fg_color=('gray75', 'gray35')).pack(fill='x')

        n_filled = len(self._data)
        total_cap = self._capacity

        rows_to_render = []
        if n_filled == 0:
            if total_cap <= 3:
                for i in range(total_cap):
                    rows_to_render.append((str(i + 1), '', None, False))
            else:
                rows_to_render.append(('1', '', None, False))
                rows_to_render.append(('⋮', '', None, False))
                rows_to_render.append((str(total_cap), '', None, False))
        else:
            for i in range(n_filled):
                rows_to_render.append((str(i + 1), str(self._data[i]), i, True))
            
            remaining = total_cap - n_filled
            if remaining == 1:
                rows_to_render.append((str(total_cap), '', None, False))
            elif remaining > 1:
                rows_to_render.append(('⋮', '', None, False))
                rows_to_render.append((str(total_cap), '', None, False))

        for idx_row, (idx_str, val_str, data_idx, is_real_cell) in enumerate(rows_to_render):
            if idx_row > 0:
                ctk.CTkFrame(table_box, height=1, fg_color=('gray80', 'gray30')).pack(fill='x')

            bg = ('gray90', 'gray20') if idx_row % 2 == 0 else ('gray94', 'gray17')
            row = ctk.CTkFrame(table_box, height=38, corner_radius=0, fg_color=bg)
            row._default_bg = bg
            row.pack(fill='x')
            row.pack_propagate(False)

            ctk.CTkLabel(row, text=idx_str, font=ctk.CTkFont(family='Consolas', size=14, weight='bold'), text_color=('gray30', 'gray75') if idx_str == '⋮' else ('black', 'white'), width=140, anchor='center').pack(side='left')
            ctk.CTkFrame(row, width=2, fg_color=('gray75', 'gray35')).pack(side='left', fill='y')
            ctk.CTkLabel(row, text=val_str, font=ctk.CTkFont(family='Consolas', size=14, weight='bold' if val_str not in ('', '⋮') else 'normal'), text_color=('gray40', 'gray60') if val_str in ('', '⋮') else ('black', 'white'), anchor='center').pack(side='left', fill='x', expand=True)

            if is_real_cell and data_idx is not None:
                self._cell_frames.append(row)

    def _on_speed_change(self, value):
        self._speed_label.configure(text=f'{int(value)} ms')

    def _set_controls_state(self, state):
        disabled = state == 'disabled'
        for widget in (self._mode_seg, self._key_size_entry, self._size_entry, self._manual_entry, self._btn_structure, self._btn_generate, self._btn_clear, self._btn_save, self._btn_load, self._search_entry, self._btn_search, self._btn_delete, self._btn_reset_search, self._speed_slider):
            widget.configure(state='disabled' if disabled else 'normal')
        if not disabled:
            self._on_mode_change(self._mode_var.get())

    def _reset_search_visuals(self):
        for row in self._cell_frames:
            if row is not None and hasattr(row, '_default_bg'):
                row.configure(fg_color=row._default_bg)

    def _get_target(self):
        raw = self._search_entry.get().strip()
        if not raw:
            self._show_error('Ingresa el valor objetivo.')
            return None
        try:
            val = int(raw)
            cfg = self._validate_configuration()
            if cfg is not None:
                key_size, _, min_key, max_key = cfg
                if not (min_key <= val <= max_key):
                    self._show_error(f'El valor a buscar debe tener exactamente {key_size} dígitos (entre {min_key} y {max_key}).')
                    return None
            return val
        except ValueError:
            self._show_error('El valor a buscar debe ser un número entero.')
            return None

    def _on_start_search(self):
        if self._is_animating:
            return
        if not self._structure_created or not self._data:
            self._show_error('Primero genera la estructura y añade registros.')
            return
        target = self._get_target()
        if target is None:
            return
        self._pending_action = 'search'
        self._begin_sequential_animation(target)

    def _begin_sequential_animation(self, target):
        self._reset_search_visuals()
        self._clear_error()
        self._set_controls_state('disabled')
        self._is_animating = True
        self._status_label.configure(text=f'Buscando {target} de forma secuencial...')
        self._step_sequential(0, target, 1)

    def _step_sequential(self, index, target, step):
        if not self._is_animating:
            return
        if index >= len(self._data):
            for row in self._cell_frames[:len(self._data)]:
                if row is not None:
                    row.configure(fg_color=('#FEE2E2', '#450A0A'))
            action = 'Eliminación' if self._pending_action == 'delete' else 'Búsqueda'
            self._status_label.configure(text=f'{action}: {target} no fue encontrado después de revisar {len(self._data)} registros.')
            if self._pending_action == 'delete':
                self._show_error(f'El registro {target} no existe; no se eliminó nada.')
            self._is_animating = False
            self._pending_action = None
            self._set_controls_state('normal')
            return
        if index > 0 and index - 1 < len(self._cell_frames) and hasattr(self._cell_frames[index - 1], '_default_bg'):
            self._cell_frames[index - 1].configure(fg_color=self._cell_frames[index - 1]._default_bg)
        row = self._cell_frames[index]
        row.configure(fg_color=('#FDE047', '#854D0E'))
        current = self._data[index]
        display_index = index + 1
        if current == target:
            row.configure(fg_color=('#4ADE80', '#166534'))
            if self._pending_action == 'delete':
                del self._data[index]
                self._render_structure()
                self._info_label.configure(text=f'{len(self._data)}/{self._capacity} registros ordenados')
                self._status_label.configure(text=f'{target} encontrado en el índice {display_index} y eliminado correctamente.')
            else:
                self._last_found_index = index
                self._status_label.configure(text=f'Elemento {target} encontrado en el índice {display_index}. Paso {step}')
            self._is_animating = False
            self._pending_action = None
            self._set_controls_state('normal')
            return
        self._status_label.configure(text=f'Paso {step}: comparando índice {display_index}: {current} ≠ {target}')
        self._anim_job = self.after(int(self._speed_slider.get()), lambda: self._step_sequential(index + 1, target, step + 1))

    def _on_delete(self):
        if self._is_animating:
            return
        if not self._structure_created or not self._data:
            self._show_error('No hay registros para eliminar.')
            return
        target = self._get_target()
        if target is None:
            return
        self._pending_action = 'delete'
        self._begin_sequential_animation(target)

    def _on_reset_search(self):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
        self._anim_job = None
        self._is_animating = False
        self._last_found_index = None
        self._pending_action = None
        if hasattr(self, '_cell_frames'):
            self._reset_search_visuals()
        if hasattr(self, '_status_label'):
            self._status_label.configure(text='Estado: búsqueda reiniciada. Listo para buscar.')
        self._clear_error()
        if hasattr(self, '_btn_search'):
            self._set_controls_state('normal')

    def _scroll_to_index(self, index):
        return

    def _on_save(self):
        if not self._structure_created:
            self._show_error('Primero genera la estructura.')
            return
        payload = {
            'tipo': 'secuencial',
            'key_size': self._key_size_entry.get().strip(),
            'size': self._capacity,
            'mode': self._mode_var.get(),
            'data': self._data,
            'structure_created': self._structure_created,
        }
        save_json(self, payload, 'Guardar búsqueda secuencial')

    def _on_load(self):
        payload = load_json(self, 'Cargar búsqueda secuencial')
        if payload is None:
            return
        if payload.get('tipo') != 'secuencial' or not isinstance(payload.get('data'), list):
            self._show_error('El archivo no corresponde a una búsqueda secuencial válida.')
            return
        try:
            data = sorted(int(x) for x in payload['data'])
            capacity = int(payload.get('size', len(data)))
            key_size = int(payload.get('key_size', _DEFAULT_KEY_SIZE))
            if capacity <= 0 or capacity > _MAX_ELEMENTS:
                raise ValueError('La cantidad de registros no es válida.')
            max_key = (10 ** key_size) - 1
            if any(x < 1 or x > max_key for x in data) or len(data) > capacity:
                raise ValueError('Los datos del archivo no son compatibles con la configuración.')
            self._capacity = capacity
            self._structure_created = True
            self._data = data
            self._key_size_entry.delete(0, 'end')
            self._key_size_entry.insert(0, str(key_size))
            self._size_entry.delete(0, 'end')
            self._size_entry.insert(0, str(capacity))
            if payload.get('mode') in ('Aleatorio', 'Manual'):
                self._mode_var.set(payload['mode'])
                self._mode_seg.set(payload['mode'])
            self._render_structure()
            self._info_label.configure(text=f'{len(self._data)}/{self._capacity} registros ordenados')
            self._status_label.configure(text='Estructura cargada correctamente.')
            self._clear_error()
            self._on_mode_change(self._mode_var.get())
        except (ValueError, TypeError) as exc:
            self._show_error(f'Archivo inválido: {exc}')

    def _show_placeholder(self):
        for w in self._scroll_frame.winfo_children():
            w.destroy()
        self._cell_frames.clear()
        ctk.CTkLabel(self._scroll_frame, text='Configura tamaño de clave y cantidad de registros, luego presiona «Generar estructura».', font=ctk.CTkFont(size=14), text_color=('gray50', 'gray55')).pack(pady=40)

    def _show_error(self, msg):
        self._error_box.pack(fill='x', padx=20, pady=(0, 4))
        self._error_label.configure(text=msg)

    def _clear_error(self):
        self._error_label.configure(text='')
        self._error_box.pack_forget()

    def destroy(self):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
        self._anim_job = None
        super().destroy()
