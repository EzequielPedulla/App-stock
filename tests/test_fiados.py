"""Tests del cuaderno de fiados (clientes, ventas fiadas y pagos)."""

import pytest

from app.models import database as database_module
from app.models.database import Database


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Base de datos temporal y aislada (no toca la base real)."""
    monkeypatch.setattr(database_module, 'DB_PATH', tmp_path / 'test.db')
    anterior = (Database._instance, Database._connection)
    Database._instance = None
    Database._connection = None
    base = Database()
    yield base
    base.connection.close()
    Database._instance, Database._connection = anterior


def _venta(db, total, metodo, payments=None, cliente_id=None):
    sale_id = db.add_sale(
        '2026-10-09 10:00:00', total, 0.0, 0.0, metodo, payments,
        cliente_id=cliente_id)
    return sale_id


def test_fiado_total_suma_al_saldo(db):
    cid = db.add_cliente('Juan Perez', '1111')
    _venta(db, 100.0, 'fiado', cliente_id=cid)
    c = db.get_cliente(cid)
    assert c['total_fiado'] == 100.0
    assert c['saldo'] == 100.0


def test_fiado_parcial_solo_cuenta_la_parte_fiada(db):
    cid = db.add_cliente('Ana')
    _venta(db, 100.0, 'mixto', [
        {'method': 'efectivo', 'amount': 40.0},
        {'method': 'fiado', 'amount': 60.0}], cliente_id=cid)
    assert db.get_cliente(cid)['saldo'] == 60.0
    # Caja: la parte fiada se reparte como fiado, el resto como efectivo
    totales = db.get_ventas_totales_por_metodo('2026-10-09')
    assert totales['efectivo'] == 40.0
    assert totales['fiado'] == 60.0


def test_pago_parcial_baja_la_deuda_y_entra_en_caja(db):
    cid = db.add_cliente('Luis')
    _venta(db, 100.0, 'fiado', cliente_id=cid)
    assert db.add_pago_cliente(cid, 60.0, 'efectivo') is True
    assert db.get_cliente(cid)['saldo'] == 40.0
    sesion = db._get_or_create_caja_sesion_hoy()
    movs = db.get_caja_movimientos(sesion['id'])
    assert len(movs) == 1
    assert movs[0]['tipo'] == 'cobro' and movs[0]['monto'] == 60.0


def test_venta_anulada_no_cuenta_en_la_deuda(db):
    cid = db.add_cliente('Marta')
    sale_id = _venta(db, 80.0, 'fiado', cliente_id=cid)
    db.connection.commit()
    assert db.cancel_sale(sale_id)
    assert db.get_cliente(cid)['saldo'] == 0.0


def test_anular_pago_vuelve_a_subir_la_deuda_y_saca_el_cobro(db):
    cid = db.add_cliente('Pedro')
    _venta(db, 50.0, 'fiado', cliente_id=cid)
    db.add_pago_cliente(cid, 50.0, 'transferencia')
    pago = db.get_pagos_cliente(cid)[0]
    assert db.delete_pago_cliente(pago['id']) is True
    assert db.get_cliente(cid)['saldo'] == 50.0
    sesion = db._get_or_create_caja_sesion_hoy()
    assert db.get_caja_movimientos(sesion['id']) == []


def test_pago_con_caja_cerrada_baja_deuda_pero_no_va_a_caja(db):
    cid = db.add_cliente('Rosa')
    _venta(db, 30.0, 'fiado', cliente_id=cid)
    sesion = db._get_or_create_caja_sesion_hoy()
    db.cerrar_caja_sesion(sesion['id'], 0.0)
    assert db.add_pago_cliente(cid, 10.0) is False
    assert db.get_cliente(cid)['saldo'] == 20.0
    assert db.get_caja_movimientos(sesion['id']) == []


def test_busqueda_y_filtro_con_deuda(db):
    a = db.add_cliente('Carlos Gomez', '2222', '30111222')
    db.add_cliente('Beatriz Lopez')
    _venta(db, 10.0, 'fiado', cliente_id=a)
    assert [c['nombre'] for c in db.get_clientes('gomez')] == ['Carlos Gomez']
    assert [c['nombre'] for c in db.get_clientes('30111')] == ['Carlos Gomez']
    assert [c['nombre'] for c in db.get_clientes(solo_con_deuda=True)] == [
        'Carlos Gomez']
    # Los que más deben, primero
    assert db.get_clientes()[0]['nombre'] == 'Carlos Gomez'


def test_eliminar_cliente_con_historial_no_se_borra(db):
    cid = db.add_cliente('Zoe')
    _venta(db, 10.0, 'fiado', cliente_id=cid)
    assert db.delete_cliente(cid) is False
    sin_historial = db.add_cliente('Nadie')
    assert db.delete_cliente(sin_historial) is True


def test_resumen_periodo_suma_los_dias_con_la_logica_de_caja(db):
    cid = db.add_cliente('Ana')
    # Día 1: 100 efectivo, y una venta fiada de 60 (40 efectivo + 60 fiado)
    db.add_sale('2026-10-01 10:00:00', 100.0, 100.0, 0.0, 'efectivo')
    db.add_sale('2026-10-01 11:00:00', 100.0, 40.0, 0.0, 'mixto', [
        {'method': 'efectivo', 'amount': 40.0},
        {'method': 'fiado', 'amount': 60.0}], cliente_id=cid)
    # Día 3: una venta por transferencia y una anulada que no cuenta
    db.add_sale('2026-10-03 09:00:00', 50.0, 50.0, 0.0, 'transferencia')
    anulada = db.add_sale('2026-10-03 09:30:00', 999.0, 999.0, 0.0, 'efectivo')
    db.connection.commit()
    db.cancel_sale(anulada)
    # Caja del día 1: un gasto y un cobro de fiado
    db.create_caja_sesion('2026-10-01', 0.0)
    ses = db.get_caja_sesion_by_fecha('2026-10-01')
    db.add_caja_movimiento(ses['id'], 'gasto', 'Luz', 30.0, 'efectivo')
    db.add_caja_movimiento(ses['id'], 'cobro', 'Cobro', 20.0, 'efectivo')
    # Fuera del rango: no tiene que contarse
    db.add_sale('2026-10-09 10:00:00', 500.0, 500.0, 0.0, 'efectivo')
    db.connection.commit()

    r = db.get_resumen_periodo('2026-10-01', '2026-10-03')
    t = r['totales']
    assert t['dias'] == 3 and len(r['dias']) == 3
    assert t['efectivo'] == 140.0 and t['transferencia'] == 50.0
    assert t['fiado'] == 60.0
    assert t['cobros'] == 20.0 and t['gastos'] == 30.0
    assert t['vendido'] == 140.0 + 50.0 + 20.0
    assert t['resultado'] == t['vendido'] - 30.0
    assert t['ventas'] == 3
    assert t['ticket_promedio'] == pytest.approx((100 + 100 + 50) / 3)
    # El día sin movimientos igual aparece, en cero
    assert r['dias'][1]['fecha'] == '2026-10-02' and r['dias'][1]['vendido'] == 0


def test_busqueda_ignora_tildes_y_mayusculas(db):
    db.add_cliente('José Ángel Pérez')
    assert [c['nombre'] for c in db.get_clientes('jose angel')] == [
        'José Ángel Pérez']
    assert [c['nombre'] for c in db.get_clientes('PEREZ')] == [
        'José Ángel Pérez']


def test_cambiar_metodo_de_pago_a_fiado_asigna_cliente_y_sacarlo_lo_borra(db):
    cid = db.add_cliente('Luz')
    sale_id = db.add_sale('2026-10-09 10:00:00', 70.0, 70.0, 0.0, 'efectivo')
    db.connection.commit()
    db.update_sale_payment_method(sale_id, 'fiado', cid)
    assert db.get_cliente(cid)['saldo'] == 70.0
    db.update_sale_payment_method(sale_id, 'efectivo')
    assert db.get_cliente(cid)['saldo'] == 0.0
    fila = db.execute_query("SELECT cliente_id FROM sales WHERE id = ?", (sale_id,))
    assert fila[0]['cliente_id'] is None
