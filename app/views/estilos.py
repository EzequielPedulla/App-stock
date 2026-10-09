"""Ajustes visuales compartidos."""

import ttkbootstrap as ttk


def _descendientes(widget):
    for hijo in widget.winfo_children():
        yield hijo
        yield from _descendientes(hijo)


def fix_label_backgrounds(root) -> None:
    """Los ttk.Label sin estilo propio se pintan con fondo blanco aunque
    estén sobre una tarjeta gris (queda un parche blanco detrás del texto).
    Les pone el mismo fondo que el contenedor donde están."""
    estilo = ttk.Style()
    for w in _descendientes(root):
        if w.winfo_class() != 'TLabel':
            continue
        padre = w.nametowidget(w.winfo_parent())
        try:
            if 'style' in padre.keys():
                fondo = estilo.lookup(
                    str(padre.cget('style')) or padre.winfo_class(),
                    'background')
            else:
                fondo = padre.cget('bg')
        except Exception:
            continue
        if fondo:
            w.configure(background=fondo)
