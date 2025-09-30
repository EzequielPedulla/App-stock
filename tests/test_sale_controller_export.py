"""Tests para la funcionalidad de exportación de tickets en SaleController."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch
import pytest
from app.controllers.sale_controller import SaleController

if TYPE_CHECKING:
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def mock_sale_form() -> MagicMock:
    """
    Fixture que proporciona un formulario de ventas simulado.

    Returns:
        MagicMock: Mock del formulario de ventas
    """
    form = MagicMock()
    form.barcode_entry = MagicMock()
    form.qty_entry = MagicMock()
    form.add_button = MagicMock()
    form.edit_button = MagicMock()
    form.delete_button = MagicMock()
    form.tree = MagicMock()
    form.total_label = MagicMock()
    return form


@pytest.fixture
def mock_database(mocker: "MockerFixture") -> MagicMock:
    """
    Fixture que proporciona una base de datos simulada.

    Args:
        mocker: Fixture de pytest-mock

    Returns:
        MagicMock: Mock de la base de datos
    """
    mock_db = MagicMock()
    mocker.patch(
        'app.controllers.sale_controller.Database',
        return_value=mock_db
    )
    return mock_db


@pytest.fixture
def sale_controller(
    mock_sale_form: MagicMock,
    mock_database: MagicMock
) -> SaleController:
    """
    Fixture que proporciona un controlador de ventas.

    Args:
        mock_sale_form: Mock del formulario de ventas
        mock_database: Mock de la base de datos

    Returns:
        SaleController: Instancia del controlador de ventas
    """
    controller = SaleController(mock_sale_form)
    controller.db = mock_database
    return controller


class TestSaleControllerExport:
    """Tests para la exportación de tickets en SaleController."""

    def test_generate_sale_ticket_success(
        self,
        sale_controller: SaleController,
        mocker: "MockerFixture"
    ) -> None:
        """
        Test de generación exitosa de ticket.

        Args:
            sale_controller: Fixture del controlador de ventas
            mocker: Fixture de pytest-mock
        """
        # Mock de los detalles de la venta
        mock_details = [
            {
                'producto': 'Producto 1',
                'cantidad': 2,
                'precio': 10.00,
                'subtotal': 20.00
            },
            {
                'producto': 'Producto 2',
                'cantidad': 1,
                'precio': 15.00,
                'subtotal': 15.00
            }
        ]

        # Configurar mock de base de datos
        sale_controller.db.execute_query = MagicMock(
            return_value=mock_details)

        # Mock del servicio de exportación
        mock_export = mocker.patch.object(
            sale_controller.export_service,
            'export_sale_ticket_to_pdf',
            return_value='test_reportes/ticket_venta_1_20240930_120000.pdf'
        )

        # Mock de messagebox (incluyendo el módulo importado en la función)
        mock_messagebox = mocker.patch(
            'app.controllers.sale_controller.messagebox')
        mock_mb = mocker.patch('tkinter.messagebox')
        mock_mb.askyesnocancel.return_value = None  # Usuario cancela

        # Ejecutar
        sale_controller._generate_sale_ticket(
            sale_id=1,
            sale_date='2024-09-30 12:00:00',
            sale_total=35.00,
            sale_paid=50.00,
            sale_change=15.00
        )

        # Verificar que se llamó al servicio de exportación
        mock_export.assert_called_once_with(
            sale_id=1,
            sale_date='2024-09-30 12:00:00',
            sale_total=35.00,
            sale_paid=50.00,
            sale_change=15.00,
            details=mock_details
        )

        # Verificar que se preguntó qué hacer con el ticket
        assert mock_mb.askyesnocancel.called

    def test_generate_sale_ticket_no_details(
        self,
        sale_controller: SaleController,
        mocker: "MockerFixture"
    ) -> None:
        """
        Test cuando no hay detalles de venta.

        Args:
            sale_controller: Fixture del controlador de ventas
            mocker: Fixture de pytest-mock
        """
        # Configurar mock para retornar lista vacía
        sale_controller.db.execute_query = MagicMock(return_value=[])

        # Mock de messagebox
        mock_messagebox = mocker.patch(
            'app.controllers.sale_controller.messagebox')

        # Ejecutar
        sale_controller._generate_sale_ticket(
            sale_id=999,
            sale_date='2024-09-30 12:00:00',
            sale_total=0.00,
            sale_paid=0.00,
            sale_change=0.00
        )

        # Verificar que se mostró advertencia
        mock_messagebox.showwarning.assert_called_once()

    def test_generate_sale_ticket_with_file_open(
        self,
        sale_controller: SaleController,
        mocker: "MockerFixture"
    ) -> None:
        """
        Test de generación de ticket con apertura de archivo.

        Args:
            sale_controller: Fixture del controlador de ventas
            mocker: Fixture de pytest-mock
        """
        # Mock de los detalles
        mock_details = [{'producto': 'Test', 'cantidad': 1,
                        'precio': 10.0, 'subtotal': 10.0}]
        sale_controller.db.execute_query = MagicMock(
            return_value=mock_details)

        # Mock del servicio de exportación
        test_filename = 'test_reportes/ticket_test.pdf'
        mocker.patch.object(
            sale_controller.export_service,
            'export_sale_ticket_to_pdf',
            return_value=test_filename
        )

        # Mock de messagebox (usuario dice NO = solo abrir PDF)
        mock_messagebox = mocker.patch(
            'app.controllers.sale_controller.messagebox')
        mock_mb = mocker.patch('tkinter.messagebox')
        mock_mb.askyesnocancel.return_value = False  # False = Abrir PDF

        # Mock de os.startfile
        mock_startfile = mocker.patch(
            'app.controllers.sale_controller.os.startfile')

        # Ejecutar
        sale_controller._generate_sale_ticket(
            sale_id=1,
            sale_date='2024-09-30 12:00:00',
            sale_total=10.00,
            sale_paid=10.00,
            sale_change=0.00
        )

        # Verificar que se intentó abrir el archivo
        mock_startfile.assert_called_once_with(test_filename)

    def test_generate_sale_ticket_error_handling(
        self,
        sale_controller: SaleController,
        mocker: "MockerFixture"
    ) -> None:
        """
        Test de manejo de errores al generar ticket.

        Args:
            sale_controller: Fixture del controlador de ventas
            mocker: Fixture de pytest-mock
        """
        # Configurar mock para lanzar excepción
        sale_controller.db.execute_query = MagicMock(
            side_effect=Exception("Error de base de datos")
        )

        # Mock de messagebox
        mock_messagebox = mocker.patch(
            'app.controllers.sale_controller.messagebox')

        # Ejecutar
        sale_controller._generate_sale_ticket(
            sale_id=1,
            sale_date='2024-09-30 12:00:00',
            sale_total=10.00,
            sale_paid=10.00,
            sale_change=0.00
        )

        # Verificar que se mostró el error
        mock_messagebox.showerror.assert_called_once()
        assert "Error al generar ticket" in mock_messagebox.showerror.call_args[0][0]

    @patch('app.controllers.sale_controller.messagebox')
    def test_confirm_sale_with_ticket_prompt(
        self,
        mock_messagebox: MagicMock,
        sale_controller: SaleController,
        mocker: "MockerFixture"
    ) -> None:
        """
        Test que verifica que se pregunta por el ticket después de confirmar venta.

        Args:
            mock_messagebox: Mock de messagebox
            sale_controller: Fixture del controlador de ventas
            mocker: Fixture de pytest-mock
        """
        # Preparar datos de venta
        sale_controller.items = [
            {
                'barcode': '123456',
                'name': 'Producto Test',
                'qty': 2,
                'price': 10.00,
                'subtotal': 20.00
            }
        ]
        sale_controller.temp_stock = {'123456': 2}
        sale_controller.sale_form.paid = 25.00
        sale_controller.sale_form.change = 5.00

        # Mock de producto
        mock_product = MagicMock()
        mock_product.id = 1
        mock_product.stock = 10
        sale_controller.db.get_product_by_barcode = MagicMock(
            return_value=mock_product)
        sale_controller.db.add_sale = MagicMock(return_value=1)
        sale_controller.db.add_sale_detail = MagicMock()
        sale_controller.db.update_product = MagicMock()

        # Mock para que NO genere el ticket
        mock_messagebox.askyesno.return_value = False
        mock_messagebox.showinfo = MagicMock()

        # Mock del método _generate_sale_ticket
        mock_generate = mocker.patch.object(
            sale_controller, '_generate_sale_ticket')

        # Ejecutar
        result = sale_controller.confirm_sale()

        # Verificar
        assert result is True
        # Verificar que se preguntó por el ticket
        assert any(
            'ticket' in str(call).lower()
            for call in mock_messagebox.askyesno.call_args_list
        )
        # Como respondió No, no se debe generar el ticket
        mock_generate.assert_not_called()


class TestExportServicePrinting:
    """Tests para la funcionalidad de impresión."""

    def test_print_pdf_windows(self, mocker: "MockerFixture") -> None:
        """
        Test de impresión en Windows.

        Args:
            mocker: Fixture de pytest-mock
        """
        from app.services.export_service import ExportService

        service = ExportService()

        # Mock de platform.system
        mocker.patch('platform.system', return_value='Windows')
        mock_startfile = mocker.patch('os.startfile')

        # Ejecutar
        result = service.print_pdf('test.pdf')

        # Verificar
        assert result is True
        mock_startfile.assert_called_once_with('test.pdf', 'print')

    def test_print_pdf_error(self, mocker: "MockerFixture") -> None:
        """
        Test de manejo de errores al imprimir.

        Args:
            mocker: Fixture de pytest-mock
        """
        from app.services.export_service import ExportService

        service = ExportService()

        # Mock que lanza excepción
        mocker.patch('platform.system', return_value='Windows')
        mocker.patch('os.startfile', side_effect=Exception(
            "Error de impresión"))

        # Ejecutar
        result = service.print_pdf('test.pdf')

        # Verificar que retorna False en caso de error
        assert result is False
