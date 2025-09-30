"""Tests para la funcionalidad de anulación de ventas."""

from typing import TYPE_CHECKING
from unittest.mock import MagicMock
import pytest
from app.models.database import Database
from app.models.product import Product

if TYPE_CHECKING:
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def db():
    """
    Fixture que proporciona una instancia de base de datos para tests.

    Returns:
        Database: Instancia de la base de datos
    """
    return Database()


class TestCancelSale:
    """Tests para la anulación de ventas."""

    def test_cancel_sale_updates_status(self, db: Database, mocker: "MockerFixture") -> None:
        """
        Test que verifica que se actualiza el estado de la venta.

        Args:
            db: Fixture de la base de datos
            mocker: Fixture de pytest-mock
        """
        # Mock de execute_query para simular venta activa
        mock_query_results = [
            [{'status': 'active'}],  # Primera llamada: verificar estado
            # Segunda llamada: obtener detalles
            [{'product_id': 1, 'quantity': 2}],
        ]
        mocker.patch.object(db, 'execute_query',
                            side_effect=mock_query_results)

        # Mock de get_product_by_id
        mock_product = Product(
            barcode='123', name='Test', price=10.0, stock=10)
        mock_product.id = 1
        mocker.patch.object(db, 'get_product_by_id', return_value=mock_product)

        # Mock de update_product
        mock_update = mocker.patch.object(db, 'update_product')

        # Mock de cursor.execute y commit
        mocker.patch.object(db.cursor, 'execute')
        mocker.patch.object(db.connection, 'commit')

        # Ejecutar
        result = db.cancel_sale(1, "Producto defectuoso")

        # Verificar
        assert result is True
        assert db.cursor.execute.called

    def test_cancel_sale_already_cancelled(
        self, db: Database, mocker: "MockerFixture"
    ) -> None:
        """
        Test que verifica que no se puede anular una venta ya anulada.

        Args:
            db: Fixture de la base de datos
            mocker: Fixture de pytest-mock
        """
        # Mock de execute_query para simular venta ya anulada
        mocker.patch.object(
            db, 'execute_query', return_value=[{'status': 'cancelled'}]
        )

        # Ejecutar
        result = db.cancel_sale(1, "Test")

        # Verificar
        assert result is False

    def test_cancel_sale_not_found(
        self, db: Database, mocker: "MockerFixture"
    ) -> None:
        """
        Test que verifica que retorna False si la venta no existe.

        Args:
            db: Fixture de la base de datos
            mocker: Fixture de pytest-mock
        """
        # Mock de execute_query para simular venta no encontrada
        mocker.patch.object(db, 'execute_query', return_value=[])

        # Ejecutar
        result = db.cancel_sale(999, "Test")

        # Verificar
        assert result is False

    def test_cancel_sale_reintegrates_stock(
        self, db: Database, mocker: "MockerFixture"
    ) -> None:
        """
        Test que verifica que se reintegra el stock correctamente.

        Args:
            db: Fixture de la base de datos
            mocker: Fixture de pytest-mock
        """
        # Mock de execute_query
        mock_query_results = [
            [{'status': 'active'}],  # Verificar estado
            [  # Detalles de venta
                {'product_id': 1, 'quantity': 2},
                {'product_id': 2, 'quantity': 3},
            ],
        ]
        mocker.patch.object(db, 'execute_query',
                            side_effect=mock_query_results)

        # Mock de productos
        product1 = Product(barcode='123', name='Producto 1',
                           price=10.0, stock=5)
        product1.id = 1
        product2 = Product(barcode='456', name='Producto 2',
                           price=20.0, stock=3)
        product2.id = 2

        mocker.patch.object(
            db, 'get_product_by_id', side_effect=[product1, product2]
        )

        # Mock de update_product
        mock_update = mocker.patch.object(db, 'update_product')

        # Mock de cursor y commit
        mocker.patch.object(db.cursor, 'execute')
        mocker.patch.object(db.connection, 'commit')

        # Ejecutar
        result = db.cancel_sale(1, "Test")

        # Verificar que se actualizó el stock
        assert result is True
        assert mock_update.call_count == 2
        assert product1.stock == 7  # 5 + 2
        assert product2.stock == 6  # 3 + 3

    def test_cancel_sale_ignores_varios_products(
        self, db: Database, mocker: "MockerFixture"
    ) -> None:
        """
        Test que verifica que no reintegra stock de productos VARIOS.

        Args:
            db: Fixture de la base de datos
            mocker: Fixture de pytest-mock
        """
        # Mock de execute_query
        mock_query_results = [
            [{'status': 'active'}],  # Verificar estado
            [  # Detalles de venta
                {'product_id': 1, 'quantity': 2},  # Normal
                {'product_id': 2, 'quantity': 1},  # VARIOS
            ],
        ]
        mocker.patch.object(db, 'execute_query',
                            side_effect=mock_query_results)

        # Mock de productos
        product1 = Product(
            barcode='123', name='Producto Normal', price=10.0, stock=5)
        product1.id = 1
        product_varios = Product(barcode='VAR-123456',
                                 name='Pila', price=5.0, stock=0)
        product_varios.id = 2

        mocker.patch.object(
            db, 'get_product_by_id', side_effect=[product1, product_varios]
        )

        # Mock de update_product
        mock_update = mocker.patch.object(db, 'update_product')

        # Mock de cursor y commit
        mocker.patch.object(db.cursor, 'execute')
        mocker.patch.object(db.connection, 'commit')

        # Ejecutar
        result = db.cancel_sale(1, "Test")

        # Verificar que solo se actualizó el producto normal
        assert result is True
        assert mock_update.call_count == 1  # Solo producto1
        assert product1.stock == 7  # 5 + 2

    def test_cancel_sale_with_reason(
        self, db: Database, mocker: "MockerFixture"
    ) -> None:
        """
        Test que verifica que se guarda el motivo de anulación.

        Args:
            db: Fixture de la base de datos
            mocker: Fixture de pytest-mock
        """
        # Mock de execute_query
        mock_query_results = [
            [{'status': 'active'}],
            [],  # Sin detalles para simplificar
        ]
        mocker.patch.object(db, 'execute_query',
                            side_effect=mock_query_results)

        # Mock de cursor y commit
        mock_execute = mocker.patch.object(db.cursor, 'execute')
        mocker.patch.object(db.connection, 'commit')

        # Ejecutar
        reason = "Cliente insatisfecho con el producto"
        result = db.cancel_sale(1, reason)

        # Verificar que se llamó a execute con el motivo
        assert result is True
        assert mock_execute.called
        # Verificar que el motivo está en alguno de los argumentos
        calls = str(mock_execute.call_args_list)
        assert reason in calls
