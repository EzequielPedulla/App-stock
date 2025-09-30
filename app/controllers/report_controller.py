"""Controlador para el módulo de reportes."""

from typing import Any
from tkinter import messagebox
import tkinter.filedialog as filedialog
import os

from ..models.database import Database
from ..services.export_service import ExportService


class ReportController:
    """Controlador para gestionar reportes y exportaciones."""

    def __init__(self, report_form: Any, product_list: Any = None) -> None:
        """
        Inicializa el controlador de reportes.

        Args:
            report_form: Formulario de reportes (vista)
            product_list: Lista de productos para refrescar después de anular ventas
        """
        self.report_form = report_form
        self.product_list = product_list
        self.db = Database()
        self.export_service = ExportService()
        # Establecer la referencia del controlador en la vista
        self.report_form.report_controller = self
        self.refresh()
        self._connect_events()

    def _connect_events(self) -> None:
        """Conecta los eventos de la vista."""
        self.report_form.tabla_ventas.bind(
            '<Double-1>', self._on_sale_double_click)

    def refresh(self) -> None:
        """Actualiza todos los datos de los reportes."""
        total = self._get_total_ventas()
        ultima = self._get_ultima_venta()
        ultimas = self._get_ultimas_ventas()
        mas_vendidos = self._get_productos_mas_vendidos()

        self.report_form.update_data(
            total_ventas=total,
            ultima_venta=ultima,
            ultimas_ventas=ultimas,
            productos_vendidos=mas_vendidos
        )
        self.report_form.update_idletasks()

    def _get_total_ventas(self) -> float:
        """
        Suma todas las ventas activas de la base de datos (excluye anuladas).

        Returns:
            float: Total acumulado de ventas activas
        """
        query = "SELECT COALESCE(SUM(total), 0) as total FROM sales WHERE status = 'active'"
        result = self.db.execute_query(query)
        return float(result[0]['total']) if result else 0.0

    def _get_ultima_venta(self) -> float:
        """
        Obtiene el monto de la última venta activa.

        Returns:
            float: Monto de la última venta activa
        """
        query = "SELECT total FROM sales WHERE status = 'active' ORDER BY date DESC LIMIT 1"
        result = self.db.execute_query(query)
        return float(result[0]['total']) if result else 0.0

    def _get_ultimas_ventas(self) -> list[dict[str, Any]]:
        """
        Obtiene todas las ventas ordenadas por fecha descendente.

        Returns:
            list: Lista de ventas con sus datos
        """
        query = """
            SELECT id, date, total, paid, `change`, status
            FROM sales
            ORDER BY date DESC
        """
        result = self.db.execute_query(query)
        return result if result else []

    def _get_productos_mas_vendidos(self) -> list[dict[str, Any]]:
        """
        Obtiene los productos más vendidos con cantidad total vendida y monto total.

        Returns:
            list: Lista de productos con estadísticas de ventas
        """
        query = """
            SELECT p.name as producto, 
                   SUM(sd.quantity) as cantidad_vendida,
                   SUM(sd.quantity * sd.unit_price) as monto_total
            FROM sale_details sd
            JOIN products p ON sd.product_id = p.id
            GROUP BY p.id, p.name
            ORDER BY cantidad_vendida DESC
            LIMIT 10
        """
        result = self.db.execute_query(query)
        return result if result else []

    def _get_sale_details(self, sale_id: int) -> list[dict[str, Any]]:
        """
        Obtiene los detalles de una venta específica.

        Args:
            sale_id: ID de la venta

        Returns:
            list: Lista de detalles de productos de la venta
        """
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

    def _on_sale_double_click(self, event: Any) -> None:
        """
        Maneja el doble clic en una venta para mostrar su detalle.

        Args:
            event: Evento de doble clic
        """
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

    def export_sales_to_excel(self) -> None:
        """Exporta el historial de ventas a Excel."""
        try:
            ventas = self._get_ultimas_ventas()
            productos_vendidos = self._get_productos_mas_vendidos()

            if not ventas:
                messagebox.showwarning(
                    "Sin datos", "No hay ventas para exportar.")
                return

            filename = self.export_service.export_sales_to_excel(
                ventas, productos_vendidos)

            if messagebox.askyesno(
                "Exportación exitosa",
                f"Archivo generado:\n{filename}\n\n¿Desea abrirlo?"
            ):
                os.startfile(filename)

        except Exception as e:
            messagebox.showerror(
                "Error al exportar",
                f"No se pudo exportar a Excel:\n{str(e)}"
            )

    def export_inventory_to_excel(self) -> None:
        """Exporta el inventario de productos a Excel."""
        try:
            query = "SELECT * FROM products ORDER BY name"
            productos = self.db.execute_query(query)

            if not productos:
                messagebox.showwarning(
                    "Sin datos", "No hay productos para exportar.")
                return

            filename = self.export_service.export_inventory_to_excel(productos)

            if messagebox.askyesno(
                "Exportación exitosa",
                f"Archivo generado:\n{filename}\n\n¿Desea abrirlo?"
            ):
                os.startfile(filename)

        except Exception as e:
            messagebox.showerror(
                "Error al exportar",
                f"No se pudo exportar a Excel:\n{str(e)}"
            )

    def export_sales_report_to_pdf(self) -> None:
        """Exporta un reporte completo de ventas a PDF."""
        try:
            total_ventas = self._get_total_ventas()
            ultima_venta = self._get_ultima_venta()
            ventas = self._get_ultimas_ventas()
            productos_vendidos = self._get_productos_mas_vendidos()

            if not ventas:
                messagebox.showwarning(
                    "Sin datos", "No hay ventas para generar el reporte.")
                return

            filename = self.export_service.export_sales_report_to_pdf(
                total_ventas, ultima_venta, ventas, productos_vendidos
            )

            if messagebox.askyesno(
                "Reporte generado",
                f"Archivo generado:\n{filename}\n\n¿Desea abrirlo?"
            ):
                os.startfile(filename)

        except Exception as e:
            messagebox.showerror(
                "Error al generar reporte",
                f"No se pudo generar el PDF:\n{str(e)}"
            )

    def export_sale_ticket_to_pdf(
        self,
        sale_id: int,
        sale_date: str,
        sale_total: float,
        sale_paid: float,
        sale_change: float,
        details: list[dict[str, Any]]
    ) -> None:
        """
        Exporta un ticket individual de venta a PDF.

        Args:
            sale_id: ID de la venta
            sale_date: Fecha de la venta
            sale_total: Total de la venta
            sale_paid: Monto pagado
            sale_change: Cambio entregado
            details: Detalles de productos vendidos
        """
        try:
            filename = self.export_service.export_sale_ticket_to_pdf(
                sale_id, sale_date, sale_total, sale_paid, sale_change, details
            )

            if messagebox.askyesno(
                "Ticket generado",
                f"Archivo generado:\n{filename}\n\n¿Desea abrirlo?"
            ):
                os.startfile(filename)

        except Exception as e:
            messagebox.showerror(
                "Error al generar ticket",
                f"No se pudo generar el ticket:\n{str(e)}"
            )

    def cancel_sale(self, sale_id: int) -> None:
        """
        Anula una venta y reintegra el stock.

        Args:
            sale_id: ID de la venta a anular
        """
        # Verificar si la venta ya está anulada
        query = "SELECT status FROM sales WHERE id = %s"
        result = self.db.execute_query(query, (sale_id,))

        if not result:
            messagebox.showerror("Error", "Venta no encontrada")
            return

        if result[0]['status'] == 'cancelled':
            messagebox.showwarning(
                "Advertencia",
                "Esta venta ya está anulada"
            )
            return

        # Confirmar anulación
        if not messagebox.askyesno(
            "Confirmar Anulación",
            f"¿Está seguro de anular la venta N° {sale_id}?\n\n" +
            "Esta acción:\n" +
            "• Reintegrará el stock de los productos\n" +
            "• Marcará la venta como ANULADA\n" +
            "• No se podrá revertir\n\n" +
            "¿Continuar?"
        ):
            return

        # Pedir motivo
        from tkinter import simpledialog
        reason = simpledialog.askstring(
            "Motivo de Anulación",
            "Ingrese el motivo de la anulación:",
            parent=self.report_form
        )

        if not reason:
            reason = "Sin especificar"

        # Anular venta
        if self.db.cancel_sale(sale_id, reason):
            messagebox.showinfo(
                "Éxito",
                f"Venta N° {sale_id} anulada correctamente.\n" +
                "El stock ha sido reintegrado."
            )
            # Refrescar reportes
            self.refresh()
            # Refrescar lista de productos para mostrar stock actualizado
            if self.product_list:
                self.product_list.refresh()
        else:
            messagebox.showerror(
                "Error",
                "No se pudo anular la venta.\n" +
                "Verifique los logs para más detalles."
            )
