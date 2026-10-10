"""Tests de los avisos de pedidos (cartel diario y numerito del menú)."""

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.controllers.pedidos_controller import PedidosController, CLAVE_AVISO
from app.models import database as database_module
from app.models.database import Database

HOY = date(2026, 10, 14)


@pytest.fixture
def ctrl(tmp_path, monkeypatch):
    monkeypatch.setattr(database_module, 'DB_PATH', tmp_path / 'test.db')
    anterior = (Database._instance, Database._connection)
    Database._instance = None
    Database._connection = None
    monkeypatch.setattr(PedidosController, '_hoy', staticmethod(lambda: HOY))
    form = MagicMock()
    form.filtro_combo.get.return_value = 'Pendientes'
    c = PedidosController(form)
    yield c
    c.db.connection.close()
    Database._instance, Database._connection = anterior


def _pedido(c, dias, monto=1000.0, proveedor='Prov'):
    prov = c.db.get_or_create_proveedor(proveedor)
    return c.db.add_pedido(
        prov, (HOY + timedelta(days=dias)).isoformat(), monto)


def test_sin_pedidos_no_hay_aviso_ni_numerito(ctrl):
    assert ctrl.mensaje_aviso() is None
    assert ctrl.contar_urgentes() == 0
    ctrl.mostrar_aviso_diario()
    ctrl.form.show_aviso_dialog.assert_not_called()
    # no marca el día: si después aparece un pedido, todavía puede avisar
    assert ctrl.db.get_config(CLAVE_AVISO) is None


def test_aviso_lista_atrasados_hoy_y_manana_pero_no_lo_lejano(ctrl):
    _pedido(ctrl, -3, 500.0, 'Atrasado SA')
    _pedido(ctrl, 0, 2000.0, 'Hoy SA')
    _pedido(ctrl, 0, 3000.0, 'Hoy 2')
    _pedido(ctrl, 1, 700.0, 'Mañana SA')
    _pedido(ctrl, 5, 9999.0, 'Lejano SA')
    lineas = ctrl.mensaje_aviso()
    assert len(lineas) == 3
    titulos = [linea[0] for linea in lineas]
    assert titulos[0].startswith('⚠ Atrasados') and '1 pedido ' in titulos[0]
    assert 'Hoy: 2 pedidos' in titulos[1] and '$5000.00' in titulos[1]
    assert 'Mañana: 1 pedido' in titulos[2]
    assert 'Lejano SA' not in ' '.join(linea[1] for linea in lineas)
    assert lineas[0][2] is True and lineas[1][2] is False
    # el numerito cuenta atrasados + hoy + mañana
    assert ctrl.contar_urgentes() == 4


def test_pedido_sin_monto_no_dice_cero_pesos(ctrl):
    _pedido(ctrl, 0, 0.0, 'Sin precio')
    assert 'monto sin definir' in ctrl.mensaje_aviso()[0][0]


def test_el_aviso_sale_una_sola_vez_por_dia(ctrl):
    _pedido(ctrl, 0)
    ctrl.mostrar_aviso_diario()
    ctrl.mostrar_aviso_diario()
    assert ctrl.form.show_aviso_dialog.call_count == 1
    assert ctrl.db.get_config(CLAVE_AVISO) == HOY.isoformat()


def test_al_dia_siguiente_vuelve_a_avisar(ctrl, monkeypatch):
    _pedido(ctrl, 0)
    ctrl.mostrar_aviso_diario()
    monkeypatch.setattr(PedidosController, '_hoy',
                        staticmethod(lambda: HOY + timedelta(days=1)))
    ctrl.mostrar_aviso_diario()   # el pedido sigue pendiente: ahora atrasado
    assert ctrl.form.show_aviso_dialog.call_count == 2
    assert ctrl.mensaje_aviso()[0][0].startswith('⚠ Atrasados')


def test_recibidos_y_cancelados_no_avisan(ctrl):
    a = _pedido(ctrl, 0)
    b = _pedido(ctrl, 0)
    ctrl.db.recibir_pedido(a, 100.0, 'efectivo')
    ctrl.db.set_pedido_cancelado(b)
    assert ctrl.mensaje_aviso() is None
    assert ctrl.contar_urgentes() == 0


def test_chequeo_periodico_actualiza_numerito_y_avisa_solo_si_hay_ocio(ctrl):
    cambios = []
    ctrl.on_cambio = cambios.append
    _pedido(ctrl, 0)
    ctrl.chequeo_periodico(ocioso=False)
    assert cambios[-1] == 1                 # numerito al día
    ctrl.form.show_aviso_dialog.assert_not_called()   # no interrumpe
    ctrl.chequeo_periodico(ocioso=True)
    assert ctrl.form.show_aviso_dialog.call_count == 1


def test_chequeo_periodico_refresca_pantalla_si_cambia_el_dia(ctrl, monkeypatch):
    ctrl.form.load_pedidos.reset_mock()
    ctrl.chequeo_periodico(ocioso=False)
    ctrl.form.load_pedidos.assert_not_called()      # mismo día: no repinta
    monkeypatch.setattr(PedidosController, '_hoy',
                        staticmethod(lambda: HOY + timedelta(days=1)))
    ctrl.chequeo_periodico(ocioso=False)
    ctrl.form.load_pedidos.assert_called_once()     # día nuevo: sí


def test_el_aviso_dice_pagos_si_son_servicios_y_distingue_mezclas(ctrl):
    luz = ctrl.db.get_or_create_proveedor('Luz')
    ctrl.db.add_pedido(luz, HOY.isoformat(), 20000.0, tipo='servicio')
    lineas = ctrl.mensaje_aviso()
    assert 'Hoy: 1 pago ' in lineas[0][0] and '🧾 Luz' in lineas[0][1]
    _pedido(ctrl, 0, 1000.0, 'Arcor')
    lineas = ctrl.mensaje_aviso()
    assert '2 pedidos y pagos' in lineas[0][0]
    assert '📦 Arcor' in lineas[0][1] and '🧾 Luz' in lineas[0][1]
