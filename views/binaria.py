import random
from bisect import insort
import customtkinter as ctk
from views.base_view import BaseView
from views.persistence import save_json, load_json

_MAX_ELEMENTS = 1_000
_DEFAULT_RANGE = 100
_DEFAULT_KEY_SIZE = 3
_DEFAULT_SIZE = 10


class BinariaView(BaseView):

    def __init__(self, master, *, view_manager, **kwargs):
        super().__init__(
            master,
            view_manager=view_manager,
            title='Búsqueda Binaria',
            **kwargs
        )

        self._data = []
        self._cell_frames = []
        self._mode_var = ctk.StringVar(value='Aleatorio')
        self._anim_job = None
        self._is_animating = False
        self._pending_action = None

        self._build_ui()

    def _build_ui(self):
        self.add_title('Búsqueda Binaria')

        self.add_subtitle(
            'Divide el conjunto ordenado a la mitad en cada paso para localizar el valor.'
        )

        config = ctk.CTkFrame(
            self.content,
            corner_radius=12,
            fg_color=('gray92', 'gray17'),
            border_width=2,
            border_color=('gray78', 'gray30')
        )
        config.pack(fill='x', padx=10, pady=(0, 8))

        inner = ctk.CTkFrame(
            config,
            fg_color='transparent'
        )
        inner.pack(padx=16, pady=14, fill='x')

        row1 = ctk.CTkFrame(
            inner,
            fg_color='transparent'
        )
        row1.pack(fill='x', pady=(0, 10))

        ctk.CTkLabel(
            row1,
            text='Modo de carga:',
            font=ctk.CTkFont(size=14, weight='bold')
        ).pack(side='left', padx=(0, 12))

        self._mode_seg = ctk.CTkSegmentedButton(
            row1,
            values=['Aleatorio', 'Manual'],
            variable=self._mode_var,
            command=self._on_mode_change,
            font=ctk.CTkFont(size=13)
        )
        self._mode_seg.pack(side='left')

        row2 = ctk.CTkFrame(
            inner,
            fg_color='transparent'
        )
        row2.pack(fill='x', pady=(0, 10))

        self._range_entry = self._entry_with_label(
            row2,
            'Rango:',
            str(_DEFAULT_RANGE)
        )

        self._key_size_entry = self._entry_with_label(
            row2,
            'Tamaño de clave:',
            str(_DEFAULT_KEY_SIZE)
        )

        self._size_entry = self._entry_with_label(
            row2,
            'Cantidad:',
            str(_DEFAULT_SIZE)
        )

        self._btn_generate = ctk.CTkButton(
            row2,
            text='Añadir',
            width=120,
            height=34,
            font=ctk.CTkFont(size=13, weight='bold'),
            command=self._on_generate
        )
        self._btn_generate.pack(side='left', padx=(0, 8))

        self._btn_clear = ctk.CTkButton(
            row2,
            text='Limpiar',
            width=100,
            height=34,
            fg_color=('gray70', 'gray30'),
            hover_color=('gray60', 'gray40'),
            text_color=('black', 'white'),
            font=ctk.CTkFont(size=13, weight='bold'),
            command=self._on_clear
        )
        self._btn_clear.pack(side='left', padx=(0, 8))

        self._btn_save = ctk.CTkButton(
            row2,
            text='Guardar',
            width=100,
            height=34,
            command=self._on_save
        )
        self._btn_save.pack(side='right', padx=(8, 0))

        self._btn_load = ctk.CTkButton(
            row2,
            text='Cargar',
            width=100,
            height=34,
            command=self._on_load
        )
        self._btn_load.pack(side='right')

        self._info_label = ctk.CTkLabel(
            row2,
            text='',
            font=ctk.CTkFont(size=12),
            text_color=('gray50', 'gray55')
        )
        self._info_label.pack(side='left', padx=(0, 10))

        row3 = ctk.CTkFrame(
            inner,
            fg_color='transparent'
        )
        row3.pack(fill='x')

        ctk.CTkLabel(
            row3,
            text='Agregar valores:',
            font=ctk.CTkFont(size=14, weight='bold')
        ).pack(side='left', padx=(0, 8))

        self._manual_entry = ctk.CTkEntry(
            row3,
            height=34,
            placeholder_text='Ej: 12, 45, 7, 89, 23',
            font=ctk.CTkFont(size=14)
        )
        self._manual_entry.pack(side='left', fill='x', expand=True)

        search = ctk.CTkFrame(
            self.content,
            corner_radius=12,
            fg_color=('gray92', 'gray17'),
            border_width=2,
            border_color=('gray78', 'gray30')
        )
        search.pack(fill='x', padx=10, pady=(0, 8))

        si = ctk.CTkFrame(
            search,
            fg_color='transparent'
        )
        si.pack(padx=16, pady=12, fill='x')

        sr1 = ctk.CTkFrame(
            si,
            fg_color='transparent'
        )
        sr1.pack(fill='x', pady=(0, 8))

        ctk.CTkLabel(
            sr1,
            text='Valor objetivo:',
            font=ctk.CTkFont(size=14, weight='bold')
        ).pack(side='left', padx=(0, 8))

        self._search_entry = ctk.CTkEntry(
            sr1,
            width=110,
            height=34,
            placeholder_text='Ej: 45',
            font=ctk.CTkFont(size=14),
            justify='center'
        )
        self._search_entry.pack(side='left', padx=(0, 12))

        self._btn_search = ctk.CTkButton(
            sr1,
            text='Buscar',
            width=110,
            height=34,
            font=ctk.CTkFont(size=13, weight='bold'),
            command=self._on_start_search
        )
        self._btn_search.pack(side='left', padx=(0, 8))

        self._btn_delete = ctk.CTkButton(
            sr1,
            text='Eliminar',
            width=110,
            height=34,
            fg_color='#C62828',
            hover_color='#8E0000',
            text_color='white',
            font=ctk.CTkFont(size=13, weight='bold'),
            command=self._on_delete
        )
        self._btn_delete.pack(side='left', padx=(0, 8))

        self._btn_reset_search = ctk.CTkButton(
            sr1,
            text='Reiniciar Búsqueda',
            width=160,
            height=34,
            fg_color=('gray70', 'gray30'),
            hover_color=('gray60', 'gray40'),
            text_color=('black', 'white'),
            font=ctk.CTkFont(size=13, weight='bold'),
            command=self._on_reset_search
        )
        self._btn_reset_search.pack(side='left')

        sr2 = ctk.CTkFrame(
            si,
            fg_color='transparent'
        )
        sr2.pack(fill='x', pady=(0, 8))

        ctk.CTkLabel(
            sr2,
            text='Velocidad (ms):',
            font=ctk.CTkFont(size=13, weight='bold')
        ).pack(side='left', padx=(0, 8))

        self._speed_slider = ctk.CTkSlider(
            sr2,
            from_=100,
            to=2000,
            number_of_steps=19,
            width=180,
            command=self._on_speed_change
        )
        self._speed_slider.set(500)
        self._speed_slider.pack(side='left', padx=(0, 8))

        self._speed_label = ctk.CTkLabel(
            sr2,
            text='500 ms',
            font=ctk.CTkFont(size=13),
            text_color=('gray40', 'gray60'),
            width=65
        )
        self._speed_label.pack(side='left')

        box = ctk.CTkFrame(
            si,
            corner_radius=8,
            fg_color=('gray85', 'gray22'),
            border_width=1,
            border_color=('gray75', 'gray35')
        )
        box.pack(fill='x', pady=(4, 0))

        self._status_label = ctk.CTkLabel(
            box,
            text='Estado: Listo para realizar una búsqueda binaria.',
            font=ctk.CTkFont(size=13),
            text_color=('gray20', 'gray80'),
            anchor='w',
            padx=12,
            pady=8
        )
        self._status_label.pack(fill='x')

        # CORRECCIÓN: ahora sí existe _error_box
        self._error_box = ctk.CTkFrame(
            self.content,
            corner_radius=8,
            fg_color=('#FEE2E2', '#450A0A'),
            border_width=1,
            border_color=('#FCA5A5', '#7F1D1D')
        )
        self._error_box.pack(
            fill='x',
            padx=20,
            pady=(0, 4)
        )

        self._error_label = ctk.CTkLabel(
            self._error_box,
            text='',
            font=ctk.CTkFont(size=13, weight='bold'),
            text_color=('#991B1B', '#FCA5A5'),
            anchor='w',
            padx=12,
            pady=6
        )
        self._error_label.pack(fill='x')

        self._error_box.pack_forget()

        self._scroll_frame = ctk.CTkScrollableFrame(
            self.content,
            corner_radius=12,
            fg_color=('gray96', 'gray14'),
            border_width=2,
            border_color=('gray78', 'gray30'),
            label_text='Estructura generada (ordenada)',
            label_font=ctk.CTkFont(size=13, weight='bold')
        )
        self._scroll_frame.pack(
            fill='both',
            expand=True,
            padx=10,
            pady=(0, 10)
        )

        self._show_placeholder()
        self._on_mode_change(self._mode_var.get())

    def _entry_with_label(self, parent, text, default):
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=14, weight='bold')
        ).pack(side='left', padx=(0, 8))

        e = ctk.CTkEntry(
            parent,
            width=80,
            height=34,
            placeholder_text=default,
            font=ctk.CTkFont(size=14),
            justify='center'
        )
        e.pack(side='left', padx=(0, 16))
        e.insert(0, default)
        return e

    def _on_mode_change(self, selected_mode):
        if selected_mode == 'Aleatorio':
            self._manual_entry.configure(
                state='disabled',
                fg_color=('gray85', 'gray25')
            )
        else:
            self._manual_entry.configure(
                state='normal',
                fg_color=('white', 'gray20')
            )

        self._clear_error()

    def _validate_configuration(self):
        try:
            vr = int(self._range_entry.get().strip())
            ks = int(self._key_size_entry.get().strip())
            size = int(self._size_entry.get().strip())
        except ValueError:
            self._show_error(
                'Rango, tamaño de clave y cantidad deben ser números enteros.'
            )
            return None

        if vr <= 0 or ks <= 0 or size <= 0:
            self._show_error(
                'Rango, tamaño de clave y cantidad deben ser mayores que cero.'
            )
            return None

        if size > _MAX_ELEMENTS:
            self._show_error(
                f'La cantidad máxima es {_MAX_ELEMENTS:,}.'
            )
            return None

        max_key = 10 ** ks - 1

        if vr > max_key:
            self._show_error(
                f'El rango {vr} supera el máximo permitido para una clave '
                f'de {ks} dígitos ({max_key}).'
            )
            return None

        return vr, ks, size

    def _parse_manual_values(self, vr, ks):
        text = self._manual_entry.get().strip()

        if not text:
            self._show_error('Ingresa al menos un valor.')
            return None

        values = []

        for part in [p.strip() for p in text.split(',') if p.strip()]:
            try:
                v = int(part)
            except ValueError:
                self._show_error(
                    f'«{part}» no es un número entero válido.'
                )
                return None

            if not 1 <= v <= vr:
                self._show_error(
                    f'El valor {v} está fuera del rango permitido: 1 - {vr}.'
                )
                return None

            if len(str(abs(v))) > ks:
                self._show_error(
                    f'El valor {v} supera el tamaño de clave de {ks} dígitos.'
                )
                return None

            values.append(v)

        return values

    def _on_generate(self):
        self._on_reset_search()
        cfg = self._validate_configuration()

        if cfg is None:
            return

        vr, ks, size = cfg

        if self._mode_var.get() == 'Aleatorio':
            self._data = sorted(
                random.randint(1, vr)
                for _ in range(size)
            )
        else:
            vals = self._parse_manual_values(vr, ks)

            if vals is None:
                return

            remaining = size - len(self._data)

            if len(vals) > remaining:
                self._show_error(
                    f'Intentas agregar {len(vals)} valores, '
                    f'pero solo quedan {remaining} espacios disponibles.'
                )
                return

            for v in vals:
                insort(self._data, v)

            self._manual_entry.delete(0, 'end')

        self._render_structure()

        if self._mode_var.get() == 'Manual':
            self._info_label.configure(
                text=f'{len(self._data)}/{size} elementos ordenados'
            )
        else:
            self._info_label.configure(
                text=f'{len(self._data)} elementos generados y ordenados'
            )

        self._clear_error()

    def _on_clear(self):
        self._on_reset_search()
        self._data.clear()
        self._manual_entry.delete(0, 'end')
        self._info_label.configure(text='')
        self._clear_error()
        self._show_placeholder()

    def _render_structure(self):
        for w in self._scroll_frame.winfo_children():
            w.destroy()

        self._cell_frames.clear()

        if not self._data:
            return

        h = ctk.CTkFrame(
            self._scroll_frame,
            fg_color='transparent'
        )
        h.pack(fill='x', padx=6, pady=(8, 4))

        ctk.CTkLabel(
            h,
            text='Índice',
            width=80,
            font=ctk.CTkFont(size=13, weight='bold')
        ).pack(side='left', padx=(4, 16))

        ctk.CTkLabel(
            h,
            text='Valor',
            font=ctk.CTkFont(size=13, weight='bold')
        ).pack(side='left')

        for i, v in enumerate(self._data):
            bg = (
                ('gray88', 'gray22')
                if i % 2 == 0
                else ('gray94', 'gray17')
            )

            row = ctk.CTkFrame(
                self._scroll_frame,
                height=36,
                corner_radius=8,
                fg_color=bg
            )

            row._default_bg = bg

            row.pack(
                fill='x',
                padx=6,
                pady=2
            )
            row.pack_propagate(False)

            ctk.CTkLabel(
                row,
                text=str(i),
                width=80,
                font=ctk.CTkFont(
                    family='Consolas',
                    size=14
                ),
                anchor='center'
            ).pack(side='left', padx=(8, 16))

            ctk.CTkLabel(
                row,
                text=str(v),
                font=ctk.CTkFont(
                    family='Consolas',
                    size=14,
                    weight='bold'
                ),
                anchor='w'
            ).pack(side='left', padx=4)

            self._cell_frames.append(row)

    def _on_speed_change(self, v):
        self._speed_label.configure(
            text=f'{int(v)} ms'
        )

    def _set_controls_state(self, state):
        disabled = state == 'disabled'

        for w in (
            self._mode_seg,
            self._range_entry,
            self._key_size_entry,
            self._size_entry,
            self._manual_entry,
            self._btn_generate,
            self._btn_clear,
            self._btn_save,
            self._btn_load,
            self._search_entry,
            self._btn_search,
            self._btn_delete
        ):
            w.configure(
                state='disabled' if disabled else 'normal'
            )

        if not disabled:
            self._on_mode_change(
                self._mode_var.get()
            )

    def _reset_search_visuals(self):
        for r in self._cell_frames:
            if hasattr(r, '_default_bg'):
                r.configure(
                    fg_color=r._default_bg
                )

    def _get_target(self):
        raw = self._search_entry.get().strip()

        if not raw:
            self._show_error(
                'Ingresa el valor objetivo.'
            )
            return None

        try:
            return int(raw)
        except ValueError:
            self._show_error(
                'El valor a buscar debe ser un número entero.'
            )
            return None

    def _on_start_search(self):
        if self._is_animating:
            return

        if not self._data:
            self._show_error(
                'Primero genera o carga datos para buscar.'
            )
            return

        target = self._get_target()

        if target is None:
            return

        self._pending_action = 'search'
        self._begin_binary_animation(target)

    def _begin_binary_animation(self, target):
        self._reset_search_visuals()
        self._clear_error()
        self._set_controls_state('disabled')
        self._is_animating = True

        self._status_label.configure(
            text=f'Buscando {target} mediante búsqueda binaria...'
        )

        self._step_binary(
            0,
            len(self._data) - 1,
            target,
            1
        )

    def _step_binary(self, inicio, fin, target, step):
        if not self._is_animating:
            return

        if inicio > fin:
            for r in self._cell_frames:
                r.configure(
                    fg_color=('#FEE2E2', '#450A0A')
                )

            action = (
                'Eliminar'
                if self._pending_action == 'delete'
                else 'Búsqueda'
            )

            self._status_label.configure(
                text=f'{action}: {target} no fue encontrado. '
                     f'Intervalo agotado en {step - 1} paso(s).'
            )

            if self._pending_action == 'delete':
                self._show_error(
                    f'El elemento {target} no existe; no se eliminó nada.'
                )

            self._is_animating = False
            self._pending_action = None
            self._set_controls_state('normal')
            return

        medio = (inicio + fin) // 2

        for idx, row in enumerate(self._cell_frames):
            if idx < inicio or idx > fin:
                row.configure(
                    fg_color=('gray90', 'gray20')
                )
            else:
                row.configure(
                    fg_color=('gray82', 'gray28')
                )

        row = self._cell_frames[medio]

        row.configure(
            fg_color=('#FB923C', '#9A3412')
        )

        self._scroll_to_index(medio)

        val = self._data[medio]

        if val == target:
            row.configure(
                fg_color=('#4ADE80', '#166534')
            )

            if self._pending_action == 'delete':
                del self._data[medio]

                self._render_structure()

                self._info_label.configure(
                    text=f'{len(self._data)} elementos ordenados'
                )

                self._status_label.configure(
                    text=f'{target} encontrado en el índice '
                         f'{medio} y eliminado correctamente.'
                )

            else:
                self._status_label.configure(
                    text=f'Elemento {target} encontrado en el índice '
                         f'{medio}. Paso {step}'
                )

            self._is_animating = False
            self._pending_action = None
            self._set_controls_state('normal')
            return

        if target < val:
            self._status_label.configure(
                text=f'Paso {step}: MEDIO={medio}, valor={val}. '
                     f'{target} < {val} → descarto mitad derecha.'
            )

            self._anim_job = self.after(
                int(self._speed_slider.get()),
                lambda: self._step_binary(
                    inicio,
                    medio - 1,
                    target,
                    step + 1
                )
            )

        else:
            self._status_label.configure(
                text=f'Paso {step}: MEDIO={medio}, valor={val}. '
                     f'{target} > {val} → descarto mitad izquierda.'
            )

            self._anim_job = self.after(
                int(self._speed_slider.get()),
                lambda: self._step_binary(
                    medio + 1,
                    fin,
                    target,
                    step + 1
                )
            )

    def _on_delete(self):
        if self._is_animating:
            return

        if not self._data:
            self._show_error(
                'No hay datos para eliminar.'
            )
            return

        target = self._get_target()

        if target is None:
            return

        self._pending_action = 'delete'
        self._begin_binary_animation(target)

    def _on_reset_search(self):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass

        self._anim_job = None
        self._is_animating = False
        self._pending_action = None

        if hasattr(self, '_cell_frames'):
            self._reset_search_visuals()

        if hasattr(self, '_status_label'):
            self._status_label.configure(
                text='Estado: Búsqueda reiniciada. Listo para buscar.'
            )

        if hasattr(self, '_error_label'):
            self._clear_error()

        if hasattr(self, '_btn_search'):
            self._set_controls_state('normal')

    def _scroll_to_index(self, index):
        if not self._data:
            return

        try:
            self._scroll_frame._parent_canvas.yview_moveto(
                max(
                    0.0,
                    min(
                        1.0,
                        index / len(self._data)
                    )
                )
            )
        except Exception:
            pass

    def _on_save(self):
        if not self._data:
            self._show_error(
                'No hay información para guardar.'
            )
            return

        payload = {
            'tipo': 'binaria',
            'range': self._range_entry.get().strip(),
            'key_size': self._key_size_entry.get().strip(),
            'size': self._size_entry.get().strip(),
            'mode': self._mode_var.get(),
            'data': self._data
        }

        save_json(
            self,
            payload,
            'Guardar búsqueda binaria'
        )

    def _on_load(self):
        payload = load_json(
            self,
            'Cargar búsqueda binaria'
        )

        if payload is None:
            return

        if (
            payload.get('tipo') != 'binaria'
            or not isinstance(payload.get('data'), list)
        ):
            self._show_error(
                'El archivo no corresponde a una búsqueda binaria válida.'
            )
            return

        try:
            self._data = sorted(
                int(x)
                for x in payload['data']
            )

            if len(self._data) > _MAX_ELEMENTS:
                raise ValueError(
                    'La cantidad de elementos supera el máximo permitido.'
                )

            for entry, key in (
                (self._range_entry, 'range'),
                (self._key_size_entry, 'key_size'),
                (self._size_entry, 'size')
            ):
                if key in payload:
                    entry.delete(0, 'end')
                    entry.insert(
                        0,
                        str(payload[key])
                    )

            if payload.get('mode') in (
                'Aleatorio',
                'Manual'
            ):
                self._mode_var.set(
                    payload['mode']
                )
                self._mode_seg.set(
                    payload['mode']
                )

            self._render_structure()

            self._info_label.configure(
                text=f'{len(self._data)} elementos cargados y ordenados'
            )

            self._status_label.configure(
                text='Datos cargados correctamente.'
            )

            self._clear_error()
            self._on_mode_change(
                self._mode_var.get()
            )

        except (ValueError, TypeError) as exc:
            self._show_error(
                f'Archivo inválido: {exc}'
            )

    def _show_placeholder(self):
        for w in self._scroll_frame.winfo_children():
            w.destroy()

        self._cell_frames.clear()

        ctk.CTkLabel(
            self._scroll_frame,
            text='Configura los parámetros y presiona «Generar» para comenzar.',
            font=ctk.CTkFont(size=14),
            text_color=('gray50', 'gray55')
        ).pack(pady=40)

    def _show_error(self, msg):
        self._error_box.pack(
            fill='x',
            padx=20,
            pady=(0, 4)
        )

        self._error_label.configure(
            text=f'⚠ {msg}'
        )

    def _clear_error(self):
        self._error_label.configure(
            text=''
        )

        self._error_box.pack_forget()

    def destroy(self):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass

        self._anim_job = None
        super().destroy()