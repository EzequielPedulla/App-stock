import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk


class SaleForm(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self._create_widgets()

    def _create_widgets(self):
        # Título grande
        title_label = ttk.Label(self, text="Ventas",
                                font=("Segoe UI", 24, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 20))

        # Card para el formulario
        card = ttk.Frame(self, style="Card.TFrame", padding=20)
        card.pack(fill=tk.X, pady=(0, 20))

        # Subtítulo
        sub_label = ttk.Label(card, text="Registrar Venta",
                              font=("Segoe UI", 16, "bold"))
        sub_label.grid(row=0, column=0, columnspan=3,
                       sticky=tk.W, pady=(0, 10))

        # Código de barras
        barcode_label = ttk.Label(card, text="Código de barras",
                                  font=("Segoe UI", 11))
        barcode_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))

        self.barcode_entry = ttk.Entry(card, font=("Segoe UI", 12))
        self.barcode_entry.bind("<Return>", self._on_barcode_return)
        self.barcode_entry.grid(
            row=2, column=0, sticky=tk.EW, pady=(0, 10), padx=(0, 10))

        # Cantidad
        qty_label = ttk.Label(card, text="Cantidad",
                              font=("Segoe UI", 11))
        qty_label.grid(row=3, column=0, sticky=tk.W, pady=(0, 5))

        self.qty_entry = ttk.Entry(card, font=("Segoe UI", 12))
        self.qty_entry.grid(row=4, column=0, sticky=tk.EW,
                            pady=(0, 10), padx=(0, 10))

        # Botón Agregar
        self.add_button = ttk.Button(
            card, text="Agregar", style="primary.TButton", width=15)
        self.add_button.grid(row=5, column=1, sticky=tk.E,
                             padx=(10, 0), pady=5)

        card.columnconfigure(0, weight=1)

        # Productos seleccionados
        prod_sel_label = ttk.Label(
            self, text="Productos Seleccionados", font=("Segoe UI", 14, "bold"))
        prod_sel_label.pack(anchor=tk.W, pady=(10, 0))

        # Frame para la tabla y botones
        table_frame = ttk.Frame(self, style="Card.TFrame", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Frame para los botones de acción
        buttons_frame = ttk.Frame(table_frame)
        buttons_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        # Botones de acción
        self.edit_button = ttk.Button(
            buttons_frame, text="Editar", style="warning.TButton", width=15)
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = ttk.Button(
            buttons_frame, text="Eliminar", style="danger.TButton", width=15)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        # Tabla de productos
        columns = ("barcode", "name", "qty", "price", "subtotal")
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=6)
        self.tree.heading("barcode", text="Código de barras")
        self.tree.heading("name", text="Nombre")
        self.tree.heading("qty", text="Cantidad")
        self.tree.heading("price", text="Precio")
        self.tree.heading("subtotal", text="Subtotal")
        self.tree.column("barcode", width=140, anchor=tk.CENTER)
        self.tree.column("name", width=140, anchor=tk.CENTER)
        self.tree.column("qty", width=80, anchor=tk.CENTER)
        self.tree.column("price", width=80, anchor=tk.CENTER)
        self.tree.column("subtotal", width=100, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Total general
        total_frame = ttk.Frame(self)
        total_frame.pack(fill=tk.X, pady=(10, 0))

        self.total_label = ttk.Label(
            total_frame,
            text="Total: $0.00",
            font=("Segoe UI", 16, "bold"),
            anchor=tk.E
        )
        self.total_label.pack(side=tk.RIGHT)

    def _on_barcode_return(self, event) -> None:
        """Maneja el evento cuando se presiona Enter en el campo de código de barras.

        Args:
            event: El evento de tecla.
        """
        self.event_generate("<<AddItem>>")
