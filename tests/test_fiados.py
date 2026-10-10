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


def test_recibir_pedido_registra_gasto_en_caja_con_el_monto_real(db):
    prov = db.get_or_create_proveedor('Coca-Cola', '1111')
    # El mismo proveedor escrito distinto no se duplica
    assert db.get_or_create_proveedor('  coca-cola ') == prov
    pid = db.add_pedido(prov, '2026-10-14', 50000.0, 'viene a la tarde')
    assert db.get_pedido(pid)['estado'] == 'pendiente'

    assert db.recibir_pedido(pid, 52300.0, 'transferencia') is True
    p = db.get_pedido(pid)
    assert p['estado'] == 'recibido' and p['monto_final'] == 52300.0
    sesion = db._get_or_create_caja_sesion_hoy()
    movs = db.get_caja_movimientos(sesion['id'])
    assert len(movs) == 1
    assert movs[0]['tipo'] == 'gasto' and movs[0]['monto'] == 52300.0
    assert movs[0]['forma_pago'] == 'transferencia'
    assert 'Coca-Cola' in movs[0]['descripcion']
    # No se puede recibir dos veces (no duplica el gasto)
    assert db.recibir_pedido(pid, 1.0, 'efectivo') is None
    assert len(db.get_caja_movimientos(sesion['id'])) == 1


def test_deshacer_recepcion_saca_el_gasto_de_caja(db):
    prov = db.get_or_create_proveedor('Arcor')
    pid = db.add_pedido(prov, '2026-10-14', 1000.0)
    db.recibir_pedido(pid, 900.0, 'efectivo')
    assert db.deshacer_recepcion(pid) is True
    assert db.get_pedido(pid)['estado'] == 'pendiente'
    assert db.get_pedido(pid)['monto_final'] is None
    sesion = db._get_or_create_caja_sesion_hoy()
    assert db.get_caja_movimientos(sesion['id']) == []


def test_recibir_con_caja_cerrada_no_va_a_caja_y_no_se_puede_deshacer(db):
    prov = db.get_or_create_proveedor('Bimbo')
    pid = db.add_pedido(prov, '2026-10-14', 500.0)
    sesion = db._get_or_create_caja_sesion_hoy()
    db.cerrar_caja_sesion(sesion['id'], 0.0)
    assert db.recibir_pedido(pid, 500.0, 'efectivo') is False
    assert db.get_pedido(pid)['estado'] == 'recibido'
    assert db.get_caja_movimientos(sesion['id']) == []
    # Pedido recibido con gasto en caja cerrada: se puede volver a pendiente
    # (no hay gasto que sacar)
    assert db.deshacer_recepcion(pid) is True


def test_cancelar_y_borrar_pedidos(db):
    prov = db.get_or_create_proveedor('Lácteos')
    a = db.add_pedido(prov, '2026-10-14', 100.0)
    b = db.add_pedido(prov, '2026-10-15', 200.0)
    db.set_pedido_cancelado(a)
    assert db.get_pedido(a)['estado'] == 'cancelado'
    assert [p['id'] for p in db.get_pedidos(['pendiente'])] == [b]
    db.recibir_pedido(b, 200.0, 'efectivo')
    assert db.delete_pedido(b) is False   # recibido: no se borra
    assert db.delete_pedido(a) is True


def test_pedido_pagado_del_bolsillo_del_dueno_no_es_gasto_del_negocio(db):
    prov = db.get_or_create_proveedor('Distribuidora')
    pid = db.add_pedido(prov, '2026-10-14', 1000.0)
    assert db.recibir_pedido(pid, 1200.0, 'bolsillo') is True
    assert db.get_pedido(pid)['forma_pago'] == 'bolsillo'
    sesion = db._get_or_create_caja_sesion_hoy()
    movs = db.get_caja_movimientos(sesion['id'])
    assert len(movs) == 1
    # En Caja queda como pago de bolsillo (no como gasto) y sin tocar
    # transferencia: no resta del efectivo ni del resultado del día.
    assert movs[0]['tipo'] == 'bolsillo' and movs[0]['monto'] == 1200.0
    assert movs[0]['forma_pago'] == 'efectivo'
    # y se puede deshacer igual que los demás
    assert db.deshacer_recepcion(pid) is True
    assert db.get_caja_movimientos(sesion['id']) == []


def test_deuda_anterior_del_cuaderno_cuenta_pero_no_es_una_venta(db):
    cid = db.add_cliente('Doña Rosa', saldo_inicial=15000.0)
    c = db.get_cliente(cid)
    assert c['saldo_inicial'] == 15000.0
    assert c['total_fiado'] == 15000.0 and c['saldo'] == 15000.0
    # No es una venta: no hay ventas ni movimientos de caja
    assert db.execute_query("SELECT COUNT(*) n FROM sales")[0]['n'] == 0
    # Una compra fiada nueva se suma a la deuda anterior
    _venta(db, 500.0, 'fiado', cliente_id=cid)
    assert db.get_cliente(cid)['saldo'] == 15500.0
    # El fiado otorgado del período solo cuenta lo nuevo (no el cuaderno)
    r = db.get_resumen_periodo('2026-10-09', '2026-10-09')
    assert r['totales']['fiado'] == 500.0
    # pero lo que nos deben en total sí incluye todo
    assert r['totales']['fiado_pendiente'] == 15500.0


def test_pagar_la_deuda_anterior_entra_a_caja_como_cobro(db):
    cid = db.add_cliente('Don Luis', saldo_inicial=8000.0)
    assert db.add_pago_cliente(cid, 3000.0, 'efectivo') is True
    assert db.get_cliente(cid)['saldo'] == 5000.0
    ses = db._get_or_create_caja_sesion_hoy()
    assert [m['monto'] for m in db.get_caja_movimientos(ses['id'])
            if m['tipo'] == 'cobro'] == [3000.0]


def test_cliente_con_deuda_anterior_no_se_borra_y_se_edita(db):
    cid = db.add_cliente('Marta', saldo_inicial=100.0)
    assert db.delete_cliente(cid) is False
    db.update_cliente(cid, 'Marta', '', '', '', '', None, 250.0)
    assert db.get_cliente(cid)['saldo'] == 250.0


def test_base_vieja_sin_saldo_inicial_se_actualiza(tmp_path, monkeypatch):
    import sqlite3
    ruta = tmp_path / 'vieja.db'
    con = sqlite3.connect(ruta)
    con.executescript("""
        CREATE TABLE clientes (id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL, telefono VARCHAR(30) NOT NULL DEFAULT '',
            dni VARCHAR(20) NOT NULL DEFAULT '', direccion VARCHAR(150) NOT NULL DEFAULT '',
            notas TEXT NOT NULL DEFAULT '', limite REAL NULL,
            activo INTEGER NOT NULL DEFAULT 1, created_at DATETIME NOT NULL);
        INSERT INTO clientes (nombre, created_at) VALUES ('Antiguo', '2026-01-01 10:00:00');
    """)
    con.commit(); con.close()
    monkeypatch.setattr(database_module, 'DB_PATH', ruta)
    anterior = (Database._instance, Database._connection)
    Database._instance = None
    Database._connection = None
    try:
        base = Database()
        c = base.get_clientes()[0]
        assert c['nombre'] == 'Antiguo' and c['saldo_inicial'] == 0 and c['saldo'] == 0
        base.connection.close()
    finally:
        Database._instance, Database._connection = anterior


# ===== Servicios y pagos que se repiten =====

def test_siguiente_vencimiento_semanal_y_mensual(db):
    f = Database._sumar_periodo
    assert f('2026-10-10', 'semanal') == '2026-10-17'
    assert f('2026-10-10', 'mensual') == '2026-11-10'
    assert f('2026-12-15', 'mensual') == '2027-01-15'      # cambia de año
    assert f('2026-01-31', 'mensual') == '2026-02-28'      # mes más corto
    assert f('2028-01-31', 'mensual') == '2028-02-29'      # bisiesto


def test_pagar_un_servicio_mensual_crea_el_del_mes_siguiente(db):
    luz = db.get_or_create_proveedor('Luz')
    pid = db.add_pedido(luz, '2026-10-10', 20000.0, 'cuenta 123',
                        tipo='servicio', repetir='mensual')
    assert db.recibir_pedido(pid, 23500.0, 'transferencia') is True
    pagado = db.get_pedido(pid)
    assert pagado['estado'] == 'recibido' and pagado['siguiente_id']
    sig = db.get_pedido(pagado['siguiente_id'])
    assert sig['estado'] == 'pendiente'
    assert sig['fecha_estimada'] == '2026-11-10'
    assert sig['monto_estimado'] == 23500.0          # lo que se pagó esta vez
    assert sig['tipo'] == 'servicio' and sig['repetir'] == 'mensual'
    assert sig['nota'] == 'cuenta 123' and sig['proveedor'] == 'Luz'
    # En Caja queda como "Pago - Luz" (no "Pedido")
    ses = db._get_or_create_caja_sesion_hoy()
    mov = db.get_caja_movimientos(ses['id'])[0]
    assert mov['descripcion'] == 'Pago - Luz' and mov['tipo'] == 'gasto'


def test_deshacer_el_pago_borra_el_siguiente_que_se_creo_solo(db):
    prov = db.get_or_create_proveedor('Alquiler')
    pid = db.add_pedido(prov, '2026-10-05', 300000.0, tipo='servicio',
                        repetir='mensual')
    db.recibir_pedido(pid, 300000.0, 'efectivo')
    assert len(db.get_pedidos(['pendiente'])) == 1       # el de noviembre
    assert db.deshacer_recepcion(pid) is True
    pendientes = db.get_pedidos(['pendiente'])
    assert [p['id'] for p in pendientes] == [pid]         # solo el original
    # y se puede volver a pagar sin duplicar
    db.recibir_pedido(pid, 310000.0, 'efectivo')
    assert len(db.get_pedidos(['pendiente'])) == 1


def test_pedido_que_no_se_repite_no_crea_siguiente_y_cancelar_corta_la_serie(db):
    prov = db.get_or_create_proveedor('Prov')
    a = db.add_pedido(prov, '2026-10-10', 100.0)               # no se repite
    db.recibir_pedido(a, 100.0, 'efectivo')
    assert db.get_pedidos(['pendiente']) == []
    b = db.add_pedido(prov, '2026-10-10', 100.0, tipo='servicio',
                      repetir='semanal')
    db.set_pedido_cancelado(b)                                  # corta
    assert db.get_pedidos(['pendiente']) == []


def test_semanal_con_pago_de_bolsillo_tambien_repite(db):
    prov = db.get_or_create_proveedor('Limpieza')
    pid = db.add_pedido(prov, '2026-10-12', 5000.0, tipo='servicio',
                        repetir='semanal')
    db.recibir_pedido(pid, 5000.0, 'bolsillo')
    sig = db.get_pedido(db.get_pedido(pid)['siguiente_id'])
    assert sig['fecha_estimada'] == '2026-10-19'


def test_base_con_pedidos_viejos_sin_tipo_se_actualiza(tmp_path, monkeypatch):
    import sqlite3
    ruta = tmp_path / 'vieja2.db'
    con = sqlite3.connect(ruta)
    con.executescript("""
        CREATE TABLE proveedores (id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(100) NOT NULL, telefono VARCHAR(30) NOT NULL DEFAULT '',
            activo INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE pedidos (id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER NOT NULL, fecha_estimada DATE NOT NULL,
            monto_estimado REAL NOT NULL DEFAULT 0, nota VARCHAR(200) NOT NULL DEFAULT '',
            estado VARCHAR(20) NOT NULL DEFAULT 'pendiente', monto_final REAL NULL,
            forma_pago VARCHAR(20) NULL, fecha_recibido DATETIME NULL,
            movimiento_id INTEGER NULL, created_at DATETIME NOT NULL);
        INSERT INTO proveedores (nombre) VALUES ('Viejo');
        INSERT INTO pedidos (proveedor_id, fecha_estimada, monto_estimado, created_at)
            VALUES (1, '2026-10-20', 1000, '2026-10-01 10:00:00');
    """)
    con.commit(); con.close()
    monkeypatch.setattr(database_module, 'DB_PATH', ruta)
    anterior = (Database._instance, Database._connection)
    Database._instance = None
    Database._connection = None
    try:
        base = Database()
        p = base.get_pedidos()[0]
        assert p['tipo'] == 'pedido' and p['repetir'] == 'no'
        assert p['siguiente_id'] is None and p['monto_estimado'] == 1000
        base.connection.close()
    finally:
        Database._instance, Database._connection = anterior
