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
        barcode = values[0]  # El código de barras está en la primera columna

        # Mostrar diálogo para editar cantidad
        new_qty = self._show_qty_dialog(current_qty)
        if new_qty is not None and new_qty != current_qty:
            # Obtener el producto de la base de datos
            product = self.db.get_product_by_barcode(barcode)
            if product:
                # Calcular la diferencia de cantidad
                qty_diff = new_qty - current_qty
                # Verificar si hay suficiente stock disponible
                available_stock = self._get_available_stock(barcode)
                if available_stock >= qty_diff:
                    try:
                        # Actualizar el stock temporal
                        self.temp_stock[barcode] = self.temp_stock.get(
                            barcode, 0) + qty_diff

                        # Actualizar la cantidad en la lista de items
                        for item in self.items:
                            if item['barcode'] == barcode:
                                # Actualizar cantidad y subtotal
                                item['qty'] = new_qty
                                item['subtotal'] = new_qty * \
                                    float(item['price'])
                                break

                        # Actualizar la tabla
                        self._update_table()
                    except Exception as e:
                        messagebox.showerror(
                            "Error", f"Error al actualizar la cantidad: {str(e)}")
                else:
                    messagebox.showerror(
                        "Error",
                        f"No hay suficiente stock disponible\nStock disponible: {available_stock}"
                    )

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

    def _show_qty_dialog(self, current_qty: int) -> int | None:
        """Muestra un diálogo para editar la cantidad.

        Args:
            current_qty: La cantidad actual del producto.

        Returns:
            La nueva cantidad si se ingresó una válida, None en caso contrario.
        """
        from tkinter import simpledialog
        try:
            new_qty = simpledialog.askinteger(
                "Editar Cantidad",
                "Ingrese la nueva cantidad:",
                initialvalue=current_qty,
                minvalue=1
            )
            if new_qty is not None and new_qty > 0:
                return new_qty
            return None
        except:
            return None

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
        for item in self.items:
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
            self.sale_form.tree.insert('', 'end', values=values)

        # Actualizar el total
        self._update_total()

    def _update_total(self):
        """Actualiza el total de la venta."""
        total = 0
        for item in self.items:
            total += float(item['subtotal'])
        self.sale_form.total_label.config(text=f"Total: ${total:.2f}")

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
