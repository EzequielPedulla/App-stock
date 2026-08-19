"""Controlador para el módulo de caja (cierre de caja diario)."""

from typing import Any
from datetime import datetime, timedelta
from tkinter import messagebox

from ..models.database import Database


class CajaController:
    """Controlador para gestionar el cierre de caja del día."""

    def __init__(self, caja_form: Any) -> None:
        self.caja_form = caja_form
        self.caja_form.caja_controller = self
        self.db = Database()
        self.sesion = None
        self.fecha_actual = self._hoy()
        self._fecha_pendiente = None
        self._connect_events()
        self.refresh()

    def _connect_events(self) -> None:
        self.caja_form.guardar_fondo_button.configure(
            command=self.guardar_fondo_inicial)
        self.caja_form.agregar_movimiento_button.configure(
            command=self.agregar_movimiento)
        self.caja_form.cerrar_button.configure(command=self.abrir_cierre)
        self.caja_form.tree.bind(
            '<Delete>', lambda e: self.eliminar_movimiento())
        self.caja_form.tree.bind(
            '<Double-1>', lambda e: self.editar_movimiento_seleccionado())
        self.caja_form.dia_anterior_button.configure(
            command=self.ir_dia_anterior)
        self.caja_form.dia_siguiente_button.configure(
            command=self.ir_dia_siguiente)
        self.caja_form.volver_hoy_button.configure(
            command=self.volver_a_hoy)
        self.caja_form.ir_a_pendiente_button.configure(
            command=self.ir_a_dia_pendiente)

    def _hoy(self) -> str:
        return datetime.now().strftime('%Y-%m-%d')

    def ir_dia_anterior(self) -> None:
        fecha = datetime.strptime(self.fecha_actual, '%Y-%m-%d')
        self.fecha_actual = (fecha - timedelta(days=1)).strftime('%Y-%m-%d')
        self.refresh()

    def ir_dia_siguiente(self) -> None:
        if self.fecha_actual >= self._hoy():
            return
        fecha = datetime.strptime(self.fecha_actual, '%Y-%m-%d')
        self.fecha_actual = (fecha + timedelta(days=1)).strftime('%Y-%m-%d')
        self.refresh()

    def volver_a_hoy(self) -> None:
        self.fecha_actual = self._hoy()
        self.refresh()

    def ir_a_dia_pendiente(self) -> None:
        if self._fecha_pendiente:
            self.fecha_actual = self._fecha_pendiente
            self.refresh()

    def refresh(self) -> None:
        """Carga (o crea) la sesión de caja del día que se está viendo y
        actualiza la pantalla. Un día se puede editar mientras su caja
        siga sin cerrar (sea hoy o un día anterior que se olvidaron de
        cerrar); una vez cerrada queda fija. Los días que nunca se
        abrieron se muestran en modo solo lectura (pero igual con las
        ventas reales de ese día, que sí quedaron registradas)."""
        fecha = self.fecha_actual
        es_hoy = (fecha == self._hoy())
        sesion = self.db.get_caja_sesion_by_fecha(fecha)

        if sesion is None and es_hoy:
            # Nueva sesión: el fondo inicial arranca con lo que se contó al
            # cerrar el día anterior (si hay), si no en $0.
            anterior = self.db.get_last_caja_sesion()
            fondo_inicial = 0.0
            if anterior and anterior['efectivo_contado'] is not None:
                fondo_inicial = float(anterior['efectivo_contado'])
            self.db.create_caja_sesion(fecha, fondo_inicial)
            sesion = self.db.get_caja_sesion_by_fecha(fecha)

        self.sesion = sesion
        self._actualizar_pantalla()

    def _totales_movimientos(self, movimientos: list) -> dict:
        """Suma los movimientos del día, separando los gastos según cómo se
        pagaron: solo el gasto en efectivo sale de la caja física, uno
        pagado por transferencia (o directamente del bolsillo del dueño)
        no la toca. El ingreso es plata que el dueño mete a la caja sin
        que sea una venta (ej. para tener cambio)."""
        gastos_efectivo = sum(
            float(m['monto']) for m in movimientos
            if m['tipo'] == 'gasto' and m['forma_pago'] == 'efectivo')
        gastos_transferencia = sum(
            float(m['monto']) for m in movimientos
            if m['tipo'] == 'gasto' and m['forma_pago'] == 'transferencia')
        total_retiros = sum(
            float(m['monto']) for m in movimientos if m['tipo'] == 'retiro')
        total_bolsillo = sum(
            float(m['monto']) for m in movimientos if m['tipo'] == 'bolsillo')
        total_ingresos = sum(
            float(m['monto']) for m in movimientos if m['tipo'] == 'ingreso')
        return {
            'gastos_efectivo': gastos_efectivo,
            'gastos_transferencia': gastos_transferencia,
            'total_retiros': total_retiros,
            'total_bolsillo': total_bolsillo,
            'total_ingresos': total_ingresos,
        }

    def _calcular_efectivo_esperado(self, sesion, movimientos, ventas) -> float:
        totales = self._totales_movimientos(movimientos)
        return (float(sesion['fondo_inicial']) + ventas['efectivo']
                + totales['total_ingresos']
                - totales['gastos_efectivo'] - totales['total_retiros'])

    def _calcular_resultado_dia(self, movimientos, ventas) -> float:
        """Cuánto se ganó hoy en limpio: todo lo vendido y cobrado (no
        cuenta fiado, todavía no entró esa plata) menos todo lo que salió
        por gastos y retiros (no cuenta bolsillo, no es plata del negocio).
        """
        totales = self._totales_movimientos(movimientos)
        total_vendido = (
            ventas['efectivo'] + ventas['transferencia'] + ventas['posnet'])
        total_egresos = (
            totales['gastos_efectivo'] + totales['gastos_transferencia']
            + totales['total_retiros'])
        return total_vendido - total_egresos

    def _actualizar_pantalla(self) -> None:
        fecha = self.fecha_actual
        es_hoy = (fecha == self._hoy())
        sesion = self.sesion

        # Un día pasado en el que nunca se abrió la caja no tiene sesión
        # guardada: se arma una "vacía" solo para mostrar en pantalla (no
        # se guarda nada), pero las ventas de ese día sí son reales.
        if sesion is not None:
            movimientos = self.db.get_caja_movimientos(sesion['id'])
            fondo_inicial = float(sesion['fondo_inicial'])
            cerrada = bool(sesion['cerrada'])
            efectivo_contado = (
                float(sesion['efectivo_contado'])
                if sesion['efectivo_contado'] is not None else 0.0)
        else:
            movimientos = []
            fondo_inicial = 0.0
            cerrada = False
            efectivo_contado = 0.0

        ventas = self.db.get_ventas_totales_por_metodo(fecha)
        totales = self._totales_movimientos(movimientos)

        efectivo_esperado = self._calcular_efectivo_esperado(
            {'fondo_inicial': fondo_inicial}, movimientos, ventas)
        resultado_dia = self._calcular_resultado_dia(movimientos, ventas)
        total_ventas_dia = (
            ventas['efectivo'] + ventas['transferencia'] + ventas['posnet'])
        total_gastos_dia = (
            totales['gastos_efectivo'] + totales['gastos_transferencia']
            + totales['total_retiros'])

        # Un día sin sesión (nunca se abrió la caja ese día) o ya cerrado
        # queda como consulta. Un día abierto (hoy, o uno anterior que
        # quedó sin cerrar) se puede seguir editando.
        bloqueada = cerrada or sesion is None

        # Si hoy hay un día anterior que quedó sin cerrar, se avisa para
        # que lo puedan terminar (si no, el fondo inicial de hoy no
        # arrastra bien el efectivo contado de ese día).
        pendiente = (
            self.db.get_caja_sesion_abierta_anterior(fecha) if es_hoy else None)
        self._fecha_pendiente = pendiente['fecha'] if pendiente else None

        self.caja_form.update_fecha(fecha, es_hoy)
        self.caja_form.update_aviso_pendiente(self._fecha_pendiente)
        self.caja_form.load_movimientos(movimientos)
        self.caja_form.update_summary({
            'resultado_dia': resultado_dia,
            'total_ventas_dia': total_ventas_dia,
            'total_gastos_dia': total_gastos_dia,
            'fondo_inicial': fondo_inicial,
            'ventas_efectivo': ventas['efectivo'],
            'ventas_transferencia': ventas['transferencia'],
            'ventas_posnet': ventas['posnet'],
            'ventas_fiado': ventas['fiado'],
            'total_gastos_efectivo': totales['gastos_efectivo'],
            'total_gastos_transferencia': totales['gastos_transferencia'],
            'total_retiros': totales['total_retiros'],
            'total_bolsillo': totales['total_bolsillo'],
            'total_ingresos': totales['total_ingresos'],
            'efectivo_esperado': efectivo_esperado,
            'cerrada': cerrada,
            'bloqueada': bloqueada,
            'es_hoy': es_hoy,
            'sin_datos': sesion is None,
            'efectivo_contado': efectivo_contado,
            'diferencia': efectivo_contado - efectivo_esperado,
        })

    def _puede_editar(self) -> bool:
        if self.sesion is None:
            return False
        return not bool(self.sesion['cerrada'])

    def guardar_fondo_inicial(self) -> None:
        if not self._puede_editar():
            return
        try:
            monto = float(self.caja_form.fondo_inicial_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Ingrese un monto válido")
            self.refresh()
            return
        self.db.update_caja_fondo_inicial(self.sesion['id'], monto)
        self.refresh()

    def agregar_movimiento(self) -> None:
        if not self._puede_editar():
            return
        data = self.caja_form.get_movimiento_data()

        descripcion = data['descripcion']
        if not descripcion:
            if data['tipo'] == 'retiro':
                # El retiro no necesita explicación como un gasto puntual.
                descripcion = 'Retiro'
            elif data['tipo'] == 'ingreso':
                descripcion = 'Ingreso'
            else:
                messagebox.showerror("Error", "Ingrese una descripción")
                return
        try:
            monto = float(data['monto'])
            if monto <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Ingrese un monto válido")
            return

        # La forma de pago solo aplica a gastos (retiro y bolsillo siempre
        # son "no efectivo desde la caja" o "efectivo", respectivamente,
        # por definición).
        forma_pago = data['forma_pago'] if data['tipo'] == 'gasto' else 'efectivo'

        self.db.add_caja_movimiento(
            self.sesion['id'], data['tipo'], descripcion, monto, forma_pago)
        self.caja_form.clear_movimiento_fields()
        self.refresh()

    def editar_movimiento_seleccionado(self) -> None:
        if not self._puede_editar():
            return
        selected = self.caja_form.tree.selection()
        if not selected:
            return
        movimiento_id = int(selected[0])
        movimientos = self.db.get_caja_movimientos(self.sesion['id'])
        movimiento = next(
            (m for m in movimientos if m['id'] == movimiento_id), None)
        if movimiento is None:
            return
        self.caja_form.show_editar_movimiento_dialog(
            movimiento, self._guardar_edicion_movimiento)

    def _guardar_edicion_movimiento(
            self, movimiento_id: int, descripcion: str, monto: float,
            forma_pago: str) -> None:
        self.db.update_caja_movimiento(
            movimiento_id, descripcion, monto, forma_pago)
        self.refresh()

    def eliminar_movimiento(self) -> None:
        if not self._puede_editar():
            return
        selected = self.caja_form.tree.selection()
        if not selected:
            return
        if not messagebox.askyesno(
                "Confirmar", "¿Eliminar este movimiento?"):
            return
        self.db.delete_caja_movimiento(int(selected[0]))
        self.refresh()

    def abrir_cierre(self) -> None:
        if not self._puede_editar():
            return
        self.caja_form.show_cerrar_dialog(self._efectivo_esperado_actual())

    def _efectivo_esperado_actual(self) -> float:
        movimientos = self.db.get_caja_movimientos(self.sesion['id'])
        ventas = self.db.get_ventas_totales_por_metodo(self.sesion['fecha'])
        return self._calcular_efectivo_esperado(self.sesion, movimientos, ventas)

    def cerrar_caja(self, efectivo_contado: float) -> None:
        self.db.cerrar_caja_sesion(self.sesion['id'], efectivo_contado)
        self.refresh()
