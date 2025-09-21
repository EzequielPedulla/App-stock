import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class ProductForm(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Agregar Producto", padding=20, **kwargs)
        self.pack(fill="x", pady=(0, 20))
        self._create_widgets()
        self.editing_mode = False

    def _create_widgets(self):
        # Configurar el grid
        self.columnconfigure(1, weight=1)

        # Campos del formulario
        ttk.Label(self, text="Código de barras",
                  font=("Segoe UI", 11)).grid(row=0, column=0, pady=10, sticky='w')
        self.barcode_entry = ttk.Entry(self)
        self.barcode_entry.grid(row=0, column=1, padx=(20, 0), sticky='ew')

        ttk.Label(self, text="Nombre",
                  font=("Segoe UI", 11)).grid(row=1, column=0, pady=10, sticky='w')
        self.name_entry = ttk.Entry(self)
        self.name_entry.grid(row=1, column=1, padx=(20, 0), sticky='ew')

        ttk.Label(self, text="Precio",
                  font=("Segoe UI", 11)).grid(row=2, column=0, pady=10, sticky='w')
        self.price_entry = ttk.Entry(self)
        self.price_entry.grid(row=2, column=1, padx=(20, 0), sticky='ew')

        ttk.Label(self, text="Stock",
                  font=("Segoe UI", 11)).grid(row=3, column=0, pady=10, sticky='w')
        self.stock_entry = ttk.Entry(self)
        self.stock_entry.grid(row=3, column=1, padx=(20, 0), sticky='ew')

        # Frame para los botones
        frame_botones = ttk.Frame(self)
        frame_botones.grid(row=4, column=1, pady=20, sticky='e')

        self.edit_button = ttk.Button(frame_botones, text="Editar",
                                      bootstyle="warning", width=15, state="enabled")
        self.edit_button.pack(side='left', padx=5)

        self.delete_button = ttk.Button(frame_botones, text="Eliminar",
                                        bootstyle="danger", width=15, state="enabled")
        self.delete_button.pack(side='left', padx=5)

        self.save_button = ttk.Button(frame_botones, text="Guardar",
                                      bootstyle="primary", width=15)
        self.save_button.pack(side='left')

        self.cancel_button = ttk.Button(frame_botones, text="Cancelar",
                                        bootstyle="secondary", width=15,
                                        command=self.cancel_edit)
        self.cancel_button.pack(side='left', padx=5)
        self.cancel_button.pack_forget()  # Inicialmente oculto

    def get_product_data(self):
        return {
            'barcode': self.barcode_entry.get(),
            'name': self.name_entry.get(),
            'price': self.price_entry.get(),
            'stock': self.stock_entry.get()
        }

    def clear_fields(self):
        self.barcode_entry.delete(0, 'end')
        self.name_entry.delete(0, 'end')
        self.price_entry.delete(0, 'end')
        self.stock_entry.delete(0, 'end')
        self.set_editing_mode(False)
        self.set_action_buttons_state(False)
        # Asegurar que esté habilitado al limpiar
        self.barcode_entry.configure(state='normal')

    def set_editing_mode(self, editing):
        self.editing_mode = editing
        if editing:
            self.configure(text="Editar Producto")
            self.save_button.configure(text="Guardar Cambios")
            self.cancel_button.pack(side='left', padx=5)
            # Deshabilitar solo en modo edición
            self.barcode_entry.configure(state='disabled')
        else:
            self.configure(text="Agregar Producto")
            self.save_button.configure(text="Guardar")
            self.cancel_button.pack_forget()
            # Habilitar en modo normal
            self.barcode_entry.configure(state='normal')

    def set_action_buttons_state(self, state: str) -> None:
        """Configura el estado de los botones de acción.

        Args:
            state: El estado de los botones ("normal" o "disabled").
        """
        self.edit_button.configure(state=state)
        self.delete_button.configure(state=state)

    def cancel_edit(self):
        self.clear_fields()
        self.set_action_buttons_state(False)


class ProductList(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.pack(fill=BOTH, expand=True)
        self._create_widgets()

    def _create_widgets(self):
        # Título de la lista
        title_label = ttk.Label(self, text="Lista de Productos",
                                font=("Segoe UI", 16, "bold"))
        title_label.pack(pady=(0, 20), anchor='w')

        # Configurar el estilo antes de crear la tabla
        style = ttk.Style()

        # Estilo para la tabla
        style.configure(
            "Custom.Treeview",
            background="white",
            foreground="black",
            rowheight=35,  # Reducido de 50 a 35
            fieldbackground="white",
            borderwidth=0,  # Sin borde
            font=('Segoe UI', 11)  # Reducido de 14 a 11
        )

        # Estilo para los encabezados
        style.configure(
            "Custom.Treeview.Heading",
            background="#2c3e50",
            foreground="white",
            relief="flat",
            borderwidth=0,  # Sin borde
            font=('Segoe UI', 12, 'bold')  # Reducido de 16 a 12
        )

        # Estilo para la selección
        style.map(
            "Custom.Treeview",
            background=[("selected", "#3498db")],
            foreground=[("selected", "white")]
        )

        # Tabla usando Treeview
        columns = ("codigo", "nombre", "precio", "stock")
        self.tabla = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=10,  # Ajustado a 10 filas
            style="Custom.Treeview"
        )

        # Definir los encabezados
        self.tabla.heading("codigo", text="Código de barras", anchor="center")
        self.tabla.heading("nombre", text="Nombre", anchor="center")
        self.tabla.heading("precio", text="Precio", anchor="center")
        self.tabla.heading("stock", text="Stock", anchor="center")

        # Configurar el ancho y alineación de las columnas
        self.tabla.column("codigo", width=180, anchor="center",
                          minwidth=180)  # Reducido de 250 a 180
        self.tabla.column("nombre", width=250, anchor="center",
                          minwidth=250)  # Reducido de 400 a 250
        self.tabla.column("precio", width=120, anchor="center",
                          minwidth=120)  # Reducido de 200 a 120
        self.tabla.column("stock", width=120, anchor="center",
                          minwidth=120)   # Reducido de 200 a 120

        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(
            self, orient=VERTICAL, command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)

        # Empaquetar la tabla y el scrollbar
        self.tabla.pack(side=LEFT, fill=BOTH, expand=True, padx=20, pady=20)
        scrollbar.pack(side=RIGHT, fill=Y, pady=20)

    def load_products(self, products):
        # Limpiar tabla
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        # Cargar productos
        for i, product in enumerate(products):
            # Formatear el precio con 2 decimales
            precio_formateado = f"${product.price:.2f}"
            # Formatear el stock como número entero
            stock_formateado = f"{int(product.stock)}"

            # Insertar el producto con tags para alternar colores
            item = self.tabla.insert("", END, values=(
                product.barcode,
                product.name,
                precio_formateado,
                stock_formateado
            ), tags=('evenrow' if i % 2 == 0 else 'oddrow',))

        # Configurar colores alternados
        self.tabla.tag_configure('evenrow', background='#ecf0f1')
        self.tabla.tag_configure('oddrow', background='white')

    def refresh(self) -> None:
        """Actualiza la lista de productos en la vista. Puedes implementar la lógica real aquí."""
        self.load_products([])
