"""Controlador para el módulo de ventas."""

from typing import Any
from tkinter import messagebox
import datetime

from ..models.database import Database
from ..models.product import Product


class SaleController:
    """Controlador para gestionar ventas."""

    def __init__(
        self,
        sale_form: Any,
        product_list: Any = None,
        report_controller: Any = None
    ) -> None:
        """
        Inicializa el controlador de ventas.

        Args:
            sale_form: Formulario de ventas (vista)
            product_list: Lista de productos (vista)
            report_controller: Controlador de reportes
        """
        self.sale_form = sale_form
        self.product_list = product_list
        self.report_controller = report_controller
        self.db = Database()
        self.items = []
        self.temp_stock = {}
        self._varios_counter = 0
        self._editing_barcode = None
        # Hasta 3 ventas en curso a la vez (ej. dos clientes en el
        # mostrador): cada una guarda su propio carrito por separado.
        self.active_slot = 0
        self.slots = [{'items': [], 'temp_stock': {}} for _ in range(3)]
        self._connect_events()
        self._refresh_slot_buttons()

    def _connect_events(self):
        self.sale_form.add_button.configure(command=self.add_item)
        self.sale_form.bind("<<AddItem>>", lambda e: self.add_item())
        # Conectar eventos de los botones
        self.sale_form.edit_button.configure(command=self.edit_item)
        self.sale_form.delete_button.configure(command=self.delete_item)
        # Conectar evento de selección en la tabla
        self.sale_form.tree.bind('<<TreeviewSelect>>', self._on_select_item)
        # Conectar doble clic para seleccionar
        self.sale_form.tree.bind('<Double-1>', self._on_double_click)
        # Tecla Suprimir para eliminar el item seleccionado del carrito
        self.sale_form.tree.bind('<Delete>', lambda e: self.delete_item())
        # Conectar evento de confirmación de venta
        self.sale_form.bind("<<ConfirmSale>>", lambda e: self.confirm_sale())
        # F5 vacía la venta en curso (carrito), con confirmación si tiene algo
        self.sale_form.bind("<<ClearSale>>", lambda e: self.limpiar_venta())
        # Conectar evento de artículo varios
        self.sale_form.bind("<<AddVarios>>", lambda e: self.add_varios())
        # Conectar evento de guardado del diálogo de edición (cantidad/precio)
        self.sale_form.bind(
            "<<SaveEditItem>>", lambda e: self._on_save_edit_item())
        # Conectar botón y evento de búsqueda de productos
        self.sale_form.search_button.configure(command=self.show_search_dialog)
        self.sale_form.bind(
            "<<AddFromSearch>>", lambda e: self._on_add_from_search())
        # Conectar evento de registro rápido de producto no encontrado
        self.sale_form.bind(
            "<<RegisterProduct>>", lambda e: self.register_product())
        # Conectar pestañas y atajos (Ctrl+1/2/3) para cambiar de venta
        for i, btn in enumerate(self.sale_form.slot_buttons):
            btn.configure(command=lambda idx=i: self.switch_slot(idx))
        for i in range(3):
            self.sale_form.bind(
                f"<<SwitchSlot{i}>>", lambda e, idx=i: self.switch_slot(idx))

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

    def _on_double_click(self, event) -> None:
        """Maneja el evento de doble clic en la tabla.

        Args:
            event: El evento de doble clic.
        """
        # Asegurar que el item esté seleccionado
        item = self.sale_form.tree.identify('item', event.x, event.y)
        if item:
            self.sale_form.tree.selection_set(item)
            # Habilitar botones
            self.sale_form.edit_button.configure(state="normal")
            self.sale_form.delete_button.configure(state="normal")

    def _update_product_list(self):
        """Actualiza la lista de productos si está disponible."""
        if self.product_list:
            self.product_list.refresh()

    def edit_item(self) -> None:
        """Abre el diálogo para editar la cantidad y el precio del item
        seleccionado."""
        selected_items = self.sale_form.tree.selection()
        if not selected_items:
            return

        # Obtener el item seleccionado
        item = selected_items[0]
        values = self.sale_form.tree.item(item)['values']
        # El código de barras está en la primera columna
        barcode = str(values[0])

        # Los artículos "Varios" no tienen un producto real detrás, así que
        # no hay datos que recargar para editarlos.
        cart_item = next(
            (i for i in self.items if str(i['barcode']) == barcode), None)
        if not cart_item:
            return

        if cart_item.get('is_varios', False):
            messagebox.showinfo(
                "No editable",
                "Los artículos 'Varios' no se pueden editar.\n"
                "Eliminelo y agréguelo de nuevo con los datos correctos."
            )
            return

        self._editing_barcode = barcode
        self.sale_form.show_edit_item_dialog(
            barcode, cart_item['name'],
            int(cart_item['qty']), float(cart_item['price']))

    def _on_save_edit_item(self) -> None:
        """Aplica la cantidad/precio editados al item del carrito. Si el
        precio cambió, pregunta si también hay que actualizarlo en el
        inventario (Productos)."""
        if not hasattr(self.sale_form, 'edit_item_data'):
            return

        data = self.sale_form.edit_item_data
        delattr(self.sale_form, 'edit_item_data')

        barcode = self._editing_barcode
        cart_item = next(
            (i for i in self.items if str(i['barcode']) == barcode), None)
        if not cart_item:
            return

        old_qty = int(cart_item['qty'])
        old_price = float(cart_item['price'])
        new_qty = data['qty']
        new_price = data['price']

        # Liberar el stock temporal reservado con la cantidad anterior y
        # reservarlo de nuevo con la cantidad nueva.
        if barcode in self.temp_stock:
            self.temp_stock[barcode] -= old_qty
            if self.temp_stock[barcode] <= 0:
                del self.temp_stock[barcode]
        self.temp_stock[barcode] = self.temp_stock.get(barcode, 0) + new_qty

        cart_item['qty'] = new_qty
        cart_item['price'] = new_price
        cart_item['subtotal'] = new_qty * new_price

        self._update_table()

        # Limpiar la selección de la tabla
        for item in self.sale_form.tree.selection():
            self.sale_form.tree.selection_remove(item)

        # Si el precio cambió, ofrecer actualizarlo también en el inventario
        if new_price != old_price:
            if messagebox.askyesno(
                "Actualizar precio",
                f"El precio de '{cart_item['name']}' se cambió a "
                f"${new_price:.2f}.\n\n"
                "¿Desea actualizar también el precio en el inventario "
                "(Productos)?"
            ):
                product = self.db.get_product_by_barcode(barcode)
                if product:
                    product.price = new_price
                    self.db.update_product(product)
                    self._update_product_list()

    def delete_item(self) -> None:
        """Elimina el item seleccionado de la venta."""
        selected_items = self.sale_form.tree.selection()
        if not selected_items:
            messagebox.showwarning(
                "Advertencia", "Por favor selecciona un producto para eliminar.")
            return

        item = selected_items[0]
        values = self.sale_form.tree.item(item)['values']
        barcode = values[0]
        qty = int(values[2])

        if messagebox.askyesno("Confirmar", "¿Desea eliminar este producto de la venta?"):
            if barcode in self.temp_stock:
                self.temp_stock[barcode] -= qty
                if self.temp_stock[barcode] <= 0:
                    del self.temp_stock[barcode]

            self.items = [
                item for item in self.items if str(item['barcode']) != str(barcode)]

            self._update_table()

            if not self.items:
                self.sale_form.edit_button.configure(state="disabled")
                self.sale_form.delete_button.configure(state="disabled")

    def limpiar_venta(self) -> None:
        """Vacía por completo la venta en curso (F5): saca todos los
        productos del carrito, sin tocar stock real (el temporal reservado
        para esta venta simplemente se libera)."""
        if not self.items:
            return
        if not messagebox.askyesno(
                "Confirmar",
                "¿Vaciar la venta en curso? Se van a quitar todos los "
                "productos agregados."):
            return
        self.items = []
        self.temp_stock = {}
        self._update_table()
        self._clear_form()
        self.sale_form.edit_button.configure(state="disabled")
        self.sale_form.delete_button.configure(state="disabled")

    def add_varios(self) -> None:
        """Agrega un artículo 'varios' sin registro en inventario."""
        if not hasattr(self.sale_form, 'varios_data'):
            return

        data = self.sale_form.varios_data

        # Cada "varios" necesita un código propio dentro del carrito: si todos
        # comparten el literal "VARIOS", borrar o editar uno afecta a todos
        # los demás (se buscan/filtran por barcode).
        self._varios_counter += 1
        varios_cart_code = f"VARIOS-{self._varios_counter}"

        # Agregar a la lista de items
        new_item = {
            'barcode': varios_cart_code,
            'name': data['name'],  # Nombre real que puso el usuario
            'qty': data['qty'],
            'price': float(data['price']),
            'subtotal': data['qty'] * float(data['price']),
            'is_varios': True,  # Flag para identificarlo
            'varios_name': data['name']  # Guardar el nombre original
        }

        self.items.append(new_item)
        self._update_table()

        # Limpiar datos temporales
        delattr(self.sale_form, 'varios_data')

    def register_product(self) -> None:
        """Registra en el inventario un código escaneado que no existía, y
        lo agrega a la venta actual con la cantidad ya cargada en el
        formulario (sin pedir stock: no se controla en el uso real)."""
        if not hasattr(self.sale_form, 'register_data'):
            return

        data = self.sale_form.register_data
        delattr(self.sale_form, 'register_data')

        if self.db.get_product_by_barcode(data['barcode']):
            messagebox.showerror(
                "Error", "Ya existe un producto con ese código de barras")
            return

        new_product = Product(
            barcode=data['barcode'],
            name=data['name'],
            price=data['price'],
            stock=0
        )
        self.db.add_product(new_product)
        self._update_product_list()

        # El barcode y la cantidad siguen cargados en el formulario:
        # continuar el flujo normal para sumarlo a la venta.
        self.add_item()

    def show_search_dialog(self) -> None:
        """Abre el diálogo de búsqueda de productos por nombre/código para
        agregarlos a la venta sin necesidad del código de barras a mano."""
        products = self.db.get_all_products()
        self.sale_form.show_search_products_dialog(products)

    def _on_add_from_search(self) -> None:
        """Agrega a la venta el producto elegido en el diálogo de
        búsqueda, reutilizando la misma lógica que agregar por código de
        barras (suma cantidad si ya estaba en el carrito, etc.)."""
        if not hasattr(self.sale_form, 'search_add_data'):
            return

        data = self.sale_form.search_add_data
        delattr(self.sale_form, 'search_add_data')

        self.sale_form.barcode_entry.delete(0, 'end')
        self.sale_form.barcode_entry.insert(0, data['barcode'])
        self.sale_form.qty_entry.delete(0, 'end')
        self.sale_form.qty_entry.insert(0, str(data['qty']))
        self.add_item()

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
            if messagebox.askyesno(
                "Producto no encontrado",
                f"El código '{barcode}' no está registrado.\n\n"
                "¿Desea registrarlo ahora?"
            ):
                # No se limpia el formulario: barcode/cantidad quedan
                # cargados para agregarlo a la venta apenas se registre.
                self.sale_form.show_register_product_dialog(barcode)
            else:
                self.sale_form.barcode_entry.delete(0, 'end')
                self.sale_form.barcode_entry.focus()
            return

        # Ver si ya está en la lista
        for item in self.items:
            if item['barcode'] == barcode:
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

        # Actualizar el contador de productos (suma de cantidades, no de
        # líneas: 2 Coca-Colas + 3 panes son "5 productos")
        unit_count = sum(int(item['qty']) for item in self.items)
        label = "1 producto" if unit_count == 1 else f"{unit_count} productos"
        self.sale_form.count_label.config(text=label)

        # Actualizar el estado de los botones
        self.sale_form.set_action_buttons_state("disabled")

        # Actualizar las pestañas de venta (cantidad de items por venta)
        self._refresh_slot_buttons()

        # Forzar la actualización de la interfaz
        self.sale_form.update_idletasks()

    def _refresh_slot_buttons(self) -> None:
        """Actualiza el texto/resaltado de las pestañas Venta 1/2/3."""
        counts = []
        for i in range(len(self.slots)):
            if i == self.active_slot:
                counts.append(len(self.items))
            else:
                counts.append(len(self.slots[i]['items']))
        self.sale_form.set_slot_buttons(self.active_slot, counts)

    def switch_slot(self, index: int) -> None:
        """Cambia a otra de las ventas en curso, sin perder la actual."""
        if index == self.active_slot:
            return

        # Guardar el estado de la venta que se está dejando
        self.slots[self.active_slot]['items'] = self.items
        self.slots[self.active_slot]['temp_stock'] = self.temp_stock

        self.active_slot = index
        self.items = self.slots[index]['items']
        self.temp_stock = self.slots[index]['temp_stock']

        # Evitar que quede un filtro de búsqueda de la venta anterior
        self.sale_form._clear_search()
        self._clear_form()
        self._update_table()

    def _clear_form(self):
        # Limpiar campos
        self.sale_form.barcode_entry.delete(0, 'end')
        self.sale_form.qty_entry.delete(0, 'end')
        # Enfocar el campo de código de barras
        self.sale_form.barcode_entry.focus()

    def confirm_sale(self) -> bool:
        """Confirma la venta, registra la venta y sus detalles, y actualiza el stock en la base de datos.

        Returns:
            bool: True si la venta se realizó correctamente, False en caso contrario.
        """
        if not self.items:
            messagebox.showerror("Error", "No hay productos en la venta")
            return False

        try:
            # Obtener datos de pago
            paid = getattr(self.sale_form, 'paid', 0.0)
            change = getattr(self.sale_form, 'change', 0.0)
            payment_method = getattr(self.sale_form, 'payment_method', 'efectivo')
            # Solo presente si la venta se pagó dividida entre dos métodos
            payments = getattr(self.sale_form, 'payments', None)
            total = sum(float(item['subtotal']) for item in self.items)
            date = datetime.datetime.now().isoformat(sep=' ', timespec='seconds')

            # Registrar la venta y todos sus movimientos en una única transacción:
            # si algo falla a mitad de camino, se revierte todo (rollback) en vez
            # de dejar una venta a medio registrar.
            sale_id = self.db.add_sale(
                date=date, total=total, paid=paid, change=change,
                payment_method=payment_method, payments=payments, commit=False)

            # Registrar los detalles de la venta
            for item in self.items:
                # Si es un artículo "varios", crear producto temporal único
                if item.get('is_varios', False):
                    # Crear producto con el nombre real del artículo varios
                    import random

                    # Generar código corto único (máximo 13 caracteres)
                    # Formato: VAR-XXXXXX (10 caracteres total)
                    varios_barcode = f"VAR-{random.randint(100000, 999999)}"

                    # Asegurar que sea único
                    while self.db.get_product_by_barcode(varios_barcode):
                        varios_barcode = f"VAR-{random.randint(100000, 999999)}"

                    # Crear el producto temporal con el nombre real
                    varios_product = Product(
                        barcode=varios_barcode,
                        # Nombre real
                        name=item.get('varios_name', item['name']),
                        price=float(item['price']),
                        stock=0  # Sin stock porque no se controla
                    )
                    self.db.add_product(varios_product, commit=False)

                    # Obtener el producto recién creado (visible en la misma
                    # transacción aunque todavía no se hizo commit)
                    varios_product = self.db.get_product_by_barcode(
                        varios_barcode)

                    # Agregar detalle de venta
                    self.db.add_sale_detail(
                        sale_id=sale_id,
                        product_id=varios_product.id,
                        quantity=int(item['qty']),
                        unit_price=float(item['price']),
                        commit=False
                    )
                else:
                    # Producto normal
                    product = self.db.get_product_by_barcode(item['barcode'])
                    if product:
                        self.db.add_sale_detail(
                            sale_id=sale_id,
                            product_id=product.id,
                            quantity=int(item['qty']),
                            unit_price=float(item['price']),
                            commit=False
                        )

            # Actualizar el stock en la base de datos (solo productos normales)
            for barcode, qty in self.temp_stock.items():
                product = self.db.get_product_by_barcode(barcode)
                if product:
                    product.stock -= qty
                    self.db.update_product(product, commit=False)

            # Recién acá, con todo registrado sin errores, se confirma de una
            self.db.connection.commit()

            numero_dia = self.db.get_numero_venta_del_dia(sale_id, date[:10])
            self.sale_form.set_ultima_venta(
                f"✓ Venta N° {numero_dia} del día registrada — "
                f"Total ${total:.2f}")

            # Limpiar la venta
            self.items = []
            self.temp_stock = {}
            self._update_table()
            self._clear_form()

            # Actualizar la lista de productos
            self._update_product_list()

            # Actualizar reportes si existe el controller
            if self.report_controller:
                self.report_controller.refresh()

            # No se pregunta por el ticket automáticamente (todavía no hay
            # impresora). El ticket de una venta se puede seguir generando
            # a mano desde Reportes cuando haga falta.

            return True
        except Exception as e:
            self.db.connection.rollback()
            messagebox.showerror(
                "Error", f"Error al confirmar la venta: {str(e)}")
            return False
