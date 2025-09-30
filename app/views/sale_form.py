import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox


class SaleForm(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self._payment_dialog = None
        self.paid = 0.0
        self.change = 0.0
        self._original_items = []  # Cache de items originales
        self._is_filtering = False  # Flag para saber si estamos filtrando
        self._create_widgets()

    def _create_widgets(self):
        # Título grande
        title_label = ttk.Label(self, text="Ventas",
                                font=("Segoe UI", 24, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 20))

        # Card para el formulario
        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.pack(fill=tk.X, pady=(0, 20))

        # Subtítulo
        sub_label = ttk.Label(card, text="Registrar Venta",
                              font=("Segoe UI", 16, "bold"))
        sub_label.grid(row=0, column=0, columnspan=3,
                       sticky=tk.W, pady=(0, 10))

        # Código de barras
        barcode_label = ttk.Label(card, text="Código de barras",
                                  font=("Segoe UI", 11))
        barcode_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))

        self.barcode_entry = ttk.Entry(card, font=("Segoe UI", 12))
        self.barcode_entry.bind("<Return>", self._on_barcode_return)
        self.barcode_entry.grid(
            row=2, column=0, sticky=tk.EW, pady=(0, 10), padx=(0, 10))

        # Cantidad
        qty_label = ttk.Label(card, text="Cantidad",
                              font=("Segoe UI", 11))
        qty_label.grid(row=1, column=1, sticky=tk.W, pady=(0, 5))

        self.qty_entry = ttk.Entry(card, font=("Segoe UI", 12))
        self.qty_entry.grid(row=2, column=1, sticky=tk.EW,
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
        card.columnconfigure(1, weight=1)

        # Productos seleccionados
        prod_sel_label = ttk.Label(
            self, text="Productos Seleccionados", font=("Segoe UI", 14, "bold"))
        prod_sel_label.pack(anchor=tk.W, pady=(10, 0))

        # ===== FRAME DE BÚSQUEDA =====
        search_frame = ttk.Frame(self)
        search_frame.pack(fill='x', pady=(10, 10))

        ttk.Label(search_frame, text="🔍 Buscar en carrito:",
                  font=("Segoe UI", 11)).pack(side='left', padx=(0, 10))

        self.search_var = ttk.StringVar()
        self.search_var.trace('w', self._on_search)

        search_entry = ttk.Entry(search_frame, textvariable=self.search_var,
                                 font=("Segoe UI", 11), width=40)
        search_entry.pack(side='left', fill='x', expand=True)

        # Botón para limpiar búsqueda
        clear_btn = ttk.Button(search_frame, text="✕", width=3,
                               bootstyle="secondary",
                               command=self._clear_search)
        clear_btn.pack(side='left', padx=(5, 0))

        # Label informativo
        self.info_label = ttk.Label(search_frame, text="",
                                    font=("Segoe UI", 9), foreground="gray")
        self.info_label.pack(side='left', padx=(10, 0))

        # Frame para la tabla
        table_frame = ttk.Frame(self, style="Card.TFrame", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Configurar el estilo antes de crear la tabla
        style = ttk.Style()

        # Estilo para la tabla
        style.configure(
            "Custom.Treeview",
            background="white",
            foreground="black",
            rowheight=35,
            fieldbackground="white",
            borderwidth=1,
            font=('Segoe UI', 11)
        )

        # Estilo para los encabezados
        style.configure(
            "Custom.Treeview.Heading",
            background="#2c3e50",
            foreground="white",
            relief="flat",
            borderwidth=1,
            font=('Segoe UI', 12, 'bold')
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
            height=3,
            style="Custom.Treeview"
        )

        # Definir los encabezados
        self.tree.heading("barcode", text="Código de barras", anchor="center")
        self.tree.heading("name", text="Nombre", anchor="center")
        self.tree.heading("qty", text="Cantidad", anchor="center")
        self.tree.heading("price", text="Precio", anchor="center")
        self.tree.heading("subtotal", text="Subtotal", anchor="center")

        # Configurar el ancho y alineación de las columnas
        self.tree.column("barcode", width=180, anchor="center", minwidth=180)
        self.tree.column("name", width=250, anchor="center", minwidth=250)
        self.tree.column("qty", width=120, anchor="center", minwidth=120)
        self.tree.column("price", width=120, anchor="center", minwidth=120)
        self.tree.column("subtotal", width=120, anchor="center", minwidth=120)

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

        # Frame para el total
        total_frame = ttk.Frame(bottom_frame)
        total_frame.pack(side=tk.RIGHT, padx=(0, 15))

        # Total general
        self.total_label = ttk.Label(
            total_frame,
            text="Total: $0.00",
            font=("Segoe UI", 18, "bold"),
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

        # Vincular la tecla Enter a la ventana principal
        self.bind_all('<Return>', self._on_enter_pressed)

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
        self._payment_dialog.geometry("400x300")
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

        # Título
        ttk.Label(
            main_frame,
            text="Pago",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(0, 20))

        # Obtener el total actual
        total_text = self.total_label.cget("text")
        total = float(total_text.replace("Total: $", ""))

        # Mostrar el total
        ttk.Label(
            main_frame,
            text=f"Total a pagar: ${total:.2f}",
            font=("Segoe UI", 12)
        ).pack(pady=(0, 10))

        # Frame para el monto pagado
        payment_frame = ttk.Frame(main_frame)
        payment_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(
            payment_frame,
            text="Monto pagado:",
            font=("Segoe UI", 11)
        ).pack(side=LEFT)

        payment_entry = ttk.Entry(payment_frame, font=("Segoe UI", 12))
        payment_entry.pack(side=LEFT, padx=(10, 0), fill=X, expand=True)
        payment_entry.focus()

        # Label para mostrar el vuelto
        change_label = ttk.Label(
            main_frame,
            text="Vuelto: $0.00",
            font=("Segoe UI", 14, "bold")
        )
        change_label.pack(pady=(10, 20))

        def calculate_change():
            try:
                paid = float(payment_entry.get() or 0)
                change = paid - total
                if change >= 0:
                    change_label.configure(text=f"Vuelto: ${change:.2f}")
                else:
                    change_label.configure(text="Monto insuficiente")
            except ValueError:
                change_label.configure(text="Monto inválido")

        # Vincular el cálculo al cambio en el entry
        payment_entry.bind('<KeyRelease>', lambda e: calculate_change())

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(20, 0))

        def confirm_payment():
            try:
                paid = float(payment_entry.get() or 0)
                if paid < total:
                    messagebox.showerror(
                        "Error", "El monto pagado es insuficiente")
                    return
                self.paid = paid
                self.change = paid - total
                self._payment_dialog.destroy()
                self._payment_dialog = None
                self.event_generate("<<ConfirmSale>>")
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

    def _on_barcode_return(self, event) -> None:
        """Maneja el evento cuando se presiona Enter en el campo de código de barras."""
        self.event_generate("<<AddItem>>")

    def _on_enter_pressed(self, event) -> None:
        """Maneja el evento cuando se presiona Enter en la ventana principal."""
        # Si el foco está en los campos de entrada, no hacer nada
        if event.widget in (self.barcode_entry, self.qty_entry):
            return

        # Verificar si hay productos en la tabla
        if self.tree.get_children():
            self._show_payment_dialog()

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

    def set_action_buttons_state(self, state: str) -> None:
        """Configura el estado de los botones de acción."""
        self.edit_button.configure(state=state)
        self.delete_button.configure(state=state)

    def _show_varios_dialog(self) -> None:
        """Muestra un diálogo para agregar un artículo 'varios' sin registro."""
        # Crear ventana modal
        dialog = ttk.Toplevel(self)
        dialog.title("Artículo Varios")
        dialog.geometry("450x300")
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
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(0, 20))

        # Descripción
        ttk.Label(
            main_frame,
            text="Para productos que no están en el inventario",
            font=("Segoe UI", 10),
            foreground="gray"
        ).pack(pady=(0, 15))

        # Campo: Nombre
        ttk.Label(
            main_frame,
            text="Nombre del artículo:",
            font=("Segoe UI", 11)
        ).pack(anchor=W, pady=(0, 5))

        name_entry = ttk.Entry(main_frame, font=("Segoe UI", 12))
        name_entry.pack(fill=X, pady=(0, 15))
        name_entry.focus()

        # Frame para precio y cantidad
        grid_frame = ttk.Frame(main_frame)
        grid_frame.pack(fill=X, pady=(0, 15))

        # Campo: Precio
        ttk.Label(
            grid_frame,
            text="Precio unitario:",
            font=("Segoe UI", 11)
        ).grid(row=0, column=0, sticky=W, pady=(0, 5))

        price_entry = ttk.Entry(grid_frame, font=("Segoe UI", 12))
        price_entry.grid(row=1, column=0, sticky=EW, padx=(0, 10))
        grid_frame.columnconfigure(0, weight=1)

        # Campo: Cantidad
        ttk.Label(
            grid_frame,
            text="Cantidad:",
            font=("Segoe UI", 11)
        ).grid(row=0, column=1, sticky=W, pady=(0, 5))

        qty_entry = ttk.Entry(grid_frame, font=("Segoe UI", 12))
        qty_entry.insert(0, "1")  # Default: 1
        qty_entry.grid(row=1, column=1, sticky=EW)
        grid_frame.columnconfigure(1, weight=1)

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(20, 0))

        def confirm_varios():
            """Confirma y agrega el artículo varios."""
            name = name_entry.get().strip()
            price_str = price_entry.get().strip()
            qty_str = qty_entry.get().strip()

            # Validaciones
            if not name:
                messagebox.showerror("Error", "Ingrese el nombre del artículo")
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
        dialog.bind('<Return>', lambda e: confirm_varios())
