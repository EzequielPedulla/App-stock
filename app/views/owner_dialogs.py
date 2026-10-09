"""Diálogos del modo dueño: pedir la clave, crearla y cambiarla."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from ..security import owner_lock
from .cliente_dialogs import _centrar


def _dialogo_clave(parent, titulo: str, subtitulo: str, campos: list,
                   validar) -> bool:
    """Diálogo con uno o más campos de clave. `validar(valores)` devuelve
    None si está bien (se cierra) o un texto de error (queda abierto).
    Enter acepta y Esc cancela. Devuelve True si se aceptó."""
    resultado = {'ok': False}
    dialog = ttk.Toplevel(parent)
    dialog.title(titulo)
    dialog.geometry("580x%d" % (360 + 95 * (len(campos) - 1)))
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    _centrar(dialog)

    main = ttk.Frame(dialog, padding=25)
    main.pack(fill=BOTH, expand=True)
    ttk.Label(main, text=f"🔒 {titulo}", font=("Segoe UI", 20, "bold")
              ).pack(pady=(0, 8))
    ttk.Label(main, text=subtitulo, font=("Segoe UI", 14),
              foreground="#566573", wraplength=520, justify=CENTER
              ).pack(pady=(0, 15))

    entradas = []
    for etiqueta in campos:
        ttk.Label(main, text=etiqueta, font=("Segoe UI", 15)).pack(anchor=W)
        e = ttk.Entry(main, font=("Segoe UI", 16), show="•")
        e.pack(fill=X, pady=(0, 8))
        entradas.append(e)
    entradas[0].focus()

    error = ttk.Label(main, text="", font=("Segoe UI", 14, "bold"),
                      foreground="#c0392b")
    error.pack(pady=(4, 0))

    def aceptar(event=None):
        msg = validar([e.get() for e in entradas])
        if msg:
            error.configure(text=msg)
            entradas[0].delete(0, 'end')
            entradas[0].focus()
            return "break"
        resultado['ok'] = True
        dialog.destroy()
        return "break"

    botones = ttk.Frame(main)
    botones.pack(side=BOTTOM, fill=X)
    ttk.Button(botones, text="Aceptar (Enter)", bootstyle="success",
               command=aceptar).pack(side=RIGHT, padx=(8, 0))
    ttk.Button(botones, text="Cancelar (Esc)", bootstyle="secondary",
               command=dialog.destroy).pack(side=RIGHT)
    dialog.bind('<Return>', aceptar)
    dialog.bind('<Escape>', lambda e: dialog.destroy())
    dialog.wait_window()
    return resultado['ok']


def pedir_clave(parent) -> bool:
    """Desbloquea el modo dueño. La primera vez (todavía no hay clave) la
    hace crear. Devuelve True si quedó desbloqueado."""
    if not owner_lock.has_password():
        guardada = {}

        def validar_nueva(v):
            if len(v[0]) < 4:
                return "La clave tiene que tener al menos 4 caracteres"
            if v[0] != v[1]:
                return "Las dos claves no coinciden"
            guardada['clave'] = v[0]
            return None
        if _dialogo_clave(
                parent, "Crear clave de dueño",
                "Es la primera vez: elegí la clave que va a destapar los "
                "totales y montos. Anotala en un lugar seguro: si la perdés "
                "no se puede recuperar desde la app.",
                ["Nueva clave:", "Repetir la clave:"], validar_nueva):
            owner_lock.set_password(guardada['clave'])
            owner_lock.unlock_after_setup()
            return True
        return False

    def validar(v):
        return None if owner_lock.unlock(v[0]) else "Clave incorrecta"
    return _dialogo_clave(
        parent, "Modo dueño",
        "Ingresá la clave para ver los montos tapados.", ["Clave:"],
        validar)


def ensure_unlocked(parent) -> bool:
    """True si ya está desbloqueado, o si se logró desbloquear."""
    return owner_lock.unlocked or pedir_clave(parent)


def cambiar_clave(parent) -> bool:
    """Cambia la clave (solo con el modo dueño desbloqueado)."""
    if not ensure_unlocked(parent):
        return False
    guardada = {}

    def validar(v):
        if not owner_lock.verify(v[0]):
            return "La clave actual es incorrecta"
        if len(v[1]) < 4:
            return "La clave nueva tiene que tener al menos 4 caracteres"
        if v[1] != v[2]:
            return "Las dos claves nuevas no coinciden"
        guardada['clave'] = v[1]
        return None
    if _dialogo_clave(
            parent, "Cambiar clave", "Escribí la clave actual y la nueva.",
            ["Clave actual:", "Clave nueva:", "Repetir la clave nueva:"],
            validar):
        owner_lock.set_password(guardada['clave'])
        return True
    return False
