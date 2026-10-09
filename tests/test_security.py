"""Tests del candado de dueño."""

import pytest

from app.models import database as database_module
from app.models.database import Database
from app.security import OwnerLock, TAPADO, money
import app.security as security


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(database_module, 'DB_PATH', tmp_path / 'test.db')
    anterior = (Database._instance, Database._connection)
    Database._instance = None
    Database._connection = None
    base = Database()
    yield base
    base.connection.close()
    Database._instance, Database._connection = anterior


@pytest.fixture
def lock(db, monkeypatch):
    nuevo = OwnerLock()
    monkeypatch.setattr(security, 'owner_lock', nuevo)
    return nuevo


def test_arranca_bloqueado_y_sin_clave(lock):
    assert lock.unlocked is False
    assert lock.has_password() is False


def test_clave_se_guarda_hasheada_y_se_verifica(lock, db):
    lock.set_password('1234')
    guardado = db.get_config(OwnerLock.CLAVE_CONFIG)
    assert '1234' not in guardado
    assert lock.verify('1234') and not lock.verify('0000')


def test_unlock_con_clave_incorrecta_no_desbloquea(lock):
    lock.set_password('1234')
    assert lock.unlock('mal') is False
    assert lock.unlocked is False
    assert lock.unlock('1234') is True
    assert lock.unlocked is True


def test_lock_avisa_a_los_listeners(lock):
    lock.set_password('1234')
    avisos = []
    lock.on_change(lambda: avisos.append(lock.unlocked))
    lock.unlock('1234')
    lock.lock()
    assert avisos == [True, False]


def test_autobloqueo_por_inactividad(lock):
    lock.set_password('1234')
    lock.unlock('1234')
    lock._ultima_actividad -= OwnerLock.AUTOLOCK_SEGUNDOS + 1
    lock.check_autolock()
    assert lock.unlocked is False


def test_actividad_evita_el_autobloqueo(lock):
    lock.set_password('1234')
    lock.unlock('1234')
    lock._ultima_actividad -= OwnerLock.AUTOLOCK_SEGUNDOS - 5
    lock.check_autolock()
    assert lock.unlocked is True


def test_money_tapa_el_monto_si_esta_bloqueado(lock):
    assert money(1500) == TAPADO
    lock.set_password('1234')
    lock.unlock('1234')
    assert money(1500) == "$1500.00"
