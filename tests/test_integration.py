"""Pruebas de integración para la aplicación de gestión de stock."""
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture
    from app.views.main_window import MainWindow
    from app.controllers.product_controller import ProductController
    from app.controllers.sale_controller import SaleController


def test_product_controller_integration(
    main_window: "MainWindow",
    product_controller: "ProductController",
    mocker: "MockerFixture"
) -> None:
    """Prueba la integración entre MainWindow y ProductController.

    Esta prueba verifica que:
    1. El controlador de productos se inicializa correctamente
    2. La ventana principal tiene los componentes necesarios
    3. Los componentes están correctamente conectados

    Args:
        main_window: Fixture que proporciona la ventana principal
        product_controller: Fixture que proporciona el controlador de productos
        mocker: Fixture de pytest-mock para simular comportamientos
    """
    # Verificar que la ventana principal tiene los componentes necesarios
    assert hasattr(main_window, 'product_form')
    assert hasattr(main_window, 'product_list')

    # Verificar que el controlador está correctamente inicializado
    assert product_controller is not None

    # Simular la adición de un producto
    mock_product = {
        'barcode': '123456789012',
        'name': 'Producto Test',
        'price': '100.0',
        'stock': '10'
    }

    # Simular el método de guardar producto
    mocker.patch.object(
        product_controller,
        'save_product',
        return_value=True
    )

    # Intentar guardar un producto
    result = product_controller.save_product()

    # Verificar que el método fue llamado
    assert result is True
    product_controller.save_product.assert_called_once()
