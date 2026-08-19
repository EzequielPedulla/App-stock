import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox


class CajaForm(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.pack(fill=BOTH, expand=True)
        self.caja_controller = None  # Lo setea el controlador
        self.tipo_seleccionado = 'gasto'
        self.forma_pago_seleccionada = 'efectivo'
        self._create_widgets()

    def _create_widgets(self):
        # Título
        ttk.Label(
            self, text="Caja", font=("Segoe UI", 24, "bold")
        ).pack(anchor=W, pady=(0, 15))

        # ===== Navegación entre días: por defecto se ve hoy, pero se
        # puede ir para atrás a revisar días anteriores (sin poder
        # editarlos) y volver a hoy con un solo botón. =====
        nav_row = ttk.Frame(self)
        nav_row.pack(fill=X, pady=(0, 10))
        self.dia_anterior_button = ttk.Button(
            nav_row, text="◀ Día anterior", bootstyle="secondary", width=14)
        self.dia_anterior_button.pack(side=LEFT)
        self.fecha_label = ttk.Label(
            nav_row, text="Hoy", font=("Segoe UI", 13, "bold"))
        self.fecha_label.pack(side=LEFT, padx=15)
        self.dia_siguiente_button = ttk.Button(
            nav_row, text="Día siguiente ▶", bootstyle="secondary", width=14)
        self.dia_siguiente_button.pack(side=LEFT)
        self.volver_hoy_button = ttk.Button(
            nav_row, text="Volver a hoy", bootstyle="info", width=12)
        # Se muestra/oculta según el día que se esté viendo (ver update_fecha).

        self.estado_label = ttk.Label(
            self, text="", font=("Segoe UI", 11, "bold"), foreground="#c0392b")
        self.estado_label.pack(anchor=W, pady=(0, 10))

        # ===== Resultado del día: el número más importante de la
        # pantalla, arriba de todo, bien grande. Se muestra como una
        # cuenta simple: total vendido menos total gastado = resultado,
        # para que se entienda de un vistazo de dónde sale ese número. =====
        resultado_card = ttk.Frame(self, bootstyle="light", padding=20)
        resultado_card.pack(fill=X, pady=(0, 15))

        cuenta_row = ttk.Frame(resultado_card)
        cuenta_row.pack(fill=X)

        ventas_col = ttk.Frame(cuenta_row)
        ventas_col.pack(side=LEFT)
        ttk.Label(
            ventas_col, text="Total Ventas", font=("Segoe UI", 13)
        ).pack(anchor=W)
        self.label_total_ventas_dia = ttk.Label(
            ventas_col, text="$0.00", font=("Segoe UI", 22, "bold"),
            bootstyle="success")
        self.label_total_ventas_dia.pack(anchor=W)

        ttk.Label(
            cuenta_row, text="−", font=("Segoe UI", 22)
        ).pack(side=LEFT, padx=15, pady=(20, 0))

        gastos_col = ttk.Frame(cuenta_row)
        gastos_col.pack(side=LEFT)
        ttk.Label(
            gastos_col, text="Total Gastos", font=("Segoe UI", 13)
        ).pack(anchor=W)
        self.label_total_gastos_dia = ttk.Label(
            gastos_col, text="$0.00", font=("Segoe UI", 22, "bold"),
            bootstyle="danger")
        self.label_total_gastos_dia.pack(anchor=W)

        ttk.Label(
            cuenta_row, text="=", font=("Segoe UI", 22)
        ).pack(side=LEFT, padx=15, pady=(20, 0))

        resultado_col = ttk.Frame(cuenta_row)
        resultado_col.pack(side=LEFT)
        ttk.Label(
            resultado_col, text="Resultado de hoy", font=("Segoe UI", 13)
        ).pack(anchor=W)
        self.label_resultado_dia = ttk.Label(
            resultado_col, text="$0.00", font=("Segoe UI", 32, "bold"),
            bootstyle="success")
        self.label_resultado_dia.pack(anchor=W)

        ttk.Label(
            resultado_card,
            text="Gastos incluye retiros. No cuenta lo fiado (todavía no se cobró) "
                 "ni el bolsillo del dueño (no es plata del negocio).",
            font=("Segoe UI", 9), foreground="gray"
        ).pack(anchor=W, pady=(10, 0))

        # ===== Fila de tarjetas: ventas del día por método =====
        ventas_row = ttk.Frame(self)
        ventas_row.pack(fill=X, pady=(0, 15))

        self.label_ventas_efectivo = self._stat_card(
            ventas_row, "Ventas Efectivo", "success")
        self.label_ventas_transferencia = self._stat_card(
            ventas_row, "Ventas Transferencia", "info")
        self.label_ventas_posnet = self._stat_card(
            ventas_row, "Ventas Posnet", "info")
        self.label_ventas_fiado = self._stat_card(
            ventas_row, "Ventas Fiado (no cobradas)", "secondary")

        # ===== Card de fondo inicial y egresos =====
        resumen_card = ttk.Frame(self, bootstyle="light", padding=20)
        resumen_card.pack(fill=X, pady=(0, 15))

        ttk.Label(
            resumen_card, text="Fondo, ingresos y egresos del día",
            font=("Segoe UI", 14, "bold")
        ).grid(row=0, column=0, columnspan=4, sticky=W, pady=(0, 15))

        # Fondo inicial (editable)
        ttk.Label(resumen_card, text="Fondo inicial:",
                 font=("Segoe UI", 11)).grid(row=1, column=0, sticky=W, pady=4)
        fondo_frame = ttk.Frame(resumen_card)
        fondo_frame.grid(row=1, column=1, sticky=W, padx=(10, 30))
        self.fondo_inicial_entry = ttk.Entry(fondo_frame, width=12)
        self.fondo_inicial_entry.pack(side=LEFT)
        self.guardar_fondo_button = ttk.Button(
            fondo_frame, text="Guardar", width=9, bootstyle="secondary")
        self.guardar_fondo_button.pack(side=LEFT, padx=(5, 0))

        self._resumen_label("Ingresos (plata que entró):", 1, 2, resumen_card, "label_total_ingresos")
        self._resumen_label("Gastos en efectivo:", 2, 0, resumen_card, "label_total_gastos_efectivo")
        self._resumen_label("Gastos por transferencia:", 2, 2, resumen_card, "label_total_gastos_transferencia")
        self._resumen_label("Total Retiros:", 3, 0, resumen_card, "label_total_retiros")
        self._resumen_label("Bolsillo del dueño:", 3, 2, resumen_card, "label_total_bolsillo")

        ttk.Label(
            resumen_card, text="Transferencia y bolsillo no afectan el efectivo de la caja",
            font=("Segoe UI", 9), foreground="gray"
        ).grid(row=4, column=0, columnspan=4, sticky=W, pady=(8, 0))

        # ===== Banner de efectivo esperado (color según el signo) =====
        efectivo_card = ttk.Frame(self, bootstyle="light", padding=20)
        efectivo_card.pack(fill=X, pady=(0, 15))

        ttk.Label(
            efectivo_card, text="Efectivo esperado en caja",
            font=("Segoe UI", 13)
        ).pack(side=LEFT)
        self.label_efectivo_esperado = ttk.Label(
            efectivo_card, text="$0.00", font=("Segoe UI", 22, "bold"),
            bootstyle="success")
        self.label_efectivo_esperado.pack(side=LEFT, padx=(15, 0))

        self.cerrar_button = ttk.Button(
            efectivo_card, text="🔒 Cerrar Caja", bootstyle="danger", width=18)
        self.cerrar_button.pack(side=RIGHT)

        # ===== Card para agregar movimientos =====
        mov_card = ttk.Frame(self, bootstyle="light", padding=20)
        mov_card.pack(fill=X, pady=(0, 15))

        ttk.Label(
            mov_card, text="Agregar gasto / retiro / pago de bolsillo",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor=W, pady=(0, 10))

        tipo_row = ttk.Frame(mov_card)
        tipo_row.pack(fill=X, pady=(0, 10))
        self.tipo_buttons = {}
        for tipo, label in (
            ('gasto', 'Gastos'),
            ('retiro', 'Retiro'),
            ('bolsillo', 'Bolsillo del dueño'),
            ('ingreso', 'Ingreso a la caja'),
        ):
            btn = ttk.Button(
                tipo_row, text=label, width=18,
                bootstyle="primary" if tipo == 'gasto' else "secondary",
                command=lambda t=tipo: self._select_tipo(t)
            )
            btn.pack(side=LEFT, padx=(0, 5))
            self.tipo_buttons[tipo] = btn

        # Forma de pago del gasto: solo aplica cuando tipo == 'gasto' (un
        # retiro siempre es efectivo por definición, y el bolsillo del
        # dueño ya está separado como su propia categoría).
        self.forma_pago_row = ttk.Frame(mov_card)
        self.forma_pago_row.pack(fill=X, pady=(0, 10))
        ttk.Label(
            self.forma_pago_row, text="¿Cómo se pagó este gasto?",
            font=("Segoe UI", 10), foreground="gray"
        ).pack(side=LEFT, padx=(0, 10))
        self.forma_pago_buttons = {}
        for forma, label in (('efectivo', 'Efectivo (caja)'),
                             ('transferencia', 'Transferencia')):
            btn = ttk.Button(
                self.forma_pago_row, text=label, width=15,
                bootstyle="primary" if forma == 'efectivo' else "secondary",
                command=lambda f=forma: self._select_forma_pago(f)
            )
            btn.pack(side=LEFT, padx=(0, 5))
            self.forma_pago_buttons[forma] = btn

        form_row = self.mov_form_row = ttk.Frame(mov_card)
        form_row.pack(fill=X)

        ttk.Label(form_row, text="Descripción:", font=("Segoe UI", 11)).grid(
            row=0, column=0, sticky=W)
        self.descripcion_entry = ttk.Entry(form_row, font=("Segoe UI", 11))
        self.descripcion_entry.grid(row=1, column=0, sticky=EW, padx=(0, 10))

        ttk.Label(form_row, text="Monto:", font=("Segoe UI", 11)).grid(
            row=0, column=1, sticky=W)
        self.monto_entry = ttk.Entry(form_row, font=("Segoe UI", 11), width=15)
        self.monto_entry.grid(row=1, column=1, sticky=EW, padx=(0, 10))

        self.agregar_movimiento_button = ttk.Button(
            form_row, text="Agregar", bootstyle="success", width=12)
        self.agregar_movimiento_button.grid(row=1, column=2)

        form_row.columnconfigure(0, weight=1)

        # ===== Tabla de movimientos del día =====
        self.movimientos_title_label = ttk.Label(
            self, text="Movimientos de hoy", font=("Segoe UI", 14, "bold"))
        self.movimientos_title_label.pack(anchor=W, pady=(0, 10))

        table_frame = ttk.Frame(self, bootstyle="light", padding=10)
        table_frame.pack(fill=BOTH, expand=True)

        # Esta tabla era la única de toda la app sin un estilo de letra
        # propio, así que quedaba con el tamaño chico por defecto de ttk
        # en vez de acompañar al resto (11-12pt en todos lados).
        style = ttk.Style()
        style.configure("Caja.Treeview", rowheight=38, font=('Segoe UI', 12))
        style.configure("Caja.Treeview.Heading", font=('Segoe UI', 12, 'bold'))

        columns = ("hora", "tipo", "descripcion", "monto")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=8,
            style="Caja.Treeview")
        self.tree.heading("hora", text="Hora", anchor=CENTER)
        self.tree.heading("tipo", text="Tipo", anchor=CENTER)
        self.tree.heading("descripcion", text="Descripción", anchor=W)
        self.tree.heading("monto", text="Monto", anchor=E)
        self.tree.column("hora", width=90, anchor=CENTER)
        self.tree.column("tipo", width=140, anchor=CENTER)
        self.tree.column("descripcion", width=350, anchor=W)
        self.tree.column("monto", width=120, anchor=E)

        scrollbar = ttk.Scrollbar(
            table_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.tree.tag_configure('evenrow', background='#ecf0f1')
        self.tree.tag_configure('oddrow', background='white')

    def _resumen_label(self, text, row, col, parent, attr_name):
        ttk.Label(parent, text=text, font=("Segoe UI", 11)).grid(
            row=row, column=col, sticky=W, pady=4)
        label = ttk.Label(parent, text="$0.00", font=("Segoe UI", 12, "bold"))
        label.grid(row=row, column=col + 1, sticky=W, padx=(10, 30))
        setattr(self, attr_name, label)

    def _stat_card(self, parent, title: str, bootstyle: str) -> ttk.Label:
        """Crea una tarjeta chica tipo Reportes (título + número grande) y
        devuelve el label del número para que se pueda actualizar después."""
        card = ttk.Frame(parent, bootstyle="light", padding=15)
        card.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        ttk.Label(
            card, text=title, font=("Segoe UI", 10), wraplength=140
        ).pack(anchor=W)
        value_label = ttk.Label(
            card, text="$0.00", font=("Segoe UI", 18, "bold"),
            bootstyle=bootstyle)
        value_label.pack(anchor=W, pady=(6, 0))
        return value_label

    def _select_tipo(self, tipo: str) -> None:
        self.tipo_seleccionado = tipo
        for t, btn in self.tipo_buttons.items():
            btn.configure(bootstyle="primary" if t == tipo else "secondary")

        if tipo == 'gasto':
            self.forma_pago_row.pack(fill=X, pady=(0, 10), before=self.mov_form_row)
        else:
            self.forma_pago_row.pack_forget()

    def _select_forma_pago(self, forma: str) -> None:
        self.forma_pago_seleccionada = forma
        for f, btn in self.forma_pago_buttons.items():
            btn.configure(bootstyle="primary" if f == forma else "secondary")

    def get_movimiento_data(self) -> dict:
        return {
            'descripcion': self.descripcion_entry.get().strip(),
            'monto': self.monto_entry.get().strip(),
            'tipo': self.tipo_seleccionado,
            'forma_pago': self.forma_pago_seleccionada,
        }

    def clear_movimiento_fields(self) -> None:
        self.descripcion_entry.delete(0, 'end')
        self.monto_entry.delete(0, 'end')
        self.descripcion_entry.focus()

    def load_movimientos(self, movimientos: list) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        etiquetas_tipo = {
            'retiro': 'Retiro',
            'bolsillo': 'Bolsillo',
            'ingreso': 'Ingreso',
        }
        for i, mov in enumerate(movimientos):
            hora = str(mov['fecha'])[11:16] if len(str(mov['fecha'])) > 10 else ''
            if mov['tipo'] == 'gasto':
                tipo_texto = ('Gasto (efectivo)' if mov['forma_pago'] == 'efectivo'
                              else 'Gasto (transferencia)')
            else:
                tipo_texto = etiquetas_tipo.get(mov['tipo'], mov['tipo'])
            self.tree.insert('', 'end', iid=str(mov['id']), values=(
                hora,
                tipo_texto,
                mov['descripcion'],
                f"${float(mov['monto']):.2f}"
            ), tags=('evenrow' if i % 2 == 0 else 'oddrow',))

    def update_fecha(self, fecha: str, es_hoy: bool) -> None:
        """Actualiza la barra de navegación de días y el título de la
        tabla de movimientos según el día que se está viendo."""
        anio, mes, dia = fecha.split('-')
        texto_fecha = f"Hoy ({dia}/{mes})" if es_hoy else f"{dia}/{mes}/{anio}"
        self.fecha_label.configure(text=texto_fecha)
        self.movimientos_title_label.configure(
            text="Movimientos de hoy" if es_hoy else f"Movimientos del {dia}/{mes}/{anio}")

        self.dia_siguiente_button.configure(
            state='disabled' if es_hoy else 'normal')
        if es_hoy:
            self.volver_hoy_button.pack_forget()
        else:
            self.volver_hoy_button.pack(side=LEFT, padx=(15, 0))

    def update_summary(self, data: dict) -> None:
        self.label_resultado_dia.configure(
            text=f"${data['resultado_dia']:.2f}",
            bootstyle="success" if data['resultado_dia'] >= 0 else "danger")
        self.label_total_ventas_dia.configure(text=f"${data['total_ventas_dia']:.2f}")
        self.label_total_gastos_dia.configure(text=f"${data['total_gastos_dia']:.2f}")
        self.fondo_inicial_entry.delete(0, 'end')
        self.fondo_inicial_entry.insert(0, f"{data['fondo_inicial']:.2f}")
        self.label_ventas_efectivo.configure(text=f"${data['ventas_efectivo']:.2f}")
        self.label_ventas_transferencia.configure(text=f"${data['ventas_transferencia']:.2f}")
        self.label_ventas_posnet.configure(text=f"${data['ventas_posnet']:.2f}")
        self.label_ventas_fiado.configure(text=f"${data['ventas_fiado']:.2f}")
        self.label_total_gastos_efectivo.configure(text=f"${data['total_gastos_efectivo']:.2f}")
        self.label_total_gastos_transferencia.configure(text=f"${data['total_gastos_transferencia']:.2f}")
        self.label_total_retiros.configure(text=f"${data['total_retiros']:.2f}")
        self.label_total_bolsillo.configure(text=f"${data['total_bolsillo']:.2f}")
        self.label_total_ingresos.configure(text=f"${data['total_ingresos']:.2f}")
        self.label_efectivo_esperado.configure(
            text=f"${data['efectivo_esperado']:.2f}",
            bootstyle="success" if data['efectivo_esperado'] >= 0 else "danger")

        if data['cerrada']:
            self.estado_label.configure(
                text=f"Caja cerrada. Efectivo contado: ${data['efectivo_contado']:.2f} "
                     f"(diferencia: ${data['diferencia']:+.2f})")
        elif not data['es_hoy']:
            if data['sin_datos']:
                self.estado_label.configure(
                    text="Ese día no se abrió la caja (no hay movimientos guardados). "
                         "Solo lectura.")
            else:
                self.estado_label.configure(
                    text="Estás viendo un día anterior. Solo lectura.")
        else:
            self.estado_label.configure(text="")

        estado_edicion = 'disabled' if data['bloqueada'] else 'normal'
        self.fondo_inicial_entry.configure(state=estado_edicion)
        self.guardar_fondo_button.configure(state=estado_edicion)
        self.agregar_movimiento_button.configure(state=estado_edicion)
        self.cerrar_button.configure(state=estado_edicion)
        self.descripcion_entry.configure(state=estado_edicion)
        self.monto_entry.configure(state=estado_edicion)
        for btn in self.tipo_buttons.values():
            btn.configure(state=estado_edicion)
        for btn in self.forma_pago_buttons.values():
            btn.configure(state=estado_edicion)

    def show_cerrar_dialog(self, efectivo_esperado: float) -> None:
        """Pide el efectivo contado y muestra la diferencia antes de cerrar."""
        dialog = ttk.Toplevel(self)
        dialog.title("Cerrar Caja")
        dialog.geometry("380x260")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        width, height = dialog.winfo_width(), dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        ttk.Label(
            main_frame, text="Cerrar Caja", font=("Segoe UI", 16, "bold")
        ).pack(pady=(0, 15))

        ttk.Label(
            main_frame, text=f"Efectivo esperado: ${efectivo_esperado:.2f}",
            font=("Segoe UI", 12)
        ).pack(pady=(0, 15))

        ttk.Label(
            main_frame, text="Efectivo contado:", font=("Segoe UI", 11)
        ).pack(anchor=W, pady=(0, 5))
        contado_entry = ttk.Entry(main_frame, font=("Segoe UI", 12))
        contado_entry.pack(fill=X, pady=(0, 10))
        contado_entry.focus()

        diferencia_label = ttk.Label(
            main_frame, text="", font=("Segoe UI", 12, "bold"))
        diferencia_label.pack(pady=(0, 10))

        def calcular_diferencia(event=None):
            try:
                contado = float(contado_entry.get() or 0)
                diferencia = contado - efectivo_esperado
                if abs(diferencia) < 0.01:
                    diferencia_label.configure(text="Cuadra ✓", bootstyle="success")
                elif diferencia > 0:
                    diferencia_label.configure(
                        text=f"Sobran ${diferencia:.2f}", bootstyle="warning")
                else:
                    diferencia_label.configure(
                        text=f"Faltan ${-diferencia:.2f}", bootstyle="danger")
            except ValueError:
                diferencia_label.configure(text="Monto inválido")

        contado_entry.bind('<KeyRelease>', calcular_diferencia)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(15, 0))

        def confirmar():
            try:
                contado = float(contado_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Ingrese el efectivo contado")
                return
            if not messagebox.askyesno(
                "Confirmar cierre",
                "Una vez cerrada, la caja de hoy no se puede volver a editar.\n"
                "¿Confirmar el cierre?"
            ):
                return
            dialog.destroy()
            if self.caja_controller:
                self.caja_controller.cerrar_caja(contado)

        ttk.Button(
            button_frame, text="Cerrar Caja", bootstyle="danger",
            command=confirmar
        ).pack(side=RIGHT, padx=(5, 0))
        ttk.Button(
            button_frame, text="Cancelar", bootstyle="secondary",
            command=dialog.destroy
        ).pack(side=RIGHT)
