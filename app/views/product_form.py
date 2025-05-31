import ttkbootstrap as ttk


class ProductForm(ttk.LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, text="Agregar Producto", padding=20, **kwargs)
        self.pack(fill="x", pady=(0, 20))
        self._create_widgets()
        self.editing_mode = False

    def _create_widgets(self):
        # Configurar el grid
        self.columnconfigure(1, weight=1)

        # Campos del formulario
        ttk.Label(self, text="Código de barras",
                  font=("Segoe UI", 11)).grid(row=0, column=0, pady=10, sticky='w')
        self.barcode_entry = ttk.Entry(self)
        self.barcode_entry.grid(row=0, column=1, padx=(20, 0), sticky='ew')

        ttk.Label(self, text="Nombre",
                  font=("Segoe UI", 11)).grid(row=1, column=0, pady=10, sticky='w')
        self.name_entry = ttk.Entry(self)
        self.name_entry.grid(row=1, column=1, padx=(20, 0), sticky='ew')

        ttk.Label(self, text="Precio",
                  font=("Segoe UI", 11)).grid(row=2, column=0, pady=10, sticky='w')
        self.price_entry = ttk.Entry(self)
        self.price_entry.grid(row=2, column=1, padx=(20, 0), sticky='ew')

        ttk.Label(self, text="Stock",
                  font=("Segoe UI", 11)).grid(row=3, column=0, pady=10, sticky='w')
        self.stock_entry = ttk.Entry(self)
        self.stock_entry.grid(row=3, column=1, padx=(20, 0), sticky='ew')

        # Frame para los botones
        frame_botones = ttk.Frame(self)
        frame_botones.grid(row=4, column=1, pady=20, sticky='e')

        self.edit_button = ttk.Button(frame_botones, text="Editar",
                                      bootstyle="warning", width=15, state="enabled")
        self.edit_button.pack(side='left', padx=5)

        self.delete_button = ttk.Button(frame_botones, text="Eliminar",
                                        bootstyle="danger", width=15, state="enabled")
        self.delete_button.pack(side='left', padx=5)

        self.save_button = ttk.Button(frame_botones, text="Guardar",
                                      bootstyle="primary", width=15)
        self.save_button.pack(side='left')

        self.cancel_button = ttk.Button(frame_botones, text="Cancelar",
                                        bootstyle="secondary", width=15,
                                        command=self.cancel_edit)
        self.cancel_button.pack(side='left', padx=5)
        self.cancel_button.pack_forget()  # Inicialmente oculto

    def get_product_data(self):
        return {
            'barcode': self.barcode_entry.get(),
            'name': self.name_entry.get(),
            'price': self.price_entry.get(),
            'stock': self.stock_entry.get()
        }

    def clear_fields(self):
        self.barcode_entry.delete(0, 'end')
        self.name_entry.delete(0, 'end')
        self.price_entry.delete(0, 'end')
        self.stock_entry.delete(0, 'end')
        self.set_editing_mode(False)
        self.set_action_buttons_state(False)
        # Asegurar que esté habilitado al limpiar
        self.barcode_entry.configure(state='normal')

    def set_editing_mode(self, editing):
        self.editing_mode = editing
        if editing:
            self.configure(text="Editar Producto")
            self.save_button.configure(text="Guardar Cambios")
            self.cancel_button.pack(side='left', padx=5)
        else:
            self.configure(text="Agregar Producto")
            self.save_button.configure(text="Guardar")
            self.cancel_button.pack_forget()

    def set_action_buttons_state(self, state: str) -> None:
        """Configura el estado de los botones de acción.

        Args:
            state: El estado de los botones ("normal" o "disabled").
        """
        self.edit_button.configure(state=state)
        self.delete_button.configure(state=state)

    def cancel_edit(self):
        self.clear_fields()
        self.set_action_buttons_state(False)
