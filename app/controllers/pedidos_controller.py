"""Controlador de pedidos a proveedores."""

from datetime import date, timedelta
from typing import Any
from tkinter import messagebox

from ..models.database import Database
from ..utils import texto_dia

CLAVE_AVISO = 'aviso_pedidos_fecha'


class PedidosController:
    """Controlador de la pestaña Pedidos: qué pedidos vienen, cuándo y
    cuánta plata hace falta, y confirmar la recepción (que se anota como
    gasto en Caja)."""

    def __init__(self, pedidos_form: Any) -> None:
        self.form = pedidos_form
        self.form.pedidos_controller = self
        self.db = Database()
        # Lo setea la ventana principal: se llama cuando cambia la cantidad
        # de pedidos urgentes (para el numerito del menú).
        self.on_cambio = None
        self._ultimo_dia = self._hoy()
        self._connect_events()
        self.refresh()

    def _connect_events(self) -> None:
        f = self.form
        f.nuevo_button.configure(command=self.nuevo_pedido)
        f.recibir_button.configure(command=self.recibir_seleccionado)
        f.editar_button.configure(command=self.editar_seleccionado)
        f.cancelar_button.configure(command=self.cancelar_seleccionado)
        f.deshacer_button.configure(command=self.deshacer_seleccionado)
        f.tree.bind('<Return>', lambda e: self.recibir_seleccionado())
        f.tree.bind('<Double-1>', lambda e: self.recibir_seleccionado())
        f.filtro_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh())

    @staticmethod
    def _hoy() -> date:
        return date.today()

    # ----- datos para la pantalla -----

    def _estados_filtro(self):
        return {'Pendientes': ['pendiente'],
                'Recibidos': ['recibido'],
                'Cancelados': ['cancelado'],
                'Todos': None}.get(self.form.filtro_combo.get(), ['pendiente'])

    def resumen(self) -> dict:
        """Cantidad y plata aproximada de hoy, de los próximos 7 días (hoy
        incluido) y de lo atrasado (pendiente con fecha ya pasada)."""
        hoy = self._hoy()
        hoy_s = hoy.isoformat()
        fin_s = (hoy + timedelta(days=6)).isoformat()
        pendientes = self.db.get_pedidos(['pendiente'])

        def suma(lista):
            return {'cantidad': len(lista),
                    'monto': sum(float(p['monto_estimado']) for p in lista)}
        return {
            'hoy': suma([p for p in pendientes
                         if p['fecha_estimada'] == hoy_s]),
            'semana': suma([p for p in pendientes
                            if hoy_s <= p['fecha_estimada'] <= fin_s]),
            'atrasados': suma([p for p in pendientes
                               if p['fecha_estimada'] < hoy_s]),
        }

    def dias_con_pedidos(self, dias: int = 14) -> list:
        """Plata aproximada por día para los próximos `dias` días (solo los
        que tienen pedidos pendientes); lo atrasado va al principio."""
        hoy_s = self._hoy().isoformat()
        fin_s = (self._hoy() + timedelta(days=dias - 1)).isoformat()
        por_dia = {}
        for p in self.db.get_pedidos(['pendiente']):
            f = p['fecha_estimada']
            if f > fin_s:
                continue
            clave = 'atrasado' if f < hoy_s else f
            d = por_dia.setdefault(
                clave, {'fecha': clave, 'cantidad': 0, 'monto': 0.0,
                        'proveedores': []})
            d['cantidad'] += 1
            d['monto'] += float(p['monto_estimado'])
            d['proveedores'].append(p['proveedor'])
        orden = sorted(por_dia, key=lambda k: '0' if k == 'atrasado' else k)
        return [por_dia[k] for k in orden]

    def contar_urgentes(self) -> int:
        """Pedidos pendientes que vienen hoy, mañana o ya se pasaron."""
        limite = (self._hoy() + timedelta(days=1)).isoformat()
        return sum(1 for p in self.db.get_pedidos(['pendiente'])
                   if p['fecha_estimada'] <= limite)

    def refresh(self) -> None:
        pedidos = self.db.get_pedidos(self._estados_filtro())
        self.form.load_pedidos(pedidos, self._hoy().isoformat())
        self.form.update_resumen(self.resumen())
        self.form.load_dias(self.dias_con_pedidos())
        if self.on_cambio:
            self.on_cambio(self.contar_urgentes())

    def _seleccionado(self):
        sel = self.form.tree.selection()
        if not sel:
            messagebox.showwarning(
                "Advertencia", "Seleccioná un pedido de la lista.")
            return None
        return self.db.get_pedido(int(sel[0]))

    # ----- pedidos -----

    def nuevo_pedido(self) -> None:
        self.form.show_pedido_dialog(self.db.get_proveedores(), None,
                                     self._guardar_nuevo)

    def _guardar_nuevo(self, data: dict) -> bool:
        try:
            prov = self.db.get_or_create_proveedor(
                data['proveedor'], data['telefono'])
            self.db.add_pedido(prov, data['fecha'], data['monto'],
                               data['nota'], data['tipo'], data['repetir'])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el pedido: {e}")
            return False
        self.refresh()
        return True

    def editar_seleccionado(self) -> None:
        pedido = self._seleccionado()
        if not pedido:
            return
        if pedido['estado'] != 'pendiente':
            messagebox.showinfo(
                "No se puede editar",
                "Solo se editan pedidos pendientes. Si ya se recibió, "
                "usá \"Deshacer recepción\" primero.")
            return

        def guardar(data):
            try:
                prov = self.db.get_or_create_proveedor(
                    data['proveedor'], data['telefono'])
                self.db.update_pedido(pedido['id'], prov, data['fecha'],
                                      data['monto'], data['nota'],
                                      data['tipo'], data['repetir'])
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")
                return False
            self.refresh()
            return True
        self.form.show_pedido_dialog(self.db.get_proveedores(), pedido,
                                     guardar)

    def recibir_seleccionado(self) -> None:
        pedido = self._seleccionado()
        if not pedido:
            return
        if pedido['estado'] != 'pendiente':
            messagebox.showinfo(
                "Ya está cerrado",
                "Ese pedido ya se recibió o se canceló.")
            return
        self.form.show_recibir_dialog(pedido, self.confirmar_recepcion)

    def confirmar_recepcion(self, pedido_id: int, monto: float,
                            forma_pago: str) -> bool:
        try:
            en_caja = self.db.recibir_pedido(pedido_id, monto, forma_pago)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar: {e}")
            return False
        if en_caja is not None:
            nuevo = self.db.get_pedido(pedido_id)
            if nuevo and nuevo['siguiente_id']:
                prox = self.db.get_pedido(nuevo['siguiente_id'])
                messagebox.showinfo(
                    "Se repite",
                    f"Quedó cargado el próximo de {prox['proveedor']} para el "
                    f"{texto_dia(prox['fecha_estimada'])}. Para que deje de "
                    "repetirse, cancelalo cuando ya no haga falta.")
        if en_caja is None:
            messagebox.showwarning(
                "No se puede", "Ese pedido ya no está pendiente.")
        elif en_caja is False:
            messagebox.showinfo(
                "Caja cerrada",
                "El pedido quedó como recibido, pero la caja de hoy ya está "
                "cerrada, así que el gasto no se sumó a Caja.")
        self.refresh()
        return True

    def cancelar_seleccionado(self) -> None:
        pedido = self._seleccionado()
        if not pedido:
            return
        if pedido['estado'] != 'pendiente':
            messagebox.showinfo(
                "No se puede", "Solo se cancelan pedidos pendientes.")
            return
        if messagebox.askyesno(
                "Confirmar",
                f"¿Cancelar el pedido de {pedido['proveedor']} del "
                f"{texto_dia(pedido['fecha_estimada'])}?"):
            self.db.set_pedido_cancelado(pedido['id'])
            self.refresh()

    def deshacer_seleccionado(self) -> None:
        pedido = self._seleccionado()
        if not pedido:
            return
        if pedido['estado'] != 'recibido':
            messagebox.showinfo(
                "No se puede", "Solo se deshace la recepción de un pedido "
                "ya recibido.")
            return
        if not messagebox.askyesno(
                "Confirmar",
                f"¿Deshacer la recepción del pedido de {pedido['proveedor']}?"
                "\nVuelve a pendiente y se saca el gasto de Caja."):
            return
        if not self.db.deshacer_recepcion(pedido['id']):
            messagebox.showwarning(
                "No se puede deshacer",
                "Ese gasto quedó en una caja que ya se cerró.")
            return
        self.refresh()

    # ----- aviso al abrir la app -----

    def mensaje_aviso(self):
        """Líneas del aviso diario (hoy, mañana y atrasados), o None si no
        hay nada para avisar."""
        hoy = self._hoy()
        hoy_s = hoy.isoformat()
        man_s = (hoy + timedelta(days=1)).isoformat()
        pendientes = self.db.get_pedidos(['pendiente'])
        grupos = (
            ("⚠ Atrasados",
             [p for p in pendientes if p['fecha_estimada'] < hoy_s]),
            ("Hoy", [p for p in pendientes if p['fecha_estimada'] == hoy_s]),
            ("Mañana", [p for p in pendientes if p['fecha_estimada'] == man_s]),
        )
        lineas = []
        for titulo, lista in grupos:
            if not lista:
                continue
            total = sum(float(p['monto_estimado']) for p in lista)
            nombres = ", ".join(
                ("🧾 " if p['tipo'] == 'servicio' else "📦 ") + p['proveedor']
                for p in lista)
            monto = (f"aprox. ${total:.2f}" if total > 0
                     else "monto sin definir")
            tipos = {p['tipo'] for p in lista}
            if tipos == {'servicio'}:
                sust = "pago" if len(lista) == 1 else "pagos"
            elif tipos == {'pedido'}:
                sust = "pedido" if len(lista) == 1 else "pedidos"
            else:
                sust = "pedidos y pagos"
            lineas.append((f"{titulo}: {len(lista)} {sust} · {monto}",
                           nombres, titulo.startswith('⚠')))
        return lineas or None

    def chequeo_periodico(self, ocioso: bool) -> None:
        """Se llama cada tanto con la app abierta (por si pasó la medianoche
        o se cargó un pedido para hoy): actualiza el numerito del menú y,
        si cambió el día, la pantalla. El aviso emergente solo sale cuando
        `ocioso` es True (nadie está usando la app), para no interrumpir un
        cobro."""
        hoy = self._hoy()
        cambio_dia = hoy != self._ultimo_dia
        self._ultimo_dia = hoy
        if cambio_dia:
            self.refresh()
        elif self.on_cambio:
            self.on_cambio(self.contar_urgentes())
        if ocioso:
            self.mostrar_aviso_diario()

    def mostrar_aviso_diario(self) -> None:
        """Muestra una sola vez por día los pedidos de hoy, mañana y los
        atrasados."""
        hoy_s = self._hoy().isoformat()
        if self.db.get_config(CLAVE_AVISO) == hoy_s:
            return
        lineas = self.mensaje_aviso()
        if not lineas:
            return
        self.db.set_config(CLAVE_AVISO, hoy_s)
        self.form.show_aviso_dialog(lineas)
