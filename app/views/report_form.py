import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class ReportForm(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.pack(fill=BOTH, expand=True)
        self.canvas_widget = None  # Para almacenar el canvas del gráfico
        self.report_controller = None  # Se establecerá desde el controlador
        self._create_widgets()

    def _create_widgets(self):
        # Título y botones de exportación
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=X, pady=(0, 20))

        ttk.Label(
            header_frame,
            text="Reportes",
            font=("Segoe UI", 24, "bold")
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

        # Card: Total de ventas
        card_total = ttk.Frame(top_cards, bootstyle="light", padding=20)
        card_total.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        ttk.Label(
            card_total,
            text="Total de ventas",
            font=("Segoe UI", 12)
        ).pack(anchor=W)

        self.label_total_ventas = ttk.Label(
            card_total,
            text="$0",
            font=("Segoe UI", 28, "bold"),
            bootstyle="success"
        )
        self.label_total_ventas.pack(anchor=W, pady=(10, 0))

        # Card: Última venta
        card_ultima = ttk.Frame(top_cards, bootstyle="light", padding=20)
        card_ultima.pack(side=RIGHT, fill=BOTH, expand=True, padx=(10, 0))

        ttk.Label(
            card_ultima,
            text="Última venta",
            font=("Segoe UI", 12)
        ).pack(anchor=W)

        self.label_ultima_venta = ttk.Label(
            card_ultima,
            text="$0",
            font=("Segoe UI", 28, "bold"),
            bootstyle="info"
        )
        self.label_ultima_venta.pack(anchor=W, pady=(10, 0))

        # Container para gráfico y tabla
        bottom_container = ttk.Frame(self)
        bottom_container.pack(fill=BOTH, expand=True)

        # Card: Productos más vendidos (placeholder para gráfico)
        card_grafico = ttk.Frame(
            bottom_container, bootstyle="light", padding=20)
        card_grafico.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))

        ttk.Label(
            card_grafico,
            text="Productos más vendidos",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor=W, pady=(0, 15))

        # Frame para el gráfico
        self.grafico_frame = ttk.Frame(card_grafico, height=300)
        self.grafico_frame.pack(fill=BOTH, expand=True)

        # Card: Historial de ventas (tabla)
        card_tabla = ttk.Frame(bottom_container, bootstyle="light", padding=20)
        card_tabla.pack(side=RIGHT, fill=Y, padx=(10, 0))

        ttk.Label(
            card_tabla,
            text="Historial de ventas",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor=W, pady=(0, 15))

        # Configurar estilo para la tabla de ventas
        style = ttk.Style()
        style.configure(
            "Ventas.Treeview",
            rowheight=35,
            font=('Segoe UI', 11)
        )
        style.configure(
            "Ventas.Treeview.Heading",
            font=('Segoe UI', 12, 'bold')
        )

        # Frame para la tabla con scrollbar
        table_container = ttk.Frame(card_tabla)
        table_container.pack(fill=BOTH, expand=True)

        # Tabla de ventas (solo fecha y total, el ID se guarda oculto)
        columns = ("id", "fecha", "total")
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
        self.tabla_ventas.heading("total", text="Total", anchor=E)

        self.tabla_ventas.column("fecha", width=150, anchor=W)
        self.tabla_ventas.column("total", width=100, anchor=E)

        # Colores alternados
        self.tabla_ventas.tag_configure('evenrow', background='#ecf0f1')
        self.tabla_ventas.tag_configure('oddrow', background='white')

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            table_container, orient=VERTICAL, command=self.tabla_ventas.yview)
        self.tabla_ventas.configure(yscrollcommand=scrollbar.set)

        self.tabla_ventas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

    def update_data(self, total_ventas=0, ultima_venta=0, productos_vendidos=None, ultimas_ventas=None):
        """Actualiza los datos mostrados en los reportes"""
        # Actualizar cards
        self.label_total_ventas.configure(text=f"${total_ventas:,.2f}")
        self.label_ultima_venta.configure(text=f"${ultima_venta:,.2f}")

        # Actualizar gráfico de productos más vendidos
        if productos_vendidos:
            self._update_grafico(productos_vendidos)
        else:
            self._update_grafico([])

        # Actualizar tabla de últimas ventas
        if ultimas_ventas:
            # Limpiar tabla
            for item in self.tabla_ventas.get_children():
                self.tabla_ventas.delete(item)

            # Insertar ventas
            for i, venta in enumerate(ultimas_ventas):
                # Formatear la fecha (solo fecha y hora, sin microsegundos)
                fecha_str = str(venta['date'])
                if len(fecha_str) > 19:
                    fecha_str = fecha_str[:19]

                self.tabla_ventas.insert(
                    "", END,
                    values=(venta['id'], fecha_str, f"${venta['total']:.2f}"),
                    tags=('evenrow' if i % 2 == 0 else 'oddrow',)
                )

    def show_sale_detail(self, sale_id, sale_date, sale_total, details):
        """Muestra una ventana con el detalle de la venta"""
        # Crear ventana modal
        detail_window = ttk.Toplevel(self)
        detail_window.title(f"Detalle de Venta N° {sale_id}")
        detail_window.geometry("800x600")
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
            font=("Segoe UI", 20, "bold")
        ).pack(side=LEFT)

        ttk.Label(
            header_frame,
            text=f"Fecha: {sale_date}",
            font=("Segoe UI", 12)
        ).pack(side=RIGHT)

        # Tabla de productos
        ttk.Label(
            main_frame,
            text="Productos",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor=W, pady=(0, 10))

        # Estilo para la tabla de detalles
        style = ttk.Style()
        style.configure(
            "Details.Treeview",
            rowheight=35,
            font=('Segoe UI', 11)
        )
        style.configure(
            "Details.Treeview.Heading",
            font=('Segoe UI', 12, 'bold')
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

        tree.column("producto", width=350, anchor=W)
        tree.column("cantidad", width=120, anchor=CENTER)
        tree.column("precio", width=130, anchor=E)
        tree.column("subtotal", width=130, anchor=E)

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
            font=("Segoe UI", 14)
        ).pack(side=LEFT)

        ttk.Label(
            total_frame,
            text=f"${sale_total:,.2f}",
            font=("Segoe UI", 22, "bold"),
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
                sale_id, sale_date, sale_total, details
            ),
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
                    font=("Segoe UI", 11),
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
                font=("Segoe UI", 10),
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

    def _on_export_ticket_pdf(self, sale_id, sale_date, sale_total, details):
        """Maneja el clic en el botón de exportar ticket de venta"""
        if self.report_controller:
            # Obtener datos completos de la venta
            query = f"SELECT paid, `change` FROM sales WHERE id = {sale_id}"
            from ..models.database import Database
            db = Database()
            result = db.execute_query(query)

            if result:
                sale_paid = float(result[0]['paid'])
                sale_change = float(result[0]['change'])
                self.report_controller.export_sale_ticket_to_pdf(
                    sale_id, sale_date, sale_total, sale_paid, sale_change, details
                )
