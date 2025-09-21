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
        self._setup_custom_styles()
        self._create_widgets()

    def _setup_custom_styles(self) -> None:
        """Configura estilos personalizados para los botones del menú."""
        style = ttk.Style()

        # Estilo para botones del menú lateral
        style.configure(
            "Custom.TButton",
            background="#34495e",
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            font=("Segoe UI", 13, "normal"),
            padding=(20, 18),
            relief="flat"
        )

        style.map(
            "Custom.TButton",
            background=[("active", "#3498db"), ("pressed", "#2980b9")],
            foreground=[("active", "white"), ("pressed", "white")]
        )

    def _create_widgets(self):
        # Frame de navegación (menú lateral)
        self.frame_nav = ttk.Frame(self, bootstyle="primary", width=200)
        self.frame_nav.pack(side=LEFT, fill=Y)
        self.frame_nav.pack_propagate(False)

        # Contenedor para el menú con padding y fondo
        menu_container = ttk.Frame(self.frame_nav, bootstyle="primary")
        menu_container.pack(padx=0, pady=0, fill=Y, expand=True)

        # Título del menú dinámico
        self.titulo_label = ttk.Label(menu_container, text="Productos",
                                      font=("Segoe UI", 20),
                                      foreground="white",
                                      background="#34495e")
        self.titulo_label.pack(pady=(30, 20), padx=20, anchor="center")

        # Botones del menú
        self._create_menu_buttons(menu_container)

        # Espaciador para alinear abajo la configuración
        ttk.Frame(menu_container, bootstyle="primary").pack(
            expand=True, fill=Y)

        # Frame principal con fondo oscuro
        self.frame_contenido = ttk.Frame(self, bootstyle="dark")
        self.frame_contenido.pack(side=LEFT, expand=True, fill=BOTH)

        # Contenedor interno con padding y fondo oscuro
        self.contenido_interno = ttk.Frame(
            self.frame_contenido, bootstyle="dark")
        self.contenido_interno.pack(padx=30, pady=30, fill=BOTH, expand=True)

        # Frame para productos (formulario + lista)
        self.productos_frame = ttk.Frame(
            self.contenido_interno, bootstyle="dark")
        self.productos_frame.pack(fill=BOTH, expand=True)
        self.product_form = ProductForm(self.productos_frame)
        self.product_list = ProductList(self.productos_frame)
        self.product_form.pack(side="top", fill="x", pady=(0, 10))
        self.product_list.pack(side="top", fill="both", expand=True)

        # Frame para ventas (solo se muestra cuando corresponde)
        self.ventas_frame = ttk.Frame(
            self.contenido_interno, bootstyle="dark")
        self.sale_form = SaleForm(self.ventas_frame)
        self.sale_form.pack(fill=BOTH, expand=True)

        self.show_products()

    def _create_menu_buttons(self, container):
        """Crea los botones del menú lateral con el estilo moderno."""
        buttons_data = [
            ("📦", "Productos", self.show_products),
            ("💰", "Ventas", self.show_sales),
            # ("📊", "Reportes", self._on_reportes_click),
            # ("⚙️", "Configuración", self._on_config_click)
        ]

        for icon, text, command in buttons_data:
            # Frame para cada botón
            btn_frame = ttk.Frame(container, bootstyle="dark")
            btn_frame.pack(fill=X, padx=20, pady=2)

            # Botón con icono y texto
            btn = ttk.Button(btn_frame,
                             text=f"{icon}  {text}",
                             style="Custom.TButton",
                             command=command)
            btn.pack(fill=X)

    def show_products(self):
        """Muestra la sección de productos y actualiza el título."""
        self.ventas_frame.pack_forget()
        self.productos_frame.pack(fill=BOTH, expand=True)
        self.titulo_label.config(text="Productos")

    def show_sales(self):
        """Muestra la sección de ventas y actualiza el título."""
        self.productos_frame.pack_forget()
        self.ventas_frame.pack(fill=BOTH, expand=True)
        self.titulo_label.config(text="Ventas")

    # def _on_reportes_click(self):
    #     """Maneja el evento de clic en el botón de reportes."""
    #     print("Reportes clicked")

    # def _on_config_click(self):
    #     """Maneja el evento de clic en el botón de configuración."""
    #     print("Configuración clicked")
