import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox


class SaleForm(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self._payment_dialog = None  # Variable para controlar la ventana de pago
        self.paid = 0.0  # Monto pagado por el cliente
        self.change = 0.0  # Vuelto entregado al cliente
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

        # Frame para el total y botón de confirmar
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))

        # Frame para el total
        total_frame = ttk.Frame(bottom_frame)
        total_frame.pack(side=tk.RIGHT, padx=(0, 15))

        # Total general
        self.total_label = ttk.Label(
            total_frame,
            text="Total: $0.00",
            font=("Segoe UI", 18, "bold"),
            anchor=tk.E,
            width=15  # Asegura un ancho mínimo para el total
        )
        self.total_label.pack(side=tk.RIGHT)

        # Botón de confirmar venta
        self.confirm_button = ttk.Button(
            bottom_frame,
            text="Confirmar Venta",
            style="success.TButton",
            width=18,
            command=self._show_payment_dialog
        )
        self.confirm_button.pack(side=tk.RIGHT)

        # Vincular la tecla Enter a la ventana principal
        self.bind_all('<Return>', self._on_enter_pressed)

    def _show_payment_dialog(self) -> None:
        """Muestra el diálogo para ingresar el monto pagado y calcular el vuelto."""
        # Si ya existe una ventana de pago, no crear otra
        if self._payment_dialog is not None:
            return

        # Crear ventana modal
        self._payment_dialog = ttk.Toplevel(self)
        self._payment_dialog.title("Pago")
        self._payment_dialog.geometry("400x300")
        self._payment_dialog.resizable(False, False)
        self._payment_dialog.transient(self)  # Hacer la ventana modal
        self._payment_dialog.grab_set()  # Hacer la ventana modal

        # Centrar la ventana
        self._payment_dialog.update_idletasks()
        width = self._payment_dialog.winfo_width()
        height = self._payment_dialog.winfo_height()
        x = (self._payment_dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self._payment_dialog.winfo_screenheight() // 2) - (height // 2)
        self._payment_dialog.geometry(f'{width}x{height}+{x}+{y}')

        # Frame principal
        main_frame = ttk.Frame(self._payment_dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        # Título
        ttk.Label(
            main_frame,
            text="Pago",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(0, 20))

        # Obtener el total actual
        total_text = self.total_label.cget("text")
        total = float(total_text.replace("Total: $", ""))

        # Mostrar el total
        ttk.Label(
            main_frame,
            text=f"Total a pagar: ${total:.2f}",
            font=("Segoe UI", 12)
        ).pack(pady=(0, 10))

        # Frame para el monto pagado
        payment_frame = ttk.Frame(main_frame)
        payment_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(
            payment_frame,
            text="Monto pagado:",
            font=("Segoe UI", 11)
        ).pack(side=LEFT)

        payment_entry = ttk.Entry(payment_frame, font=("Segoe UI", 12))
        payment_entry.pack(side=LEFT, padx=(10, 0), fill=X, expand=True)
        payment_entry.focus()

        # Label para mostrar el vuelto
        change_label = ttk.Label(
            main_frame,
            text="Vuelto: $0.00",
            font=("Segoe UI", 14, "bold")
        )
        change_label.pack(pady=(10, 20))

        def calculate_change():
            try:
                paid = float(payment_entry.get() or 0)
                change = paid - total
                if change >= 0:
                    change_label.configure(text=f"Vuelto: ${change:.2f}")
                else:
                    change_label.configure(text="Monto insuficiente")
            except ValueError:
                change_label.configure(text="Monto inválido")

        # Vincular el cálculo al cambio en el entry
        payment_entry.bind('<KeyRelease>', lambda e: calculate_change())

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=(20, 0))

        def confirm_payment():
            try:
                paid = float(payment_entry.get() or 0)
                if paid < total:
                    messagebox.showerror(
                        "Error", "El monto pagado es insuficiente")
                    return
                self.paid = paid
                self.change = paid - total
                self._payment_dialog.destroy()
                self._payment_dialog = None
                self.event_generate("<<ConfirmSale>>")
            except ValueError:
                messagebox.showerror("Error", "Ingrese un monto válido")

        def on_closing():
            self._payment_dialog.destroy()
            self._payment_dialog = None

        ttk.Button(
            button_frame,
            text="Confirmar",
            style="success.TButton",
            command=confirm_payment
        ).pack(side=RIGHT, padx=(5, 0))

        ttk.Button(
            button_frame,
            text="Cancelar",
            style="secondary.TButton",
            command=on_closing
        ).pack(side=RIGHT)

        # Prevenir que se cierre la ventana con la X
        self._payment_dialog.protocol("WM_DELETE_WINDOW", on_closing)

    def _on_barcode_return(self, event) -> None:
        """Maneja el evento cuando se presiona Enter en el campo de código de barras.

        Args:
            event: El evento de tecla.
        """
        self.event_generate("<<AddItem>>")

    def _on_enter_pressed(self, event) -> None:
        """Maneja el evento cuando se presiona Enter en la ventana principal."""
        # Si el foco está en los campos de entrada, no hacer nada
        if event.widget in (self.barcode_entry, self.qty_entry):
            return

        # Verificar si hay productos en la tabla
        if self.tree.get_children():
            self._show_payment_dialog()

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
