"""Ajustes visuales compartidos."""

import locale

import ttkbootstrap as ttk
from ttkbootstrap.localization import MessageCatalog, initialize_localities


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


def configurar_idioma() -> None:
    """Pone en español los calendarios (nombres de meses y días) y los
    textos propios de ttkbootstrap. Hay que llamarla con la ventana
    principal ya creada."""
    for nombre in ('es_AR', 'es-AR', 'Spanish_Argentina.1252',
                   'Spanish_Spain.1252', 'es_ES', 'es'):
        try:
            locale.setlocale(locale.LC_TIME, nombre)
            break
        except locale.Error:
            continue
    initialize_localities()
    MessageCatalog.locale('es')
    # Los días de la semana del encabezado del calendario no vienen
    # traducidos en el catálogo de ttkbootstrap.
    for en, es in (('Mo', 'Lu'), ('Tu', 'Ma'), ('We', 'Mi'), ('Th', 'Ju'),
                   ('Fr', 'Vi'), ('Sa', 'Sá'), ('Su', 'Do')):
        MessageCatalog.set('es', en, es)


_icono_instalado = False


def instalar_icono_en_dialogos(ico) -> None:
    """Hace que todos los diálogos (Toplevel de ttkbootstrap) lleven el
    ícono de la app en vez del de ttkbootstrap. Se instala una sola vez."""
    global _icono_instalado
    if _icono_instalado or not ico.exists():
        return
    _icono_instalado = True
    original = ttk.Toplevel.__init__

    def con_icono(self, *args, **kwargs):
        original(self, *args, **kwargs)
        try:
            self.iconbitmap(str(ico))
        except Exception:
            pass
    ttk.Toplevel.__init__ = con_icono
