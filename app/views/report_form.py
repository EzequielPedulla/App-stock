import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from datetime import date, datetime, timedelta
import tkinter as tk

from ..utils import formatear_fecha_hora
from ..security import owner_lock, money
from .owner_dialogs import ensure_unlocked
from .cliente_dialogs import show_cliente_picker

METODO_PAGO_LABELS = {
    'efectivo': 'Efectivo',
    'transferencia': 'Transferencia',
    'posnet': 'Posnet',
    'fiado': 'Fiado',
    'mixto': 'Mixto',
}


class ReportForm(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.pack(fill=BOTH, expand=True)
        self.report_controller = None  # Se establecerá desde el controlador
        self._ventas = []  # Última lista completa recibida, para filtrar sin ir a la base
        self._filtro_metodo = 'todos'
        # Día que se está mirando en el historial ('YYYY-MM-DD').
        self._dia_filtro = self._hoy_str()
        self._create_widgets()

    # ===== Resumen por período: cálculo general entre dos fechas =====

    def _create_periodo_section(self) -> None:
        card = ttk.Frame(self, bootstyle="light", padding=20)
        card.pack(fill=X, pady=(0, 20))

        ttk.Label(card, text="📅 Resumen por período",
                  font=("Segoe UI", 20, "bold")).pack(anchor=W)
        ttk.Label(card, text="Elegí desde qué día hasta qué día y se calcula "
                  "todo junto (mismo criterio que Caja).",
                  font=("Segoe UI", 14), foreground="#566573"
                  ).pack(anchor=W, pady=(2, 12))

        # --- fechas y atajos ---
        fila = ttk.Frame(card, bootstyle="light")
        fila.pack(fill=X, pady=(0, 12))
        ttk.Label(fila, text="Desde:", font=("Segoe UI", 16, "bold")
                  ).pack(side=LEFT, padx=(0, 6))
        self._desde_var = tk.StringVar()
        self.desde_entry = ttk.DateEntry(
            fila, dateformat='%d/%m/%Y', width=11, bootstyle="primary",
            firstweekday=0)
        self.desde_entry.entry.configure(
            textvariable=self._desde_var, font=("Segoe UI", 16))
        self.desde_entry.pack(side=LEFT, padx=(0, 18))
        ttk.Label(fila, text="Hasta:", font=("Segoe UI", 16, "bold")
                  ).pack(side=LEFT, padx=(0, 6))
        self._hasta_var = tk.StringVar()
        self.hasta_entry = ttk.DateEntry(
            fila, dateformat='%d/%m/%Y', width=11, bootstyle="primary",
            firstweekday=0)
        self.hasta_entry.entry.configure(
            textvariable=self._hasta_var, font=("Segoe UI", 16))
        self.hasta_entry.pack(side=LEFT, padx=(0, 18))

        ttk.Button(
            fila, text="📊 Exportar Excel", bootstyle="success",
            command=self._on_export_periodo
        ).pack(side=RIGHT)

        atajos = ttk.Frame(card, bootstyle="light")
        atajos.pack(fill=X, pady=(0, 12))
        for texto, rango in (("Hoy", 'hoy'), ("Ayer", 'ayer'),
                             ("Esta semana", 'semana'),
                             ("Este mes", 'mes'),
                             ("Mes pasado", 'mes_pasado')):
            ttk.Button(
                atajos, text=texto, bootstyle="secondary-outline",
                command=lambda r=rango: self._set_atajo_periodo(r)
            ).pack(side=LEFT, padx=(0, 8))

        self.periodo_aviso = ttk.Label(
            card, text="", font=("Segoe UI", 14, "bold"),
            foreground="#c0392b")
        self.periodo_aviso.pack(anchor=W)

        # --- tarjetas con los números principales ---
        tarjetas = ttk.Frame(card, bootstyle="light")
        tarjetas.pack(fill=X, pady=(0, 10))
        self.periodo_labels = {}
        for clave, titulo, estilo in (
                ('vendido', "Total vendido", "success"),
                ('gastos', "Gastos", "danger"),
                ('resultado', "Resultado", "primary"),
                ('ventas', "Ventas realizadas", "info")):
            t = ttk.Frame(tarjetas, padding=12)
            t.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
            ttk.Label(t, text=titulo, font=("Segoe UI", 15)).pack(anchor=W)
            lbl = ttk.Label(t, text="—", font=("Segoe UI", 25, "bold"),
                            bootstyle=estilo)
            lbl.pack(anchor=W)
            self.periodo_labels[clave] = lbl
        self.periodo_ticket_label = ttk.Label(
            card, text="", font=("Segoe UI", 15), foreground="#2c3e50")
        self.periodo_detalle_label = ttk.Label(
            card, text="", font=("Segoe UI", 15), justify=LEFT,
            foreground="#2c3e50")
        self.periodo_detalle_label.pack(anchor=W, pady=(4, 0))
        self.periodo_ticket_label.pack(anchor=W, pady=(2, 10))

        # --- tablas: día por día y productos del período ---
        tablas = ttk.Frame(card, bootstyle="light")
        tablas.pack(fill=X)

        izq = ttk.Frame(tablas, bootstyle="light")
        izq.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 12))
        ttk.Label(izq, text="Día por día", font=("Segoe UI", 18, "bold"),
                  foreground="#2c3e50").pack(anchor=W, pady=(0, 6))
        cols = ("fecha", "ventas", "vendido", "gastos", "resultado")
        self.periodo_dias_tree = ttk.Treeview(
            izq, columns=cols, show="headings", height=7)
        for col, texto, ancho in (("fecha", "Fecha", 130),
                                  ("ventas", "Ventas", 90),
                                  ("vendido", "Vendido", 140),
                                  ("gastos", "Gastos", 130),
                                  ("resultado", "Resultado", 150)):
            self.periodo_dias_tree.heading(col, text=texto, anchor="center")
            self.periodo_dias_tree.column(col, width=ancho, anchor="center")
        sb = ttk.Scrollbar(izq, orient=VERTICAL,
                           command=self.periodo_dias_tree.yview)
        self.periodo_dias_tree.configure(yscrollcommand=sb.set)
        self.periodo_dias_tree.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=LEFT, fill=Y)

        der = ttk.Frame(tablas, bootstyle="light")
        der.pack(side=LEFT, fill=BOTH, expand=True)
        ttk.Label(der, text="Productos más vendidos",
                  font=("Segoe UI", 18, "bold"), foreground="#2c3e50"
                  ).pack(anchor=W, pady=(0, 6))
        self.periodo_prod_tree = ttk.Treeview(
            der, columns=("producto", "cantidad"), show="headings", height=7)
        self.periodo_prod_tree.heading("producto", text="Producto",
                                       anchor="center")
        self.periodo_prod_tree.heading("cantidad", text="Unidades",
                                       anchor="center")
        self.periodo_prod_tree.column("producto", width=260, anchor="w")
        self.periodo_prod_tree.column("cantidad", width=110, anchor="center")
        self.periodo_prod_tree.pack(fill=BOTH, expand=True)
        self.periodo_dias_tree.tag_configure('cero', foreground='#7f8c8d')

        self._periodo_bloqueado = False
        self._set_atajo_periodo('mes')
        for var in (self._desde_var, self._hasta_var):
            var.trace_add('write', lambda *a: self._actualizar_periodo())

    def _fechas_periodo(self):
        """(desde, hasta) como date, o None si alguna no es válida."""
        try:
            return (datetime.strptime(self._desde_var.get(), '%d/%m/%Y').date(),
                    datetime.strptime(self._hasta_var.get(), '%d/%m/%Y').date())
        except ValueError:
            return None

    def _set_atajo_periodo(self, rango: str) -> None:
        hoy = date.today()
        if rango == 'hoy':
            d1 = d2 = hoy
        elif rango == 'ayer':
            d1 = d2 = hoy - timedelta(days=1)
        elif rango == 'semana':
            d1, d2 = hoy - timedelta(days=hoy.weekday()), hoy
        elif rango == 'mes_pasado':
            d2 = hoy.replace(day=1) - timedelta(days=1)
            d1 = d2.replace(day=1)
        else:
            d1, d2 = hoy.replace(day=1), hoy
        # Se cambia todo junto y se calcula una sola vez al final (si no,
        # cada campo dispararía su propio cálculo con fechas a medias).
        self._periodo_pausa = True
        for entry, d in ((self.desde_entry.entry, d1),
                         (self.hasta_entry.entry, d2)):
            entry.delete(0, 'end')
            entry.insert(0, d.strftime('%d/%m/%Y'))
        self._periodo_pausa = False
        self._actualizar_periodo()

    def _actualizar_periodo(self) -> None:
        """Calcula y muestra el resumen del rango de fechas elegido. Con el
        modo dueño bloqueado los montos aparecen tapados."""
        if getattr(self, '_periodo_pausa', False) or not self.report_controller:
            return
        fechas = self._fechas_periodo()
        for tree in (self.periodo_dias_tree, self.periodo_prod_tree):
            for i in tree.get_children():
                tree.delete(i)
        if fechas is None:
            self.periodo_aviso.configure(text="Fecha inválida (usá DD/MM/AAAA)")
            return
        d1, d2 = fechas
        if d1 > d2:
            self.periodo_aviso.configure(
                text="⚠ La fecha \"Desde\" es posterior a \"Hasta\".")
            return
        self.periodo_aviso.configure(text="")

        r = self.report_controller.get_resumen_periodo(
            d1.isoformat(), d2.isoformat())
        t = r['totales']
        self.periodo_labels['vendido'].configure(text=money(t['vendido']))
        self.periodo_labels['gastos'].configure(text=money(t['gastos']))
        self.periodo_labels['resultado'].configure(
            text=money(t['resultado']),
            bootstyle=("success" if t['resultado'] >= 0 else "danger")
            if owner_lock.unlocked else "secondary")
        self.periodo_labels['ventas'].configure(text=str(int(t['ventas'])))
        self.periodo_detalle_label.configure(
            text=f"Efectivo {money(t['efectivo'])}  ·  "
                 f"Transferencia {money(t['transferencia'])}  ·  "
                 f"Posnet {money(t['posnet'])}  ·  "
                 f"Cobros de fiados {money(t['cobros'])}\n"
                 f"Fiado otorgado {money(t['fiado'])}  ·  "
                 f"Fiado pendiente (total hoy) {money(t['fiado_pendiente'])}  ·  "
                 f"Retiros {money(t['retiros'])}")
        dias_txt = "1 día" if t['dias'] == 1 else f"{t['dias']} días"
        extra = ""
        if owner_lock.unlocked:
            con_ventas = [x for x in r['dias'] if x['vendido'] > 0]
            if len(con_ventas) >= 2:
                mejor = max(con_ventas, key=lambda x: x['vendido'])
                peor = min(con_ventas, key=lambda x: x['vendido'])
                extra = (f"  ·  Mejor día: {self._texto_dia(mejor['fecha'])} "
                         f"({money(mejor['vendido'])})  ·  Peor día: "
                         f"{self._texto_dia(peor['fecha'])} "
                         f"({money(peor['vendido'])})")
        self.periodo_ticket_label.configure(
            text=f"Período de {dias_txt}  ·  Ticket promedio "
                 f"{money(t['ticket_promedio'])}{extra}")

        for x in r['dias']:
            self.periodo_dias_tree.insert('', END, values=(
                datetime.strptime(x['fecha'], '%Y-%m-%d').strftime('%d/%m/%Y'),
                x['ventas'], money(x['vendido']), money(x['gastos']),
                money(x['resultado'])),
                tags=('cero',) if x['ventas'] == 0 and x['vendido'] == 0
                else ())
        if owner_lock.unlocked:
            for p in r['productos']:
                self.periodo_prod_tree.insert('', END, values=(
                    p['producto'], int(p['cantidad'])))
            if not r['productos']:
                self.periodo_prod_tree.insert(
                    '', END, values=("Sin ventas en el período", ""))
        else:
            self.periodo_prod_tree.insert(
                '', END, values=("🔒 Bloqueado (Modo dueño)", ""))

    def _on_export_periodo(self) -> None:
        fechas = self._fechas_periodo()
        if fechas is None or fechas[0] > fechas[1]:
            messagebox.showwarning(
                "Fechas", "Revisá las fechas elegidas antes de exportar.")
            return
        if self.report_controller and ensure_unlocked(self):
            self.report_controller.export_period_summary_to_excel(
                fechas[0].isoformat(), fechas[1].isoformat())

    def _hoy_str(self) -> str:
        return datetime.now().strftime('%Y-%m-%d')

    def _create_widgets(self):
        # Título y botones de exportación
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=X, pady=(0, 20))

        ttk.Label(
            header_frame,
            text="Reportes",
            font=("Segoe UI", 27, "bold")
        ).pack(side=LEFT, anchor=W)

        # Frame para botones de exportación
        export_buttons_frame = ttk.Frame(header_frame)
        export_buttons_frame.pack(side=RIGHT)

        # Botón: Exportar Reporte PDF
        ttk.Button(
            export_buttons_frame,
            text="📊 Reporte PDF",
            bootstyle="info",
            command=self._on_export_pdf_report,
            width=18
        ).pack(side=LEFT, padx=5)

        # Botón: Exportar Ventas Excel
        ttk.Button(
            export_buttons_frame,
            text="📈 Ventas Excel",
            bootstyle="success",
            command=self._on_export_sales_excel,
            width=18
        ).pack(side=LEFT, padx=5)

        # Botón: Exportar Inventario Excel
        ttk.Button(
            export_buttons_frame,
            text="📦 Inventario Excel",
            bootstyle="success",
            command=self._on_export_inventory_excel,
            width=18
        ).pack(side=LEFT, padx=5)

        self._create_periodo_section()

        # Container para las cards superiores
        top_cards = ttk.Frame(self)
        top_cards.pack(fill=X, pady=(0, 20))

        # Card: Total de ventas del día elegido (misma lógica que Caja: no
        # cuenta fiado, todavía no se cobró esa plata).
        card_total = ttk.Frame(top_cards, bootstyle="light", padding=20)
        card_total.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        self.card_total_titulo = ttk.Label(
            card_total,
            text="Total de ventas",
            font=("Segoe UI", 16)
        )
        self.card_total_titulo.pack(anchor=W)

        self.label_total_ventas = ttk.Label(
            card_total,
            text="$0",
            font=("Segoe UI", 31, "bold"),
            bootstyle="success"
        )
        self.label_total_ventas.pack(anchor=W, pady=(10, 0))

        # Card: Cantidad de ventas del día elegido (mismo criterio: no
        # cuenta fiado).
        card_cantidad = ttk.Frame(top_cards, bootstyle="light", padding=20)
        card_cantidad.pack(side=RIGHT, fill=BOTH, expand=True, padx=(10, 0))

        self.card_cantidad_titulo = ttk.Label(
            card_cantidad,
            text="Cantidad de ventas",
            font=("Segoe UI", 16)
        )
        self.card_cantidad_titulo.pack(anchor=W)

        self.label_cantidad_ventas = ttk.Label(
            card_cantidad,
            text="0",
            font=("Segoe UI", 31, "bold"),
            bootstyle="info"
        )
        self.label_cantidad_ventas.pack(anchor=W, pady=(10, 0))

        # Container del historial
        bottom_container = ttk.Frame(self)
        bottom_container.pack(fill=BOTH, expand=True)

        # Card: Historial de ventas (tabla)
        card_tabla = ttk.Frame(bottom_container, bootstyle="light", padding=20)
        card_tabla.pack(side=TOP, fill=BOTH, expand=True)

        # ===== Navegación por día: el historial se ve un día a la vez
        # (arranca en hoy), con flechas para ir para atrás/adelante. =====
        dia_nav_row = ttk.Frame(card_tabla)
        dia_nav_row.pack(fill=X, pady=(0, 10))

        self.dia_anterior_button = ttk.Button(
            dia_nav_row, text="◀ Día anterior", bootstyle="secondary",
            width=14, command=self._ir_dia_anterior)
        self.dia_anterior_button.pack(side=LEFT)
        self.dia_label = ttk.Label(
            dia_nav_row, text="Hoy", font=("Segoe UI", 16, "bold"))
        self.dia_label.pack(side=LEFT, padx=15)
        self.dia_siguiente_button = ttk.Button(
            dia_nav_row, text="Día siguiente ▶", bootstyle="secondary",
            width=14, command=self._ir_dia_siguiente)
        self.dia_siguiente_button.pack(side=LEFT)
        self.volver_hoy_button = ttk.Button(
            dia_nav_row, text="Volver a hoy", bootstyle="info", width=12,
            command=self._volver_a_hoy)
        # Se muestra/oculta según el día (ver _actualizar_dia_label).

        # ===== Resumen de ventas por método de pago del día: cuenta
        # cuántos pagos se hicieron con cada método y cuánto sumaron, con
        # la misma lógica que Caja (una venta con pago dividido se reparte
        # entre los métodos reales que la componen), para que los números
        # de las dos pantallas siempre coincidan. =====
        resumen_metodos_row = ttk.Frame(card_tabla)
        resumen_metodos_row.pack(fill=X, pady=(0, 15))

        self.resumen_metodo_labels = {}
        for metodo in ('efectivo', 'transferencia', 'posnet', 'fiado'):
            card = ttk.Frame(resumen_metodos_row, bootstyle="light", padding=10)
            card.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 8))
            ttk.Label(
                card, text=METODO_PAGO_LABELS[metodo],
                font=("Segoe UI", 13, "bold")
            ).pack(anchor=W)
            lbl = ttk.Label(card, text="0 pagos — $0.00", font=("Segoe UI", 13))
            lbl.pack(anchor=W, pady=(4, 0))
            self.resumen_metodo_labels[metodo] = lbl

        tabla_header = ttk.Frame(card_tabla)
        tabla_header.pack(fill=X, pady=(0, 15))

        ttk.Label(
            tabla_header,
            text="Historial de ventas",
            font=("Segoe UI", 18, "bold")
        ).pack(side=LEFT)

        filtro_frame = ttk.Frame(tabla_header)
        filtro_frame.pack(side=RIGHT)
        ttk.Label(
            filtro_frame, text="Método de pago:", font=("Segoe UI", 14)
        ).pack(side=LEFT, padx=(0, 8))
        self.filtro_metodo_combo = ttk.Combobox(
            filtro_frame, state="readonly", width=16, font=("Segoe UI", 14),
            values=["Todos", "Efectivo", "Transferencia", "Posnet", "Fiado",
                    "Mixto"])
        self.filtro_metodo_combo.current(0)
        self.filtro_metodo_combo.pack(side=LEFT)
        self.filtro_metodo_combo.bind(
            '<<ComboboxSelected>>', self._on_filtro_metodo_changed)

        # Configurar estilo para la tabla de ventas
        style = ttk.Style()
        style.configure(
            "Ventas.Treeview",
            rowheight=46,
            font=('Segoe UI', 15)
        )
        style.configure(
            "Ventas.Treeview.Heading",
            font=('Segoe UI', 16, 'bold')
        )

        # Frame para la tabla con scrollbar
        table_container = ttk.Frame(card_tabla)
        table_container.pack(fill=BOTH, expand=True)

        # Tabla de ventas (fecha, método de pago y total; el ID global va
        # oculto)
        columns = ("id", "fecha", "metodo", "total")
        self.tabla_ventas = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            height=15,
            style="Ventas.Treeview"
        )

        # Ocultar la columna ID pero mantenerla para referencia
        self.tabla_ventas.heading("id", text="ID")
        self.tabla_ventas.column("id", width=0, stretch=False)

        self.tabla_ventas.heading("fecha", text="Fecha", anchor=W)
        self.tabla_ventas.heading("metodo", text="Método de pago", anchor=CENTER)
        self.tabla_ventas.heading("total", text="Total", anchor=E)

        self.tabla_ventas.column("fecha", width=190, anchor=W)
        self.tabla_ventas.column("metodo", width=168, anchor=CENTER)
        self.tabla_ventas.column("total", width=123, anchor=E)

        # Colores alternados
        self.tabla_ventas.tag_configure('evenrow', background='#ecf0f1')
        self.tabla_ventas.tag_configure('oddrow', background='white')

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            table_container, orient=VERTICAL, command=self.tabla_ventas.yview)
        self.tabla_ventas.configure(yscrollcommand=scrollbar.set)

        self.tabla_ventas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        self._actualizar_dia_label()

    def _ir_dia_anterior(self) -> None:
        fecha = datetime.strptime(self._dia_filtro, '%Y-%m-%d') - timedelta(days=1)
        self._dia_filtro = fecha.strftime('%Y-%m-%d')
        self._actualizar_dia_label()
        self._render_ventas()

    def _ir_dia_siguiente(self) -> None:
        if self._dia_filtro >= self._hoy_str():
            return
        fecha = datetime.strptime(self._dia_filtro, '%Y-%m-%d') + timedelta(days=1)
        self._dia_filtro = fecha.strftime('%Y-%m-%d')
        self._actualizar_dia_label()
        self._render_ventas()

    def _volver_a_hoy(self) -> None:
        self._dia_filtro = self._hoy_str()
        self._actualizar_dia_label()
        self._render_ventas()

    def _texto_dia(self, fecha_str: str) -> str:
        es_hoy = fecha_str == self._hoy_str()
        anio, mes, dia = fecha_str.split('-')
        return f"Hoy ({dia}/{mes})" if es_hoy else f"{dia}/{mes}/{anio}"

    def _actualizar_dia_label(self) -> None:
        """Actualiza el texto del día mostrado y si tiene sentido seguir
        avanzando (no se puede ir más adelante que hoy)."""
        es_hoy = self._dia_filtro == self._hoy_str()
        self.dia_label.configure(text=self._texto_dia(self._dia_filtro))
        self.dia_siguiente_button.configure(
            state='disabled' if es_hoy else 'normal')
        if es_hoy:
            self.volver_hoy_button.pack_forget()
        else:
            self.volver_hoy_button.pack(side=LEFT, padx=(15, 0))

    def _actualizar_resumen_dia(self) -> None:
        """Total vendido y cantidad de ventas del día elegido, con la
        misma lógica que usa Caja (no cuenta fiado en el total vendido),
        para que las dos pantallas siempre coincidan."""
        if not self.report_controller:
            return
        resumen = self.report_controller.get_resumen_dia(self._dia_filtro)
        dia_texto = self._texto_dia(self._dia_filtro)
        self.label_total_ventas.configure(
            text=(f"${resumen['total_ventas']:,.2f}"
                  if owner_lock.unlocked else money(0)))
        self.card_total_titulo.configure(text=f"Total de ventas — {dia_texto}")
        cantidad = resumen['cantidad_ventas']
        self.label_cantidad_ventas.configure(text=f"{cantidad}")
        self.card_cantidad_titulo.configure(
            text=f"Cantidad de ventas — {dia_texto}")

    def update_data(self, ultimas_ventas=None):
        """Actualiza los datos mostrados en los reportes"""

        # Guardar la lista completa para poder filtrar sin volver a consultar
        self._ventas = ultimas_ventas or []
        self._render_ventas()
        self._actualizar_periodo()

    def _ventas_del_dia_filtrado(self) -> list:
        """Ventas que corresponden al día elegido en la navegación."""
        return [
            v for v in self._ventas
            if str(v['date'])[:10] == self._dia_filtro]

    def _render_ventas(self) -> None:
        """Vuelca en la tabla las ventas del día elegido que además
        coincidan con el filtro de método de pago, y actualiza el resumen
        por método (que ignora ese filtro: siempre muestra los cuatro,
        para poder compararlos)."""
        for item in self.tabla_ventas.get_children():
            self.tabla_ventas.delete(item)

        ventas_dia = self._ventas_del_dia_filtrado()

        if self._filtro_metodo == 'todos':
            ventas = ventas_dia
        else:
            ventas = [
                v for v in ventas_dia
                if v.get('payment_method', 'efectivo') == self._filtro_metodo]

        for i, venta in enumerate(ventas):
            fecha_str = formatear_fecha_hora(venta['date'])

            metodo_texto = METODO_PAGO_LABELS.get(
                venta.get('payment_method', 'efectivo'), 'Efectivo')

            # Determinar el tag según el estado
            status = venta.get('status', 'active')
            if status == 'cancelled':
                tag = 'cancelled'
                total_text = f"${venta['total']:.2f} [ANULADA]"
            else:
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                total_text = f"${venta['total']:.2f}"

            self.tabla_ventas.insert(
                "", END,
                values=(venta['id'], fecha_str, metodo_texto, total_text),
                tags=(tag,)
            )

        # Configurar estilo para ventas anuladas
        self.tabla_ventas.tag_configure(
            'cancelled', background='#ffcccc', foreground='#cc0000')

        self._actualizar_resumen_metodos()
        self._actualizar_resumen_dia()

    def _actualizar_resumen_metodos(self) -> None:
        """Cuenta cuántos pagos se hicieron con cada método y cuánto
        sumaron, para el día elegido. Se pide al controlador (que usa la
        misma consulta que Caja) en vez de calcularlo acá con los datos en
        caché, para que una venta con pago dividido ('mixto') se reparta
        entre los métodos reales que la componen y los números de las dos
        pantallas coincidan siempre."""
        if not self.report_controller:
            return
        resumen = self.report_controller.get_resumen_metodos(self._dia_filtro)
        for metodo, label in self.resumen_metodo_labels.items():
            c = resumen.get(metodo, {'cantidad': 0, 'total': 0.0})
            cantidad = c['cantidad']
            texto_cant = "1 pago" if cantidad == 1 else f"{cantidad} pagos"
            label.configure(text=f"{texto_cant} — {money(c['total'])}")

    def _on_filtro_metodo_changed(self, event=None) -> None:
        texto = self.filtro_metodo_combo.get()
        etiqueta_a_valor = {v: k for k, v in METODO_PAGO_LABELS.items()}
        self._filtro_metodo = etiqueta_a_valor.get(texto, 'todos')
        self._render_ventas()

    def show_sale_detail(self, sale_id, sale_date, sale_total,
                          payment_method, details):
        """Muestra una ventana con el detalle de la venta"""
        # Crear ventana modal
        detail_window = ttk.Toplevel(self)
        detail_window.title(f"Detalle de Venta N° {sale_id}")
        detail_window.geometry("1052x896")
        detail_window.resizable(False, False)
        detail_window.transient(self)
        detail_window.grab_set()

        # Centrar la ventana
        detail_window.update_idletasks()
        width = detail_window.winfo_width()
        height = detail_window.winfo_height()
        x = (detail_window.winfo_screenwidth() // 2) - (width // 2)
        y = (detail_window.winfo_screenheight() // 2) - (height // 2)
        detail_window.geometry(f'{width}x{height}+{x}+{y}')

        # Frame principal
        main_frame = ttk.Frame(detail_window, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        # Encabezado
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=X, pady=(0, 20))

        ttk.Label(
            header_frame,
            text=f"Venta N° {sale_id}",
            font=("Segoe UI", 23, "bold")
        ).pack(side=LEFT)

        ttk.Label(
            header_frame,
            text=f"Fecha: {sale_date}",
            font=("Segoe UI", 16)
        ).pack(side=RIGHT)

        # ===== Método de pago: se puede corregir por si se cargó mal al
        # momento de la venta. Si estaba dividido ('mixto'), corregirlo a
        # un método simple reemplaza el detalle dividido guardado aparte. =====
        metodo_frame = ttk.Frame(main_frame, bootstyle="light", padding=12)
        metodo_frame.pack(fill=X, pady=(0, 15))

        metodo_top_row = ttk.Frame(metodo_frame)
        metodo_top_row.pack(fill=X, pady=(0, 10))
        ttk.Label(
            metodo_top_row, text="Método de pago:", font=("Segoe UI", 15)
        ).pack(side=LEFT, padx=(0, 10))

        metodo_actual = {'valor': payment_method or 'efectivo'}
        metodo_label = ttk.Label(
            metodo_top_row,
            text=METODO_PAGO_LABELS.get(metodo_actual['valor'], 'Efectivo'),
            font=("Segoe UI", 15, "bold"))
        metodo_label.pack(side=LEFT)

        # Fila propia para los botones: así entran todos (4 métodos +
        # Guardar) sin competir por espacio con la etiqueta de arriba.
        botones_row = ttk.Frame(metodo_frame)
        botones_row.pack(fill=X)

        metodo_buttons = {}

        def elegir_metodo(m):
            metodo_actual['valor'] = m
            for mm, b in metodo_buttons.items():
                b.configure(bootstyle="primary" if mm == m else "secondary")

        for m in ('efectivo', 'transferencia', 'posnet', 'fiado'):
            btn = ttk.Button(
                botones_row, text=METODO_PAGO_LABELS[m], width=13,
                bootstyle="primary" if m == metodo_actual['valor']
                else "secondary",
                command=lambda m=m: elegir_metodo(m))
            btn.pack(side=LEFT, padx=(0, 5))
            metodo_buttons[m] = btn

        def guardar_metodo():
            nuevo = metodo_actual['valor']
            if nuevo == payment_method:
                return
            cliente_id = None
            if nuevo == 'fiado':
                # Una venta fiada tiene que quedar anotada a un cliente.
                from ..controllers.fiados_controller import ClientesApi
                api = ClientesApi()
                cliente = show_cliente_picker(
                    detail_window, api.buscar_clientes, api.crear_cliente,
                    float(sale_total))
                if cliente is None:
                    return
                cliente_id = cliente['id']
            if self.report_controller:
                self.report_controller.update_sale_payment_method(
                    sale_id, nuevo, cliente_id)
            metodo_label.configure(text=METODO_PAGO_LABELS[nuevo])
            messagebox.showinfo(
                "Guardado",
                f"Método de pago actualizado a {METODO_PAGO_LABELS[nuevo]}.")

        ttk.Button(
            botones_row, text="Guardar", bootstyle="success", width=10,
            command=guardar_metodo
        ).pack(side=LEFT, padx=(15, 0))

        # Tabla de productos
        ttk.Label(
            main_frame,
            text="Productos",
            font=("Segoe UI", 18, "bold")
        ).pack(anchor=W, pady=(0, 10))

        # Estilo para la tabla de detalles
        style = ttk.Style()
        style.configure(
            "Details.Treeview",
            rowheight=46,
            font=('Segoe UI', 15)
        )
        style.configure(
            "Details.Treeview.Heading",
            font=('Segoe UI', 16, 'bold')
        )

        # Crear tabla
        columns = ("producto", "cantidad", "precio", "subtotal")
        tree = ttk.Treeview(
            main_frame,
            columns=columns,
            show="headings",
            height=8,
            style="Details.Treeview"
        )

        tree.heading("producto", text="Producto", anchor=W)
        tree.heading("cantidad", text="Cantidad", anchor=CENTER)
        tree.heading("precio", text="Precio", anchor=E)
        tree.heading("subtotal", text="Subtotal", anchor=E)

        tree.column("producto", width=448, anchor=W)
        tree.column("cantidad", width=156, anchor=CENTER)
        tree.column("precio", width=168, anchor=E)
        tree.column("subtotal", width=168, anchor=E)

        # Insertar productos
        for i, detail in enumerate(details):
            tree.insert(
                "", END,
                values=(
                    detail['producto'],
                    detail['cantidad'],
                    f"${detail['precio']:.2f}",
                    f"${detail['subtotal']:.2f}"
                ),
                tags=('evenrow' if i % 2 == 0 else 'oddrow',)
            )

        # Colores alternados
        tree.tag_configure('evenrow', background='#ecf0f1')
        tree.tag_configure('oddrow', background='white')

        tree.pack(fill=BOTH, expand=True, pady=(0, 15))

        # Separador
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill=X, pady=(15, 15))

        # Total
        total_frame = ttk.Frame(main_frame)
        total_frame.pack(fill=X, pady=(5, 0))

        ttk.Label(
            total_frame,
            text="Total de la venta:",
            font=("Segoe UI", 18)
        ).pack(side=LEFT)

        ttk.Label(
            total_frame,
            text=f"${sale_total:,.2f}",
            font=("Segoe UI", 25, "bold"),
            bootstyle="success"
        ).pack(side=RIGHT, padx=(20, 0))

        # Frame para botones
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(pady=(15, 0))

        # Botón: Exportar Ticket
        ttk.Button(
            buttons_frame,
            text="🎫 Exportar Ticket PDF",
            bootstyle="info",
            command=lambda: self._on_export_ticket_pdf(
                sale_id, sale_date, metodo_actual['valor'], sale_total,
                details
            ),
            width=20
        ).pack(side=LEFT, padx=5)

        # Botón: Anular Venta
        ttk.Button(
            buttons_frame,
            text="❌ Anular Venta",
            bootstyle="danger",
            command=lambda: self._on_cancel_sale(sale_id, detail_window),
            width=20
        ).pack(side=LEFT, padx=5)

        # Botón cerrar
        ttk.Button(
            buttons_frame,
            text="Cerrar",
            bootstyle="secondary",
            command=detail_window.destroy,
            width=20
        ).pack(side=LEFT, padx=5)

    def _on_export_pdf_report(self):
        """Maneja el clic en el botón de exportar reporte PDF"""
        if self.report_controller and ensure_unlocked(self):
            self.report_controller.export_sales_report_to_pdf()

    def _on_export_sales_excel(self):
        """Maneja el clic en el botón de exportar ventas a Excel"""
        if self.report_controller and ensure_unlocked(self):
            self.report_controller.export_sales_to_excel()

    def _on_export_inventory_excel(self):
        """Maneja el clic en el botón de exportar inventario a Excel"""
        if self.report_controller and ensure_unlocked(self):
            self.report_controller.export_inventory_to_excel()

    def _on_export_ticket_pdf(
            self, sale_id, sale_date, payment_method, sale_total, details):
        """Maneja el clic en el botón de exportar ticket de venta"""
        if self.report_controller:
            # Obtener datos completos de la venta
            query = "SELECT paid, `change` FROM sales WHERE id = ?"
            from ..models.database import Database
            db = Database()
            result = db.execute_query(query, (sale_id,))

            if result:
                sale_paid = float(result[0]['paid'])
                sale_change = float(result[0]['change'])
                self.report_controller.export_sale_ticket_to_pdf(
                    sale_id, sale_date, payment_method, sale_total,
                    sale_paid, sale_change, details
                )

    def _on_cancel_sale(self, sale_id, detail_window):
        """Maneja el clic en el botón de anular venta"""
        if self.report_controller:
            self.report_controller.cancel_sale(sale_id)
            # Cerrar ventana de detalle si la anulación fue exitosa
            detail_window.destroy()
