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
        qty_label.grid(row=1, column=1, sticky=tk.W, pady=(0, 5))

        self.qty_entry = ttk.Entry(card, font=("Segoe UI", 12))
        self.qty_entry.grid(row=2, column=1, sticky=tk.EW,
                            pady=(0, 10), padx=(0, 10))

        # Botones de acción
        self.add_button = ttk.Button(
            card, text="Agregar", style="primary.TButton", width=15)
        self.add_button.grid(row=2, column=2, sticky=tk.E,
                             padx=(10, 0), pady=5)

        self.edit_button = ttk.Button(
            card, text="Editar", style="warning.TButton", width=15)
        self.edit_button.grid(row=2, column=3, sticky=tk.E,
                              padx=(10, 0), pady=5)
        self.edit_button.configure(state="disabled")

        self.delete_button = ttk.Button(
            card, text="Eliminar", style="danger.TButton", width=15)
        self.delete_button.grid(row=2, column=4, sticky=tk.E,
                                padx=(10, 0), pady=5)
        self.delete_button.configure(state="disabled")

        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)

        # Productos seleccionados
        prod_sel_label = ttk.Label(
            self, text="Productos Seleccionados", font=("Segoe UI", 14, "bold"))
        prod_sel_label.pack(anchor=tk.W, pady=(10, 0))

        # Frame para la tabla
        table_frame = ttk.Frame(self, style="Card.TFrame", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Configurar el estilo antes de crear la tabla
        style = ttk.Style()

        # Estilo para la tabla
        style.configure(
            "Custom.Treeview",
            background="white",
            foreground="black",
            rowheight=35,
            fieldbackground="white",
            borderwidth=1,
            font=('Segoe UI', 11)
        )

        # Estilo para los encabezados
        style.configure(
            "Custom.Treeview.Heading",
            background="#2c3e50",
            foreground="white",
            relief="flat",
            borderwidth=1,
            font=('Segoe UI', 12, 'bold')
        )

        # Estilo para la selección
        style.map(
            "Custom.Treeview",
            background=[("selected", "#3498db")],
            foreground=[("selected", "white")]
        )

        # Tabla de productos
        columns = ("barcode", "name", "qty", "price", "subtotal")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=6,
            style="Custom.Treeview"
        )

        # Definir los encabezados
        self.tree.heading("barcode", text="Código de barras", anchor="center")
        self.tree.heading("name", text="Nombre", anchor="center")
        self.tree.heading("qty", text="Cantidad", anchor="center")
        self.tree.heading("price", text="Precio", anchor="center")
        self.tree.heading("subtotal", text="Subtotal", anchor="center")

        # Configurar el ancho y alineación de las columnas
        self.tree.column("barcode", width=180, anchor="center", minwidth=180)
        self.tree.column("name", width=250, anchor="center", minwidth=250)
        self.tree.column("qty", width=120, anchor="center", minwidth=120)
        self.tree.column("price", width=120, anchor="center", minwidth=120)
        self.tree.column("subtotal", width=120, anchor="center", minwidth=120)

        # Agregar scrollbar
        scrollbar = ttk.Scrollbar(
            table_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Empaquetar la tabla y el scrollbar
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

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

    def get_item_data(self) -> dict:
        """Obtiene los datos del formulario.

        Returns:
            dict: Diccionario con los datos del formulario.
        """
        return {
            'barcode': self.barcode_entry.get().strip(),
            'qty': self.qty_entry.get().strip()
        }

    def clear_fields(self) -> None:
        """Limpia los campos del formulario."""
        self.barcode_entry.delete(0, 'end')
        self.qty_entry.delete(0, 'end')
        self.barcode_entry.focus()

    def set_action_buttons_state(self, state: str) -> None:
        """Configura el estado de los botones de acción.

        Args:
            state: El estado de los botones ("normal" o "disabled").
        """
        self.edit_button.configure(state=state)
        self.delete_button.configure(state=state)
