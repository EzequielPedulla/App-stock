import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from .product_form import ProductForm
from .product_list import ProductList
from .sale_form import SaleForm
from .caja_form import CajaForm
from .report_form import ReportForm
from .fiados_form import FiadosForm
from .pedidos_form import PedidosForm
from .scrollable_frame import ScrollableFrame
from .estilos import (
    fix_label_backgrounds, configurar_idioma, instalar_icono_en_dialogos)
from .owner_dialogs import pedir_clave, cambiar_clave
from ..security import owner_lock
from config import resource_path


class MainWindow(ttk.Window):
    def __init__(self):
        super().__init__(title="Sistema de Gestión de Inventario",
                         themename="flatly")
        self.resizable(True, True)
        self.minsize(1024, 700)
        configurar_idioma()
        self._poner_icono()
        self._ajustar_tamano_inicial()
        self._setup_custom_styles()
        self._create_widgets()

    def _poner_icono(self) -> None:
        """Ícono de la app en la ventana, la barra de tareas y todos los
        diálogos. Si el archivo no está, se sigue con el ícono por defecto.

        Se usa iconbitmap con el .ico directo sobre cada ventana: en Windows
        ni iconphoto ni iconbitmap(default=...) lo muestran (ttkbootstrap
        deja su ícono propio)."""
        ico = resource_path('assets/icono.ico')
        try:
            self.iconbitmap(str(ico))
        except tk.TclError:
            pass
        instalar_icono_en_dialogos(ico)

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

        # Colores con más contraste: el gris "secondary" del tema (#95a5a6)
        # con letra blanca cuesta leer en un monitor chico.
        style.colors.set('secondary', '#5d6d7e')
        style.colors.set('selectbg', '#2c3e50')
        style.colors.set('selectfg', '#ffffff')
        style.theme_use('flatly')
        # La fila seleccionada de las tablas también era gris claro con
        # letra blanca: se pasa a azul oscuro, bien visible.
        style.map("Treeview",
                  background=[("selected", "#2c3e50")],
                  foreground=[("selected", "white")])

        # Fuente base: cubre los widgets que no definen su propia fuente
        # explícita (algunos Entry, y cualquier Treeview sin estilo propio,
        # como el de "Buscar Producto" en Ventas).
        style.configure(".", font=("Segoe UI", 15))
        style.configure("Treeview", font=("Segoe UI", 15), rowheight=46)
        style.configure("Treeview.Heading", font=("Segoe UI", 16, "bold"))
        style.configure("TButton", font=("Segoe UI", 15))
        style.configure("TEntry", font=("Segoe UI", 15))
        style.configure("TLabel", font=("Segoe UI", 15))
        style.configure("TCheckbutton", font=("Segoe UI", 15))
        style.configure("TRadiobutton", font=("Segoe UI", 15))
        style.configure("TCombobox", font=("Segoe UI", 15))
        style.configure("TMenubutton", font=("Segoe UI", 15))
        style.configure("TNotebook.Tab", font=("Segoe UI", 15))
        # La lista desplegable de los combobox es un widget tk clásico: no
        # toma el estilo ttk, hay que darle la fuente aparte.
        self.option_add("*TCombobox*Listbox.font", ("Segoe UI", 15))

        # Estilo para botones del menú lateral
        style.configure(
            "Custom.TButton",
            background="#34495e",
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            font=("Segoe UI", 17, "normal"),
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
        self.frame_nav = ttk.Frame(self, bootstyle="primary", width=270)
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
        self._menu_spacer = ttk.Frame(menu_container, bootstyle="primary")
        self._menu_spacer.pack(expand=True, fill=Y)

        # Modo dueño: con la clave se destapan los montos sensibles
        # (totales de Caja, Reportes y Fiados).
        self.cambiar_clave_button = ttk.Button(
            menu_container, text="🔑 Cambiar clave", bootstyle="info", width=16,
            command=lambda: cambiar_clave(self))
        self.lock_button = ttk.Button(
            menu_container, text="🔒 Modo dueño", bootstyle="warning", width=16,
            command=self._toggle_modo_dueno)
        self.lock_button.pack(fill=X, padx=20, pady=(0, 20), side=BOTTOM,
                              before=self._menu_spacer)

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

        # Frame para fiados (cuaderno de clientes que deben)
        self.fiados_frame = tk.Frame(self.contenido_interno, bg="white")
        fiados_scroll = ScrollableFrame(self.fiados_frame)
        fiados_scroll.pack(fill=BOTH, expand=True)
        self.fiados_form = FiadosForm(fiados_scroll.interior)
        self.fiados_form.pack(fill=BOTH, expand=True)

        # Frame para pedidos a proveedores
        self.pedidos_frame = tk.Frame(self.contenido_interno, bg="white")
        pedidos_scroll = ScrollableFrame(self.pedidos_frame)
        pedidos_scroll.pack(fill=BOTH, expand=True)
        self.pedidos_form = PedidosForm(pedidos_scroll.interior)
        self.pedidos_form.pack(fill=BOTH, expand=True)

        self.reports_frame = tk.Frame(self.contenido_interno, bg="white")
        reports_scroll = ScrollableFrame(self.reports_frame)
        reports_scroll.pack(fill=BOTH, expand=True)
        self.report_form = ReportForm(reports_scroll.interior)
        self.report_form.pack(fill=BOTH, expand=True)

        fix_label_backgrounds(self)
        self._iniciar_modo_dueno()
        self._iniciar_atajos_pestanas()
        self.show_products()

    def _iniciar_atajos_pestanas(self) -> None:
        """Alt+1..6 cambia de pestaña sin usar el mouse."""
        for i, accion in enumerate((
                self.show_products, self.show_sales, self.show_caja,
                self.show_fiados, self.show_pedidos,
                self.show_reports), start=1):
            self.bind_all(f'<Alt-Key-{i}>', lambda e, a=accion: a())

    def _iniciar_modo_dueno(self) -> None:
        """Conecta el candado de dueño: cada vez que se bloquea o desbloquea
        se actualizan los botones y las pantallas con montos, y se vuelve a
        bloquear solo tras un rato sin usar la app."""
        owner_lock.on_change(self._on_modo_dueno_cambio)
        for evento in ('<Key>', '<Button>', '<Motion>'):
            self.bind_all(evento, lambda e: owner_lock.touch(), add='+')
        self._revisar_autobloqueo()
        self._actualizar_boton_dueno()

    def _revisar_autobloqueo(self) -> None:
        owner_lock.check_autolock()
        self.after(10_000, self._revisar_autobloqueo)

    def _toggle_modo_dueno(self) -> None:
        if owner_lock.unlocked:
            owner_lock.lock()
        else:
            pedir_clave(self)

    def _actualizar_boton_dueno(self) -> None:
        if owner_lock.unlocked:
            self.lock_button.configure(
                text="🔓 Bloquear", bootstyle="danger")
            self.cambiar_clave_button.pack(
                fill=X, padx=20, pady=(0, 10), side=BOTTOM,
                after=self.lock_button)
        else:
            self.lock_button.configure(
                text="🔒 Modo dueño", bootstyle="warning")
            self.cambiar_clave_button.pack_forget()

    def _on_modo_dueno_cambio(self) -> None:
        self._actualizar_boton_dueno()
        for form, nombre in ((self.caja_form, 'caja_controller'),
                             (self.fiados_form, 'fiados_controller'),
                             (self.pedidos_form, 'pedidos_controller'),
                             (self.report_form, 'report_controller')):
            controlador = getattr(form, nombre, None)
            if controlador:
                controlador.refresh()

    def _create_menu_buttons(self, container):
        """Crea los botones del menú lateral con el estilo moderno."""
        buttons_data = [
            ("📦", "Productos", self.show_products),
            ("💰", "Ventas", self.show_sales),
            ("🧮", "Caja", self.show_caja),
            ("📒", "Fiados", self.show_fiados),
            ("🚚", "Pedidos", self.show_pedidos),
            ("📊", "Reportes", self.show_reports)
        ]

        self.menu_buttons = {}
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
            self.menu_buttons[text] = btn

    def show_products(self):
        """Muestra la sección de productos y actualiza el título."""
        self.ventas_frame.pack_forget()
        self.caja_frame.pack_forget()
        self.reports_frame.pack_forget()
        self.fiados_frame.pack_forget()
        self.pedidos_frame.pack_forget()
        self.productos_frame.pack(fill=BOTH, expand=True)
        self.titulo_label.config(text="Productos")

    def show_sales(self):
        """Muestra la sección de ventas y actualiza el título."""
        self.productos_frame.pack_forget()
        self.caja_frame.pack_forget()
        self.reports_frame.pack_forget()
        self.fiados_frame.pack_forget()
        self.pedidos_frame.pack_forget()
        self.ventas_frame.pack(fill=BOTH, expand=True)
        self.titulo_label.config(text="Ventas")

    def show_caja(self):
        """Muestra la sección de caja y actualiza el título."""
        self.productos_frame.pack_forget()
        self.ventas_frame.pack_forget()
        self.reports_frame.pack_forget()
        self.fiados_frame.pack_forget()
        self.pedidos_frame.pack_forget()
        self.caja_frame.pack(fill=BOTH, expand=True)
        self.titulo_label.config(text="Caja")
        if getattr(self.caja_form, 'caja_controller', None):
            self.caja_form.caja_controller.refresh()

    def show_fiados(self):
        """Muestra el cuaderno de fiados y actualiza el título."""
        self.productos_frame.pack_forget()
        self.ventas_frame.pack_forget()
        self.caja_frame.pack_forget()
        self.reports_frame.pack_forget()
        self.pedidos_frame.pack_forget()
        self.fiados_frame.pack(fill=BOTH, expand=True)
        self.titulo_label.config(text="Fiados")
        if getattr(self.fiados_form, 'fiados_controller', None):
            self.fiados_form.fiados_controller.refresh()

    def show_pedidos(self):
        """Muestra los pedidos a proveedores y actualiza el título."""
        self.productos_frame.pack_forget()
        self.ventas_frame.pack_forget()
        self.caja_frame.pack_forget()
        self.reports_frame.pack_forget()
        self.fiados_frame.pack_forget()
        self.pedidos_frame.pack(fill=BOTH, expand=True)
        self.titulo_label.config(text="Pedidos")
        if getattr(self.pedidos_form, 'pedidos_controller', None):
            self.pedidos_form.pedidos_controller.refresh()

    def set_badge_pedidos(self, cantidad: int) -> None:
        """Muestra en el menú cuántos pedidos vienen hoy, mañana o están
        atrasados."""
        btn = self.menu_buttons.get("Pedidos")
        if btn:
            btn.configure(text="🚚  Pedidos" + (f" ({cantidad})" if cantidad
                                               else ""))

    def show_reports(self):
        self.productos_frame.pack_forget()
        self.ventas_frame.pack_forget()
        self.caja_frame.pack_forget()
        self.fiados_frame.pack_forget()
        self.pedidos_frame.pack_forget()
        self.reports_frame.pack(fill=BOTH, expand=True)
        self.titulo_label.config(text="Reportes")
        if getattr(self.report_form, 'report_controller', None):
            self.report_form.report_controller.refresh()
