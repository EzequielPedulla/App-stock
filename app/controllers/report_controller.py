from ..models.database import Database
from tkinter import messagebox


class ReportController:
    def __init__(self, report_form):
        self.report_form = report_form
        self.db = Database()
        self.refresh()
        self._connect_events()

    def _connect_events(self):
        """Conecta los eventos de la vista"""
        self.report_form.tabla_ventas.bind(
            '<Double-1>', self._on_sale_double_click)

    def refresh(self):
        """Actualiza todos los datos de los reportes"""
        total = self._get_total_ventas()
        ultima = self._get_ultima_venta()
        ultimas = self._get_ultimas_ventas()

        self.report_form.update_data(
            total_ventas=total,
            ultima_venta=ultima,
            ultimas_ventas=ultimas
        )
        self.report_form.update_idletasks()

    def _get_total_ventas(self):
        """Suma todas las ventas de la base de datos"""
        query = "SELECT COALESCE(SUM(total), 0) as total FROM sales"
        result = self.db.execute_query(query)
        return float(result[0]['total']) if result else 0.0

    def _get_ultima_venta(self):
        """Obtiene el monto de la última venta"""
        query = "SELECT total FROM sales ORDER BY date DESC LIMIT 1"
        result = self.db.execute_query(query)
        return float(result[0]['total']) if result else 0.0

    def _get_ultimas_ventas(self):
        """Obtiene todas las ventas ordenadas por fecha descendente"""
        query = """
            SELECT id, date, total, paid, `change`
            FROM sales
            ORDER BY date DESC
        """
        result = self.db.execute_query(query)
        return result if result else []

    def _get_sale_details(self, sale_id):
        """Obtiene los detalles de una venta específica"""
        query = """
            SELECT p.name as producto, sd.quantity as cantidad,
                   sd.unit_price as precio, (sd.quantity * sd.unit_price) as subtotal
            FROM sale_details sd
            JOIN products p ON sd.product_id = p.id
            WHERE sd.sale_id = %s
            ORDER BY sd.id
        """
        result = self.db.execute_query(query, (sale_id,))
        return result if result else []

    def _on_sale_double_click(self, event):
        """Maneja el doble clic en una venta para mostrar su detalle"""
        selected = self.report_form.tabla_ventas.selection()
        if not selected:
            return

        # Obtener el ID de la venta seleccionada
        item = self.report_form.tabla_ventas.item(selected[0])
        sale_id = item['values'][0]  # El ID está en la primera columna
        sale_date = item['values'][1]
        sale_total_str = item['values'][2]  # Viene como "$X.XX"

        # Extraer el valor numérico del total (quitar el $ y convertir)
        sale_total = float(sale_total_str.replace('$', '').replace(',', ''))

        # Obtener los detalles de la venta
        details = self._get_sale_details(sale_id)

        if details:
            self.report_form.show_sale_detail(
                sale_id, sale_date, sale_total, details)
        else:
            messagebox.showinfo(
                "Sin detalles", "No se encontraron detalles para esta venta.")
