from app.views.main_window import MainWindow
from app.controllers.product_controller import ProductController


def main():
    window = MainWindow()

    # Inicializar el controlador
    ProductController(window.product_form, window.product_list)

    # Iniciar la aplicación
    window.mainloop()


if __name__ == "__main__":
    main()
