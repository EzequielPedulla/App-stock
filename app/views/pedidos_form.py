import tkinter as tk
from datetime import date, datetime, timedelta

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from ..utils import texto_dia
from .cliente_dialogs import _centrar, parse_monto, confirmar_enter


FORMAS_PAGO = {'efectivo': 'Efectivo', 'transferencia': 'Transferencia',
               'bolsillo': 'Bolsillo del dueño'}


REPETIR_TEXTO = {'no': 'No se repite', 'semanal': 'Cada semana',
                 'mensual': 'Cada mes'}


def money(valor: float) -> str:
    """Los pedidos los ven y cargan todos los empleados: sin tapar."""
    return f"${valor:.2f}"


class PedidosForm(ttk.Frame):
    """Pedidos a proveedores: qué viene, qué día y cuánta plata hace falta.
    Al llegar un pedido se confirma con lo realmente pagado y eso se anota
    como gasto en Caja."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.pack(fill=BOTH, expand=True)
        self.pedidos_controller = None  # Lo setea el controlador
        self._create_widgets()

    def _create_widgets(self):
        ttk.Label(
            self, text="Pedidos y pagos", font=("Segoe UI", 27, "bold")
        ).pack(anchor=W, pady=(0, 15))

        # ===== Resumen: hoy, próximos 7 días y atrasados =====
        resumen = ttk.Frame(self, bootstyle="light", padding=15)
        resumen.pack(fill=X, pady=(0, 15))
        self.resumen_labels = {}
        for clave, titulo in (('hoy', "Hoy"),
                              ('semana', "Próximos 7 días"),
                              ('atrasados', "⚠ Atrasados")):
            col = ttk.Frame(resumen, bootstyle="light")
            col.pack(side=LEFT, padx=(0, 50))
            ttk.Label(col, text=titulo, font=("Segoe UI", 15)).pack(anchor=W)
            monto = ttk.Label(col, text="—", font=("Segoe UI", 23, "bold"),
                              bootstyle="danger" if clave == 'atrasados'
                              else "primary")
            monto.pack(anchor=W)
            detalle = ttk.Label(col, text="", font=("Segoe UI", 14),
                                foreground="#2c3e50")
            detalle.pack(anchor=W)
            self.resumen_labels[clave] = (monto, detalle)

        # ===== Acciones =====
        acciones = ttk.Frame(self)
        acciones.pack(fill=X, pady=(0, 10))
        self.nuevo_button = ttk.Button(
            acciones, text="➕ Nuevo pedido", bootstyle="success")
        self.nuevo_button.pack(side=LEFT, padx=(0, 10))
        self.recibir_button = ttk.Button(
            acciones, text="✅ Llegó / pagado", bootstyle="primary")
        self.recibir_button.pack(side=LEFT, padx=(0, 10))
        self.editar_button = ttk.Button(
            acciones, text="✏️ Editar", bootstyle="secondary")
        self.editar_button.pack(side=LEFT, padx=(0, 10))
        self.cancelar_button = ttk.Button(
            acciones, text="Cancelar pedido", bootstyle="danger-outline")
        self.cancelar_button.pack(side=LEFT, padx=(0, 10))
        self.deshacer_button = ttk.Button(
            acciones, text="↩ Deshacer recepción",
            bootstyle="warning-outline")
        self.deshacer_button.pack(side=LEFT)

        filtro = ttk.Frame(self)
        filtro.pack(fill=X, pady=(0, 10))
        ttk.Label(filtro, text="Mostrar:", font=("Segoe UI", 16, "bold")
                  ).pack(side=LEFT, padx=(0, 8))
        self.filtro_combo = ttk.Combobox(
            filtro, values=["Pendientes", "Recibidos", "Cancelados", "Todos"],
            state="readonly", width=14, font=("Segoe UI", 15))
        self.filtro_combo.set("Pendientes")
        self.filtro_combo.pack(side=LEFT)

        # ===== Lista de pedidos (izquierda) y plata por día (derecha) =====
        cuerpo = ttk.Frame(self)
        cuerpo.pack(fill=BOTH, expand=True)

        izq = ttk.Frame(cuerpo)
        izq.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 12))
        cols = ("fecha", "proveedor", "estimado", "estado", "detalle")
        self.tree = ttk.Treeview(izq, columns=cols, show="headings",
                                 height=12, selectmode="browse")
        for col, texto, ancho, anchor in (
                ("fecha", "Llega", 120, "center"),
                ("proveedor", "Proveedor", 230, "center"),
                ("estimado", "Aprox.", 130, "center"),
                ("estado", "Estado", 130, "center"),
                ("detalle", "Detalle", 340, "w")):
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor=anchor)
        sb = ttk.Scrollbar(izq, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=LEFT, fill=Y)
        self.tree.tag_configure('atrasado', foreground='#c0392b')
        self.tree.tag_configure('hoy', foreground='#d35400')
        self.tree.tag_configure('recibido', foreground='#1e8449')
        self.tree.tag_configure('cancelado', foreground='#7b8794')

        der = ttk.Frame(cuerpo)
        der.pack(side=LEFT, fill=Y)
        ttk.Label(der, text="Plata necesaria por día",
                  font=("Segoe UI", 18, "bold"), foreground="#2c3e50"
                  ).pack(anchor=W, pady=(0, 6))
        self.dias_tree = ttk.Treeview(
            der, columns=("dia", "pedidos", "monto"), show="headings",
            height=12, selectmode="none")
        for col, texto, ancho in (("dia", "Día", 150), ("pedidos", "Pedidos", 115),
                                  ("monto", "Aprox.", 140)):
            self.dias_tree.heading(col, text=texto, anchor="center")
            self.dias_tree.column(col, width=ancho, anchor="center")
        self.dias_tree.pack(fill=Y)
        self.dias_tree.tag_configure('atrasado', foreground='#c0392b')

        self.vacio_label = ttk.Label(
            self, text="", font=("Segoe UI", 13), foreground="#566573")
        self.vacio_label.pack(anchor=W, pady=(8, 0))

    # ----- carga de datos -----

    def load_pedidos(self, pedidos: list, hoy_iso: str) -> None:
        seleccionado = self.tree.selection()
        for i in self.tree.get_children():
            self.tree.delete(i)
        for p in pedidos:
            f = p['fecha_estimada']
            tags = ()
            if p['estado'] == 'pendiente':
                if f < hoy_iso:
                    estado, tags = "⚠ Atrasado", ('atrasado',)
                elif f == hoy_iso:
                    estado, tags = "Hoy", ('hoy',)
                else:
                    estado = "Pendiente"
                detalle = p['nota']
            elif p['estado'] == 'recibido':
                estado, tags = ("✔ Pagado" if p['tipo'] == 'servicio'
                                else "✔ Recibido"), ('recibido',)
                forma = FORMAS_PAGO.get(p['forma_pago'], p['forma_pago'])
                detalle = f"Pagó {money(p['monto_final'])} ({forma})"
                if p['nota']:
                    detalle += f" · {p['nota']}"
            else:
                estado, tags = "Cancelado", ('cancelado',)
                detalle = p['nota']
            if p['repetir'] in REPETIR_TEXTO and p['repetir'] != 'no':
                detalle = f"🔁 {REPETIR_TEXTO[p['repetir']]}" + (
                    f" · {detalle}" if detalle else "")
            icono = "🧾" if p['tipo'] == 'servicio' else "📦"
            self.tree.insert('', END, iid=str(p['id']), tags=tags, values=(
                texto_dia(f), f"{icono} {p['proveedor']}",
                money(p['monto_estimado']) if p['monto_estimado'] else "—",
                estado, detalle))
        if seleccionado and self.tree.exists(seleccionado[0]):
            self.tree.selection_set(seleccionado[0])
        self.vacio_label.configure(
            text="" if pedidos else
            "No hay pedidos para mostrar. Cargá uno con \"Nuevo pedido\".")

    def update_resumen(self, r: dict) -> None:
        for clave, (monto, detalle) in self.resumen_labels.items():
            d = r[clave]
            monto.configure(text=money(d['monto']))
            if d['cantidad'] == 0:
                detalle.configure(text="sin pedidos")
            else:
                detalle.configure(text="1 pedido" if d['cantidad'] == 1
                                  else f"{d['cantidad']} pedidos")

    def load_dias(self, dias: list) -> None:
        for i in self.dias_tree.get_children():
            self.dias_tree.delete(i)
        for d in dias:
            atrasado = d['fecha'] == 'atrasado'
            self.dias_tree.insert('', END, tags=('atrasado',) if atrasado
                                  else (), values=(
                "⚠ Atrasados" if atrasado else texto_dia(d['fecha']),
                d['cantidad'], money(d['monto'])))
        if not dias:
            self.dias_tree.insert('', END, values=("—", "", "Nada en 14 días"))

    # ----- diálogos -----

    def _fecha_entry(self, parent, var, fecha: date):
        """Campo de fecha con calendario (en español, semana desde lunes)."""
        entry = ttk.DateEntry(parent, dateformat='%d/%m/%Y', width=11,
                              bootstyle="primary", firstweekday=0)
        entry.entry.configure(textvariable=var, font=("Segoe UI", 16))
        entry.entry.delete(0, 'end')
        entry.entry.insert(0, fecha.strftime('%d/%m/%Y'))
        return entry

    def show_pedido_dialog(self, proveedores: list, pedido, on_save) -> None:
        """Alta o edición de un pedido: proveedor (se elige o se escribe uno
        nuevo), día en que llega, monto aproximado y una nota."""
        editando = pedido is not None
        dialog = ttk.Toplevel(self)
        dialog.title("Editar pedido" if editando else "Nuevo pedido")
        dialog.geometry("640x900")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        _centrar(dialog)

        main = ttk.Frame(dialog, padding=22)
        main.pack(fill=BOTH, expand=True)
        ttk.Label(main, text="✏️ Editar" if editando else "➕ Nuevo",
                  font=("Segoe UI", 20, "bold")).pack(pady=(0, 10))

        def etiqueta(texto):
            lbl = ttk.Label(main, text=texto, font=("Segoe UI", 15))
            lbl.pack(anchor=W, pady=(0, 3))
            return lbl

        # ¿Es un pedido a un proveedor o un servicio / pago (luz, alquiler)?
        tipo = {'v': pedido['tipo'] if editando else 'pedido'}
        fila_tipo = ttk.Frame(main)
        fila_tipo.pack(fill=X, pady=(0, 12))
        botones_tipo = {}
        etiquetas = {}

        def elegir_tipo(t):
            tipo['v'] = t
            for k, b in botones_tipo.items():
                b.configure(bootstyle="primary" if k == t else "secondary")
            etiquetas['prov'].configure(
                text="Proveedor * (elegí uno o escribí uno nuevo)"
                if t == 'pedido' else
                "Servicio o pago * (ej. Luz, Alquiler, Internet)")
            etiquetas['fecha'].configure(
                text="Día en que llega *" if t == 'pedido'
                else "Día de vencimiento *")

        for t, texto in (('pedido', '📦 Pedido a proveedor'),
                         ('servicio', '🧾 Servicio o pago')):
            b = ttk.Button(fila_tipo, text=texto, width=24,
                           command=lambda t=t: elegir_tipo(t))
            b.pack(side=LEFT, padx=(0, 8))
            botones_tipo[t] = b

        etiquetas['prov'] = etiqueta("")
        prov = ttk.Combobox(main, values=[p['nombre'] for p in proveedores],
                            font=("Segoe UI", 16))
        prov.pack(fill=X, pady=(0, 10))
        if editando:
            prov.set(pedido['proveedor'])

        etiqueta("Teléfono (opcional, solo si es nuevo)")
        tel = ttk.Entry(main, font=("Segoe UI", 16))
        tel.pack(fill=X, pady=(0, 10))

        etiquetas['fecha'] = etiqueta("")
        fecha_var = tk.StringVar()
        fecha0 = (datetime.strptime(pedido['fecha_estimada'], '%Y-%m-%d').date()
                  if editando else date.today() + timedelta(days=1))
        self._fecha_entry(main, fecha_var, fecha0).pack(
            anchor=W, pady=(0, 10))

        etiqueta("Monto aproximado en $ (vacío si todavía no lo saben)")
        monto = ttk.Entry(main, font=("Segoe UI", 16))
        monto.pack(fill=X, pady=(0, 10))
        if editando and pedido['monto_estimado']:
            monto.insert(0, f"{pedido['monto_estimado']:.2f}")

        etiqueta("Se repite")
        repetir = ttk.Combobox(
            main, values=list(REPETIR_TEXTO.values()), state="readonly",
            font=("Segoe UI", 16))
        repetir.set(REPETIR_TEXTO.get(
            pedido['repetir'] if editando else 'no', 'No se repite'))
        repetir.pack(fill=X, pady=(0, 10))

        etiqueta("Nota (ej. \"viene a la tarde\")")
        nota = ttk.Entry(main, font=("Segoe UI", 16))
        nota.pack(fill=X, pady=(0, 10))
        if editando:
            nota.insert(0, pedido['nota'])
        elegir_tipo(tipo['v'])
        prov.focus()

        def guardar(event=None):
            nombre = prov.get().strip()
            if not nombre:
                messagebox.showerror(
                    "Error", "Ingresá el proveedor o el servicio",
                    parent=dialog)
                return "break"
            try:
                f = datetime.strptime(fecha_var.get(), '%d/%m/%Y').date()
            except ValueError:
                messagebox.showerror(
                    "Error", "Fecha inválida (usá DD/MM/AAAA)", parent=dialog)
                return "break"
            try:
                m = parse_monto(monto.get())
                m = 0.0 if m is None else m
                if m < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Ingresá un monto válido",
                                     parent=dialog)
                return "break"
            if on_save({'proveedor': nombre, 'telefono': tel.get().strip(),
                        'fecha': f.isoformat(), 'monto': m,
                        'nota': nota.get().strip(), 'tipo': tipo['v'],
                        'repetir': {v: k for k, v in REPETIR_TEXTO.items()}
                        .get(repetir.get(), 'no')}):
                dialog.destroy()
            return "break"

        botones = ttk.Frame(main)
        botones.pack(side=BOTTOM, fill=X)
        ttk.Button(botones, text="Guardar (Enter)", bootstyle="success",
                   command=guardar).pack(side=RIGHT, padx=(8, 0))
        ttk.Button(botones, text="Cancelar (Esc)", bootstyle="secondary",
                   command=dialog.destroy).pack(side=RIGHT)
        dialog.bind('<Return>', guardar)
        dialog.bind('<Escape>', lambda e: dialog.destroy())

    def show_recibir_dialog(self, pedido: dict, on_confirm) -> None:
        """Confirma que llegó un pedido: cuánto se pagó en total (lo real,
        no lo aproximado) y cómo. Después se anota como gasto en Caja."""
        dialog = ttk.Toplevel(self)
        dialog.title("Pedido recibido")
        dialog.geometry("690x640")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        _centrar(dialog)

        main = ttk.Frame(dialog, padding=22)
        main.pack(fill=BOTH, expand=True)
        servicio = pedido['tipo'] == 'servicio'
        dialog.title("Pago realizado" if servicio else "Pedido recibido")
        ttk.Label(main, text="✅ Se pagó" if servicio else "✅ Llegó el pedido",
                  font=("Segoe UI", 20, "bold")).pack(pady=(0, 6))
        ttk.Label(main, text=pedido['proveedor'],
                  font=("Segoe UI", 18, "bold"), foreground="#2c3e50"
                  ).pack()
        aprox = (money(pedido['monto_estimado'])
                 if pedido['monto_estimado'] else "sin monto")
        ttk.Label(main, text=f"{'Vencía' if servicio else 'Estaba para'} el "
                  f"{texto_dia(pedido['fecha_estimada'])}"
                  f"  ·  aprox. {aprox}", font=("Segoe UI", 15),
                  foreground="#566573").pack(pady=(2, 16))

        ttk.Label(main, text="¿Cuánto se pagó en total?",
                  font=("Segoe UI", 16, "bold")).pack(anchor=W, pady=(0, 4))
        monto = ttk.Entry(main, font=("Segoe UI", 18))
        monto.pack(fill=X, pady=(0, 12))
        # Se sugiere el monto aproximado (se corrige si fue otro).
        if pedido['monto_estimado']:
            monto.insert(0, f"{pedido['monto_estimado']:.2f}")
            monto.select_range(0, 'end')
        monto.focus()

        ttk.Label(main, text="Forma de pago:",
                  font=("Segoe UI", 16, "bold")).pack(anchor=W, pady=(0, 4))
        forma = {'valor': 'efectivo'}
        fila = ttk.Frame(main)
        fila.pack(fill=X, pady=(0, 6))
        botones_forma = {}

        def elegir(f):
            forma['valor'] = f
            for k, b in botones_forma.items():
                b.configure(bootstyle="primary" if k == f else "secondary")
            if forma.get('cb'):
                forma['cb']()

        orden = list(FORMAS_PAGO)
        for f in orden:
            b = ttk.Button(fila, text=FORMAS_PAGO[f],
                           width=14 if f != 'bolsillo' else 20,
                           bootstyle="primary" if f == 'efectivo'
                           else "secondary",
                           command=lambda f=f: elegir(f))
            b.pack(side=LEFT, padx=(0, 8))
            botones_forma[f] = b

        def mover(delta):
            elegir(orden[(orden.index(forma['valor']) + delta) % len(orden)])
            return "break"

        # ← → (fuera de un campo de texto) y ↑ ↓ cambian la forma de pago
        dialog.bind('<Left>', lambda e: None if e.widget.winfo_class() in (
            'TEntry', 'Entry') else mover(-1))
        dialog.bind('<Right>', lambda e: None if e.widget.winfo_class() in (
            'TEntry', 'Entry') else mover(1))
        dialog.bind('<Up>', lambda e: mover(-1))
        dialog.bind('<Down>', lambda e: mover(1))

        destino = ttk.Label(main, text="", font=("Segoe UI", 14),
                            foreground="#566573", wraplength=540,
                            justify=LEFT)
        destino.pack(anchor=W, pady=(8, 0))

        def actualizar_destino(*_):
            destino.configure(
                text="Lo paga el dueño de su bolsillo: en Caja queda como "
                     "pago de bolsillo (no mueve el efectivo del cajón ni "
                     "cuenta como gasto del negocio)."
                if forma['valor'] == 'bolsillo' else
                "Se anota como gasto en la Caja de hoy.")
        forma['cb'] = actualizar_destino
        actualizar_destino()

        def confirmar(event=None):
            try:
                m = parse_monto(monto.get())
                if not m or m <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Ingresá el monto pagado",
                                     parent=dialog)
                return "break"
            if not confirmar_enter(
                    dialog, "Confirmar pedido",
                    [(f"{pedido['proveedor']}: se pagaron ${m:.2f}",
                      "#2c3e50"),
                     (f"Forma de pago: {FORMAS_PAGO[forma['valor']]}",
                      "#2c3e50"),
                     (("Pago de bolsillo del dueño (no es gasto del negocio)"
                       if forma['valor'] == 'bolsillo' else
                       "Se suma como gasto en la Caja de hoy"),
                      "#c0392b")]):
                return "break"
            if on_confirm(pedido['id'], m, forma['valor']):
                dialog.destroy()
            return "break"

        botones = ttk.Frame(main)
        botones.pack(side=BOTTOM, fill=X)
        ttk.Button(botones, text="Confirmar (Enter)", bootstyle="success",
                   command=confirmar).pack(side=RIGHT, padx=(8, 0))
        ttk.Button(botones, text="Cancelar (Esc)", bootstyle="secondary",
                   command=dialog.destroy).pack(side=RIGHT)
        dialog.bind('<Return>', confirmar)
        dialog.bind('<Escape>', lambda e: dialog.destroy())

    def show_aviso_dialog(self, lineas: list) -> None:
        """Aviso de los pedidos de hoy, mañana y atrasados."""
        dialog = ttk.Toplevel(self)
        dialog.title("Pedidos")
        dialog.geometry("700x%d" % min(260 + 110 * len(lineas), 700))
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        _centrar(dialog)

        main = ttk.Frame(dialog, padding=24)
        main.pack(fill=BOTH, expand=True)
        ttk.Label(main, text="🚚 Pedidos y pagos de los próximos días",
                  font=("Segoe UI", 21, "bold")).pack(pady=(0, 14))
        for titulo, nombres, atrasado in lineas:
            ttk.Label(main, text=titulo, font=("Segoe UI", 17, "bold"),
                      foreground="#c0392b" if atrasado else "#2c3e50",
                      wraplength=640).pack(anchor=W)
            ttk.Label(main, text=nombres, font=("Segoe UI", 15),
                      foreground="#566573", wraplength=640
                      ).pack(anchor=W, pady=(0, 12))
        botones = ttk.Frame(main)
        botones.pack(side=BOTTOM, fill=X)
        ttk.Button(botones, text="Entendido (Enter)", bootstyle="primary",
                   command=dialog.destroy).pack(side=RIGHT)
        dialog.bind('<Return>', lambda e: dialog.destroy())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
