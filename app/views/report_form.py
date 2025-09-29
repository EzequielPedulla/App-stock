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

        # Card: Últimas ventas (tabla)
        card_tabla = ttk.Frame(bottom_container, bootstyle="light", padding=20)
        card_tabla.pack(side=RIGHT, fill=BOTH, expand=True, padx=(10, 0))

        ttk.Label(
            card_tabla,
            text="Últimas ventas",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor=W, pady=(0, 15))

        # Tabla de últimas ventas
        columns = ("producto", "monto")
        self.tabla_ventas = ttk.Treeview(
            card_tabla,
            columns=columns,
            show="headings",
            height=8
        )

        self.tabla_ventas.heading("producto", text="Producto", anchor=W)
        self.tabla_ventas.heading("monto", text="Monto", anchor=E)

        self.tabla_ventas.column("producto", width=200, anchor=W)
        self.tabla_ventas.column("monto", width=100, anchor=E)

        # Colores alternados
        self.tabla_ventas.tag_configure('evenrow', background='#ecf0f1')
        self.tabla_ventas.tag_configure('oddrow', background='white')

        self.tabla_ventas.pack(fill=BOTH, expand=True)

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
                self.tabla_ventas.insert(
                    "", END,
                    values=(venta['producto'], f"${venta['monto']:.2f}"),
                    tags=('evenrow' if i % 2 == 0 else 'oddrow',)
                )
