import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from .product_form import ProductForm
from .product_list import ProductList
from .sale_form import SaleForm
from .caja_form import CajaForm
from .report_form import ReportForm
from .scrollable_frame import ScrollableFrame


class MainWindow(ttk.Window):
    def __init__(self):
        super().__init__(title="Sistema de Gestión de Inventario",
                         themename="flatly")
        self.resizable(True, True)
        self.minsize(1024, 700)
        self._ajustar_tamano_inicial()
        self._setup_custom_styles()
        self._create_widgets()

    def _ajustar_tamano_inicial(self) -> None:
        """Usa la mayor parte de la pantalla disponible, sin superar un
        tamaño cómodo ni exceder el monitor real (puede ser chico). Pensado
        para que en un monitor 1280x1024 (la PC donde corre el programa en
        el local) la ventana ocupe casi toda la pantalla, dejando solo un
        margen chico para la barra de tareas."""
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        width = min(1550, int(screen_w * 0.95))
        height = min(980, int(screen_h * 0.92))
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _setup_custom_styles(self) -> None:
        """Configura estilos personalizados y el tamaño base de fuente de
        toda la app. Pensado para que se vea bien en un monitor 1280x1024,
        donde el texto chico por defecto cuesta leer."""
        style = ttk.Style()

        # Fuente base: cubre los widgets que no definen su propia fuente
        # explícita (algunos Entry, y cualquier Treeview sin estilo propio,
        # como el de "Buscar Producto" en Ventas).
        style.configure(".", font=("Segoe UI", 13))
        style.configure("Treeview", font=("Segoe UI", 13), rowheight=38)
        style.configure("Treeview.Heading", font=("Segoe UI", 14, "bold"))
        style.configure("TButton", font=("Segoe UI", 13))
        style.configure("TEntry", font=("Segoe UI", 13))
        style.configure("TLabel", font=("Segoe UI", 13))

        # Estilo para botones del menú lateral
        style.configure(
            "Custom.TButton",
            background="#34495e",
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            font=("Segoe UI", 15, "normal"),
            padding=(22, 20),
            relief="flat"
        )

        style.map(
            "Custom.TButton",
            background=[("active", "#3498db"), ("pressed", "#2980b9")],
            foreground=[("active", "white"), ("pressed", "white")]
        )

    def _create_widgets(self):
        # Frame de navegación (menú lateral)
        self.frame_nav = ttk.Frame(self, bootstyle="primary", width=230)
        self.frame_nav.pack(side=LEFT, fill=Y)
        self.frame_nav.pack_propagate(False)

        # Contenedor para el menú con padding y fondo
        menu_container = ttk.Frame(self.frame_nav, bootstyle="primary")
        menu_container.pack(padx=0, pady=0, fill=Y, expand=True)

        # Título del menú dinámico
        self.titulo_label = ttk.Label(menu_container, text="Productos",
                                      font=("Segoe UI", 23),
                                      foreground="white",
                                      background="#34495e")
        self.titulo_label.pack(pady=(30, 20), padx=20, anchor="center")

        # Botones del menú
        self._create_menu_buttons(menu_container)

        # Espaciador para alinear abajo la configuración
        ttk.Frame(menu_container, bootstyle="primary").pack(
            expand=True, fill=Y)

        # Frame principal con fondo blanco puro
        self.frame_contenido = tk.Frame(self, bg="white")
        self.frame_contenido.pack(side=LEFT, expand=True, fill=BOTH)

        # Contenedor interno con padding y fondo blanco puro
        self.contenido_interno = tk.Frame(self.frame_contenido, bg="white")
        self.contenido_interno.pack(padx=30, pady=30, fill=BOTH, expand=True)

        # Cada pestaña envuelve su contenido en un ScrollableFrame: si la
        # ventana queda chica (monitor chico o achicada a mano), lo que no
        # entra se alcanza con la scrollbar en vez de quedar cortado.

        # Frame para productos (formulario + lista)
        self.productos_frame = tk.Frame(self.contenido_interno, bg="white")
        self.productos_frame.pack(fill=BOTH, expand=True)
        productos_scroll = ScrollableFrame(self.productos_frame)
        productos_scroll.pack(fill=BOTH, expand=True)
        self.product_form = ProductForm(productos_scroll.interior)
        self.product_list = ProductList(productos_scroll.interior)
        self.product_form.pack(side="top", fill="x", pady=(0, 10))
        self.product_list.pack(side="top", fill="both", expand=True)

        # Frame para ventas (solo se muestra cuando corresponde)
        self.ventas_frame = tk.Frame(self.contenido_interno, bg="white")
        ventas_scroll = ScrollableFrame(self.ventas_frame)
        ventas_scroll.pack(fill=BOTH, expand=True)
        self.sale_form = SaleForm(ventas_scroll.interior)
        self.sale_form.pack(fill=BOTH, expand=True)

        # Frame para caja (solo se muestra cuando corresponde)
        self.caja_frame = tk.Frame(self.contenido_interno, bg="white")
        caja_scroll = ScrollableFrame(self.caja_frame)
        caja_scroll.pack(fill=BOTH, expand=True)
        self.caja_form = CajaForm(caja_scroll.interior)
        self.caja_form.pack(fill=BOTH, expand=True)

        self.reports_frame = tk.Frame(self.contenido_interno, bg="white")
        reports_scroll = ScrollableFrame(self.reports_frame)
        reports_scroll.pack(fill=BOTH, expand=True)
        self.report_form = ReportForm(reports_scroll.interior)
        self.report_form.pack(fill=BOTH, expand=True)

        self.show_products()

    def _create_menu_buttons(self, container):
        """Crea los botones del menú lateral con el estilo moderno."""
        buttons_data = [
            ("📦", "Productos", self.show_products),
            ("💰", "Ventas", self.show_sales),
            ("🧮", "Caja", self.show_caja),
            ("📊", "Reportes", self.show_reports)
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
        self.caja_frame.pack_forget()
        self.reports_frame.pack_forget()
        self.productos_frame.pack(fill=BOTH, expand=True)
        self.titulo_label.config(text="Productos")

    def show_sales(self):
        """Muestra la sección de ventas y actualiza el título."""
        self.productos_frame.pack_forget()
        self.caja_frame.pack_forget()
        self.reports_frame.pack_forget()
        self.ventas_frame.pack(fill=BOTH, expand=True)
        self.titulo_label.config(text="Ventas")

    def show_caja(self):
        """Muestra la sección de caja y actualiza el título."""
        self.productos_frame.pack_forget()
        self.ventas_frame.pack_forget()
        self.reports_frame.pack_forget()
        self.caja_frame.pack(fill=BOTH, expand=True)
        self.titulo_label.config(text="Caja")
        if getattr(self.caja_form, 'caja_controller', None):
            self.caja_form.caja_controller.refresh()

    def show_reports(self):
        self.productos_frame.pack_forget()
        self.ventas_frame.pack_forget()
        self.caja_frame.pack_forget()
        self.reports_frame.pack(fill=BOTH, expand=True)
        self.titulo_label.config(text="Reportes")
        if getattr(self.report_form, 'report_controller', None):
            self.report_form.report_controller.refresh()
