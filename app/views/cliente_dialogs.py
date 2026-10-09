"""Diálogos de clientes (cuaderno de fiados) compartidos entre Ventas y la
pestaña Fiados: el formulario de alta/edición y el selector de cliente."""

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox


def _centrar(dialog) -> None:
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f'{width}x{height}+{x}+{y}')


def parse_monto(texto: str):
    """Convierte lo tipeado a número (acepta coma decimal). Devuelve None
    si está vacío y lanza ValueError si no es un número."""
    texto = (texto or '').strip().replace(',', '.')
    if not texto:
        return None
    return float(texto)


def show_cliente_form(parent, on_save, cliente: dict = None) -> None:
    """Formulario para crear (cliente=None) o editar un cliente.

    `on_save(data)` recibe un dict con nombre, telefono, dni, direccion,
    notas y limite (float o None); tiene que devolver algo verdadero si se
    guardó bien (entonces el diálogo se cierra) o falso si no (queda
    abierto para corregir)."""
    editando = cliente is not None
    dialog = ttk.Toplevel(parent)
    dialog.title("Editar cliente" if editando else "Nuevo cliente")
    dialog.geometry("582x736")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    _centrar(dialog)

    main = ttk.Frame(dialog, padding=20)
    main.pack(fill=BOTH, expand=True)

    ttk.Label(
        main, text="✏️ Editar cliente" if editando else "➕ Nuevo cliente",
        font=("Segoe UI", 20, "bold")
    ).pack(pady=(0, 15))

    entries = {}

    def campo(clave, etiqueta, valor=''):
        ttk.Label(main, text=etiqueta, font=("Segoe UI", 14)).pack(
            anchor=W, pady=(0, 3))
        entry = ttk.Entry(main, font=("Segoe UI", 15))
        entry.pack(fill=X, pady=(0, 10))
        if valor not in (None, ''):
            entry.insert(0, str(valor))
        entries[clave] = entry

    c = cliente or {}
    campo('nombre', "Nombre y apellido *", c.get('nombre', ''))
    campo('telefono', "Teléfono", c.get('telefono', ''))
    campo('dni', "DNI (opcional)", c.get('dni', ''))
    campo('direccion', "Dirección (opcional)", c.get('direccion', ''))
    limite = c.get('limite')
    campo('limite', "Límite de fiado en $ (vacío = sin límite; solo avisa)",
          f"{limite:.2f}" if limite is not None else '')
    campo('notas', "Notas (opcional)", c.get('notas', ''))
    entries['nombre'].focus()

    def guardar():
        nombre = entries['nombre'].get().strip()
        if not nombre:
            messagebox.showerror("Error", "Ingrese el nombre del cliente",
                                 parent=dialog)
            return
        try:
            limite_val = parse_monto(entries['limite'].get())
            if limite_val is not None and limite_val < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Ingrese un límite válido",
                                 parent=dialog)
            return
        data = {
            'nombre': nombre,
            'telefono': entries['telefono'].get().strip(),
            'dni': entries['dni'].get().strip(),
            'direccion': entries['direccion'].get().strip(),
            'notas': entries['notas'].get().strip(),
            'limite': limite_val,
        }
        if on_save(data):
            dialog.destroy()

    botones = ttk.Frame(main)
    botones.pack(side=BOTTOM, fill=X, pady=(10, 0))
    ttk.Button(botones, text="Guardar", bootstyle="success",
               command=guardar).pack(side=RIGHT, padx=(5, 0))
    ttk.Button(botones, text="Cancelar", bootstyle="secondary",
               command=dialog.destroy).pack(side=RIGHT)

    dialog.bind('<Return>', lambda e: guardar() or "break")
    dialog.bind('<Escape>', lambda e: dialog.destroy())


def show_cliente_picker(parent, buscar_fn, crear_fn, monto_fiado: float):
    """Ventana para elegir a quién se le anota el fiado: buscador, deuda
    actual de cada uno y botón para crear uno nuevo en el momento.

    `buscar_fn(texto)` devuelve la lista de clientes (dicts con saldo);
    `crear_fn(data)` crea uno y devuelve su dict (o None si falló).
    Bloquea hasta que se cierra y devuelve el cliente elegido o None."""
    resultado = {'cliente': None}
    clientes_por_id = {}

    dialog = ttk.Toplevel(parent)
    dialog.title("Fiado - elegir cliente")
    dialog.geometry("761x736")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    _centrar(dialog)

    main = ttk.Frame(dialog, padding=20)
    main.pack(fill=BOTH, expand=True)

    ttk.Label(main, text="📒 ¿A quién se le anota?",
              font=("Segoe UI", 20, "bold")).pack(pady=(0, 5))
    ttk.Label(main, text=f"Monto a fiar: ${monto_fiado:.2f}",
              font=("Segoe UI", 16), foreground="#c0392b").pack(pady=(0, 12))

    search_var = ttk.StringVar()
    search_entry = ttk.Entry(main, textvariable=search_var,
                             font=("Segoe UI", 16))
    search_entry.pack(fill=X, pady=(0, 10))
    search_entry.focus()
    ttk.Label(main, text="Buscá por nombre, teléfono o DNI",
              font=("Segoe UI", 13), foreground="#566573").pack(
        anchor=W, pady=(0, 8))

    botones = ttk.Frame(main)
    botones.pack(side=BOTTOM, fill=X, pady=(10, 0))

    table = ttk.Frame(main)
    table.pack(fill=BOTH, expand=True)
    tree = ttk.Treeview(table, columns=("nombre", "telefono", "debe"),
                        show="headings", height=9, selectmode="browse")
    tree.heading("nombre", text="Nombre", anchor="center")
    tree.heading("telefono", text="Teléfono", anchor="center")
    tree.heading("debe", text="Debe", anchor="center")
    tree.column("nombre", width=313, anchor="w")
    tree.column("telefono", width=190, anchor="center")
    tree.column("debe", width=145, anchor="center")
    sb = ttk.Scrollbar(table, orient=VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side=LEFT, fill=BOTH, expand=True)
    sb.pack(side=RIGHT, fill=Y)

    def render(seleccionar_id=None):
        clientes = buscar_fn(search_var.get())
        clientes_por_id.clear()
        for i in tree.get_children():
            tree.delete(i)
        for cl in clientes:
            clientes_por_id[cl['id']] = cl
            tree.insert('', END, iid=str(cl['id']), values=(
                cl['nombre'], cl['telefono'], f"${cl['saldo']:.2f}"))
        destino = (str(seleccionar_id) if seleccionar_id
                   else (str(clientes[0]['id']) if clientes else None))
        if destino and tree.exists(destino):
            tree.selection_set(destino)
            tree.focus(destino)

    def elegir(event=None):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning(
                "Advertencia", "Seleccioná un cliente o creá uno nuevo.",
                parent=dialog)
            return "break"
        resultado['cliente'] = clientes_por_id[int(sel[0])]
        dialog.destroy()
        return "break"

    def nuevo():
        def guardar(data):
            cliente = crear_fn(data)
            if not cliente:
                return False
            # Un cliente recién creado se elige directo: es el caso típico
            # (alguien que fían por primera vez) y evita un paso más.
            resultado['cliente'] = cliente
            dialog.after(0, dialog.destroy)
            return True
        show_cliente_form(dialog, guardar)

    search_var.trace_add('write', lambda *a: render())
    tree.bind('<Double-1>', elegir)
    # Flechas arriba/abajo desde el buscador mueven la selección.
    def mover(delta):
        items = tree.get_children()
        if not items:
            return "break"
        sel = tree.selection()
        idx = items.index(sel[0]) + delta if sel else 0
        idx = max(0, min(len(items) - 1, idx))
        tree.selection_set(items[idx])
        tree.see(items[idx])
        return "break"
    search_entry.bind('<Down>', lambda e: mover(1))
    search_entry.bind('<Up>', lambda e: mover(-1))
    dialog.bind('<Return>', elegir)
    dialog.bind('<Escape>', lambda e: dialog.destroy())

    ttk.Button(botones, text="Seleccionar", bootstyle="success",
               command=elegir).pack(side=RIGHT, padx=(5, 0))
    ttk.Button(botones, text="Cancelar", bootstyle="secondary",
               command=dialog.destroy).pack(side=RIGHT)
    ttk.Button(botones, text="➕ Nuevo cliente", bootstyle="info",
               command=nuevo).pack(side=LEFT)

    render()
    dialog.wait_window()
    return resultado['cliente']


def confirmar_enter(parent, titulo: str, lineas: list,
                    texto_boton: str = "Confirmar (Enter)") -> bool:
    """Último paso antes de anotar algo: muestra un resumen grande y se
    confirma con Enter (o con el botón); Esc cancela. `lineas` es una lista
    de (texto, color) con el resumen a mostrar. Bloquea hasta que se cierra
    y devuelve True si se confirmó."""
    import time
    resultado = {'ok': False}
    abierto_en = time.time()

    dialog = ttk.Toplevel(parent)
    dialog.title(titulo)
    dialog.geometry("640x420")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()
    _centrar(dialog)

    main = ttk.Frame(dialog, padding=25)
    main.pack(fill=BOTH, expand=True)
    ttk.Label(main, text=titulo, font=("Segoe UI", 20, "bold")
              ).pack(pady=(0, 15))
    for texto, color in lineas:
        ttk.Label(main, text=texto, font=("Segoe UI", 16), foreground=color,
                  wraplength=580, justify=CENTER).pack(pady=3)

    def confirmar(event=None):
        # Evita que el mismo Enter con el que se abrió este paso (o una
        # repetición de tecla) lo confirme sin que se haya leído.
        if time.time() - abierto_en < 0.35:
            return "break"
        resultado['ok'] = True
        dialog.destroy()
        return "break"

    botones = ttk.Frame(main)
    botones.pack(side=BOTTOM, fill=X)
    boton = ttk.Button(botones, text=texto_boton, bootstyle="success",
                       command=confirmar)
    boton.pack(side=RIGHT, padx=(8, 0))
    ttk.Button(botones, text="Volver (Esc)", bootstyle="secondary",
               command=dialog.destroy).pack(side=RIGHT)
    boton.focus_set()
    dialog.bind('<Return>', confirmar)
    dialog.bind('<Escape>', lambda e: dialog.destroy())
    dialog.wait_window()
    return resultado['ok']
