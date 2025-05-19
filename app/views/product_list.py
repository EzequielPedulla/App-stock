import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class ProductList(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Lista de Productos", padding=20, **kwargs)
        self.pack(fill=BOTH, expand=True)
        self._create_widgets()

    def _create_widgets(self):
        # Configurar el estilo antes de crear la tabla
        style = ttk.Style()

        # Estilo para la tabla
        style.configure(
            "Custom.Treeview",
            background="white",
            foreground="black",
            rowheight=35,  # Reducido de 50 a 35
            fieldbackground="white",
            borderwidth=1,  # Reducido de 2 a 1
            font=('Segoe UI', 11)  # Reducido de 14 a 11
        )

        # Estilo para los encabezados
        style.configure(
            "Custom.Treeview.Heading",
            background="#2c3e50",
            foreground="white",
            relief="flat",
            borderwidth=1,  # Reducido de 2 a 1
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
        self.tabla.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

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
