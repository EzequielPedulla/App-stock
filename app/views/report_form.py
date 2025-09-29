import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk


class ReportForm(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.pack(fill=BOTH, expand=True)
        self._create_widgets()

    def _create_widgets(self):
        # Título
        ttk.Label(
            self,
            text="Reportes",
            font=("Segoe UI", 24, "bold")
        ).pack(anchor=W, pady=(0, 20))

        # Container para las cards superiores
        top_cards = ttk.Frame(self)
        top_cards.pack(fill=X, pady=(0, 20))

        # Card: Total de ventas
        card_total = ttk.Frame(top_cards, bootstyle="light", padding=20)
        card_total.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        ttk.Label(
            card_total,
            text="Total de ventas",
            font=("Segoe UI", 12)
        ).pack(anchor=W)

        self.label_total_ventas = ttk.Label(
            card_total,
            text="$0",
            font=("Segoe UI", 28, "bold"),
            bootstyle="success"
        )
        self.label_total_ventas.pack(anchor=W, pady=(10, 0))

        # Card: Última venta
        card_ultima = ttk.Frame(top_cards, bootstyle="light", padding=20)
        card_ultima.pack(side=RIGHT, fill=BOTH, expand=True, padx=(10, 0))

        ttk.Label(
            card_ultima,
            text="Última venta",
            font=("Segoe UI", 12)
        ).pack(anchor=W)

        self.label_ultima_venta = ttk.Label(
            card_ultima,
            text="$0",
            font=("Segoe UI", 28, "bold"),
            bootstyle="info"
        )
        self.label_ultima_venta.pack(anchor=W, pady=(10, 0))

        # Container para gráfico y tabla
        bottom_container = ttk.Frame(self)
        bottom_container.pack(fill=BOTH, expand=True)

        # Card: Productos más vendidos (placeholder para gráfico)
        card_grafico = ttk.Frame(
            bottom_container, bootstyle="light", padding=20)
        card_grafico.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        ttk.Label(
            card_grafico,
            text="Productos más vendidos",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor=W, pady=(0, 15))

        # Placeholder para el gráfico
        self.grafico_frame = ttk.Frame(card_grafico, height=300)
        self.grafico_frame.pack(fill=BOTH, expand=True)

        ttk.Label(
            self.grafico_frame,
            text="📊 Gráfico próximamente",
            font=("Segoe UI", 11),
            foreground="gray"
        ).place(relx=0.5, rely=0.5, anchor=CENTER)

        # Card: Historial de ventas (tabla)
        card_tabla = ttk.Frame(bottom_container, bootstyle="light", padding=20)
        card_tabla.pack(side=RIGHT, fill=Y, padx=(10, 0))

        ttk.Label(
            card_tabla,
            text="Historial de ventas",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor=W, pady=(0, 15))

        # Configurar estilo para la tabla de ventas
        style = ttk.Style()
        style.configure(
            "Ventas.Treeview",
            rowheight=35,
            font=('Segoe UI', 11)
        )
        style.configure(
            "Ventas.Treeview.Heading",
            font=('Segoe UI', 12, 'bold')
        )

        # Frame para la tabla con scrollbar
        table_container = ttk.Frame(card_tabla)
        table_container.pack(fill=BOTH, expand=True)

        # Tabla de ventas (solo fecha y total, el ID se guarda oculto)
        columns = ("id", "fecha", "total")
        self.tabla_ventas = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            height=15,
            style="Ventas.Treeview"
        )

        # Ocultar la columna ID pero mantenerla para referencia
        self.tabla_ventas.heading("id", text="ID")
        self.tabla_ventas.column("id", width=0, stretch=False)

        self.tabla_ventas.heading("fecha", text="Fecha", anchor=W)
        self.tabla_ventas.heading("total", text="Total", anchor=E)

        self.tabla_ventas.column("fecha", width=150, anchor=W)
        self.tabla_ventas.column("total", width=100, anchor=E)

        # Colores alternados
        self.tabla_ventas.tag_configure('evenrow', background='#ecf0f1')
        self.tabla_ventas.tag_configure('oddrow', background='white')

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            table_container, orient=VERTICAL, command=self.tabla_ventas.yview)
        self.tabla_ventas.configure(yscrollcommand=scrollbar.set)

        self.tabla_ventas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

    def update_data(self, total_ventas=0, ultima_venta=0, productos_vendidos=None, ultimas_ventas=None):
        """Actualiza los datos mostrados en los reportes"""
        # Actualizar cards
        self.label_total_ventas.configure(text=f"${total_ventas:,.2f}")
        self.label_ultima_venta.configure(text=f"${ultima_venta:,.2f}")

        # Actualizar tabla de últimas ventas
        if ultimas_ventas:
            # Limpiar tabla
            for item in self.tabla_ventas.get_children():
                self.tabla_ventas.delete(item)

            # Insertar ventas
            for i, venta in enumerate(ultimas_ventas):
                # Formatear la fecha (solo fecha y hora, sin microsegundos)
                fecha_str = str(venta['date'])
                if len(fecha_str) > 19:
                    fecha_str = fecha_str[:19]

                self.tabla_ventas.insert(
                    "", END,
                    values=(venta['id'], fecha_str, f"${venta['total']:.2f}"),
                    tags=('evenrow' if i % 2 == 0 else 'oddrow',)
                )

    def show_sale_detail(self, sale_id, sale_date, sale_total, details):
        """Muestra una ventana con el detalle de la venta"""
        # Crear ventana modal
        detail_window = ttk.Toplevel(self)
        detail_window.title(f"Detalle de Venta N° {sale_id}")
        detail_window.geometry("800x600")
        detail_window.resizable(False, False)
        detail_window.transient(self)
        detail_window.grab_set()

        # Centrar la ventana
        detail_window.update_idletasks()
        width = detail_window.winfo_width()
        height = detail_window.winfo_height()
        x = (detail_window.winfo_screenwidth() // 2) - (width // 2)
        y = (detail_window.winfo_screenheight() // 2) - (height // 2)
        detail_window.geometry(f'{width}x{height}+{x}+{y}')

        # Frame principal
        main_frame = ttk.Frame(detail_window, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        # Encabezado
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=X, pady=(0, 20))

        ttk.Label(
            header_frame,
            text=f"Venta N° {sale_id}",
            font=("Segoe UI", 20, "bold")
        ).pack(side=LEFT)

        ttk.Label(
            header_frame,
            text=f"Fecha: {sale_date}",
            font=("Segoe UI", 12)
        ).pack(side=RIGHT)

        # Tabla de productos
        ttk.Label(
            main_frame,
            text="Productos",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor=W, pady=(0, 10))

        # Estilo para la tabla de detalles
        style = ttk.Style()
        style.configure(
            "Details.Treeview",
            rowheight=35,
            font=('Segoe UI', 11)
        )
        style.configure(
            "Details.Treeview.Heading",
            font=('Segoe UI', 12, 'bold')
        )

        # Crear tabla
        columns = ("producto", "cantidad", "precio", "subtotal")
        tree = ttk.Treeview(
            main_frame,
            columns=columns,
            show="headings",
            height=8,
            style="Details.Treeview"
        )

        tree.heading("producto", text="Producto", anchor=W)
        tree.heading("cantidad", text="Cantidad", anchor=CENTER)
        tree.heading("precio", text="Precio", anchor=E)
        tree.heading("subtotal", text="Subtotal", anchor=E)

        tree.column("producto", width=350, anchor=W)
        tree.column("cantidad", width=120, anchor=CENTER)
        tree.column("precio", width=130, anchor=E)
        tree.column("subtotal", width=130, anchor=E)

        # Insertar productos
        for i, detail in enumerate(details):
            tree.insert(
                "", END,
                values=(
                    detail['producto'],
                    detail['cantidad'],
                    f"${detail['precio']:.2f}",
                    f"${detail['subtotal']:.2f}"
                ),
                tags=('evenrow' if i % 2 == 0 else 'oddrow',)
            )

        # Colores alternados
        tree.tag_configure('evenrow', background='#ecf0f1')
        tree.tag_configure('oddrow', background='white')

        tree.pack(fill=BOTH, expand=True, pady=(0, 15))

        # Separador
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=X, pady=(15, 15))

        # Total
        total_frame = ttk.Frame(main_frame)
        total_frame.pack(fill=X, pady=(5, 0))

        ttk.Label(
            total_frame,
            text="Total de la venta:",
            font=("Segoe UI", 14)
        ).pack(side=LEFT)

        ttk.Label(
            total_frame,
            text=f"${sale_total:,.2f}",
            font=("Segoe UI", 22, "bold"),
            bootstyle="success"
        ).pack(side=RIGHT, padx=(20, 0))

        # Botón cerrar
        ttk.Button(
            main_frame,
            text="Cerrar",
            bootstyle="secondary",
            command=detail_window.destroy,
            width=20
        ).pack(pady=(15, 0))
