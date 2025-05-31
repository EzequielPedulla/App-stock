from ..models.database import Database
from ..models.product import Product
from tkinter import messagebox


class SaleController:
    def __init__(self, sale_form, product_list=None):
        self.sale_form = sale_form
        self.product_list = product_list  # Referencia a la lista de productos
        self.db = Database()
        self.items = []  # Lista de productos seleccionados (dicts)
        self.temp_stock = {}  # Diccionario para mantener el stock temporal
        self._connect_events()

    def _connect_events(self):
        self.sale_form.add_button.configure(command=self.add_item)
        self.sale_form.bind("<<AddItem>>", lambda e: self.add_item())
        # Conectar eventos de los botones
        self.sale_form.edit_button.configure(command=self.edit_item)
        self.sale_form.delete_button.configure(command=self.delete_item)
        # Conectar evento de selección en la tabla
        self.sale_form.tree.bind('<<TreeviewSelect>>', self._on_select_item)

    def _on_select_item(self, event) -> None:
        """Maneja el evento cuando se selecciona un item en la tabla.

        Args:
            event: El evento de selección.
        """
        selected_items = self.sale_form.tree.selection()
        # Habilitar/deshabilitar botones según haya selección
        state = "normal" if selected_items else "disabled"
        self.sale_form.edit_button.configure(state=state)
        self.sale_form.delete_button.configure(state=state)

    def _update_product_list(self):
        """Actualiza la lista de productos si está disponible."""
        if self.product_list:
            self.product_list.refresh()

    def _get_available_stock(self, barcode: str) -> int:
        """Obtiene el stock disponible considerando el stock temporal.

        Args:
            barcode: El código de barras del producto.

        Returns:
            El stock disponible real.
        """
        product = self.db.get_product_by_barcode(barcode)
        if not product:
            return 0

        # Obtener el stock temporal reservado
        temp_reserved = self.temp_stock.get(barcode, 0)
        return product.stock - temp_reserved

    def edit_item(self) -> None:
        """Edita la cantidad del item seleccionado."""
        selected_items = self.sale_form.tree.selection()
        if not selected_items:
            return

        # Obtener el item seleccionado
        item = selected_items[0]
        values = self.sale_form.tree.item(item)['values']
        current_qty = int(values[2])  # La cantidad está en la tercera columna
        # El código de barras está en la primera columna
        barcode = str(values[0])

        # Cargar datos en el formulario
        self.sale_form.clear_fields()
        self.sale_form.barcode_entry.insert(0, barcode)
        self.sale_form.qty_entry.insert(0, str(current_qty))
        self.sale_form.barcode_entry.configure(state="disabled")
        self.sale_form.qty_entry.focus()

        # Función para guardar la edición
        def save_edit_on_enter(event=None):
            self._save_edit(barcode, current_qty)
            # Desvincular el evento Enter después de guardar
            self.sale_form.qty_entry.unbind('<Return>')

        # Vincular el evento Enter al campo de cantidad
        self.sale_form.qty_entry.bind('<Return>', save_edit_on_enter)

        # Cambiar el botón de agregar por guardar
        self.sale_form.add_button.configure(
            text="Guardar",
            command=save_edit_on_enter
        )

        # Deshabilitar botones de edición y eliminación
        self.sale_form.set_action_buttons_state("disabled")

    def _save_edit(self, old_barcode: str, old_qty: int) -> None:
        """Guarda los cambios de la edición.

        Args:
            old_barcode: El código de barras original.
            old_qty: La cantidad original.
        """
        try:
            # Obtener datos del formulario
            data = self.sale_form.get_item_data()
            new_qty = int(data['qty'])
            barcode = str(data['barcode'])

            if new_qty <= 0:
                messagebox.showerror("Error", "La cantidad debe ser mayor a 0")
                return

            # Obtener el producto de la base de datos
            product = self.db.get_product_by_barcode(barcode)
            if not product:
                messagebox.showerror("Error", "Producto no encontrado")
                return

            # Liberar el stock temporal actual
            if barcode in self.temp_stock:
                self.temp_stock[barcode] -= old_qty
                if self.temp_stock[barcode] <= 0:
                    del self.temp_stock[barcode]

            # Verificar si hay suficiente stock disponible para la nueva cantidad
            available_stock = product.stock

            if available_stock >= new_qty:
                try:
                    # Actualizar el stock temporal con la nueva cantidad
                    self.temp_stock[barcode] = self.temp_stock.get(
                        barcode, 0) + new_qty

                    # Actualizar la cantidad en la lista de items
                    item_updated = False

                    for item in self.items:
                        if str(item['barcode']) == barcode:
                            # Actualizar cantidad y subtotal
                            item['qty'] = new_qty
                            item['subtotal'] = new_qty * float(item['price'])
                            item_updated = True
                            break

                    if not item_updated:
                        return

                    # Actualizar la tabla y el total
                    self._update_table()

                    # Restaurar el formulario
                    self.sale_form.clear_fields()
                    self.sale_form.barcode_entry.configure(state="normal")
                    self.sale_form.add_button.configure(
                        text="Agregar",
                        command=self.add_item
                    )

                    # Deshabilitar botones de acción
                    self.sale_form.set_action_buttons_state("disabled")

                    # Limpiar la selección de la tabla
                    for item in self.sale_form.tree.selection():
                        self.sale_form.tree.selection_remove(item)

                except Exception as e:
                    messagebox.showerror(
                        "Error", f"Error al actualizar la cantidad: {str(e)}")
            else:
                messagebox.showerror(
                    "Error",
                    f"No hay suficiente stock disponible\nStock disponible: {available_stock}"
                )
        except ValueError:
            messagebox.showerror("Error", "Ingrese una cantidad válida")

    def delete_item(self) -> None:
        """Elimina el item seleccionado de la venta."""
        selected_items = self.sale_form.tree.selection()
        if not selected_items:
            return

        # Obtener el item seleccionado
        item = selected_items[0]
        values = self.sale_form.tree.item(item)['values']
        barcode = values[0]  # El código de barras está en la primera columna
        qty = int(values[2])  # La cantidad está en la tercera columna

        # Confirmar eliminación
        if messagebox.askyesno("Confirmar", "¿Desea eliminar este producto de la venta?"):
            # Liberar el stock temporal
            if barcode in self.temp_stock:
                self.temp_stock[barcode] -= qty
                if self.temp_stock[barcode] <= 0:
                    del self.temp_stock[barcode]

            # Eliminar el item de la lista
            self.items = [
                item for item in self.items if item['barcode'] != barcode]
            # Actualizar la tabla y el total
            self._update_table()
            # Deshabilitar botones
            self.sale_form.edit_button.configure(state="disabled")
            self.sale_form.delete_button.configure(state="disabled")

    def add_item(self):
        # Obtener y limpiar los valores
        barcode = self.sale_form.barcode_entry.get().strip()
        qty_str = self.sale_form.qty_entry.get().strip()

        if not barcode:
            messagebox.showerror("Error", "Ingrese un código de barras válido")
            return

        # Si no hay cantidad, usar 1 por defecto
        if not qty_str:
            qty = 1
        else:
            try:
                qty = int(qty_str)
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Ingrese una cantidad válida")
                return

        # Buscar producto
        product = self.db.get_product_by_barcode(barcode)
        if not product:
            messagebox.showerror("Error", "Producto no encontrado")
            self.sale_form.barcode_entry.delete(0, 'end')
            self.sale_form.barcode_entry.focus()
            return

        # Verificar stock disponible
        available_stock = self._get_available_stock(barcode)
        if available_stock < qty:
            messagebox.showerror(
                "Error",
                f"No hay suficiente stock disponible\nStock disponible: {available_stock}"
            )
            return

        # Ver si ya está en la lista
        for item in self.items:
            if item['barcode'] == barcode:
                # Verificar si hay suficiente stock para la cantidad adicional
                if available_stock < qty:
                    messagebox.showerror(
                        "Error",
                        f"No hay suficiente stock disponible\nStock disponible: {available_stock}"
                    )
                    return
                # Actualizar stock temporal
                self.temp_stock[barcode] = self.temp_stock.get(
                    barcode, 0) + qty
                # Actualizar cantidad y subtotal
                item['qty'] = int(item['qty']) + qty
                item['subtotal'] = item['qty'] * float(item['price'])
                self._update_table()
                self._clear_form()
                return

        # Si no está, agregarlo
        # Actualizar stock temporal
        self.temp_stock[barcode] = self.temp_stock.get(barcode, 0) + qty
        # Agregar nuevo item
        new_item = {
            'barcode': product.barcode,
            'name': product.name,
            'qty': qty,
            'price': float(product.price),
            'subtotal': qty * float(product.price)
        }
        self.items.append(new_item)
        self._update_table()
        self._clear_form()

    def _update_table(self):
        """Actualiza la tabla con los items actuales."""
        # Limpiar la tabla
        for item in self.sale_form.tree.get_children():
            self.sale_form.tree.delete(item)

        # Insertar los items actualizados
        for i, item in enumerate(self.items):
            # Asegurarse de que los valores sean del tipo correcto
            qty = int(item['qty'])
            price = float(item['price'])
            subtotal = qty * price

            # Actualizar el subtotal en el item
            item['subtotal'] = subtotal

            values = (
                item['barcode'],
                item['name'],
                str(qty),
                f"${price:.2f}",
                f"${subtotal:.2f}"
            )
            # Insertar con tags para alternar colores
            self.sale_form.tree.insert('', 'end', values=values, tags=(
                'evenrow' if i % 2 == 0 else 'oddrow',))

        # Configurar colores alternados
        self.sale_form.tree.tag_configure('evenrow', background='#ecf0f1')
        self.sale_form.tree.tag_configure('oddrow', background='white')

        # Actualizar el total
        total = sum(float(item['subtotal']) for item in self.items)
        self.sale_form.total_label.config(text=f"Total: ${total:.2f}")

        # Actualizar el estado de los botones
        self.sale_form.set_action_buttons_state("disabled")

        # Forzar la actualización de la interfaz
        self.sale_form.update_idletasks()

    def _clear_form(self):
        # Limpiar campos
        self.sale_form.barcode_entry.delete(0, 'end')
        self.sale_form.qty_entry.delete(0, 'end')
        # Enfocar el campo de código de barras
        self.sale_form.barcode_entry.focus()

    def confirm_sale(self):
        """Confirma la venta y actualiza el stock en la base de datos."""
        if not self.items:
            messagebox.showerror("Error", "No hay productos en la venta")
            return False

        try:
            # Actualizar el stock en la base de datos
            for barcode, qty in self.temp_stock.items():
                product = self.db.get_product_by_barcode(barcode)
                if product:
                    product.stock -= qty
                    self.db.update_product(product)

            # Limpiar la venta
            self.items = []
            self.temp_stock = {}
            self._update_table()
            self._clear_form()

            # Actualizar la lista de productos
            self._update_product_list()

            messagebox.showinfo("Éxito", "Venta realizada correctamente")
            return True
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error al confirmar la venta: {str(e)}")
            return False
