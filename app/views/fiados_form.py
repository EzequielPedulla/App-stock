import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox

from ..utils import formatear_fecha_hora
from ..security import owner_lock, money, TAPADO
from .estilos import fix_label_backgrounds
from .cliente_dialogs import _centrar, parse_monto, confirmar_enter


class FiadosForm(ttk.Frame):
    """Cuaderno de fiados: lista de clientes con lo que debe cada uno, y
    desde ahí su cuenta corriente (compras fiadas y pagos)."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.pack(fill=BOTH, expand=True)
        self.fiados_controller = None  # Lo setea el controlador
        self._create_widgets()

    def _create_widgets(self):
        ttk.Label(
            self, text="Fiados", font=("Segoe UI", 27, "bold")
        ).pack(anchor=W, pady=(0, 15))

        # ===== Resumen: lo que nos deben en total =====
        resumen = ttk.Frame(self, bootstyle="light", padding=20)
        resumen.pack(fill=X, pady=(0, 15))

        deuda_col = ttk.Frame(resumen, bootstyle="light")
        deuda_col.pack(side=LEFT)
        ttk.Label(deuda_col, text="Total que nos deben",
                  font=("Segoe UI", 17)).pack(anchor=W)
        self.label_total_deuda = ttk.Label(
            deuda_col, text="$0.00", font=("Segoe UI", 25, "bold"),
            bootstyle="danger")
        self.label_total_deuda.pack(anchor=W)

        clientes_col = ttk.Frame(resumen, bootstyle="light")
        clientes_col.pack(side=LEFT, padx=(60, 0))
        ttk.Label(clientes_col, text="Clientes con deuda",
                  font=("Segoe UI", 17)).pack(anchor=W)
        self.label_con_deuda = ttk.Label(
            clientes_col, text="0", font=("Segoe UI", 25, "bold"))
        self.label_con_deuda.pack(anchor=W)

        # ===== Acciones (arriba) y buscador con filtro (abajo): en dos
        # filas porque en un monitor chico no entran todas en una sola. =====
        acciones = ttk.Frame(self)
        acciones.pack(fill=X, pady=(0, 10))
        self.nuevo_button = ttk.Button(
            acciones, text="➕ Nuevo cliente", bootstyle="success")
        self.nuevo_button.pack(side=LEFT, padx=(0, 10))
        self.cuenta_button = ttk.Button(
            acciones, text="📒 Ver cuenta y cobrar", bootstyle="primary")
        self.cuenta_button.pack(side=LEFT, padx=(0, 10))
        self.editar_button = ttk.Button(
            acciones, text="✏️ Editar", bootstyle="secondary")
        self.editar_button.pack(side=LEFT)

        barra = ttk.Frame(self)
        barra.pack(fill=X, pady=(0, 10))
        ttk.Label(barra, text="🔍 Buscar:", font=("Segoe UI", 16, "bold")
                  ).pack(side=LEFT, padx=(0, 8))
        self.search_var = ttk.StringVar()
        self.search_entry = ttk.Entry(
            barra, textvariable=self.search_var, font=("Segoe UI", 16),
            width=26)
        self.search_entry.pack(side=LEFT)
        ttk.Label(barra, text="  nombre, teléfono o DNI",
                  foreground="#566573").pack(side=LEFT)

        # ↓ desde el buscador pasa a la lista; Enter abre la cuenta
        self.search_entry.bind('<Down>', lambda e: self._ir_a_lista())
        self.solo_deuda_var = ttk.IntVar(value=0)
        ttk.Checkbutton(
            barra, text="Solo con deuda", variable=self.solo_deuda_var,
            bootstyle="round-toggle"
        ).pack(side=RIGHT, padx=(0, 12))

        # ===== Tabla de clientes =====
        tabla = ttk.Frame(self)
        tabla.pack(fill=BOTH, expand=True)

        columns = ("nombre", "telefono", "fiado", "pagado", "debe", "limite")
        self.tree = ttk.Treeview(
            tabla, columns=columns, show="headings", height=14,
            selectmode="browse")
        for col, texto, ancho, anchor in (
            ("nombre", "Cliente", 300, "w"),
            ("telefono", "Teléfono", 170, "center"),
            ("fiado", "Total fiado", 150, "center"),
            ("pagado", "Pagó", 150, "center"),
            ("debe", "Debe", 160, "center"),
            ("limite", "Límite", 150, "center"),
        ):
            self.tree.heading(col, text=texto, anchor="center")
            self.tree.column(col, width=ancho, anchor=anchor)
        sb = ttk.Scrollbar(tabla, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)

        # Rojo: pasó su límite (que es solo un aviso). Verde: al día.
        self.tree.tag_configure('excedido', foreground='#c0392b')
        self.tree.tag_configure('aldia', foreground='#5d6d7e')

        self.vacio_label = ttk.Label(
            self, text="", font=("Segoe UI", 14), foreground="#566573")
        self.vacio_label.pack(anchor=W, pady=(8, 0))

    def _ir_a_lista(self) -> str:
        items = self.tree.get_children()
        if items:
            if not self.tree.selection():
                self.tree.selection_set(items[0])
                self.tree.focus(items[0])
            self.tree.focus_set()
        return "break"

    def load_clientes(self, clientes: list) -> None:
        seleccionado = self.tree.selection()
        for i in self.tree.get_children():
            self.tree.delete(i)
        for c in clientes:
            limite = c.get('limite')
            excedido = limite is not None and c['saldo'] > limite + 0.005
            tags = ()
            if excedido:
                tags = ('excedido',)
            elif c['saldo'] <= 0.005:
                tags = ('aldia',)
            self.tree.insert('', END, iid=str(c['id']), tags=tags, values=(
                ("⚠ " if excedido else "") + c['nombre'],
                c['telefono'],
                f"${c['total_fiado']:.2f}",
                f"${c['total_pagado']:.2f}",
                f"${c['saldo']:.2f}",
                (money(limite) if limite is not None else "—"),
            ))
        if seleccionado and self.tree.exists(seleccionado[0]):
            self.tree.selection_set(seleccionado[0])
        self.vacio_label.configure(
            text="" if clientes else
            "No hay clientes para mostrar. Creá uno con \"Nuevo cliente\" o "
            "al elegir Fiado como método de pago en una venta.")

    def update_summary(self, total_deuda: float, con_deuda: int) -> None:
        self.label_total_deuda.configure(text=money(total_deuda))
        self.label_con_deuda.configure(text=str(con_deuda))

    # ===== Cuenta corriente de un cliente =====

    def show_cuenta_dialog(self, cliente_id: int) -> None:
        ctrl = self.fiados_controller
        dialog = ttk.Toplevel(self)
        dialog.title("Cuenta del cliente")
        dialog.geometry("1120x873")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        _centrar(dialog)

        main = ttk.Frame(dialog, padding=20)
        main.pack(fill=BOTH, expand=True)

        header = ttk.Frame(main)
        header.pack(fill=X)
        nombre_label = ttk.Label(header, text="", font=("Segoe UI", 23, "bold"))
        nombre_label.pack(side=LEFT)
        contacto_label = ttk.Label(
            header, text="", font=("Segoe UI", 14), foreground="#566573")
        contacto_label.pack(side=RIGHT)

        saldo_card = ttk.Frame(main, bootstyle="light", padding=15)
        saldo_card.pack(fill=X, pady=(12, 12))
        debe_col = ttk.Frame(saldo_card, bootstyle="light")
        debe_col.pack(side=LEFT)
        ttk.Label(debe_col, text="Debe", font=("Segoe UI", 16)).pack(anchor=W)
        debe_label = ttk.Label(
            debe_col, text="", font=("Segoe UI", 25, "bold"))
        debe_label.pack(anchor=W)
        resumen_label = ttk.Label(
            saldo_card, text="", font=("Segoe UI", 14), justify=LEFT)
        resumen_label.pack(side=LEFT, padx=(40, 0))
        limite_label = ttk.Label(
            saldo_card, text="", font=("Segoe UI", 14, "bold"))
        limite_label.pack(side=RIGHT)

        botones = ttk.Frame(main)
        botones.pack(side=BOTTOM, fill=X, pady=(12, 0))

        tabla = ttk.Frame(main)
        tabla.pack(fill=BOTH, expand=True)
        columns = ("fecha", "tipo", "detalle", "monto", "saldo")
        tree = ttk.Treeview(tabla, columns=columns, show="headings",
                            height=12, selectmode="browse")
        for col, texto, ancho, anchor in (
            ("fecha", "Fecha", 175, "center"),
            ("tipo", "Movimiento", 155, "center"),
            ("detalle", "Detalle", 400, "w"),
            ("monto", "Monto", 130, "center"),
            ("saldo", "Saldo", 130, "center"),
        ):
            tree.heading(col, text=texto, anchor="center")
            tree.column(col, width=ancho, anchor=anchor)
        sb = ttk.Scrollbar(tabla, orient=VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=LEFT, fill=BOTH, expand=True)
        sb.pack(side=RIGHT, fill=Y)
        tree.tag_configure('pago', foreground='#27ae60')
        tree.tag_configure('anulada', foreground='#6c7a89')

        pagos_por_item = {}

        def recargar():
            cuenta = ctrl.get_cuenta(cliente_id)
            c = cuenta['cliente']
            nombre_label.configure(text=c['nombre'])
            partes = [p for p in (
                f"📞 {c['telefono']}" if c['telefono'] else "",
                f"DNI {c['dni']}" if c['dni'] else "",
                c['direccion']) if p]
            contacto_label.configure(text="   ·   ".join(partes))
            saldo = c['saldo']
            if saldo > 0.005:
                debe_label.configure(text=f"${saldo:.2f}", foreground="#c0392b")
            elif saldo < -0.005:
                debe_label.configure(
                    text=f"${-saldo:.2f} a favor", foreground="#27ae60")
            else:
                debe_label.configure(text="$0.00", foreground="#27ae60")
            resumen_label.configure(
                text=f"Total fiado: ${c['total_fiado']:.2f}\n"
                     f"Total pagado: ${c['total_pagado']:.2f}")
            limite = c.get('limite')
            if limite is None:
                limite_label.configure(text="Sin límite", foreground="#566573")
            elif not owner_lock.unlocked:
                excedido = saldo > limite + 0.005
                limite_label.configure(
                    text="⚠ Pasó su límite" if excedido
                    else f"Límite {TAPADO}",
                    foreground="#c0392b" if excedido else "#566573")
            elif saldo > limite + 0.005:
                limite_label.configure(
                    text=f"⚠ Pasó el límite (${limite:.2f}) por "
                         f"${saldo - limite:.2f}", foreground="#c0392b")
            else:
                limite_label.configure(
                    text=f"Límite ${limite:.2f} · disponible "
                         f"${max(limite - saldo, 0):.2f}", foreground="#566573")
            for i in tree.get_children():
                tree.delete(i)
            pagos_por_item.clear()
            movimientos_por_item.clear()
            for n, m in enumerate(cuenta['movimientos']):
                tags = ()
                if m['tipo'] == 'Pago':
                    tags = ('pago',)
                elif not m['cuenta']:
                    tags = ('anulada',)
                iid = str(n)
                movimientos_por_item[iid] = m
                if m['pago_id'] is not None:
                    pagos_por_item[iid] = m['pago_id']
                monto = m['monto']
                tree.insert('', END, iid=iid, tags=tags, values=(
                    ('Cuaderno' if m.get('anterior')
                     else formatear_fecha_hora(m['fecha'])),
                    m['tipo'], m['detalle'],
                    f"-${-monto:.2f}" if monto < 0 else f"+${monto:.2f}",
                    f"${m['saldo']:.2f}" if m['cuenta'] else "—"))

        movimientos_por_item = {}

        def ver_detalle(event=None):
            sel = tree.selection()
            if sel and sel[0] in movimientos_por_item:
                self._show_movimiento_dialog(
                    dialog, movimientos_por_item[sel[0]])
            return "break"

        tree.bind('<Double-1>', ver_detalle)
        tree.bind('<Return>', ver_detalle)

        def cobrar():
            self._show_pago_dialog(
                dialog, cliente_id, recargar)

        def anular():
            sel = tree.selection()
            if not sel or sel[0] not in pagos_por_item:
                messagebox.showwarning(
                    "Advertencia", "Seleccioná un pago de la lista.",
                    parent=dialog)
                return
            if ctrl.anular_pago(pagos_por_item[sel[0]]):
                recargar()

        def editar():
            ctrl.editar_cliente(cliente_id, despues=recargar)

        def eliminar():
            if ctrl.eliminar_cliente(cliente_id):
                dialog.destroy()

        ttk.Button(botones, text="💵 Registrar pago", bootstyle="success",
                   command=cobrar).pack(side=LEFT)
        ttk.Button(botones, text="Anular pago seleccionado",
                   bootstyle="warning-outline", command=anular
                   ).pack(side=LEFT, padx=(10, 0))
        ttk.Button(botones, text="Cerrar", bootstyle="secondary",
                   command=dialog.destroy).pack(side=RIGHT)
        ttk.Button(botones, text="Eliminar cliente",
                   bootstyle="danger-outline", command=eliminar
                   ).pack(side=RIGHT, padx=(0, 8))
        ttk.Button(botones, text="Editar datos", bootstyle="secondary-outline",
                   command=editar).pack(side=RIGHT, padx=(0, 8))

        ttk.Label(
            main, text="💡 Doble clic (o Enter) en un movimiento para ver "
                       "el detalle de la compra o del pago",
            font=("Segoe UI", 13), foreground="#566573"
        ).pack(side=BOTTOM, anchor=W, pady=(8, 0))

        dialog.bind('<Escape>', lambda e: dialog.destroy())
        recargar()
        fix_label_backgrounds(dialog)
        tree.focus_set()
        if tree.get_children():
            tree.selection_set(tree.get_children()[0])
            tree.focus(tree.get_children()[0])

    def _show_movimiento_dialog(self, parent, mov: dict) -> None:
        """Detalle de un movimiento de la cuenta: qué se compró (con
        precios y cómo se pagó) o los datos del pago."""
        ctrl = self.fiados_controller
        if mov.get('anterior'):
            messagebox.showinfo(
                "Saldo anterior",
                f"Esta es la deuda de ${mov['monto']:.2f} que ya estaba "
                "anotada en el cuaderno de papel cuando se cargó el cliente "
                "en la app.\nNo tiene detalle de productos.", parent=parent)
            return
        dialog = ttk.Toplevel(parent)
        es_pago = mov['tipo'] == 'Pago'
        dialog.title("Detalle del pago" if es_pago else "Detalle de la compra")
        dialog.geometry("860x720")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()
        _centrar(dialog)

        main = ttk.Frame(dialog, padding=22)
        main.pack(fill=BOTH, expand=True)

        botones = ttk.Frame(main)
        botones.pack(side=BOTTOM, fill=X, pady=(12, 0))
        ttk.Button(botones, text="Cerrar (Enter)", bootstyle="primary",
                   command=dialog.destroy).pack(side=RIGHT)
        dialog.bind('<Return>', lambda e: dialog.destroy())
        dialog.bind('<Escape>', lambda e: dialog.destroy())

        fecha = formatear_fecha_hora(mov['fecha'])
        if es_pago:
            ttk.Label(main, text="💵 Pago recibido",
                      font=("Segoe UI", 23, "bold"), foreground="#27ae60"
                      ).pack(anchor=W)
            ttk.Label(main, text=fecha, font=("Segoe UI", 16)
                      ).pack(anchor=W, pady=(4, 18))
            for etiqueta, valor in (
                    ("Monto", f"${-mov['monto']:.2f}"),
                    ("Forma de pago", mov.get('forma_pago', '').capitalize()),
                    ("Nota", mov.get('nota') or "—"),
                    ("Saldo después del pago", f"${mov['saldo']:.2f}")):
                fila = ttk.Frame(main)
                fila.pack(fill=X, pady=5)
                ttk.Label(fila, text=etiqueta + ":", font=("Segoe UI", 16),
                          foreground="#566573", width=24).pack(side=LEFT)
                ttk.Label(fila, text=valor, font=("Segoe UI", 18, "bold")
                          ).pack(side=LEFT)
            return

        d = ctrl.get_detalle_venta(mov['sale_id'])
        v = d['venta']
        anulada = v.get('status') == 'cancelled'
        ttk.Label(
            main,
            text=f"🛒 Venta N° {mov['sale_id']}"
                 + ("  (ANULADA)" if anulada else ""),
            font=("Segoe UI", 23, "bold"),
            foreground="#c0392b" if anulada else "#2c3e50").pack(anchor=W)
        ttk.Label(main, text=fecha, font=("Segoe UI", 16)
                  ).pack(anchor=W, pady=(4, 12))

        cols = ("producto", "cantidad", "precio", "subtotal")
        tabla = ttk.Treeview(main, columns=cols, show="headings", height=7,
                             selectmode="none")
        for col, texto, ancho, anchor in (
                ("producto", "Producto", 380, "w"),
                ("cantidad", "Cant.", 90, "center"),
                ("precio", "Precio", 150, "center"),
                ("subtotal", "Subtotal", 160, "center")):
            tabla.heading(col, text=texto, anchor="center")
            tabla.column(col, width=ancho, anchor=anchor)
        for it in d['items']:
            tabla.insert('', END, values=(
                it['nombre'], it['cantidad'], f"${it['precio']:.2f}",
                f"${it['cantidad'] * it['precio']:.2f}"))
        tabla.pack(fill=X)

        total = float(v.get('total', 0))
        resumen = ttk.Frame(main)
        resumen.pack(fill=X, pady=(14, 0))
        ttk.Label(resumen, text=f"Total de la compra: ${total:.2f}",
                  font=("Segoe UI", 19, "bold")).pack(anchor=W)
        nombres = {'efectivo': 'Efectivo', 'transferencia': 'Transferencia',
                   'posnet': 'Posnet', 'fiado': 'Fiado'}
        for p in d['pagos']:
            es_fiado = p['metodo'] == 'fiado'
            ttk.Label(
                resumen,
                text=f"{'📒' if es_fiado else '✔'} "
                     f"{nombres.get(p['metodo'], p['metodo'])}: "
                     f"${p['monto']:.2f}"
                     + ("  ← queda a cuenta" if es_fiado else "  (pagado)"),
                font=("Segoe UI", 16),
                foreground="#c0392b" if es_fiado else "#27ae60"
            ).pack(anchor=W, pady=2)

    def _show_pago_dialog(self, parent, cliente_id: int, despues) -> None:
        """Registrar un pago del cliente: por defecto el total de lo que
        debe, pero se puede poner una parte (el resto sigue como deuda)."""
        ctrl = self.fiados_controller
        cliente = ctrl.db.get_cliente(cliente_id)
        saldo = cliente['saldo']

        dialog = ttk.Toplevel(parent)
        dialog.title("Registrar pago")
        dialog.geometry("537x644")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()
        _centrar(dialog)

        main = ttk.Frame(dialog, padding=20)
        main.pack(fill=BOTH, expand=True)

        ttk.Label(main, text="💵 Registrar pago",
                  font=("Segoe UI", 20, "bold")).pack(pady=(0, 5))
        ttk.Label(main, text=cliente['nombre'],
                  font=("Segoe UI", 16)).pack()
        ttk.Label(main, text=f"Debe: ${max(saldo, 0):.2f}",
                  font=("Segoe UI", 16, "bold"), foreground="#c0392b"
                  ).pack(pady=(4, 15))

        monto_row = ttk.Frame(main)
        monto_row.pack(fill=X, pady=(0, 5))
        ttk.Label(monto_row, text="Monto que paga:",
                  font=("Segoe UI", 15)).pack(side=LEFT)
        ttk.Button(
            monto_row, text="Todo", bootstyle="info-outline",
            command=lambda: (monto_entry.delete(0, 'end'),
                             monto_entry.insert(0, f"{max(saldo, 0):.2f}"),
                             actualizar_resta())
        ).pack(side=RIGHT)
        monto_entry = ttk.Entry(main, font=("Segoe UI", 17))
        monto_entry.pack(fill=X, pady=(0, 6))
        if saldo > 0.005:
            monto_entry.insert(0, f"{saldo:.2f}")
        monto_entry.focus()
        monto_entry.select_range(0, 'end')

        resta_label = ttk.Label(main, text="", font=("Segoe UI", 15, "bold"))
        resta_label.pack(anchor=W, pady=(0, 12))

        def actualizar_resta(*_):
            try:
                monto = parse_monto(monto_entry.get())
            except ValueError:
                resta_label.configure(text="Monto inválido",
                                      foreground="#c0392b")
                return
            if not monto or monto <= 0:
                resta_label.configure(text="")
                return
            resta = saldo - monto
            if resta > 0.005:
                resta_label.configure(
                    text=f"Le quedan debiendo ${resta:.2f}",
                    foreground="#e67e22")
            elif resta < -0.005:
                resta_label.configure(
                    text=f"Paga ${-resta:.2f} de más (quedaría a favor)",
                    foreground="#c0392b")
            else:
                resta_label.configure(
                    text="Cancela toda la deuda ✓", foreground="#27ae60")

        monto_entry.bind('<KeyRelease>', actualizar_resta)
        actualizar_resta()

        ttk.Label(main, text="Forma de pago:",
                  font=("Segoe UI", 15)).pack(anchor=W, pady=(0, 5))
        forma = {'valor': 'efectivo'}
        forma_row = ttk.Frame(main)
        forma_row.pack(fill=X, pady=(0, 12))
        botones_forma = {}

        def elegir_forma(f):
            forma['valor'] = f
            for k, b in botones_forma.items():
                b.configure(bootstyle="primary" if k == f else "secondary")

        for f, texto in (('efectivo', 'Efectivo'),
                         ('transferencia', 'Transferencia'),
                         ('posnet', 'Posnet')):
            b = ttk.Button(forma_row, text=texto, width=13,
                           bootstyle="primary" if f == 'efectivo'
                           else "secondary",
                           command=lambda f=f: elegir_forma(f))
            b.pack(side=LEFT, padx=(0, 5))
            botones_forma[f] = b

        ttk.Label(main, text="Nota (opcional):",
                  font=("Segoe UI", 15)).pack(anchor=W, pady=(0, 5))
        nota_entry = ttk.Entry(main, font=("Segoe UI", 15))
        nota_entry.pack(fill=X)

        def confirmar():
            try:
                monto = parse_monto(monto_entry.get())
                if not monto or monto <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Ingrese un monto válido",
                                     parent=dialog)
                return
            if monto > saldo + 0.005 and not messagebox.askyesno(
                    "Paga de más",
                    f"El pago (${monto:.2f}) es mayor que la deuda "
                    f"(${max(saldo, 0):.2f}).\n"
                    "El cliente va a quedar con saldo a favor. ¿Seguir?",
                    parent=dialog):
                return
            quedaria = saldo - monto
            if not confirmar_enter(
                    dialog, "Confirmar pago",
                    [(f"{cliente['nombre']} paga ${monto:.2f}", "#2c3e50"),
                     (f"Forma de pago: {forma['valor'].capitalize()}",
                      "#2c3e50"),
                     (f"Le quedan debiendo ${quedaria:.2f}" if quedaria > 0.005
                      else ("Cancela toda la deuda ✓" if quedaria > -0.005
                            else f"Queda ${-quedaria:.2f} a favor"),
                      "#27ae60" if quedaria <= 0.005 else "#e67e22")]):
                return
            if ctrl.registrar_pago(cliente_id, monto, forma['valor'],
                                   nota_entry.get().strip()):
                dialog.destroy()
                despues()

        botones = ttk.Frame(main)
        botones.pack(side=BOTTOM, fill=X)
        ttk.Button(botones, text="Confirmar pago", bootstyle="success",
                   command=confirmar).pack(side=RIGHT, padx=(5, 0))
        ttk.Button(botones, text="Cancelar", bootstyle="secondary",
                   command=dialog.destroy).pack(side=RIGHT)
        dialog.bind('<Return>', lambda e: confirmar() or "break")
        dialog.bind('<Escape>', lambda e: dialog.destroy())
