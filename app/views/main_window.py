import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from .product_form import ProductForm
from .product_list import ProductList
from .sale_form import SaleForm


class MainWindow(ttk.Window):
    def __init__(self):
        super().__init__(title="Sistema de Gestión de Inventario",
                         themename="flatly",
                         size=(1200, 700))
        self.resizable(False, False)
        self._create_widgets()

    def _create_widgets(self):
        # Frame de navegación (menú lateral)
        self.frame_nav = ttk.Frame(self, bootstyle="primary")
        self.frame_nav.pack(side=LEFT, fill=Y)

        # Contenedor para el menú con padding y fondo
        menu_container = ttk.Frame(self.frame_nav, bootstyle="primary")
        menu_container.pack(padx=0, pady=0, fill=Y, expand=True)

        # Título del menú
        ttk.Label(menu_container, text="Productos",
                  font=("Segoe UI", 24, "bold"),
                  foreground="white",
                  bootstyle="primary").pack(pady=(40, 30), anchor="w")

        # Botones del menú
        self._create_menu_buttons(menu_container)

        # Espaciador para alinear abajo la configuración
        ttk.Label(menu_container, text="", bootstyle="primary").pack(
            expand=True, fill=Y)

        # Frame principal con fondo blanco
        self.frame_contenido = ttk.Frame(self, bootstyle="light")
        self.frame_contenido.pack(side=LEFT, expand=True, fill=BOTH)

        # Contenedor interno con padding y fondo blanco
        self.contenido_interno = ttk.Frame(
            self.frame_contenido, bootstyle="light")
        self.contenido_interno.pack(padx=30, pady=30, fill=BOTH, expand=True)

        # Frame para productos (formulario + lista)
        self.productos_frame = ttk.Frame(
            self.contenido_interno, bootstyle="light")
        self.productos_frame.pack(fill=BOTH, expand=True)
        self.product_form = ProductForm(self.productos_frame)
        self.product_list = ProductList(self.productos_frame)
        self.product_form.pack(side="top", fill="x", pady=(0, 10))
        self.product_list.pack(side="top", fill="both", expand=True)

        # Frame para ventas (solo se muestra cuando corresponde)
        self.ventas_frame = ttk.Frame(
            self.contenido_interno, bootstyle="light")
        self.sale_form = SaleForm(self.ventas_frame)
        self.sale_form.pack(fill=BOTH, expand=True)

        self.show_products()

    def _create_menu_buttons(self, container):
        buttons_data = [
            ("📦 Productos", self.show_products),
            ("💰 Ventas", self.show_sales),
            ("📊 Reportes", self._on_reportes_click),
            ("⚙️ Configuración", self._on_config_click)
        ]

        for text, command in buttons_data:
            btn = ttk.Button(container, text=text,
                             bootstyle="outline-primary",
                             width=25,
                             command=command)
            btn.pack(fill=X, pady=5)

    def show_products(self):
        self.ventas_frame.pack_forget()
        self.productos_frame.pack(fill=BOTH, expand=True)

    def show_sales(self):
        self.productos_frame.pack_forget()
        self.ventas_frame.pack(fill=BOTH, expand=True)

    def _on_reportes_click(self):
        print("Reportes clicked")

    def _on_config_click(self):
        print("Configuración clicked")
