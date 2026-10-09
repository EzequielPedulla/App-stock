"""Controlador del cuaderno de fiados (clientes, deudas y pagos)."""

from typing import Any
from tkinter import messagebox

from ..models.database import Database
from ..security import owner_lock
from ..views.cliente_dialogs import show_cliente_form


class ClientesApi:
    """Lo que necesita la pantalla de Ventas para fiar: buscar clientes,
    crear uno nuevo en el momento y avisar si se pasa del límite."""

    def __init__(self) -> None:
        self.db = Database()

    def buscar_clientes(self, texto: str = '') -> list:
        return self.db.get_clientes(texto)

    def crear_cliente(self, data: dict):
        """Crea un cliente y lo devuelve (con su saldo), o None si falló."""
        try:
            cliente_id = self.db.add_cliente(**data)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el cliente: {e}")
            return None
        return self.db.get_cliente(cliente_id)

    def confirmar_limite(self, cliente: dict, monto: float,
                         parent: Any = None) -> bool:
        """El límite es solo un aviso: si con este fiado el cliente pasa
        su límite se pregunta si seguir igual (nunca se bloquea)."""
        limite = cliente.get('limite')
        if limite is None:
            return True
        nuevo_saldo = cliente['saldo'] + monto
        if nuevo_saldo <= limite + 0.005:
            return True
        if owner_lock.unlocked:
            detalle = (
                f"{cliente['nombre']} debe ${cliente['saldo']:.2f} y con este "
                f"fiado de ${monto:.2f} pasaría a deber ${nuevo_saldo:.2f}.\n"
                f"Su límite es ${limite:.2f}.")
        else:
            detalle = (
                f"Con este fiado de ${monto:.2f}, {cliente['nombre']} "
                "pasaría su límite de fiado.")
        return messagebox.askyesno(
            "Límite superado", detalle + "\n\n¿Fiar igual?", parent=parent)


class FiadosController:
    """Controlador de la pestaña Fiados."""

    def __init__(self, fiados_form: Any) -> None:
        self.form = fiados_form
        self.form.fiados_controller = self
        self.db = Database()
        self.api = ClientesApi()
        self._connect_events()
        self.refresh()

    def _connect_events(self) -> None:
        f = self.form
        f.nuevo_button.configure(command=self.nuevo_cliente)
        f.editar_button.configure(command=self.editar_cliente_seleccionado)
        f.cuenta_button.configure(command=self.ver_cuenta_seleccionado)
        f.tree.bind('<Double-1>', lambda e: self.ver_cuenta_seleccionado())
        f.tree.bind('<Return>', lambda e: self.ver_cuenta_seleccionado())
        f.search_var.trace_add('write', lambda *a: self.refresh())
        f.solo_deuda_var.trace_add('write', lambda *a: self.refresh())

    # ----- lista -----

    def refresh(self) -> None:
        clientes = self.db.get_clientes(
            self.form.search_var.get(),
            solo_con_deuda=bool(self.form.solo_deuda_var.get()))
        # Los totales de arriba son de todos los clientes, no del filtro.
        todos = self.db.get_clientes()
        total_deuda = sum(c['saldo'] for c in todos if c['saldo'] > 0.005)
        con_deuda = sum(1 for c in todos if c['saldo'] > 0.005)
        self.form.load_clientes(clientes)
        self.form.update_summary(total_deuda, con_deuda)

    def _cliente_seleccionado(self):
        sel = self.form.tree.selection()
        if not sel:
            messagebox.showwarning(
                "Advertencia", "Seleccioná un cliente de la lista.")
            return None
        return self.db.get_cliente(int(sel[0]))

    # ----- clientes -----

    def nuevo_cliente(self) -> None:
        def guardar(data):
            try:
                self.db.add_cliente(**data)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")
                return False
            self.refresh()
            return True
        show_cliente_form(self.form, guardar)

    def editar_cliente(self, cliente_id: int, despues=None) -> None:
        cliente = self.db.get_cliente(cliente_id)
        if not cliente:
            return

        def guardar(data):
            try:
                self.db.update_cliente(cliente_id, **data)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")
                return False
            self.refresh()
            if despues:
                despues()
            return True
        show_cliente_form(self.form, guardar, cliente)

    def editar_cliente_seleccionado(self) -> None:
        cliente = self._cliente_seleccionado()
        if cliente:
            self.editar_cliente(cliente['id'])

    def eliminar_cliente(self, cliente_id: int) -> bool:
        """Borra al cliente si nunca tuvo movimientos; si tiene historial
        lo da de baja (deja de aparecer, pero se conserva el registro).
        No se puede dar de baja a alguien que todavía debe plata."""
        cliente = self.db.get_cliente(cliente_id)
        if not cliente:
            return False
        if cliente['saldo'] > 0.005:
            messagebox.showwarning(
                "Tiene deuda",
                f"{cliente['nombre']} todavía debe ${cliente['saldo']:.2f}.\n"
                "Registrá el pago antes de darlo de baja.")
            return False
        if not messagebox.askyesno(
                "Confirmar", f"¿Eliminar a {cliente['nombre']}?"):
            return False
        if not self.db.delete_cliente(cliente_id):
            self.db.set_cliente_activo(cliente_id, False)
        self.refresh()
        return True

    # ----- cuenta corriente -----

    def ver_cuenta_seleccionado(self) -> None:
        cliente = self._cliente_seleccionado()
        if cliente:
            self.form.show_cuenta_dialog(cliente['id'])

    def get_cuenta(self, cliente_id: int) -> dict:
        """Cliente con todos sus movimientos (compras fiadas y pagos)
        mezclados por fecha, el más reciente primero, con el saldo que
        iba quedando después de cada uno. Las compras anuladas se
        muestran pero no cuentan."""
        cliente = self.db.get_cliente(cliente_id)
        movimientos = []
        for v in self.db.get_ventas_fiadas_cliente(cliente_id):
            activa = v['status'] != 'cancelled'
            detalle = f"Venta N° {v['id']}: {v['productos']}"
            if v['fiado'] < v['total'] - 0.005:
                detalle += f" (fiado ${v['fiado']:.2f} de ${v['total']:.2f})"
            movimientos.append({
                'fecha': v['date'],
                'tipo': 'Compra fiada' if activa else 'Compra anulada',
                'detalle': detalle,
                'monto': float(v['fiado']),
                'cuenta': activa,
                'pago_id': None,
                'sale_id': v['id'],
            })
        for p in self.db.get_pagos_cliente(cliente_id):
            detalle = p['forma_pago'].capitalize()
            if p['nota']:
                detalle += f" - {p['nota']}"
            movimientos.append({
                'fecha': p['fecha'],
                'tipo': 'Pago',
                'detalle': detalle,
                'monto': -float(p['monto']),
                'cuenta': True,
                'pago_id': p['id'],
                'forma_pago': p['forma_pago'],
                'nota': p['nota'],
            })
        movimientos.sort(key=lambda m: m['fecha'])
        saldo = 0.0
        for m in movimientos:
            if m['cuenta']:
                saldo += m['monto']
            m['saldo'] = round(saldo, 2)
        movimientos.reverse()
        return {'cliente': cliente, 'movimientos': movimientos}

    def get_detalle_venta(self, sale_id: int) -> dict:
        """Todo lo de una venta fiada: productos, cómo se pagó y cuánto
        quedó sin cobrar, para mostrarlo al tocar el movimiento."""
        venta = self.db.execute_query(
            "SELECT * FROM sales WHERE id = ?", (sale_id,))
        items = self.db.execute_query(
            """SELECT p.name AS nombre, sd.quantity AS cantidad,
                      sd.unit_price AS precio
               FROM sale_details sd JOIN products p ON p.id = sd.product_id
               WHERE sd.sale_id = ?""", (sale_id,))
        pagos = self.db.execute_query(
            "SELECT payment_method AS metodo, amount AS monto "
            "FROM sale_payments WHERE sale_id = ?", (sale_id,))
        v = venta[0] if venta else {}
        if not pagos and v:
            # Venta con un solo método: todo el total se pagó (o fió) así.
            pagos = [{'metodo': v['payment_method'], 'monto': v['total']}]
        return {'venta': v, 'items': items, 'pagos': pagos}

    def registrar_pago(self, cliente_id: int, monto: float, forma_pago: str,
                       nota: str) -> bool:
        """Anota un pago del cliente. Avisa si quedó fuera de Caja."""
        try:
            en_caja = self.db.add_pago_cliente(
                cliente_id, monto, forma_pago, nota)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar el pago: {e}")
            return False
        if not en_caja:
            messagebox.showinfo(
                "Caja cerrada",
                "El pago quedó anotado en la cuenta del cliente, pero la "
                "caja de hoy ya está cerrada, así que no se sumó a Caja.")
        self.refresh()
        return True

    def anular_pago(self, pago_id: int) -> bool:
        if not messagebox.askyesno(
                "Confirmar",
                "¿Anular este pago? La deuda del cliente vuelve a subir "
                "y se saca el cobro de Caja."):
            return False
        if not self.db.delete_pago_cliente(pago_id):
            messagebox.showwarning(
                "No se puede anular",
                "Ese cobro quedó en una caja que ya se cerró.")
            return False
        self.refresh()
        return True
