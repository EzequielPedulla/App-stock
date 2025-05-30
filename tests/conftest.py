"""Configuración compartida para las pruebas de integración."""
from typing import TYPE_CHECKING, Generator

import pytest
from app.views.main_window import MainWindow
from app.controllers.product_controller import ProductController
from app.controllers.sale_controller import SaleController

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def main_window() -> MainWindow:
    """Fixture que proporciona una instancia de MainWindow para las pruebas.

    Returns:
        MainWindow: Una instancia de la ventana principal.
    """
    return MainWindow()


@pytest.fixture
def product_controller(main_window: MainWindow) -> ProductController:
    """Fixture que proporciona una instancia de ProductController para las pruebas.

    Args:
        main_window: Instancia de MainWindow proporcionada por el fixture main_window.

    Returns:
        ProductController: Una instancia del controlador de productos.
    """
    return ProductController(main_window.product_form, main_window.product_list)


@pytest.fixture
def sale_controller(main_window: MainWindow) -> SaleController:
    """Fixture que proporciona una instancia de SaleController para las pruebas.

    Args:
        main_window: Instancia de MainWindow proporcionada por el fixture main_window.

    Returns:
        SaleController: Una instancia del controlador de ventas.
    """
    return SaleController(main_window.sale_form, main_window.product_list)
