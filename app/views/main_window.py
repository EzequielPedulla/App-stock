import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from .product_form import ProductForm
from .product_list import ProductList


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

        # Contenedor para el menú con padding
        menu_container = ttk.Frame(self.frame_nav, bootstyle="primary")
        menu_container.pack(padx=20, pady=20, fill=Y)

        # Título del menú
        ttk.Label(menu_container, text="Productos",
                  font=("Segoe UI", 24, "bold"),
                  foreground="white",
                  bootstyle="primary").pack(pady=(0, 30))

        # Botones del menú
        self._create_menu_buttons(menu_container)

        # Frame principal con fondo blanco
        self.frame_contenido = ttk.Frame(self)
        self.frame_contenido.pack(side=LEFT, expand=True, fill=BOTH)

        # Contenedor interno con padding
        contenido_interno = ttk.Frame(self.frame_contenido)
        contenido_interno.pack(padx=30, pady=30, fill=BOTH, expand=True)

        # Crear formulario y lista de productos
        self.product_form = ProductForm(contenido_interno)
        self.product_list = ProductList(contenido_interno)

    def _create_menu_buttons(self, container):
        buttons_data = [
            ("📦 Productos", self._on_productos_click),
            ("💰 Ventas", self._on_ventas_click),
            ("📊 Reportes", self._on_reportes_click),
            ("⚙️ Configuración", self._on_config_click)
        ]

        for text, command in buttons_data:
            btn = ttk.Button(container, text=text,
                             bootstyle="outline-primary",
                             width=25,
                             command=command)
            btn.pack(fill=X, pady=5)

    def _on_productos_click(self):
        print("Productos clicked")

    def _on_ventas_click(self):
        print("Ventas clicked")

    def _on_reportes_click(self):
        print("Reportes clicked")

    def _on_config_click(self):
        print("Configuración clicked")
