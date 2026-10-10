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
from app.controllers.fiados_controller import FiadosController
from app.controllers.pedidos_controller import PedidosController
from app.security import owner_lock
import tkinter as tk


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

    fiados_controller = FiadosController(window.fiados_form)

    pedidos_controller = PedidosController(window.pedidos_form)
    pedidos_controller.on_cambio = window.set_badge_pedidos
    pedidos_controller.refresh()
    # Aviso (una vez por día) de los pedidos de hoy, mañana y atrasados
    window.after(700, pedidos_controller.mostrar_aviso_diario)

    def revisar_pedidos():
        """Cada 5 minutos: actualiza el aviso del menú y avisa si cambió el
        día, siempre que nadie esté usando la app ni haya un diálogo
        abierto (para no cortar una venta)."""
        hay_dialogo = any(isinstance(w, tk.Toplevel)
                          for w in window.winfo_children())
        ocioso = owner_lock.segundos_inactivo() > 120 and not hay_dialogo
        pedidos_controller.chequeo_periodico(ocioso)
        window.after(300_000, revisar_pedidos)

    window.after(300_000, revisar_pedidos)

    window.mainloop()


if __name__ == "__main__":
    main()
