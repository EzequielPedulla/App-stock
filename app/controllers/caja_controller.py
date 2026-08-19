"""Controlador para el módulo de caja (cierre de caja diario)."""

from typing import Any
from datetime import datetime
from tkinter import messagebox

from ..models.database import Database


class CajaController:
    """Controlador para gestionar el cierre de caja del día."""

    def __init__(self, caja_form: Any) -> None:
        self.caja_form = caja_form
        self.caja_form.caja_controller = self
        self.db = Database()
        self.sesion = None
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

    def _hoy(self) -> str:
        return datetime.now().strftime('%Y-%m-%d')

    def refresh(self) -> None:
        """Carga (o crea) la sesión de caja de hoy y actualiza la pantalla."""
        fecha = self._hoy()
        sesion = self.db.get_caja_sesion_by_fecha(fecha)

        if sesion is None:
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
        sesion = self.sesion
        movimientos = self.db.get_caja_movimientos(sesion['id'])
        ventas = self.db.get_ventas_totales_por_metodo(sesion['fecha'])
        totales = self._totales_movimientos(movimientos)

        fondo_inicial = float(sesion['fondo_inicial'])
        efectivo_esperado = self._calcular_efectivo_esperado(
            sesion, movimientos, ventas)
        resultado_dia = self._calcular_resultado_dia(movimientos, ventas)

        cerrada = bool(sesion['cerrada'])
        efectivo_contado = (
            float(sesion['efectivo_contado'])
            if sesion['efectivo_contado'] is not None else 0.0)

        self.caja_form.load_movimientos(movimientos)
        self.caja_form.update_summary({
            'resultado_dia': resultado_dia,
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
            'efectivo_contado': efectivo_contado,
            'diferencia': efectivo_contado - efectivo_esperado,
        })

    def guardar_fondo_inicial(self) -> None:
        try:
            monto = float(self.caja_form.fondo_inicial_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Ingrese un monto válido")
            self.refresh()
            return
        self.db.update_caja_fondo_inicial(self.sesion['id'], monto)
        self.refresh()

    def agregar_movimiento(self) -> None:
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

    def eliminar_movimiento(self) -> None:
        selected = self.caja_form.tree.selection()
        if not selected:
            return
        if not messagebox.askyesno(
                "Confirmar", "¿Eliminar este movimiento?"):
            return
        self.db.delete_caja_movimiento(int(selected[0]))
        self.refresh()

    def abrir_cierre(self) -> None:
        self.caja_form.show_cerrar_dialog(self._efectivo_esperado_actual())

    def _efectivo_esperado_actual(self) -> float:
        movimientos = self.db.get_caja_movimientos(self.sesion['id'])
        ventas = self.db.get_ventas_totales_por_metodo(self.sesion['fecha'])
        return self._calcular_efectivo_esperado(self.sesion, movimientos, ventas)

    def cerrar_caja(self, efectivo_contado: float) -> None:
        self.db.cerrar_caja_sesion(self.sesion['id'], efectivo_contado)
        self.refresh()
