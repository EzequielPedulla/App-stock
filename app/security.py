"""Candado de dueño: una sola clave que destapa los montos sensibles.

No hay usuarios ni roles: la app arranca bloqueada, los empleados usan todas
las pestañas pero los totales aparecen tapados, y el dueño pone su clave
para verlos. Se vuelve a bloquear solo tras un rato sin usar la app.

Es un candado de *vista*: no cifra la base de datos."""

import hashlib
import hmac
import os
import time

from .models.database import Database

TAPADO = "$ ••••"
_ITERACIONES = 200_000


def money(valor: float) -> str:
    """Monto con signo $, o tapado si el modo dueño está bloqueado."""
    if not owner_lock.unlocked:
        return TAPADO
    return f"${valor:.2f}"


class OwnerLock:
    CLAVE_CONFIG = 'owner_password'
    AUTOLOCK_SEGUNDOS = 300

    def __init__(self) -> None:
        self._unlocked = False
        self._ultima_actividad = time.time()
        self._listeners = []

    @property
    def unlocked(self) -> bool:
        return self._unlocked

    def on_change(self, callback) -> None:
        """callback() se llama cada vez que se bloquea o desbloquea."""
        self._listeners.append(callback)

    def _notify(self) -> None:
        for cb in list(self._listeners):
            cb()

    # ----- clave -----

    def has_password(self) -> bool:
        return Database().get_config(self.CLAVE_CONFIG) is not None

    @staticmethod
    def _hash(clave: str, sal: bytes) -> str:
        h = hashlib.pbkdf2_hmac(
            'sha256', clave.encode('utf-8'), sal, _ITERACIONES)
        return f"{sal.hex()}${h.hex()}"

    def set_password(self, clave: str) -> None:
        Database().set_config(
            self.CLAVE_CONFIG, self._hash(clave, os.urandom(16)))

    def verify(self, clave: str) -> bool:
        guardado = Database().get_config(self.CLAVE_CONFIG)
        if not guardado:
            return False
        sal_hex, _ = guardado.split('$', 1)
        return hmac.compare_digest(
            guardado, self._hash(clave, bytes.fromhex(sal_hex)))

    # ----- estado -----

    def unlock(self, clave: str) -> bool:
        if not self.verify(clave):
            return False
        self.unlock_after_setup()
        return True

    def unlock_after_setup(self) -> None:
        """Desbloquea (también justo después de crear la clave por primera
        vez)."""
        self.touch()
        if not self._unlocked:
            self._unlocked = True
            self._notify()

    def lock(self) -> None:
        if self._unlocked:
            self._unlocked = False
            self._notify()

    def touch(self) -> None:
        self._ultima_actividad = time.time()

    def segundos_inactivo(self) -> float:
        """Cuánto hace que nadie toca la app (teclado o mouse)."""
        return time.time() - self._ultima_actividad

    def check_autolock(self) -> None:
        if self._unlocked and (
                time.time() - self._ultima_actividad > self.AUTOLOCK_SEGUNDOS):
            self.lock()


owner_lock = OwnerLock()
