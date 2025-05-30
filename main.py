from app.views.main_window import MainWindow
from app.controllers.product_controller import ProductController
from app.controllers.sale_controller import SaleController


def main():
    window = MainWindow()

    # Inicializar el controlador de productos
    product_controller = ProductController(
        window.product_form, window.product_list)

    # Inicializar el controlador de ventas con la lista de productos
    SaleController(window.sale_form, window.product_list)

    # Iniciar la aplicación
    window.mainloop()


if __name__ == "__main__":
    main()
