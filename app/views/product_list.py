import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class ProductList(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.pack(fill=BOTH, expand=True)
        self.all_products = []  # Lista completa de productos
        self._create_widgets()

    def _create_widgets(self):
        # Título de la lista
        title_label = ttk.Label(self, text="Lista de Productos",
                                font=("Segoe UI", 16, "bold"))
        title_label.pack(pady=(0, 10), anchor='w', padx=20)

        # ===== FRAME DE BÚSQUEDA =====
        search_frame = ttk.Frame(self)
        search_frame.pack(fill='x', padx=20, pady=(0, 15))

        ttk.Label(search_frame, text="🔍 Buscar:",
                  font=("Segoe UI", 11)).pack(side='left', padx=(0, 10))

        self.search_var = ttk.StringVar()
        self.search_var.trace('w', self._on_search)  # Se ejecuta al escribir

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

        # Configurar estilo
        style = ttk.Style()
        style.configure(
            "Custom.Treeview",
            background="white",
            foreground="black",
            rowheight=35,
            fieldbackground="white",
            borderwidth=0,
            font=('Segoe UI', 11)
        )
        style.configure(
            "Custom.Treeview.Heading",
            background="#2c3e50",
            foreground="white",
            relief="flat",
            borderwidth=0,
            font=('Segoe UI', 12, 'bold')
        )
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
            height=10,
            style="Custom.Treeview"
        )

        # Encabezados
        self.tabla.heading("codigo", text="Código de barras", anchor="center")
        self.tabla.heading("nombre", text="Nombre", anchor="center")
        self.tabla.heading("precio", text="Precio", anchor="center")
        self.tabla.heading("stock", text="Stock", anchor="center")

        # Columnas
        self.tabla.column("codigo", width=180, anchor="center", minwidth=180)
        self.tabla.column("nombre", width=250, anchor="center", minwidth=250)
        self.tabla.column("precio", width=120, anchor="center", minwidth=120)
        self.tabla.column("stock", width=120, anchor="center", minwidth=120)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self, orient=VERTICAL, command=self.tabla.yview)
        self.tabla.configure(yscrollcommand=scrollbar.set)

        # Empaquetar
        self.tabla.pack(side=LEFT, fill=BOTH, expand=True, padx=20, pady=20)
        scrollbar.pack(side=RIGHT, fill=Y, pady=20)

    def _on_search(self, *args):
        """Se ejecuta cada vez que el usuario escribe en el buscador"""
        search_term = self.search_var.get().lower().strip()

        if not search_term:
            # Si no hay búsqueda, mostrar todos
            self._display_products(self.all_products)
            self.info_label.configure(text="")
        else:
            # Filtrar productos
            filtered = [p for p in self.all_products
                        if search_term in p.barcode.lower() or
                        search_term in p.name.lower()]
            self._display_products(filtered)

            # Actualizar info
            if filtered:
                self.info_label.configure(
                    text=f"Mostrando {len(filtered)} de {len(self.all_products)} productos")
            else:
                self.info_label.configure(text="No se encontraron productos")

    def _clear_search(self):
        """Limpia el campo de búsqueda"""
        self.search_var.set("")

    def _display_products(self, products):
        """Muestra los productos en el Treeview"""
        # Limpiar tabla
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        # Cargar productos filtrados
        for i, product in enumerate(products):
            precio_formateado = f"${product.price:.2f}"
            stock_formateado = f"{int(product.stock)}"

            self.tabla.insert("", END, values=(
                product.barcode,
                product.name,
                precio_formateado,
                stock_formateado
            ), tags=('evenrow' if i % 2 == 0 else 'oddrow',))

        # Colores alternados
        self.tabla.tag_configure('evenrow', background='#ecf0f1')
        self.tabla.tag_configure('oddrow', background='white')

    def load_products(self, products):
        """Carga la lista completa de productos"""
        self.all_products = products
        self._display_products(products)

        # Actualizar info
        if products:
            self.info_label.configure(text=f"Total: {len(products)} productos")

    def refresh(self) -> None:
        """Actualiza la lista de productos"""
        self.load_products(self.all_products)
