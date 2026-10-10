"""Utilidades de formato compartidas entre vistas, controladores y
servicios de exportación."""

from datetime import datetime

_FORMATOS_FECHA_HORA = (
    '%Y-%m-%d %H:%M:%S.%f',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%dT%H:%M:%S.%f',
    '%Y-%m-%dT%H:%M:%S',
)


def formatear_fecha_hora(fecha) -> str:
    """Convierte una fecha guardada en la base (ISO, con hora) al formato
    argentino 'DD/MM/AAAA HH:MM'. Si viene sin hora, o no matchea ningún
    formato conocido, devuelve el día en 'DD/MM/AAAA' o el texto original."""
    texto = str(fecha)
    for formato in _FORMATOS_FECHA_HORA:
        try:
            dt = datetime.strptime(texto, formato)
            return dt.strftime('%d/%m/%Y %H:%M')
        except ValueError:
            continue
    try:
        dt = datetime.strptime(texto[:10], '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except ValueError:
        return texto


_DIAS_SEMANA = ('Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom')


def texto_dia(fecha_iso: str) -> str:
    """'2026-10-14' -> 'Mié 14/10' (día de la semana en español)."""
    d = datetime.strptime(fecha_iso[:10], '%Y-%m-%d')
    return f"{_DIAS_SEMANA[d.weekday()]} {d.strftime('%d/%m')}"
