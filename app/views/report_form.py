import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ..utils import formatear_fecha_hora

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
        self.canvas_widget = None  # Para almacenar el canvas del gráfico
        self.report_controller = None  # Se establecerá desde el controlador
        self._ventas = []  # Última lista completa recibida, para filtrar sin ir a la base
        self._filtro_metodo = 'todos'
        # Día que se está mirando en el historial ('YYYY-MM-DD').
        self._dia_filtro = self._hoy_str()
        self._create_widgets()

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
            font=("Segoe UI", 14)
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
            font=("Segoe UI", 14)
        )
        self.card_cantidad_titulo.pack(anchor=W)

        self.label_cantidad_ventas = ttk.Label(
            card_cantidad,
            text="0",
            font=("Segoe UI", 31, "bold"),
            bootstyle="info"
        )
        self.label_cantidad_ventas.pack(anchor=W, pady=(10, 0))

        # Container para gráfico y tabla
        bottom_container = ttk.Frame(self)
        bottom_container.pack(fill=BOTH, expand=True)

        # Gráfico y tabla apilados (no lado a lado): así en una ventana
        # angosta ninguno de los dos queda apretado fuera de la vista, ya
        # que el scroll de la pestaña es vertical.
        card_grafico = ttk.Frame(
            bottom_container, bootstyle="light", padding=20)
        card_grafico.pack(side=TOP, fill=BOTH, expand=True, pady=(0, 15))

        ttk.Label(
            card_grafico,
            text="Productos más vendidos",
            font=("Segoe UI", 16, "bold")
        ).pack(anchor=W, pady=(0, 15))

        # Frame para el gráfico
        self.grafico_frame = ttk.Frame(card_grafico, height=300)
        self.grafico_frame.pack(fill=BOTH, expand=True)

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
            dia_nav_row, text="Hoy", font=("Segoe UI", 14, "bold"))
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
                font=("Segoe UI", 11, "bold")
            ).pack(anchor=W)
            lbl = ttk.Label(card, text="0 pagos — $0.00", font=("Segoe UI", 11))
            lbl.pack(anchor=W, pady=(4, 0))
            self.resumen_metodo_labels[metodo] = lbl

        tabla_header = ttk.Frame(card_tabla)
        tabla_header.pack(fill=X, pady=(0, 15))

        ttk.Label(
            tabla_header,
            text="Historial de ventas",
            font=("Segoe UI", 16, "bold")
        ).pack(side=LEFT)

        filtro_frame = ttk.Frame(tabla_header)
        filtro_frame.pack(side=RIGHT)
        ttk.Label(
            filtro_frame, text="Método de pago:", font=("Segoe UI", 12)
        ).pack(side=LEFT, padx=(0, 8))
        self.filtro_metodo_combo = ttk.Combobox(
            filtro_frame, state="readonly", width=16, font=("Segoe UI", 12),
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
            rowheight=40,
            font=('Segoe UI', 13)
        )
        style.configure(
            "Ventas.Treeview.Heading",
            font=('Segoe UI', 14, 'bold')
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

        self.tabla_ventas.column("fecha", width=170, anchor=W)
        self.tabla_ventas.column("metodo", width=150, anchor=CENTER)
        self.tabla_ventas.column("total", width=110, anchor=E)

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
            text=f"${resumen['total_ventas']:,.2f}")
        self.card_total_titulo.configure(text=f"Total de ventas — {dia_texto}")
        cantidad = resumen['cantidad_ventas']
        self.label_cantidad_ventas.configure(text=f"{cantidad}")
        self.card_cantidad_titulo.configure(
            text=f"Cantidad de ventas — {dia_texto}")

    def update_data(self, productos_vendidos=None, ultimas_ventas=None):
        """Actualiza los datos mostrados en los reportes"""

        # Actualizar gráfico de productos más vendidos
        if productos_vendidos:
            self._update_grafico(productos_vendidos)
        else:
            self._update_grafico([])

        # Guardar la lista completa para poder filtrar sin volver a consultar
        self._ventas = ultimas_ventas or []
        self._render_ventas()

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
            label.configure(text=f"{texto_cant} — ${c['total']:.2f}")

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
        detail_window.geometry("940x780")
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
            font=("Segoe UI", 14)
        ).pack(side=RIGHT)

        # ===== Método de pago: se puede corregir por si se cargó mal al
        # momento de la venta. Si estaba dividido ('mixto'), corregirlo a
        # un método simple reemplaza el detalle dividido guardado aparte. =====
        metodo_frame = ttk.Frame(main_frame, bootstyle="light", padding=12)
        metodo_frame.pack(fill=X, pady=(0, 15))

        metodo_top_row = ttk.Frame(metodo_frame)
        metodo_top_row.pack(fill=X, pady=(0, 10))
        ttk.Label(
            metodo_top_row, text="Método de pago:", font=("Segoe UI", 13)
        ).pack(side=LEFT, padx=(0, 10))

        metodo_actual = {'valor': payment_method or 'efectivo'}
        metodo_label = ttk.Label(
            metodo_top_row,
            text=METODO_PAGO_LABELS.get(metodo_actual['valor'], 'Efectivo'),
            font=("Segoe UI", 13, "bold"))
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
            if self.report_controller:
                self.report_controller.update_sale_payment_method(
                    sale_id, nuevo)
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
            font=("Segoe UI", 16, "bold")
        ).pack(anchor=W, pady=(0, 10))

        # Estilo para la tabla de detalles
        style = ttk.Style()
        style.configure(
            "Details.Treeview",
            rowheight=40,
            font=('Segoe UI', 13)
        )
        style.configure(
            "Details.Treeview.Heading",
            font=('Segoe UI', 14, 'bold')
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

        tree.column("producto", width=400, anchor=W)
        tree.column("cantidad", width=140, anchor=CENTER)
        tree.column("precio", width=150, anchor=E)
        tree.column("subtotal", width=150, anchor=E)

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
            font=("Segoe UI", 16)
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

    def _update_grafico(self, productos_vendidos):
        """Actualiza el gráfico de productos más vendidos"""
        try:
            # Limpiar el canvas anterior si existe
            if self.canvas_widget:
                self.canvas_widget.get_tk_widget().destroy()

            # Limpiar el frame
            for widget in self.grafico_frame.winfo_children():
                widget.destroy()

            if not productos_vendidos:
                # Si no hay datos, mostrar mensaje
                ttk.Label(
                    self.grafico_frame,
                    text="📊 No hay datos de ventas aún",
                    font=("Segoe UI", 13),
                    foreground="gray"
                ).place(relx=0.5, rely=0.5, anchor=CENTER)
                return

            # Preparar datos (tomar solo los top 5 para que se vea bien)
            top_productos = productos_vendidos[:5]
            nombres = [p['producto'][:18]
                       for p in top_productos]  # Limitar nombre a 18 caracteres
            cantidades = [int(p['cantidad_vendida']) for p in top_productos]

            # Crear figura de matplotlib con mejor tamaño
            fig = Figure(figsize=(6.5, 4.2), dpi=100, facecolor='white')
            ax = fig.add_subplot(111)

            # Colores profesionales (gradiente de azul a verde)
            colores = ['#1e88e5', '#26a69a', '#66bb6a', '#ffa726', '#ef5350']

            # Crear gráfico de barras verticales con efecto de gradiente
            bars = ax.bar(nombres, cantidades, color=colores[:len(nombres)],
                          width=0.65, edgecolor='white', linewidth=1.5, alpha=0.9)

            # Agregar grid sutil para mejor lectura
            ax.yaxis.grid(True, linestyle='--', alpha=0.3, color='gray')
            ax.set_axisbelow(True)

            # Personalizar el gráfico
            ax.set_ylabel('Unidades Vendidas', fontsize=11,
                          weight='bold', color='#2c3e50')
            ax.set_xlabel('Productos', fontsize=11,
                          weight='bold', color='#2c3e50')
            ax.set_title('Productos Más Vendidos',
                         fontsize=14, weight='bold', pad=15, color='#2c3e50')
            ax.set_facecolor('#fafafa')

            # Rotar las etiquetas del eje X
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=35, ha='right',
                     fontsize=10, color='#34495e')
            plt.setp(ax.yaxis.get_majorticklabels(),
                     fontsize=10, color='#34495e')

            # Añadir valores encima de las barras con mejor formato
            for i, (bar, cantidad) in enumerate(zip(bars, cantidades)):
                height = bar.get_height()
                # Añadir un pequeño recuadro detrás del número
                ax.text(bar.get_x() + bar.get_width()/2, height + max(cantidades)*0.02,
                        f'{cantidad}',
                        ha='center', va='bottom', fontsize=11, weight='bold',
                        color='#2c3e50',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                  edgecolor=colores[i], alpha=0.8, linewidth=1.5))

            # Ajustar los límites del eje Y para dar espacio a las etiquetas
            ax.set_ylim(0, max(cantidades) * 1.15)

            # Quitar bordes superiores y derecho para un look más limpio
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#95a5a6')
            ax.spines['bottom'].set_color('#95a5a6')

            # Ajustar layout
            fig.tight_layout()

            # Integrar con tkinter
            self.canvas_widget = FigureCanvasTkAgg(
                fig, master=self.grafico_frame)
            self.canvas_widget.draw()
            self.canvas_widget.get_tk_widget().pack(fill=BOTH, expand=True)
        except Exception as e:
            # En caso de error, mostrar mensaje en consola
            import traceback
            traceback.print_exc()
            ttk.Label(
                self.grafico_frame,
                text=f"❌ Error al crear gráfico\n{str(e)}",
                font=("Segoe UI", 11),
                foreground="red"
            ).place(relx=0.5, rely=0.5, anchor=CENTER)

    def _on_export_pdf_report(self):
        """Maneja el clic en el botón de exportar reporte PDF"""
        if self.report_controller:
            self.report_controller.export_sales_report_to_pdf()

    def _on_export_sales_excel(self):
        """Maneja el clic en el botón de exportar ventas a Excel"""
        if self.report_controller:
            self.report_controller.export_sales_to_excel()

    def _on_export_inventory_excel(self):
        """Maneja el clic en el botón de exportar inventario a Excel"""
        if self.report_controller:
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
