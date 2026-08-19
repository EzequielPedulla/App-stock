import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox


class CajaForm(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.pack(fill=BOTH, expand=True)
        self.caja_controller = None  # Lo setea el controlador
        self.tipo_seleccionado = 'gasto'
        self._create_widgets()

    def _create_widgets(self):
        # Título
        ttk.Label(
            self, text="Caja", font=("Segoe UI", 24, "bold")
        ).pack(anchor=W, pady=(0, 15))

        self.estado_label = ttk.Label(
            self, text="", font=("Segoe UI", 11, "bold"), foreground="#c0392b")
        self.estado_label.pack(anchor=W, pady=(0, 10))

        # ===== Card de resumen =====
        resumen_card = ttk.Frame(self, style="Card.TFrame", padding=20)
        resumen_card.pack(fill=X, pady=(0, 15))

        ttk.Label(
            resumen_card, text="Resumen del día",
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

        self._resumen_label("Ventas Efectivo:", 2, 0, resumen_card, "label_ventas_efectivo")
        self._resumen_label("Ventas Transferencia:", 2, 2, resumen_card, "label_ventas_transferencia")
        self._resumen_label("Ventas Posnet:", 3, 0, resumen_card, "label_ventas_posnet")
        self._resumen_label("Ventas Fiado (no cobradas):", 3, 2, resumen_card, "label_ventas_fiado")
        self._resumen_label("Total Gastos:", 4, 0, resumen_card, "label_total_gastos")
        self._resumen_label("Total Retiros:", 4, 2, resumen_card, "label_total_retiros")
        self._resumen_label("Pagos de bolsillo (no afecta la caja):", 5, 0, resumen_card, "label_total_bolsillo")

        ttk.Separator(resumen_card, orient='horizontal').grid(
            row=6, column=0, columnspan=4, sticky=EW, pady=12)

        ttk.Label(
            resumen_card, text="Efectivo esperado en caja:",
            font=("Segoe UI", 13, "bold")
        ).grid(row=7, column=0, columnspan=2, sticky=W)
        self.label_efectivo_esperado = ttk.Label(
            resumen_card, text="$0.00", font=("Segoe UI", 16, "bold"),
            bootstyle="success")
        self.label_efectivo_esperado.grid(row=7, column=2, columnspan=2, sticky=W)

        self.cerrar_button = ttk.Button(
            resumen_card, text="🔒 Cerrar Caja", bootstyle="danger", width=18)
        self.cerrar_button.grid(row=8, column=0, columnspan=4, sticky=W, pady=(15, 0))

        # ===== Card para agregar movimientos =====
        mov_card = ttk.Frame(self, style="Card.TFrame", padding=20)
        mov_card.pack(fill=X, pady=(0, 15))

        ttk.Label(
            mov_card, text="Agregar gasto / retiro / pago de bolsillo",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor=W, pady=(0, 10))

        tipo_row = ttk.Frame(mov_card)
        tipo_row.pack(fill=X, pady=(0, 10))
        self.tipo_buttons = {}
        for tipo, label in (
            ('gasto', 'Gasto (proveedor)'),
            ('retiro', 'Retiro'),
            ('bolsillo', 'Bolsillo del dueño'),
        ):
            btn = ttk.Button(
                tipo_row, text=label, width=18,
                bootstyle="primary" if tipo == 'gasto' else "secondary",
                command=lambda t=tipo: self._select_tipo(t)
            )
            btn.pack(side=LEFT, padx=(0, 5))
            self.tipo_buttons[tipo] = btn

        form_row = ttk.Frame(mov_card)
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
        ttk.Label(
            self, text="Movimientos de hoy", font=("Segoe UI", 14, "bold")
        ).pack(anchor=W, pady=(0, 10))

        table_frame = ttk.Frame(self, style="Card.TFrame", padding=10)
        table_frame.pack(fill=BOTH, expand=True)

        columns = ("hora", "tipo", "descripcion", "monto")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=8)
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

    def _select_tipo(self, tipo: str) -> None:
        self.tipo_seleccionado = tipo
        for t, btn in self.tipo_buttons.items():
            btn.configure(bootstyle="primary" if t == tipo else "secondary")

    def get_movimiento_data(self) -> dict:
        return {
            'descripcion': self.descripcion_entry.get().strip(),
            'monto': self.monto_entry.get().strip(),
            'tipo': self.tipo_seleccionado,
        }

    def clear_movimiento_fields(self) -> None:
        self.descripcion_entry.delete(0, 'end')
        self.monto_entry.delete(0, 'end')
        self.descripcion_entry.focus()

    def load_movimientos(self, movimientos: list) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        etiquetas_tipo = {
            'gasto': 'Gasto',
            'retiro': 'Retiro',
            'bolsillo': 'Bolsillo',
        }
        for i, mov in enumerate(movimientos):
            hora = str(mov['fecha'])[11:16] if len(str(mov['fecha'])) > 10 else ''
            self.tree.insert('', 'end', iid=str(mov['id']), values=(
                hora,
                etiquetas_tipo.get(mov['tipo'], mov['tipo']),
                mov['descripcion'],
                f"${float(mov['monto']):.2f}"
            ), tags=('evenrow' if i % 2 == 0 else 'oddrow',))

    def update_summary(self, data: dict) -> None:
        self.fondo_inicial_entry.delete(0, 'end')
        self.fondo_inicial_entry.insert(0, f"{data['fondo_inicial']:.2f}")
        self.label_ventas_efectivo.configure(text=f"${data['ventas_efectivo']:.2f}")
        self.label_ventas_transferencia.configure(text=f"${data['ventas_transferencia']:.2f}")
        self.label_ventas_posnet.configure(text=f"${data['ventas_posnet']:.2f}")
        self.label_ventas_fiado.configure(text=f"${data['ventas_fiado']:.2f}")
        self.label_total_gastos.configure(text=f"${data['total_gastos']:.2f}")
        self.label_total_retiros.configure(text=f"${data['total_retiros']:.2f}")
        self.label_total_bolsillo.configure(text=f"${data['total_bolsillo']:.2f}")
        self.label_efectivo_esperado.configure(text=f"${data['efectivo_esperado']:.2f}")

        if data['cerrada']:
            self.estado_label.configure(
                text=f"Caja cerrada. Efectivo contado: ${data['efectivo_contado']:.2f} "
                     f"(diferencia: ${data['diferencia']:+.2f})")
            self.fondo_inicial_entry.configure(state='disabled')
            self.guardar_fondo_button.configure(state='disabled')
            self.agregar_movimiento_button.configure(state='disabled')
            self.cerrar_button.configure(state='disabled')
            self.descripcion_entry.configure(state='disabled')
            self.monto_entry.configure(state='disabled')
        else:
            self.estado_label.configure(text="")
            self.fondo_inicial_entry.configure(state='normal')
            self.guardar_fondo_button.configure(state='normal')
            self.agregar_movimiento_button.configure(state='normal')
            self.cerrar_button.configure(state='normal')
            self.descripcion_entry.configure(state='normal')
            self.monto_entry.configure(state='normal')

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
