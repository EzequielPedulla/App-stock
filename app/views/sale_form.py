import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import time
import tkinter as tk
from tkinter import messagebox
from .cliente_dialogs import show_cliente_picker, confirmar_enter


class SaleForm(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self._payment_dialog = None
        self.paid = 0.0
        self.change = 0.0
        # Cliente al que se le fió (total o parcialmente) la venta que se
        # está confirmando; lo setea el diálogo de pago.
        self.cliente_id = None
        # Lo setea SaleController: buscar(texto) -> clientes, crear(datos)
        # -> cliente, y chequear_limite(cliente, monto) -> bool.
        self.clientes_api = None
        # Últimas teclas tipeadas fuera del campo de código de barras, para
        # detectar un escaneo aunque el cursor no estuviera ahí.
        self._scan_buffer = []
        self._original_items = []  # Cache de items originales
        self._is_filtering = False  # Flag para saber si estamos filtrando
        self._create_widgets()

    def _create_widgets(self):
        # Título grande
        title_label = ttk.Label(self, text="Ventas",
                                font=("Segoe UI", 27, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))

        # Pestañas de venta: para poder cobrarle a varias personas a la vez
        # sin perder lo que ya se cargó en cada una.
        slots_frame = ttk.Frame(self)
        slots_frame.pack(anchor=tk.W, pady=(0, 15))

        self.slot_buttons = []
        for i in range(3):
            btn = ttk.Button(slots_frame, text=f"Venta {i + 1}", width=14)
            btn.pack(side=tk.LEFT, padx=(0, 5))
            self.slot_buttons.append(btn)

        # Card para el formulario
        card = ttk.Frame(self, bootstyle="light", padding=20)
        card.pack(fill=tk.X, pady=(0, 20))

        # Subtítulo
        sub_label = ttk.Label(card, text="Registrar Venta",
                              font=("Segoe UI", 20, "bold"))
        sub_label.grid(row=0, column=0, columnspan=3,
                       sticky=tk.W, pady=(0, 10))

        # Código de barras
        barcode_label = ttk.Label(card, text="Código de barras",
                                  font=("Segoe UI", 15))
        barcode_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))

        self.barcode_entry = ttk.Entry(card, font=("Segoe UI", 16))
        self.barcode_entry.bind("<Return>", self._on_barcode_return)
        self.barcode_entry.bind("<Escape>", self._on_escape_pressed)
        self.barcode_entry.grid(
            row=2, column=0, sticky=tk.EW, pady=(0, 10), padx=(0, 10))

        # Cantidad
        qty_label = ttk.Label(card, text="Cantidad",
                              font=("Segoe UI", 15))
        qty_label.grid(row=1, column=1, sticky=tk.W, pady=(0, 5))

        self.qty_entry = ttk.Entry(card, font=("Segoe UI", 16), width=8)
        self.qty_entry.bind("<Escape>", self._on_escape_pressed)
        self.qty_entry.grid(row=2, column=1, sticky=tk.W,
                            pady=(0, 10), padx=(0, 10))

        # Botones de acción
        self.add_button = ttk.Button(
            card, text="Agregar", bootstyle="primary", width=15)
        self.add_button.grid(row=2, column=2, sticky=tk.E,
                             padx=(10, 0), pady=5)

        # Botón VARIOS
        self.varios_button = ttk.Button(
            card, text="➕ Varios", bootstyle="info", width=15,
            command=self._show_varios_dialog)
        self.varios_button.grid(row=3, column=2, sticky=tk.E,
                                padx=(10, 0), pady=5)

        # Botón Buscar: para agregar un producto por nombre cuando no se
        # tiene el código de barras a mano (ej. sin lector, o para ubicar
        # varios productos rápido).
        self.search_button = ttk.Button(
            card, text="🔍 Buscar", bootstyle="secondary", width=15)
        self.search_button.grid(row=3, column=3, sticky=tk.E,
                                padx=(10, 0), pady=5)

        self.edit_button = ttk.Button(
            card, text="Editar", bootstyle="warning", width=15)
        self.edit_button.grid(row=2, column=3, sticky=tk.E,
                              padx=(10, 0), pady=5)
        self.edit_button.configure(state="disabled")

        self.delete_button = ttk.Button(
            card, text="Eliminar", bootstyle="danger", width=15)
        self.delete_button.grid(row=2, column=4, sticky=tk.E,
                                padx=(10, 0), pady=5)
        self.delete_button.configure(state="disabled")

        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=0)

        # Productos seleccionados
        prod_sel_label = ttk.Label(
            self, text="Productos Seleccionados", font=("Segoe UI", 18, "bold"))
        prod_sel_label.pack(anchor=tk.W, pady=(10, 0))

        # ===== FRAME DE BÚSQUEDA =====
        search_frame = ttk.Frame(self)
        search_frame.pack(fill='x', pady=(10, 10))

        ttk.Label(search_frame, text="🔍 Buscar en carrito:",
                  font=("Segoe UI", 15)).pack(side='left', padx=(0, 10))

        self.search_var = ttk.StringVar()
        self.search_var.trace('w', self._on_search)

        search_entry = ttk.Entry(search_frame, textvariable=self.search_var,
                                 font=("Segoe UI", 15), width=40)
        search_entry.pack(side='left', fill='x', expand=True)

        # Botón para limpiar búsqueda
        clear_btn = ttk.Button(search_frame, text="✕", width=3,
                               bootstyle="secondary",
                               command=self._clear_search)
        clear_btn.pack(side='left', padx=(5, 0))

        # Label informativo
        self.info_label = ttk.Label(search_frame, text="",
                                    font=("Segoe UI", 13), foreground="#566573")
        self.info_label.pack(side='left', padx=(10, 0))

        # Frame para la tabla
        table_frame = ttk.Frame(self, bootstyle="light", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Configurar el estilo antes de crear la tabla
        style = ttk.Style()

        # Estilo para la tabla
        style.configure(
            "Custom.Treeview",
            background="white",
            foreground="black",
            rowheight=48,
            fieldbackground="white",
            borderwidth=1,
            font=('Segoe UI', 16)
        )

        # Estilo para los encabezados
        style.configure(
            "Custom.Treeview.Heading",
            background="#2c3e50",
            foreground="white",
            relief="flat",
            borderwidth=1,
            font=('Segoe UI', 17, 'bold')
        )

        # Estilo para la selección
        style.map(
            "Custom.Treeview",
            background=[("selected", "#3498db")],
            foreground=[("selected", "white")]
        )

        # Tabla de productos
        columns = ("barcode", "name", "qty", "price", "subtotal")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=6,
            style="Custom.Treeview"
        )

        # Definir los encabezados
        self.tree.heading("barcode", text="Código de barras", anchor="center")
        self.tree.heading("name", text="Nombre", anchor="center")
        self.tree.heading("qty", text="Cantidad", anchor="center")
        self.tree.heading("price", text="Precio", anchor="center")
        self.tree.heading("subtotal", text="Subtotal", anchor="center")

        # Configurar el ancho y alineación de las columnas
        self.tree.column("barcode", width=235, anchor="center", minwidth=210)
        self.tree.column("name", width=324, anchor="center", minwidth=290)
        self.tree.column("qty", width=156, anchor="center", minwidth=140)
        self.tree.column("price", width=156, anchor="center", minwidth=140)
        self.tree.column("subtotal", width=156, anchor="center", minwidth=140)

        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Empaquetar la tabla y el scrollbar
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Frame para el total y botón de confirmar
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))

        # Contador de productos cargados en esta venta
        self.count_label = ttk.Label(
            bottom_frame,
            text="0 productos",
            font=("Segoe UI", 16),
            foreground="#566573"
        )
        self.count_label.pack(side=tk.LEFT)

        # Frame para el total
        total_frame = ttk.Frame(bottom_frame)
        total_frame.pack(side=tk.RIGHT, padx=(0, 15))

        # Total general
        self.total_label = ttk.Label(
            total_frame,
            text="Total: $0.00",
            font=("Segoe UI", 22, "bold"),
            anchor=tk.E,
            width=15
        )
        self.total_label.pack(side=tk.RIGHT)

        # Botón de confirmar venta
        self.confirm_button = ttk.Button(
            bottom_frame,
            text="Confirmar Venta",
            bootstyle="success",
            width=18,
            command=self._show_payment_dialog
        )
        self.confirm_button.pack(side=tk.RIGHT)

        # Aviso de la última venta confirmada (con su número del día), para
        # que quede visible sin interrumpir con un popup en cada cobro.
        self.ultima_venta_label = ttk.Label(
            self,
            text="",
            font=("Segoe UI", 14, "bold"),
            bootstyle="success"
        )
        self.ultima_venta_label.pack(anchor=tk.E, pady=(5, 0))

        # Hint de atajos de teclado (para no depender del mouse)
        ttk.Label(
            self,
            text="⌨  ↑ ↓ elegir producto del carrito  ·  F2 editar  ·  "
                 "Supr quitar  ·  F10 Varios  ·  F5 vaciar  ·  Ctrl+1/2/3 "
                 "cambiar de venta",
            font=("Segoe UI", 13), foreground="#566573"
        ).pack(anchor=tk.W, pady=(6, 0))

        # Escaneo: si se tipea un código y Enter sin tener el cursor en el
        # campo de código de barras, igual se agrega a la venta.
        self.bind_all('<KeyPress>', self._on_key_for_scan, add='+')
        # Flechas para moverse por el carrito sin mouse
        for entry in (self.barcode_entry, self.qty_entry):
            entry.bind('<Up>', lambda e: self._mover_seleccion(-1))
            entry.bind('<Down>', lambda e: self._mover_seleccion(1))
        self.tree.bind('<Up>', lambda e: self._mover_seleccion(-1))
        self.tree.bind('<Down>', lambda e: self._mover_seleccion(1))
        self.bind_all('<F2>', self._on_f2_pressed)
        self.barcode_entry.bind('<Delete>', self._on_delete_en_codigo)
        # Vincular la tecla Enter a la ventana principal
        self.bind_all('<Return>', self._on_enter_pressed)
        # F10 para agregar un artículo Varios sin tocar el mouse
        self.bind_all('<F10>', self._on_f10_pressed)
        # F5 para vaciar la venta en curso (carrito) de una
        self.bind_all('<F5>', self._on_f5_pressed)
        # Ctrl+1/2/3 para cambiar entre las ventas en curso
        for i in range(3):
            self.bind_all(f'<Control-Key-{i + 1}>',
                          lambda e, idx=i: self._on_switch_slot_shortcut(idx))

    def _mover_seleccion(self, delta: int) -> str:
        """Mueve la selección del carrito con las flechas arriba/abajo."""
        items = self.tree.get_children()
        if not items:
            return "break"
        actual = self.tree.selection()
        idx = items.index(actual[0]) + delta if actual else (
            0 if delta > 0 else len(items) - 1)
        idx = max(0, min(len(items) - 1, idx))
        self.tree.selection_set(items[idx])
        self.tree.focus(items[idx])
        self.tree.see(items[idx])
        return "break"

    def _on_f2_pressed(self, event) -> None:
        """F2 edita el producto seleccionado del carrito."""
        if self.winfo_ismapped() and self.tree.selection():
            self.edit_button.invoke()

    def _on_delete_en_codigo(self, event):
        """Supr en el código de barras vacío quita el producto seleccionado
        del carrito (si hay texto escrito, borra el carácter como siempre)."""
        if not self.barcode_entry.get() and self.tree.selection():
            self.delete_button.invoke()
            return "break"

    # --- Escaneo de código de barras con el cursor en cualquier lado ---

    _ESC_ENTRADAS = ('TEntry', 'Entry', 'TCombobox', 'TSpinbox', 'Text')
    _TECLAS_QUE_CORTAN = ('Tab', 'Escape', 'Up', 'Down', 'Left', 'Right',
                          'Delete', 'Home', 'End', 'Prior', 'Next')

    def _en_ventana_principal(self, widget) -> bool:
        """True si el evento viene de la ventana principal (no de un
        diálogo, donde se está escribiendo otra cosa)."""
        try:
            return widget.winfo_toplevel() is self.winfo_toplevel()
        except Exception:
            return False

    def _on_key_for_scan(self, event) -> None:
        """Va anotando lo tipeado mientras el foco NO está en el código de
        barras; si después llega un Enter se interpreta como un escaneo."""
        if not self.winfo_ismapped() or not self._en_ventana_principal(
                event.widget):
            return
        if event.widget is self.barcode_entry:
            self._scan_buffer.clear()
            return
        ahora = time.time()
        if self._scan_buffer and ahora - self._scan_buffer[-1][1] > 1.0:
            self._scan_buffer.clear()
        ch = event.char
        if len(ch) == 1 and ch.isprintable() and not (event.state & 0x4):
            en_campo = event.widget.winfo_class() in self._ESC_ENTRADAS
            # Lo tipeado en un campo (ej. una cantidad) y lo tipeado sin
            # ningún campo enfocado no se mezclan.
            if self._scan_buffer and self._scan_buffer[-1][2] != en_campo:
                self._scan_buffer.clear()
            self._scan_buffer.append((ch, ahora, en_campo))
        elif event.keysym == 'BackSpace':
            if self._scan_buffer:
                self._scan_buffer.pop()
        elif event.keysym in self._TECLAS_QUE_CORTAN:
            self._scan_buffer.clear()

    def _leer_escaneo(self, widget):
        """Si lo último tipeado fuera del código de barras parece un
        escaneo, lo devuelve (y lo saca del campo donde cayó)."""
        buf = self._scan_buffer
        if not buf or time.time() - buf[-1][1] > 1.0:
            buf.clear()
            return None
        if widget.winfo_class() not in self._ESC_ENTRADAS:
            # Cursor en un botón, la tabla, etc.: nada recibió las teclas,
            # así que lo tipeado antes del Enter es el código.
            codigo = ''.join(c for c, _, en_campo in buf
                             if not en_campo).strip()
            buf.clear()
            return codigo or None
        # Cursor en otro campo (ej. cantidad): solo se toma como escaneo
        # si llegó a la velocidad de un lector (varias teclas muy seguidas).
        if not buf[-1][2]:
            buf.clear()
            return None
        n = 1
        while n < len(buf) and buf[-n][1] - buf[-n - 1][1] < 0.08:
            n += 1
        if n < 4:
            buf.clear()
            return None
        codigo = ''.join(c for c, _, _ in buf[-n:]).strip()
        buf.clear()
        try:
            texto = widget.get()
            if codigo and texto.endswith(codigo):
                widget.delete(len(texto) - len(codigo), 'end')
        except Exception:
            pass
        return codigo or None

    def _on_f10_pressed(self, event) -> None:
        """Abre el diálogo de Varios con F10, solo si esta pestaña está
        visible (F10 está en bind_all, que es global a toda la app)."""
        if self.winfo_ismapped():
            self._show_varios_dialog()

    def _on_f5_pressed(self, event) -> None:
        """Vacía la venta en curso con F5, solo si esta pestaña está
        visible (bind_all es global a toda la app)."""
        if self.winfo_ismapped():
            self.event_generate("<<ClearSale>>")

    def _on_switch_slot_shortcut(self, index: int) -> None:
        """Genera el evento de cambio de venta con Ctrl+1/2/3, solo si esta
        pestaña está visible (bind_all es global a toda la app)."""
        if self.winfo_ismapped():
            self.event_generate(f"<<SwitchSlot{index}>>")

    def _save_current_items(self):
        """Guarda los items actuales del Treeview en el cache"""
        if not self._is_filtering:  # Solo guardar si NO estamos filtrando
            self._original_items = []
            for item_id in self.tree.get_children():
                values = self.tree.item(item_id)['values']
                self._original_items.append(values)

    def _on_search(self, *args):
        """Se ejecuta cada vez que el usuario escribe en el buscador"""
        search_term = self.search_var.get().lower().strip()

        if not search_term:
            # Si no hay búsqueda, restaurar todos los items originales
            self._is_filtering = False
            self._restore_items()
            self.info_label.configure(text="")
        else:
            # Guardar items originales antes de filtrar (solo la primera vez)
            if not self._is_filtering:
                self._save_current_items()
                self._is_filtering = True

            # Filtrar items
            filtered = []
            for values in self._original_items:
                barcode = str(values[0]).lower()
                name = str(values[1]).lower()
                if search_term in barcode or search_term in name:
                    filtered.append(values)

            # Mostrar items filtrados
            self._display_filtered_items(filtered)

            # Actualizar info
            if filtered:
                self.info_label.configure(
                    text=f"Mostrando {len(filtered)} de {len(self._original_items)} productos")
            else:
                self.info_label.configure(text="No se encontraron productos")

    def _clear_search(self):
        """Limpia el campo de búsqueda"""
        self.search_var.set("")

    def _restore_items(self):
        """Restaura todos los items originales al Treeview"""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Restaurar items originales
        for i, values in enumerate(self._original_items):
            self.tree.insert("", END, values=values,
                             tags=('evenrow' if i % 2 == 0 else 'oddrow',))

        # Colores alternados
        self.tree.tag_configure('evenrow', background='#ecf0f1')
        self.tree.tag_configure('oddrow', background='white')

    def _display_filtered_items(self, items):
        """Muestra los items filtrados en el Treeview"""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Cargar items filtrados
        for i, values in enumerate(items):
            self.tree.insert("", END, values=values,
                             tags=('evenrow' if i % 2 == 0 else 'oddrow',))

        # Colores alternados
        self.tree.tag_configure('evenrow', background='#ecf0f1')
        self.tree.tag_configure('oddrow', background='white')

    def _show_payment_dialog(self) -> None:
        """Muestra el diálogo para ingresar el monto pagado y calcular el vuelto."""
        # Si ya existe una ventana de pago, no crear otra
        if self._payment_dialog is not None:
            return

        # Crear ventana modal
        self._payment_dialog = ttk.Toplevel(self)
        self._payment_dialog.title("Pago")
        self._payment_dialog.geometry("537x919")
        self._payment_dialog.resizable(False, False)
        self._payment_dialog.transient(self)
        self._payment_dialog.grab_set()

        # Centrar la ventana
        self._payment_dialog.update_idletasks()
        width = self._payment_dialog.winfo_width()
        height = self._payment_dialog.winfo_height()
        x = (self._payment_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self._payment_dialog.winfo_screenheight() // 2) - (height // 2)
        self._payment_dialog.geometry(f'{width}x{height}+{x}+{y}')

        # Frame principal
        main_frame = ttk.Frame(self._payment_dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        # Botones de confirmar/cancelar: se anclan abajo del todo primero
        # (side=BOTTOM), así el resto del contenido se puede armar y
        # reordenar arriba sin depender de que este frame ya esté packeado.
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=BOTTOM, fill=X, pady=(10, 0))

        # Título
        ttk.Label(
            main_frame,
            text="Pago",
            font=("Segoe UI", 20, "bold")
        ).pack(pady=(0, 20))

        # Obtener el total actual
        total_text = self.total_label.cget("text")
        total = float(total_text.replace("Total: $", ""))

        # Mostrar el total
        ttk.Label(
            main_frame,
            text=f"Total a pagar: ${total:.2f}",
            font=("Segoe UI", 16)
        ).pack(pady=(0, 10))

        ttk.Label(
            main_frame, text="⌨ ↑ ↓ cambia el método de pago  ·  Enter confirma",
            font=("Segoe UI", 13), foreground="#566573"
        ).pack(pady=(0, 8))

        # Método de pago (por defecto Efectivo)
        self.payment_method = 'efectivo'
        self.payments = None
        self.cliente_id = None

        ttk.Label(
            main_frame,
            text="Método de pago:",
            font=("Segoe UI", 15)
        ).pack(anchor=W, pady=(0, 5))

        method_row = ttk.Frame(main_frame)
        method_row.pack(fill=X, pady=(0, 15))
        method_row.columnconfigure(0, weight=1)
        method_row.columnconfigure(1, weight=1)

        method_buttons = {}
        for i, (method, label) in enumerate((
            ('efectivo', 'Efectivo'),
            ('transferencia', 'Transferencia'),
            ('posnet', 'Posnet'),
            ('fiado', 'No pago (fiado)'),
            ('mixto', 'Dividido (parte fiado, etc.)'),
        )):
            row, col = divmod(i, 2)
            btn = ttk.Button(
                method_row, text=label, width=16,
                bootstyle="primary" if method == 'efectivo' else "secondary",
                command=lambda m=method: select_method(m)
            )
            if method == 'mixto':
                btn.grid(row=row, column=0, columnspan=2,
                         padx=(0, 5), pady=(0, 5), sticky='ew')
            else:
                btn.grid(row=row, column=col, padx=(0, 5), pady=(0, 5), sticky='ew')
            method_buttons[method] = btn

        # Frame para el monto pagado (un solo método)
        payment_frame = ttk.Frame(main_frame)
        payment_frame.pack(fill=X, pady=(0, 10))

        payment_label = ttk.Label(
            payment_frame,
            text="Monto pagado:",
            font=("Segoe UI", 15)
        )
        payment_label.pack(side=LEFT)

        payment_entry = ttk.Entry(payment_frame, font=("Segoe UI", 16))
        payment_entry.pack(side=LEFT, padx=(10, 0), fill=X, expand=True)
        payment_entry.focus()

        # Frame para pago dividido: el total se reparte entre efectivo,
        # transferencia, posnet y fiado (ej. 40 en efectivo y 60 fiado).
        mixto_frame = ttk.Frame(main_frame)

        ttk.Label(
            mixto_frame, text="Efectivo:", font=("Segoe UI", 15)
        ).pack(anchor=W)
        efectivo_entry = ttk.Entry(mixto_frame, font=("Segoe UI", 16))
        efectivo_entry.pack(fill=X, pady=(0, 6))

        ttk.Label(
            mixto_frame, text="Transferencia:", font=("Segoe UI", 15)
        ).pack(anchor=W)
        transferencia_entry = ttk.Entry(mixto_frame, font=("Segoe UI", 16))
        transferencia_entry.pack(fill=X, pady=(0, 6))

        ttk.Label(
            mixto_frame, text="Posnet:", font=("Segoe UI", 15)
        ).pack(anchor=W)
        posnet_entry = ttk.Entry(mixto_frame, font=("Segoe UI", 16))
        posnet_entry.pack(fill=X, pady=(0, 6))

        fiado_row = ttk.Frame(mixto_frame)
        fiado_row.pack(fill=X)
        ttk.Label(
            fiado_row, text="Fiado (queda debiendo):", font=("Segoe UI", 15)
        ).pack(side=LEFT)
        fiado_entry = ttk.Entry(mixto_frame, font=("Segoe UI", 16))

        def resto_a_fiado():
            """Completa Fiado con lo que falta para llegar al total."""
            try:
                otros = sum(float(en.get() or 0) for en in (
                    efectivo_entry, transferencia_entry, posnet_entry))
            except ValueError:
                return
            resto = max(total - otros, 0.0)
            fiado_entry.delete(0, 'end')
            fiado_entry.insert(0, f"{resto:.2f}")
            calculate_mixto()

        ttk.Button(
            fiado_row, text="Resto a fiado", bootstyle="info-outline",
            command=resto_a_fiado
        ).pack(side=RIGHT)
        fiado_entry.pack(fill=X, pady=(4, 6))

        # Label para mostrar el vuelto / estado del pago (compartido)
        change_label = ttk.Label(
            main_frame,
            text="Vuelto: $0.00",
            font=("Segoe UI", 18, "bold")
        )
        change_label.pack(pady=(10, 0))

        def calculate_change():
            paid_str = payment_entry.get().strip()
            # En efectivo, dejarlo vacío equivale a pagar justo (sin
            # vuelto): no hace falta tipear el total a mano.
            if self.payment_method == 'efectivo' and not paid_str:
                change_label.configure(text="Vuelto: $0.00 (pago exacto)")
                return
            try:
                paid = float(paid_str or 0)
                change = paid - total
                if change >= 0:
                    change_label.configure(text=f"Vuelto: ${change:.2f}")
                else:
                    change_label.configure(text="Monto insuficiente")
            except ValueError:
                change_label.configure(text="Monto inválido")

        def calculate_mixto():
            try:
                asignado = sum(float(en.get() or 0) for en in (
                    efectivo_entry, transferencia_entry, posnet_entry,
                    fiado_entry))
                resta = total - asignado
                if abs(resta) < 0.01:
                    change_label.configure(text="Cuadra con el total ✓")
                elif resta > 0:
                    change_label.configure(text=f"Falta asignar: ${resta:.2f}")
                else:
                    change_label.configure(text=f"Sobra: ${-resta:.2f}")
            except ValueError:
                change_label.configure(text="Monto inválido")

        def select_method(method):
            """Cambia el método de pago.
            - Efectivo: se tipea el monto y se calcula el vuelto.
            - Transferencia/Posnet: se pagan justo, sin vuelto, así que el
              monto se completa solo con el total.
            - Fiado: no se cobra nada ahora, el monto queda en $0.
            - Mixto: se reparte el total entre efectivo y transferencia."""
            self.payment_method = method
            for m, btn in method_buttons.items():
                btn.configure(bootstyle="primary" if m == method else "secondary")

            if method == 'mixto':
                payment_frame.pack_forget()
                mixto_frame.pack(fill=X, pady=(0, 10), before=change_label)
                for en in (efectivo_entry, transferencia_entry,
                           posnet_entry, fiado_entry):
                    en.delete(0, 'end')
                efectivo_entry.focus()
                calculate_mixto()
                return

            mixto_frame.pack_forget()
            payment_frame.pack(fill=X, pady=(0, 10), before=change_label)

            payment_entry.configure(state='normal')
            payment_entry.delete(0, 'end')

            if method == 'efectivo':
                payment_label.configure(text="Monto pagado (vacío = pago exacto):")
                change_label.configure(text="Vuelto: $0.00 (pago exacto)")
            elif method == 'fiado':
                payment_label.configure(text="Monto pagado:")
                payment_entry.insert(0, "0.00")
                payment_entry.configure(state='disabled')
                change_label.configure(text="Fiado (sin cobrar)")
            else:
                payment_label.configure(text="Monto pagado:")
                payment_entry.insert(0, f"{total:.2f}")
                payment_entry.configure(state='disabled')
                change_label.configure(text="Pago exacto (sin vuelto)")

        orden_metodos = ['efectivo', 'transferencia', 'posnet', 'fiado',
                         'mixto']

        def mover_metodo(delta):
            """Flechas: cambia el método de pago sin usar el mouse."""
            i = orden_metodos.index(self.payment_method)
            select_method(orden_metodos[(i + delta) % len(orden_metodos)])
            if self.payment_method != 'mixto':
                if str(payment_entry.cget('state')) == 'normal':
                    payment_entry.focus()
                else:
                    self._payment_dialog.focus_set()
            return "break"

        def flecha_horizontal(delta, event):
            # En un campo de texto, ← → mueven el cursor como siempre.
            if event.widget.winfo_class() in ('TEntry', 'Entry'):
                return None
            return mover_metodo(delta)

        self._payment_dialog.bind('<Up>', lambda e: mover_metodo(-1))
        self._payment_dialog.bind('<Down>', lambda e: mover_metodo(1))
        self._payment_dialog.bind(
            '<Left>', lambda e: flecha_horizontal(-1, e))
        self._payment_dialog.bind(
            '<Right>', lambda e: flecha_horizontal(1, e))

        # Vincular el cálculo al cambio en cada entry
        payment_entry.bind('<KeyRelease>', lambda e: calculate_change())
        efectivo_entry.bind('<KeyRelease>', lambda e: calculate_mixto())
        transferencia_entry.bind('<KeyRelease>', lambda e: calculate_mixto())
        posnet_entry.bind('<KeyRelease>', lambda e: calculate_mixto())
        fiado_entry.bind('<KeyRelease>', lambda e: calculate_mixto())

        def elegir_cliente(monto_fiado):
            """Pide a quién se le anota el fiado y avisa (sin bloquear) si
            con esto pasa su límite. Devuelve el cliente o None si se
            canceló."""
            api = self.clientes_api
            if api is None:
                messagebox.showerror(
                    "Error", "El cuaderno de fiados no está disponible")
                return None
            cliente = show_cliente_picker(
                self._payment_dialog, api.buscar_clientes,
                api.crear_cliente, monto_fiado)
            if cliente is None:
                return None
            if not api.confirmar_limite(
                    cliente, monto_fiado, self._payment_dialog):
                return None
            nuevo_saldo = cliente['saldo'] + monto_fiado
            if not confirmar_enter(
                    self._payment_dialog, "Confirmar fiado",
                    [(f"Se anotan ${monto_fiado:.2f} a", "#2c3e50"),
                     (cliente['nombre'], "#2c3e50"),
                     (f"Debe ${cliente['saldo']:.2f} → pasará a deber "
                      f"${nuevo_saldo:.2f}", "#c0392b")]):
                return None
            return cliente

        def terminar(payment_method, payments, paid, change, cliente):
            self.payment_method = payment_method
            self.payments = payments
            self.paid = paid
            self.change = change
            self.cliente_id = cliente['id'] if cliente else None
            self._payment_dialog.destroy()
            self._payment_dialog = None
            self.event_generate("<<ConfirmSale>>")

        def confirm_payment():
            if self.payment_method == 'mixto':
                try:
                    partes = {
                        'efectivo': float(efectivo_entry.get() or 0),
                        'transferencia': float(
                            transferencia_entry.get() or 0),
                        'posnet': float(posnet_entry.get() or 0),
                        'fiado': float(fiado_entry.get() or 0),
                    }
                except ValueError:
                    messagebox.showerror("Error", "Ingrese montos válidos")
                    return

                if any(v < 0 for v in partes.values()):
                    messagebox.showerror(
                        "Error", "Los montos no pueden ser negativos")
                    return

                if sum(partes.values()) <= 0:
                    messagebox.showerror(
                        "Error", "Ingrese al menos un monto")
                    return

                if abs(sum(partes.values()) - total) >= 0.01:
                    messagebox.showerror(
                        "Error",
                        f"La suma de lo asignado "
                        f"(${sum(partes.values()):.2f}) debe ser igual al "
                        f"total (${total:.2f})"
                    )
                    return

                payments = [{'method': m, 'amount': v}
                            for m, v in partes.items() if v > 0]
                fiado = partes['fiado']
                cliente = None
                if fiado > 0:
                    cliente = elegir_cliente(fiado)
                    if cliente is None:
                        return

                # Con un solo método (ej. todo a fiado, o todo efectivo)
                # no hace falta guardarla como venta dividida.
                if len(payments) == 1:
                    metodo = payments[0]['method']
                    terminar(metodo, None,
                             0.0 if metodo == 'fiado' else total, 0.0,
                             cliente)
                else:
                    terminar('mixto', payments, total - fiado, 0.0, cliente)
                return

            try:
                paid_str = payment_entry.get().strip()
                # En efectivo, dejar el monto vacío equivale a pagar justo
                # (sin vuelto): no obliga a tipear el total a mano.
                if self.payment_method == 'efectivo' and not paid_str:
                    paid = total
                else:
                    paid = float(paid_str or 0)
                # El fiado se paga $0 a propósito: no aplica el chequeo de
                # monto insuficiente.
                if self.payment_method != 'fiado' and paid < total:
                    messagebox.showerror(
                        "Error", "El monto pagado es insuficiente")
                    return
                cliente = None
                if self.payment_method == 'fiado':
                    cliente = elegir_cliente(total)
                    if cliente is None:
                        return
                terminar(
                    self.payment_method, None, paid,
                    paid - total if self.payment_method == 'efectivo'
                    else 0.0, cliente)
            except ValueError:
                messagebox.showerror("Error", "Ingrese un monto válido")

        def on_closing():
            self._payment_dialog.destroy()
            self._payment_dialog = None

        ttk.Button(
            button_frame,
            text="Confirmar",
            bootstyle="success",
            command=confirm_payment
        ).pack(side=RIGHT, padx=(5, 0))

        ttk.Button(
            button_frame,
            text="Cancelar",
            bootstyle="secondary",
            command=on_closing
        ).pack(side=RIGHT)

        # Prevenir que se cierre la ventana con la X
        self._payment_dialog.protocol("WM_DELETE_WINDOW", on_closing)

        # Enter confirma el pago. "break" corta la propagación: sin esto,
        # el mismo Enter también dispara el atajo global de confirmar
        # venta (que acá no hace nada útil, porque el diálogo ya está
        # abierto, pero igual conviene cortarlo en el origen).
        self._payment_dialog.bind('<Return>', lambda e: confirm_payment() or "break")

    def _on_barcode_return(self, event) -> None:
        """Maneja el evento cuando se presiona Enter en el campo de código de barras."""
        self.event_generate("<<AddItem>>")

    def _on_escape_pressed(self, event) -> None:
        """Saca el foco del código de barras / cantidad, para que un Enter
        posterior confirme la venta en vez de intentar agregar un ítem."""
        self.focus_set()

    def _on_enter_pressed(self, event) -> None:
        """Maneja el evento cuando se presiona Enter en la ventana principal."""
        # Este binding es global (bind_all), así que sin este chequeo
        # cualquier Enter en OTRA pestaña (ej. guardar un producto) también
        # termina abriendo el diálogo de confirmar venta.
        if not self.winfo_ismapped():
            return

        # Un código escaneado con el cursor fuera del campo de código de
        # barras: se agrega igual (y no se abre el cobro).
        if event.widget is not self.barcode_entry and (
                self._en_ventana_principal(event.widget)):
            codigo = self._leer_escaneo(event.widget)
            if codigo:
                self.barcode_entry.delete(0, 'end')
                self.barcode_entry.insert(0, codigo)
                self.event_generate("<<AddItem>>")
                return "break"

        # Si el foco está en los campos de entrada, no hacer nada
        if event.widget in (self.barcode_entry, self.qty_entry):
            return

        # Verificar si hay productos en la tabla
        if self.tree.get_children():
            self._show_payment_dialog()

    def set_ultima_venta(self, texto: str) -> None:
        """Muestra el aviso de la última venta confirmada (número del día
        y total)."""
        self.ultima_venta_label.configure(text=texto)

    def get_item_data(self) -> dict:
        """Obtiene los datos del formulario."""
        return {
            'barcode': self.barcode_entry.get().strip(),
            'qty': self.qty_entry.get().strip()
        }

    def clear_fields(self) -> None:
        """Limpia los campos del formulario."""
        self.barcode_entry.delete(0, 'end')
        self.qty_entry.delete(0, 'end')
        self.barcode_entry.focus()

    def set_slot_buttons(self, active_index: int, counts: list) -> None:
        """Actualiza el texto y resaltado de las pestañas de venta.

        Args:
            active_index: índice de la venta actualmente mostrada.
            counts: cantidad de items cargados en cada venta.
        """
        for i, btn in enumerate(self.slot_buttons):
            label = f"Venta {i + 1}"
            if counts[i] > 0:
                label += f" ({counts[i]})"
            btn.configure(
                text=label,
                bootstyle="primary" if i == active_index else "secondary"
            )

    def set_action_buttons_state(self, state: str) -> None:
        """Configura el estado de los botones de acción."""
        self.edit_button.configure(state=state)
        self.delete_button.configure(state=state)

    def _show_varios_dialog(self) -> None:
        """Muestra un diálogo para agregar un artículo 'varios' sin registro."""
        # Crear ventana modal
        dialog = ttk.Toplevel(self)
        dialog.title("Artículo Varios")
        dialog.geometry("560x471")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Centrar la ventana
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

        # Frame principal
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        # Título
        ttk.Label(
            main_frame,
            text="➕ Agregar Artículo Varios",
            font=("Segoe UI", 20, "bold")
        ).pack(pady=(0, 20))

        # Descripción
        ttk.Label(
            main_frame,
            text="Para productos que no están en el inventario",
            font=("Segoe UI", 13),
            foreground="#566573"
        ).pack(pady=(0, 15))

        # Campo: Nombre
        ttk.Label(
            main_frame,
            text="Nombre del artículo:",
            font=("Segoe UI", 15)
        ).pack(anchor=W, pady=(0, 5))

        name_entry = ttk.Entry(main_frame, font=("Segoe UI", 16))
        name_entry.pack(fill=X, pady=(0, 15))

        # Frame para precio y cantidad
        grid_frame = ttk.Frame(main_frame)
        grid_frame.pack(fill=X, pady=(0, 15))

        # Campo: Precio
        ttk.Label(
            grid_frame,
            text="Precio unitario:",
            font=("Segoe UI", 15)
        ).grid(row=0, column=0, sticky=W, pady=(0, 5))

        price_entry = ttk.Entry(grid_frame, font=("Segoe UI", 16))
        price_entry.grid(row=1, column=0, sticky=EW, padx=(0, 10))
        # El nombre es opcional (por defecto "Varios"), así que el cursor
        # arranca en precio en vez de nombre.
        price_entry.focus()
        grid_frame.columnconfigure(0, weight=1)

        # Campo: Cantidad
        ttk.Label(
            grid_frame,
            text="Cantidad:",
            font=("Segoe UI", 15)
        ).grid(row=0, column=1, sticky=W, pady=(0, 5))

        qty_entry = ttk.Entry(grid_frame, font=("Segoe UI", 16))
        qty_entry.insert(0, "1")  # Default: 1
        qty_entry.grid(row=1, column=1, sticky=EW)
        grid_frame.columnconfigure(1, weight=1)

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(20, 0))

        def confirm_varios():
            """Confirma y agrega el artículo varios."""
            name = name_entry.get().strip().upper() or "VARIOS"
            price_str = price_entry.get().strip()
            qty_str = qty_entry.get().strip()

            try:
                price = float(price_str)
                if price <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                messagebox.showerror("Error", "Ingrese un precio válido")
                price_entry.focus()
                return

            try:
                qty = int(qty_str)
                if qty <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                messagebox.showerror("Error", "Ingrese una cantidad válida")
                qty_entry.focus()
                return

            # Generar evento con los datos
            self.varios_data = {
                'name': name,
                'price': price,
                'qty': qty
            }
            dialog.destroy()
            self.event_generate("<<AddVarios>>")

        ttk.Button(
            button_frame,
            text="Agregar",
            bootstyle="success",
            command=confirm_varios,
            width=15
        ).pack(side=RIGHT, padx=(5, 0))

        ttk.Button(
            button_frame,
            text="Cancelar",
            bootstyle="secondary",
            command=dialog.destroy,
            width=15
        ).pack(side=RIGHT)

        # Enter para confirmar
        # "break" corta la propagación: sin esto, el mismo Enter también
        # dispara el atajo global de "Confirmar Venta" (bind_all en la
        # ventana principal) apenas se cierra este diálogo.
        dialog.bind('<Return>', lambda e: confirm_varios() or "break")

    def show_edit_item_dialog(self, barcode: str, name: str, qty: int, price: float) -> None:
        """Muestra un diálogo para editar la cantidad y el precio de un
        producto ya cargado en el carrito."""
        dialog = ttk.Toplevel(self)
        dialog.title("Editar Producto")
        dialog.geometry("537x379")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Centrar la ventana
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        ttk.Label(
            main_frame,
            text="✏️ Editar Producto",
            font=("Segoe UI", 20, "bold")
        ).pack(pady=(0, 15))

        ttk.Label(
            main_frame,
            text=name,
            font=("Segoe UI", 15),
            foreground="#566573"
        ).pack(pady=(0, 15))

        grid_frame = ttk.Frame(main_frame)
        grid_frame.pack(fill=X, pady=(0, 15))

        ttk.Label(
            grid_frame,
            text="Cantidad:",
            font=("Segoe UI", 15)
        ).grid(row=0, column=0, sticky=W, pady=(0, 5))

        qty_entry = ttk.Entry(grid_frame, font=("Segoe UI", 16))
        qty_entry.insert(0, str(qty))
        qty_entry.grid(row=1, column=0, sticky=EW, padx=(0, 10))
        grid_frame.columnconfigure(0, weight=1)

        ttk.Label(
            grid_frame,
            text="Precio unitario:",
            font=("Segoe UI", 15)
        ).grid(row=0, column=1, sticky=W, pady=(0, 5))

        price_entry = ttk.Entry(grid_frame, font=("Segoe UI", 16))
        price_entry.insert(0, f"{price:.2f}")
        price_entry.grid(row=1, column=1, sticky=EW)
        grid_frame.columnconfigure(1, weight=1)
        qty_entry.focus()

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(20, 0))

        def confirm_edit():
            qty_str = qty_entry.get().strip()
            price_str = price_entry.get().strip()

            try:
                new_qty = int(qty_str)
                if new_qty <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                messagebox.showerror("Error", "Ingrese una cantidad válida")
                qty_entry.focus()
                return

            try:
                new_price = float(price_str)
                if new_price <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                messagebox.showerror("Error", "Ingrese un precio válido")
                price_entry.focus()
                return

            self.edit_item_data = {'qty': new_qty, 'price': new_price}
            dialog.destroy()
            self.event_generate("<<SaveEditItem>>")

        ttk.Button(
            button_frame,
            text="Guardar",
            bootstyle="success",
            command=confirm_edit,
            width=15
        ).pack(side=RIGHT, padx=(5, 0))

        ttk.Button(
            button_frame,
            text="Cancelar",
            bootstyle="secondary",
            command=dialog.destroy,
            width=15
        ).pack(side=RIGHT)

        # "break" corta la propagación: sin esto, el mismo Enter también
        # dispara el atajo global de "Confirmar Venta" apenas se cierra
        # este diálogo.
        dialog.bind('<Return>', lambda e: confirm_edit() or "break")

    def show_search_products_dialog(self, products: list) -> None:
        """Diálogo para buscar un producto por nombre o código (sin
        necesidad de tener el código de barras a mano) y agregarlo
        directo a la venta. Queda abierto después de cada agregado para
        poder sumar varios productos seguidos."""
        dialog = ttk.Toplevel(self)
        dialog.title("Buscar Producto")
        dialog.geometry("672x655")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        ttk.Label(
            main_frame,
            text="🔍 Buscar Producto",
            font=("Segoe UI", 20, "bold")
        ).pack(pady=(0, 15))

        search_var = ttk.StringVar()
        search_entry = ttk.Entry(
            main_frame, textvariable=search_var, font=("Segoe UI", 16))
        search_entry.pack(fill=X, pady=(0, 10))
        search_entry.focus()

        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        columns = ("barcode", "name", "price", "stock")
        tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=10)
        tree.heading("barcode", text="Código", anchor="center")
        tree.heading("name", text="Nombre", anchor="center")
        tree.heading("price", text="Precio", anchor="center")
        tree.heading("stock", text="Stock", anchor="center")
        tree.column("barcode", width=156, anchor="center")
        tree.column("name", width=291, anchor="w")
        tree.column("price", width=100, anchor="center")
        tree.column("stock", width=89, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # El código de barras es único, así que sirve como iid del árbol
        # para no tener que volver a buscar el producto al seleccionarlo.
        def render(items):
            for i in tree.get_children():
                tree.delete(i)
            for p in items:
                tree.insert('', END, iid=p.barcode, values=(
                    p.barcode, p.name, f"${p.price:.2f}", int(p.stock)))
            if items:
                tree.selection_set(items[0].barcode)
                tree.focus(items[0].barcode)

        def on_search(*args):
            term = search_var.get().lower().strip()
            if not term:
                render(products)
                return
            barcode_matches = [
                p for p in products if p.barcode.lower().startswith(term)]
            matched_set = set(barcode_matches)
            others = [
                p for p in products if p not in matched_set and (
                    term in p.barcode.lower() or term in p.name.lower())]
            render(barcode_matches + others)

        search_var.trace('w', on_search)
        render(products)

        bottom_row = ttk.Frame(main_frame)
        bottom_row.pack(fill=X, pady=(0, 5))

        ttk.Label(
            bottom_row, text="Cantidad:", font=("Segoe UI", 15)
        ).pack(side=LEFT)
        qty_entry = ttk.Entry(bottom_row, font=("Segoe UI", 15), width=8)
        qty_entry.insert(0, "1")
        qty_entry.pack(side=LEFT, padx=(10, 10))

        agregar_btn = ttk.Button(
            bottom_row, text="➕ Agregar a la venta", bootstyle="success")
        agregar_btn.pack(side=LEFT)

        status_label = ttk.Label(
            main_frame, text="", font=("Segoe UI", 13), foreground="#566573")
        status_label.pack(anchor=W, pady=(0, 10))

        def agregar(event=None):
            selected = tree.selection()
            if not selected:
                messagebox.showerror(
                    "Error", "Seleccione un producto de la lista")
                return "break"

            qty_str = qty_entry.get().strip()
            try:
                qty = int(qty_str) if qty_str else 1
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Ingrese una cantidad válida")
                return "break"

            barcode = selected[0]
            nombre = tree.set(barcode, "name")

            self.search_add_data = {'barcode': barcode, 'qty': qty}
            self.event_generate("<<AddFromSearch>>")

            status_label.configure(
                text=f"✓ Agregado: {nombre} x{qty}")
            qty_entry.delete(0, 'end')
            qty_entry.insert(0, "1")
            return "break"

        agregar_btn.configure(command=agregar)
        tree.bind('<Double-1>', agregar)
        qty_entry.bind('<Return>', agregar)
        tree.bind('<Return>', agregar)

        def mover(delta):
            items = tree.get_children()
            if not items:
                return "break"
            sel = tree.selection()
            idx = items.index(sel[0]) + delta if sel else 0
            idx = max(0, min(len(items) - 1, idx))
            tree.selection_set(items[idx])
            tree.focus(items[idx])
            tree.see(items[idx])
            return "break"

        # Desde el buscador: ↑ ↓ eligen el producto y Enter lo agrega
        search_entry.bind('<Down>', lambda e: mover(1))
        search_entry.bind('<Up>', lambda e: mover(-1))
        search_entry.bind('<Return>', agregar)

        ttk.Button(
            main_frame,
            text="Cerrar",
            bootstyle="secondary",
            command=dialog.destroy
        ).pack(anchor=E)

        # Corta el Enter acá: sin esto, un Enter en la búsqueda (sin caer
        # en un binding más específico) se escapa al atajo global de
        # "Confirmar Venta" mientras este diálogo sigue abierto.
        dialog.bind('<Return>', lambda e: "break")

    def show_register_product_dialog(self, barcode: str) -> None:
        """Muestra un diálogo para registrar en el inventario un código de
        barras que no fue encontrado, sin pedir stock (no se usa acá)."""
        dialog = ttk.Toplevel(self)
        dialog.title("Registrar Producto")
        dialog.geometry("560x448")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        # Centrar la ventana
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        ttk.Label(
            main_frame,
            text="🆕 Registrar Producto",
            font=("Segoe UI", 20, "bold")
        ).pack(pady=(0, 15))

        ttk.Label(
            main_frame,
            text=f"Código de barras: {barcode}",
            font=("Segoe UI", 15),
            foreground="#566573"
        ).pack(pady=(0, 15))

        ttk.Label(
            main_frame,
            text="Nombre del producto:",
            font=("Segoe UI", 15)
        ).pack(anchor=W, pady=(0, 5))

        name_entry = ttk.Entry(main_frame, font=("Segoe UI", 16))
        name_entry.pack(fill=X, pady=(0, 15))
        name_entry.focus()

        ttk.Label(
            main_frame,
            text="Precio:",
            font=("Segoe UI", 15)
        ).pack(anchor=W, pady=(0, 5))

        price_entry = ttk.Entry(main_frame, font=("Segoe UI", 16))
        price_entry.pack(fill=X, pady=(0, 15))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(15, 0))

        def confirm_register():
            """Confirma el registro del producto."""
            name = name_entry.get().strip().upper()
            price_str = price_entry.get().strip()

            if not name:
                messagebox.showerror("Error", "Ingrese el nombre del producto")
                name_entry.focus()
                return

            try:
                price = float(price_str)
                if price <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                messagebox.showerror("Error", "Ingrese un precio válido")
                price_entry.focus()
                return

            self.register_data = {
                'barcode': barcode,
                'name': name,
                'price': price,
            }
            dialog.destroy()
            self.event_generate("<<RegisterProduct>>")

        ttk.Button(
            button_frame,
            text="Registrar",
            bootstyle="success",
            command=confirm_register,
            width=15
        ).pack(side=RIGHT, padx=(5, 0))

        ttk.Button(
            button_frame,
            text="Cancelar",
            bootstyle="secondary",
            command=dialog.destroy,
            width=15
        ).pack(side=RIGHT)

        # "break" corta la propagación: sin esto, el mismo Enter también
        # dispara el atajo global de "Confirmar Venta" apenas se cierra
        # este diálogo.
        dialog.bind('<Return>', lambda e: confirm_register() or "break")
