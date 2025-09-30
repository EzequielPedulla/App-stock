from app.views.main_window import MainWindow
from app.controllers.product_controller import ProductController
from app.controllers.sale_controller import SaleController
from app.controllers.report_controller import ReportController


def main():

    window = MainWindow()

    product_controller = ProductController(
        window.product_form, window.product_list)

    report_controller = ReportController(window.report_form)

    sale_controller = SaleController(
        window.sale_form,
        window.product_list,
        report_controller
    )

    window.mainloop()


if __name__ == "__main__":
    main()
