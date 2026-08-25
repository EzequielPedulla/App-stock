import os

# Force OpenBLAS to skip its runtime CPU auto-detection before numpy/matplotlib
# load. On some older AMD CPUs (pre-SSSE3/AVX) that detection misfires and
# picks a kernel using instructions the CPU doesn't have, crashing during DLL
# init ("DLL load failed" on _multiarray_umath). "generic" is safe everywhere.
os.environ.setdefault("OPENBLAS_CORETYPE", "generic")

from app.views.main_window import MainWindow
from app.controllers.product_controller import ProductController
from app.controllers.sale_controller import SaleController
from app.controllers.report_controller import ReportController
from app.controllers.caja_controller import CajaController


def main():

    window = MainWindow()

    product_controller = ProductController(
        window.product_form, window.product_list)

    report_controller = ReportController(
        window.report_form, window.product_list)

    sale_controller = SaleController(
        window.sale_form,
        window.product_list,
        report_controller
    )

    caja_controller = CajaController(window.caja_form)

    window.mainloop()


if __name__ == "__main__":
    main()
