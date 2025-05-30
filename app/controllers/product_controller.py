from ..models.product import Product
from ..models.database import Database
from tkinter import messagebox


class ProductController:
    def __init__(self, product_form, product_list):
        self.product_form = product_form
        self.product_list = product_list
        self.db = Database()
        self.selected_product = None

        # Configurar eventos
        self.product_form.save_button.configure(command=self.save_product)
        self.product_form.edit_button.configure(command=self.start_edit)
        self.product_form.delete_button.configure(command=self.delete_product)
        self.product_list.tabla.bind(
            '<<TreeviewSelect>>', self.on_select_product)

        # Cargar productos
        self.load_products()
        self.product_form.set_action_buttons_state(
            False)  # Deshabilitar al inicio

    def save_product(self):
        try:
            data = self.product_form.get_product_data()

            # Validar datos
            if not all([data['barcode'], data['name'], data['price'], data['stock']]):
                messagebox.showerror(
                    "Error", "Todos los campos son obligatorios")
                return

            # Verificar si el código de barras ya existe (solo si es diferente al actual)
            if self.selected_product and self.product_form.editing_mode:
                if data['barcode'] != self.selected_product.barcode:
                    existing_product = self.db.get_product_by_barcode(
                        data['barcode'])
                    if existing_product:
                        messagebox.showerror(
                            "Error", "Ya existe un producto con ese código de barras")
                        return

            # Crear producto
            product = Product(
                barcode=data['barcode'],
                name=data['name'],
                price=float(data['price']),
                stock=int(data['stock']),
                id=self.selected_product.id if self.selected_product and self.product_form.editing_mode else None
            )

            # Guardar o actualizar
            if self.selected_product and self.product_form.editing_mode:
                self.db.update_product(product)
                messagebox.showinfo(
                    "Éxito", "Producto actualizado correctamente")
            else:
                self.db.add_product(product)
                messagebox.showinfo("Éxito", "Producto agregado correctamente")

            # Limpiar y recargar
            self.product_form.clear_fields()
            self.selected_product = None
            self.load_products()
            self.product_form.set_action_buttons_state(False)

        except ValueError as e:
            if "could not convert string to float" in str(e):
                messagebox.showerror(
                    "Error", "El precio debe ser un número válido")
            elif "could not convert string to int" in str(e):
                messagebox.showerror(
                    "Error", "El stock debe ser un número entero válido")
            else:
                messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_products(self):
        products = self.db.get_all_products()
        self.product_list.load_products(products)
        self.product_form.set_action_buttons_state(
            False)  # Deshabilitar después de recargar

    def on_select_product(self, event):
        selected_items = self.product_list.tabla.selection()
        if not selected_items:
            self.selected_product = None
            self.product_form.set_action_buttons_state(False)
            return

        # Obtener el item seleccionado
        item = self.product_list.tabla.item(selected_items[0])
        values = item['values']

        # Buscar el producto en la base de datos por código de barras
        barcode = values[0]  # El código de barras está en la primera columna
        self.selected_product = self.db.get_product_by_barcode(barcode)

        # Habilitar los botones si hay un producto seleccionado
        if self.selected_product:
            self.product_form.set_action_buttons_state(True)
            # Para debug
            print(f"Producto seleccionado: {self.selected_product.name}")
        else:
            self.product_form.set_action_buttons_state(False)
            # Para debug
            print(f"No se encontró el producto con código: {barcode}")

    def start_edit(self):
        if not self.selected_product:
            messagebox.showerror(
                "Error", "Por favor seleccione un producto para editar")
            return

        try:
            # Cargar datos en el formulario
            self.product_form.clear_fields()  # Limpiar campos primero

            # Insertar los datos del producto seleccionado
            self.product_form.barcode_entry.insert(
                0, self.selected_product.barcode)
            self.product_form.name_entry.insert(0, self.selected_product.name)
            self.product_form.price_entry.insert(
                0, f"{self.selected_product.price:.2f}")
            self.product_form.stock_entry.insert(
                0, str(self.selected_product.stock))

            # Cambiar a modo edición
            self.product_form.set_editing_mode(True)
            # Ya no deshabilitamos el código de barras
            # Para debug
            print(
                f"Iniciando edición del producto: {self.selected_product.name}")
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error al iniciar la edición: {str(e)}")
            self.product_form.clear_fields()
            self.product_form.set_editing_mode(False)

    def delete_product(self):
        if not self.selected_product:
            messagebox.showerror("Error", "Por favor seleccione un producto")
            return

        try:
            if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar el producto {self.selected_product.name}?"):
                self.db.delete_product(self.selected_product.id)
                self.selected_product = None
                self.product_form.clear_fields()
                self.load_products()
                self.product_form.set_action_buttons_state(False)
                messagebox.showinfo(
                    "Éxito", "Producto eliminado correctamente")
                print("Producto eliminado exitosamente")  # Para debug
        except Exception as e:
            messagebox.showerror(
                "Error", f"Error al eliminar el producto: {str(e)}")
            print(f"Error al eliminar: {str(e)}")  # Para debug

    def cancel_edit(self):
        self.product_form.clear_fields()
        self.product_form.set_action_buttons_state(False)
