"""Tests para la funcionalidad de impresión de tickets."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock
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


class TestTicketPrinting:
    """Tests para la impresión de tickets."""

    def test_generate_ticket_and_print(
        self,
        sale_controller: SaleController,
        mocker: "MockerFixture"
    ) -> None:
        """
        Test de generación y impresión de ticket.

        Args:
            sale_controller: Fixture del controlador de ventas
            mocker: Fixture de pytest-mock
        """
        # Mock de datos
        mock_details = [
            {'producto': 'Test', 'cantidad': 1, 'precio': 10.0, 'subtotal': 10.0}
        ]
        sale_controller.db.execute_query = MagicMock(return_value=mock_details)

        # Mock de exportación
        test_filename = 'test_reportes/ticket_test.pdf'
        mocker.patch.object(
            sale_controller.export_service,
            'export_sale_ticket_to_pdf',
            return_value=test_filename
        )

        # Mock de impresión exitosa
        mock_print = mocker.patch.object(
            sale_controller.export_service,
            'print_pdf',
            return_value=True
        )

        # Mock de messagebox
        mock_messagebox = mocker.patch(
            'app.controllers.sale_controller.messagebox')
        mock_mb = mocker.patch('tkinter.messagebox')
        mock_mb.askyesnocancel.return_value = True  # True = Imprimir

        # Ejecutar
        sale_controller._generate_sale_ticket(
            sale_id=1,
            sale_date='2024-09-30 12:00:00',
            sale_total=10.00,
            sale_paid=10.00,
            sale_change=0.00
        )

        # Verificar que se llamó a print_pdf
        mock_print.assert_called_once_with(test_filename)

        # Verificar que se mostró mensaje de éxito
        assert mock_messagebox.showinfo.called

    def test_generate_ticket_print_error(
        self,
        sale_controller: SaleController,
        mocker: "MockerFixture"
    ) -> None:
        """
        Test de error al imprimir ticket.

        Args:
            sale_controller: Fixture del controlador de ventas
            mocker: Fixture de pytest-mock
        """
        # Mock de datos
        mock_details = [
            {'producto': 'Test', 'cantidad': 1, 'precio': 10.0, 'subtotal': 10.0}
        ]
        sale_controller.db.execute_query = MagicMock(return_value=mock_details)

        # Mock de exportación
        test_filename = 'test_reportes/ticket_test.pdf'
        mocker.patch.object(
            sale_controller.export_service,
            'export_sale_ticket_to_pdf',
            return_value=test_filename
        )

        # Mock de impresión fallida
        mock_print = mocker.patch.object(
            sale_controller.export_service,
            'print_pdf',
            return_value=False
        )

        # Mock de messagebox
        mock_messagebox = mocker.patch(
            'app.controllers.sale_controller.messagebox')
        mock_mb = mocker.patch('tkinter.messagebox')
        mock_mb.askyesnocancel.return_value = True  # True = Imprimir

        # Ejecutar
        sale_controller._generate_sale_ticket(
            sale_id=1,
            sale_date='2024-09-30 12:00:00',
            sale_total=10.00,
            sale_paid=10.00,
            sale_change=0.00
        )

        # Verificar que se llamó a print_pdf
        mock_print.assert_called_once_with(test_filename)

        # Verificar que se mostró mensaje de error
        assert mock_messagebox.showerror.called
