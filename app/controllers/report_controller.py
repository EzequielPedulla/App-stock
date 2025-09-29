from ..models.database import Database


class ReportController:
    def __init__(self, report_form):
        self.report_form = report_form
        self.db = Database()
        self._load_data()

    def _load_data(self):
        """Carga los datos iniciales de reportes"""
        total = self._get_total_ventas()
        ultima = self._get_ultima_venta()
        ultimas = self._get_ultimas_ventas()

        self.report_form.update_data(
            total_ventas=total,
            ultima_venta=ultima,
            ultimas_ventas=ultimas
        )

    def _get_total_ventas(self):
        """Suma todas las ventas de la base de datos"""
        try:
            query = "SELECT SUM(total) as total FROM sales"
            result = self.db.execute_query(query)
            if result and result[0]['total']:
                return float(result[0]['total'])
            return 0.0
        except:
            return 0.0

    def _get_ultima_venta(self):
        """Obtiene el monto de la última venta"""
        try:
            query = "SELECT total FROM sales ORDER BY date DESC LIMIT 1"
            result = self.db.execute_query(query)
            if result:
                return float(result[0]['total'])
            return 0.0
        except:
            return 0.0

    def _get_ultimas_ventas(self):
        """Obtiene las últimas 4 ventas con el producto principal"""
        try:
            query = """
                SELECT p.name as producto, sd.unit_price * sd.quantity as monto
                FROM sale_details sd
                JOIN products p ON sd.product_id = p.id
                JOIN sales s ON sd.sale_id = s.id
                ORDER BY s.date DESC
                LIMIT 4
            """
            result = self.db.execute_query(query)
            return result if result else []
        except:
            return []
