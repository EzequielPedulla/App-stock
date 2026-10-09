import sqlite3
import unicodedata
from datetime import datetime
from .product import Product
from config import DB_PATH


def _normalizar(texto) -> str:
    """Minúsculas y sin tildes, para buscar 'jose' y encontrar 'José'."""
    if texto is None:
        return ''
    sin_tildes = unicodedata.normalize('NFD', str(texto))
    return ''.join(
        c for c in sin_tildes if unicodedata.category(c) != 'Mn').lower()


class Database:
    _instance = None
    _connection = None

    def __new__(cls):
        """Implementa el patrón Singleton para asegurar una única instancia."""
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Inicializa la conexión solo si no existe."""
        if Database._connection is None:
            Database._connection = sqlite3.connect(str(DB_PATH))
            Database._connection.row_factory = sqlite3.Row
            Database._connection.create_function('norm', 1, _normalizar)
            Database._connection.execute('PRAGMA foreign_keys = ON')
            self.connection = Database._connection
            self.cursor = self.connection.cursor()
            self.create_tables()
        else:
            self.connection = Database._connection
            self.cursor = self.connection.cursor()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATETIME NOT NULL,
                total REAL NOT NULL,
                paid REAL NOT NULL,
                `change` REAL NOT NULL,
                payment_method VARCHAR(20) NOT NULL DEFAULT 'efectivo',
                status VARCHAR(20) DEFAULT 'active',
                cancelled_at DATETIME NULL,
                cancellation_reason TEXT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                payment_method VARCHAR(20) NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS caja_sesiones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL UNIQUE,
                fondo_inicial REAL NOT NULL DEFAULT 0,
                efectivo_contado REAL NULL,
                cerrada INTEGER NOT NULL DEFAULT 0,
                cerrada_at DATETIME NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS caja_movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sesion_id INTEGER NOT NULL,
                tipo VARCHAR(20) NOT NULL,
                descripcion VARCHAR(200) NOT NULL,
                monto REAL NOT NULL,
                fecha DATETIME NOT NULL,
                forma_pago VARCHAR(20) NOT NULL DEFAULT 'efectivo',
                FOREIGN KEY (sesion_id) REFERENCES caja_sesiones(id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(100) NOT NULL,
                telefono VARCHAR(30) NOT NULL DEFAULT '',
                dni VARCHAR(20) NOT NULL DEFAULT '',
                direccion VARCHAR(150) NOT NULL DEFAULT '',
                notas TEXT NOT NULL DEFAULT '',
                limite REAL NULL,
                activo INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pagos_cliente (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                monto REAL NOT NULL,
                forma_pago VARCHAR(20) NOT NULL DEFAULT 'efectivo',
                fecha DATETIME NOT NULL,
                nota VARCHAR(200) NOT NULL DEFAULT '',
                movimiento_id INTEGER NULL,
                FOREIGN KEY (cliente_id) REFERENCES clientes(id)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                key VARCHAR(50) PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')

        self._migrate_add_payment_method_column()
        self._migrate_add_forma_pago_column()
        self._migrate_add_cliente_id_column()
        self.connection.commit()

    def _migrate_add_payment_method_column(self):
        """Agrega payment_method a bases creadas antes de que existiera esta
        columna (CREATE TABLE IF NOT EXISTS no la agrega sola)."""
        self.cursor.execute("PRAGMA table_info(sales)")
        columns = [row[1] for row in self.cursor.fetchall()]
        if 'payment_method' not in columns:
            self.cursor.execute(
                "ALTER TABLE sales ADD COLUMN payment_method "
                "VARCHAR(20) NOT NULL DEFAULT 'efectivo'"
            )

    def _migrate_add_forma_pago_column(self):
        """Agrega forma_pago a caja_movimientos creadas antes de que
        existiera esta columna."""
        self.cursor.execute("PRAGMA table_info(caja_movimientos)")
        columns = [row[1] for row in self.cursor.fetchall()]
        if 'forma_pago' not in columns:
            self.cursor.execute(
                "ALTER TABLE caja_movimientos ADD COLUMN forma_pago "
                "VARCHAR(20) NOT NULL DEFAULT 'efectivo'"
            )

    def _migrate_add_cliente_id_column(self):
        """Agrega cliente_id a sales (a quién se le fió la venta) en bases
        creadas antes de que existiera el cuaderno de fiados."""
        self.cursor.execute("PRAGMA table_info(sales)")
        columns = [row[1] for row in self.cursor.fetchall()]
        if 'cliente_id' not in columns:
            self.cursor.execute(
                "ALTER TABLE sales ADD COLUMN cliente_id INTEGER NULL "
                "REFERENCES clientes(id)")

    def add_product(self, product, commit=True):
        self.cursor.execute('''
            INSERT INTO products (barcode, name, price, stock)
            VALUES (?, ?, ?, ?)
        ''', (product.barcode, product.name, product.price, product.stock))
        if commit:
            self.connection.commit()

    def get_all_products(self):
        self.cursor.execute('SELECT * FROM products')
        rows = self.cursor.fetchall()
        return [Product.from_db_dict(dict(row)) for row in rows]

    def update_product(self, product, commit=True):
        self.cursor.execute('''
            UPDATE products
            SET barcode=?, name=?, price=?, stock=?
            WHERE id=?
        ''', (product.barcode, product.name, product.price, product.stock, product.id))
        if commit:
            self.connection.commit()

    def delete_product(self, product_id):
        self.cursor.execute('DELETE FROM products WHERE id=?', (product_id,))
        self.connection.commit()

    def get_product_by_id(self, product_id):
        self.cursor.execute(
            'SELECT * FROM products WHERE id=?', (product_id,))
        row = self.cursor.fetchone()
        return Product.from_db_dict(dict(row)) if row else None

    def get_product_by_barcode(self, barcode):
        self.cursor.execute(
            'SELECT * FROM products WHERE barcode=?', (barcode,))
        row = self.cursor.fetchone()
        return Product.from_db_dict(dict(row)) if row else None

    def add_sale(self, date: str, total: float, paid: float, change: float,
                 payment_method: str = 'efectivo', payments: list = None,
                 commit=True, cliente_id: int = None) -> int:
        """Registra una venta. `payments` es opcional y sirve para ventas
        pagadas con más de un método a la vez (ej. parte efectivo, parte
        transferencia): una lista de {'method': str, 'amount': float}. En
        ese caso `payment_method` debe ser 'mixto', y el detalle de cada
        pago se guarda aparte en sale_payments. Una venta total o
        parcialmente fiada ('fiado', o 'mixto' con una parte 'fiado') lleva
        `cliente_id`: a quién se le anotó lo que quedó sin cobrar."""
        self.cursor.execute(
            '''INSERT INTO sales (date, total, paid, `change`, payment_method,
                                  cliente_id)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (date, total, paid, change, payment_method, cliente_id)
        )
        sale_id = self.cursor.lastrowid
        if payments:
            for p in payments:
                self.cursor.execute(
                    '''INSERT INTO sale_payments (sale_id, payment_method, amount)
                       VALUES (?, ?, ?)''',
                    (sale_id, p['method'], p['amount'])
                )
        if commit:
            self.connection.commit()
        return sale_id

    def add_sale_detail(self, sale_id: int, product_id: int, quantity: int, unit_price: float, commit=True) -> None:
        self.cursor.execute(
            '''INSERT INTO sale_details (sale_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)''',
            (sale_id, product_id, quantity, unit_price)
        )
        if commit:
            self.connection.commit()

    def execute_query(self, query, params=None):
        """Ejecuta una consulta SELECT y retorna los resultados como lista de diccionarios"""
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            return result
        except Exception as e:
            print(f"Error en consulta: {e}")
            return []

    def cancel_sale(self, sale_id: int, reason: str = "Sin especificar") -> bool:
        """
        Anula una venta y reintegra el stock.

        Args:
            sale_id: ID de la venta a anular
            reason: Motivo de la anulación

        Returns:
            bool: True si se anuló correctamente, False en caso contrario
        """
        try:
            # Verificar que la venta existe y está activa
            query = "SELECT status FROM sales WHERE id = ?"
            result = self.execute_query(query, (sale_id,))

            if not result:
                print(f"Venta {sale_id} no encontrada")
                return False

            if result[0]['status'] == 'cancelled':
                print(f"Venta {sale_id} ya está anulada")
                return False

            # Obtener detalles de la venta para reintegrar stock
            query = """
                SELECT product_id, quantity
                FROM sale_details
                WHERE sale_id = ?
            """
            details = self.execute_query(query, (sale_id,))

            # Reintegrar stock de cada producto (excepto VARIOS), en la misma transacción
            for detail in details:
                product = self.get_product_by_id(detail['product_id'])
                if product and not product.barcode.startswith('VAR'):
                    product.stock += detail['quantity']
                    self.update_product(product, commit=False)

            # Marcar venta como anulada
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            update_query = """
                UPDATE sales
                SET status = 'cancelled',
                    cancelled_at = ?,
                    cancellation_reason = ?
                WHERE id = ?
            """
            self.cursor.execute(update_query, (now, reason, sale_id))
            self.connection.commit()

            return True

        except Exception as e:
            print(f"Error al anular venta: {e}")
            self.connection.rollback()
            return False

    def get_caja_sesion_by_fecha(self, fecha: str):
        """Devuelve la sesión de caja de un día (dict) o None si no existe."""
        result = self.execute_query(
            "SELECT * FROM caja_sesiones WHERE fecha = ?", (fecha,))
        return result[0] if result else None

    def get_last_caja_sesion(self):
        """Devuelve la última sesión de caja registrada (dict) o None."""
        result = self.execute_query(
            "SELECT * FROM caja_sesiones ORDER BY fecha DESC LIMIT 1")
        return result[0] if result else None

    def get_caja_sesion_abierta_anterior(self, fecha_hoy: str):
        """Devuelve la sesión sin cerrar más antigua de un día previo a
        `fecha_hoy` (dict) o None. Sirve para avisar que quedó un día sin
        cerrar la caja."""
        result = self.execute_query(
            """SELECT * FROM caja_sesiones
               WHERE cerrada = 0 AND fecha < ?
               ORDER BY fecha ASC LIMIT 1""",
            (fecha_hoy,)
        )
        return result[0] if result else None

    def create_caja_sesion(self, fecha: str, fondo_inicial: float) -> int:
        self.cursor.execute(
            "INSERT INTO caja_sesiones (fecha, fondo_inicial) VALUES (?, ?)",
            (fecha, fondo_inicial)
        )
        self.connection.commit()
        return self.cursor.lastrowid

    def update_caja_fondo_inicial(self, sesion_id: int, fondo_inicial: float) -> None:
        self.cursor.execute(
            "UPDATE caja_sesiones SET fondo_inicial = ? WHERE id = ?",
            (fondo_inicial, sesion_id)
        )
        self.connection.commit()

    def cerrar_caja_sesion(self, sesion_id: int, efectivo_contado: float) -> None:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(
            """UPDATE caja_sesiones
               SET efectivo_contado = ?, cerrada = 1, cerrada_at = ?
               WHERE id = ?""",
            (efectivo_contado, now, sesion_id)
        )
        self.connection.commit()

    def add_caja_movimiento(self, sesion_id: int, tipo: str, descripcion: str,
                            monto: float, forma_pago: str = 'efectivo') -> int:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(
            """INSERT INTO caja_movimientos
               (sesion_id, tipo, descripcion, monto, fecha, forma_pago)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sesion_id, tipo, descripcion, monto, now, forma_pago)
        )
        self.connection.commit()
        return self.cursor.lastrowid

    def update_caja_movimiento(self, movimiento_id: int, descripcion: str,
                               monto: float, forma_pago: str) -> None:
        self.cursor.execute(
            """UPDATE caja_movimientos
               SET descripcion = ?, monto = ?, forma_pago = ?
               WHERE id = ?""",
            (descripcion, monto, forma_pago, movimiento_id)
        )
        self.connection.commit()

    def get_caja_movimientos(self, sesion_id: int) -> list:
        """Devuelve los movimientos del día, el más reciente primero (el
        cargado hace rato queda al final de la lista)."""
        return self.execute_query(
            "SELECT * FROM caja_movimientos WHERE sesion_id = ? ORDER BY id DESC",
            (sesion_id,)
        )

    def delete_caja_movimiento(self, movimiento_id: int) -> None:
        self.cursor.execute(
            "DELETE FROM caja_movimientos WHERE id = ?", (movimiento_id,))
        self.connection.commit()

    def get_numero_venta_del_dia(self, sale_id: int, fecha_dia: str) -> int:
        """Número de orden de una venta dentro de su día (1, 2, 3...), según
        el orden en que se cargaron (por id). No cambia si esa venta u otra
        del mismo día se anula después: se cuenta el lugar que ocupó al
        crearse, no cuántas siguen activas."""
        result = self.execute_query(
            "SELECT COUNT(*) as n FROM sales WHERE date LIKE ? AND id <= ?",
            (f"{fecha_dia}%", sale_id)
        )
        return int(result[0]['n']) if result else 1

    def update_sale_payment_method(self, sale_id: int, payment_method: str,
                                   cliente_id: int = None) -> None:
        """Corrige el método de pago de una venta ya cargada (por si se
        cargó mal al momento de la venta). Solo admite pasar a un método
        simple (no a 'mixto'): si la venta tenía un pago dividido, se
        borran sus filas de sale_payments para que no se sigan sumando
        aparte en get_ventas_totales_por_metodo."""
        # Solo una venta fiada lleva cliente (a quién se le anotó la deuda).
        self.cursor.execute(
            "UPDATE sales SET payment_method = ?, cliente_id = ? WHERE id = ?",
            (payment_method,
             cliente_id if payment_method == 'fiado' else None, sale_id)
        )
        self.cursor.execute(
            "DELETE FROM sale_payments WHERE sale_id = ?", (sale_id,))
        self.connection.commit()

    def get_ventas_totales_por_metodo(self, fecha: str) -> dict:
        """Suma el total de ventas activas de un día, por método de pago.
        Usa `total` (no `paid`): en efectivo es lo que efectivamente queda
        en el cajón (lo que se recibe menos el vuelto que sale del mismo
        cajón, neto = total); en fiado no entra nada de plata todavía.

        Las ventas con un solo método se suman directo desde `sales`. Las
        ventas con pago dividido ('mixto') se suman desde sale_payments,
        que guarda cuánto se pagó con cada método.
        """
        totales = {'efectivo': 0.0, 'transferencia': 0.0,
                  'posnet': 0.0, 'fiado': 0.0}

        result = self.execute_query(
            """SELECT payment_method, COALESCE(SUM(total), 0) as total
               FROM sales
               WHERE status = 'active' AND date LIKE ? AND payment_method != 'mixto'
               GROUP BY payment_method""",
            (f"{fecha}%",)
        )
        for row in result:
            totales[row['payment_method']] = float(row['total'])

        divididos = self.execute_query(
            """SELECT sp.payment_method, COALESCE(SUM(sp.amount), 0) as total
               FROM sale_payments sp
               JOIN sales s ON s.id = sp.sale_id
               WHERE s.status = 'active' AND s.date LIKE ?
               GROUP BY sp.payment_method""",
            (f"{fecha}%",)
        )
        for row in divididos:
            metodo = row['payment_method']
            totales[metodo] = totales.get(metodo, 0.0) + float(row['total'])

        return totales

    def get_ventas_conteo_por_metodo(self, fecha: str) -> dict:
        """Igual que get_ventas_totales_por_metodo, pero además cuenta
        cuántos pagos se hicieron con cada método (Reportes lo usa para el
        resumen del día). Una venta 'mixto' cuenta como un pago por cada
        método que usó, no como una venta entera de un solo método: así
        el resumen queda consistente con cómo Caja separa el efectivo real
        de una venta dividida del resto."""
        resumen = {
            'efectivo': {'cantidad': 0, 'total': 0.0},
            'transferencia': {'cantidad': 0, 'total': 0.0},
            'posnet': {'cantidad': 0, 'total': 0.0},
            'fiado': {'cantidad': 0, 'total': 0.0},
        }

        result = self.execute_query(
            """SELECT payment_method, COUNT(*) as cantidad,
                      COALESCE(SUM(total), 0) as total
               FROM sales
               WHERE status = 'active' AND date LIKE ? AND payment_method != 'mixto'
               GROUP BY payment_method""",
            (f"{fecha}%",)
        )
        for row in result:
            metodo = row['payment_method']
            if metodo in resumen:
                resumen[metodo]['cantidad'] = int(row['cantidad'])
                resumen[metodo]['total'] = float(row['total'])

        divididos = self.execute_query(
            """SELECT sp.payment_method, COUNT(*) as cantidad,
                      COALESCE(SUM(sp.amount), 0) as total
               FROM sale_payments sp
               JOIN sales s ON s.id = sp.sale_id
               WHERE s.status = 'active' AND s.date LIKE ?
               GROUP BY sp.payment_method""",
            (f"{fecha}%",)
        )
        for row in divididos:
            metodo = row['payment_method']
            if metodo not in resumen:
                resumen[metodo] = {'cantidad': 0, 'total': 0.0}
            resumen[metodo]['cantidad'] += int(row['cantidad'])
            resumen[metodo]['total'] += float(row['total'])

        return resumen

    def get_total_cobros_dia(self, fecha: str) -> float:
        """Total cobrado en el día por ventas que habían quedado fiadas
        (cualquier forma de pago). Se une por caja_sesiones.fecha (no por
        la fecha/hora cruda del movimiento) porque un movimiento cargado
        mientras se edita un día anterior sin cerrar queda con la marca de
        tiempo real de cuando se cargó, no la del día de esa sesión."""
        result = self.execute_query(
            """SELECT COALESCE(SUM(cm.monto), 0) as total
               FROM caja_movimientos cm
               JOIN caja_sesiones cs ON cs.id = cm.sesion_id
               WHERE cm.tipo = 'cobro' AND cs.fecha = ?""",
            (fecha,)
        )
        return float(result[0]['total']) if result else 0.0

    def get_cantidad_ventas_dia(self, fecha: str) -> int:
        """Cantidad de ventas activas (no anuladas) de un día que ya se
        cobraron (no cuenta fiado: todavía no entró esa plata), para que
        coincida con el mismo criterio que el total vendido."""
        result = self.execute_query(
            """SELECT COUNT(*) as n FROM sales
               WHERE status = 'active' AND date LIKE ? AND payment_method != 'fiado'""",
            (f"{fecha}%",)
        )
        return int(result[0]['n']) if result else 0

    def get_config(self, key: str):
        """Valor guardado para `key` (texto) o None si no existe."""
        result = self.execute_query(
            "SELECT value FROM config WHERE key = ?", (key,))
        return result[0]['value'] if result else None

    def set_config(self, key: str, value: str) -> None:
        self.cursor.execute(
            "INSERT INTO config (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value))
        self.connection.commit()

    # ===== Cuaderno de fiados =====

    # Cuánto de una venta quedó fiado: todo el total si fue 'fiado', o la
    # parte 'fiado' del detalle si fue un pago dividido ('mixto').
    _FIADO_DE_VENTA = """
        CASE WHEN s.payment_method = 'fiado' THEN s.total
             WHEN s.payment_method = 'mixto' THEN COALESCE((
                 SELECT SUM(sp.amount) FROM sale_payments sp
                 WHERE sp.sale_id = s.id AND sp.payment_method = 'fiado'), 0)
             ELSE 0 END"""

    def add_cliente(self, nombre: str, telefono: str = '', dni: str = '',
                    direccion: str = '', notas: str = '',
                    limite: float = None) -> int:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(
            """INSERT INTO clientes
               (nombre, telefono, dni, direccion, notas, limite, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (nombre, telefono, dni, direccion, notas, limite, now)
        )
        self.connection.commit()
        return self.cursor.lastrowid

    def update_cliente(self, cliente_id: int, nombre: str, telefono: str,
                       dni: str, direccion: str, notas: str,
                       limite: float = None) -> None:
        self.cursor.execute(
            """UPDATE clientes
               SET nombre = ?, telefono = ?, dni = ?, direccion = ?,
                   notas = ?, limite = ?
               WHERE id = ?""",
            (nombre, telefono, dni, direccion, notas, limite, cliente_id)
        )
        self.connection.commit()

    def set_cliente_activo(self, cliente_id: int, activo: bool) -> None:
        self.cursor.execute(
            "UPDATE clientes SET activo = ? WHERE id = ?",
            (1 if activo else 0, cliente_id))
        self.connection.commit()

    def delete_cliente(self, cliente_id: int) -> bool:
        """Borra un cliente solo si nunca tuvo movimientos; si tiene
        historial hay que desactivarlo (set_cliente_activo)."""
        usado = self.execute_query(
            """SELECT (SELECT COUNT(*) FROM sales WHERE cliente_id = ?) +
                      (SELECT COUNT(*) FROM pagos_cliente WHERE cliente_id = ?)
               AS n""", (cliente_id, cliente_id))
        if usado and int(usado[0]['n']) > 0:
            return False
        self.cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
        self.connection.commit()
        return True

    def get_clientes(self, texto: str = '', solo_con_deuda: bool = False,
                     incluir_inactivos: bool = False) -> list:
        """Lista de clientes (dict) con `total_fiado`, `total_pagado` y
        `saldo` (lo que deben). `texto` filtra por nombre, teléfono o DNI.
        Los que más deben primero, después por nombre."""
        condiciones = []
        params = []
        if not incluir_inactivos:
            condiciones.append("c.activo = 1")
        texto = _normalizar((texto or '').strip())
        if texto:
            condiciones.append(
                "(norm(c.nombre) LIKE ? OR norm(c.telefono) LIKE ? "
                "OR norm(c.dni) LIKE ?)")
            like = f"%{texto}%"
            params += [like, like, like]
        where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
        rows = self.execute_query(
            f"""SELECT c.*,
                  COALESCE((SELECT SUM({self._FIADO_DE_VENTA})
                            FROM sales s
                            WHERE s.cliente_id = c.id AND s.status = 'active'),
                           0) AS total_fiado,
                  COALESCE((SELECT SUM(p.monto) FROM pagos_cliente p
                            WHERE p.cliente_id = c.id), 0) AS total_pagado
                FROM clientes c {where}""", tuple(params))
        for r in rows:
            r['total_fiado'] = round(float(r['total_fiado']), 2)
            r['total_pagado'] = round(float(r['total_pagado']), 2)
            r['saldo'] = round(r['total_fiado'] - r['total_pagado'], 2)
        if solo_con_deuda:
            rows = [r for r in rows if r['saldo'] > 0.005]
        rows.sort(key=lambda r: (-r['saldo'], r['nombre'].lower()))
        return rows

    def get_cliente(self, cliente_id: int):
        """Un cliente (dict, con su saldo) o None."""
        for c in self.get_clientes(incluir_inactivos=True):
            if c['id'] == cliente_id:
                return c
        return None

    def get_ventas_fiadas_cliente(self, cliente_id: int) -> list:
        """Ventas con parte fiada del cliente (incluye las anuladas, con su
        `status`, para que se vea qué pasó), la más reciente primero. Cada
        una trae `fiado` (lo que quedó sin cobrar), `total` y `productos`
        (texto con el detalle)."""
        ventas = self.execute_query(
            f"""SELECT s.id, s.date, s.total, s.status,
                       {self._FIADO_DE_VENTA} AS fiado
                FROM sales s
                WHERE s.cliente_id = ?
                ORDER BY s.date DESC, s.id DESC""", (cliente_id,))
        for v in ventas:
            detalle = self.execute_query(
                """SELECT p.name, sd.quantity
                   FROM sale_details sd JOIN products p ON p.id = sd.product_id
                   WHERE sd.sale_id = ?""", (v['id'],))
            v['productos'] = ", ".join(
                f"{d['quantity']} x {d['name']}" for d in detalle)
        return ventas

    def get_pagos_cliente(self, cliente_id: int) -> list:
        return self.execute_query(
            "SELECT * FROM pagos_cliente WHERE cliente_id = ? "
            "ORDER BY fecha DESC, id DESC", (cliente_id,))

    def _get_or_create_caja_sesion_hoy(self) -> dict:
        """Sesión de caja de hoy; si todavía no se abrió, la crea con el
        mismo fondo inicial que CajaController (lo contado al cerrar el
        día anterior, o $0)."""
        hoy = datetime.now().strftime('%Y-%m-%d')
        sesion = self.get_caja_sesion_by_fecha(hoy)
        if sesion is None:
            anterior = self.get_last_caja_sesion()
            fondo = 0.0
            if anterior and anterior['efectivo_contado'] is not None:
                fondo = float(anterior['efectivo_contado'])
            self.create_caja_sesion(hoy, fondo)
            sesion = self.get_caja_sesion_by_fecha(hoy)
        return sesion

    def add_pago_cliente(self, cliente_id: int, monto: float,
                         forma_pago: str = 'efectivo', nota: str = '') -> bool:
        """Registra un pago (total o parcial) de un cliente y, si la caja
        de hoy sigue abierta, lo anota como 'Cobro (fiado)' para que entre
        en la plata del día. Devuelve True si quedó anotado en Caja; False
        si la caja de hoy ya estaba cerrada (el pago igual baja la deuda
        del cliente)."""
        cliente = self.get_cliente(cliente_id)
        nombre = cliente['nombre'] if cliente else 'cliente'
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sesion = self._get_or_create_caja_sesion_hoy()
        movimiento_id = None
        if not sesion['cerrada']:
            self.cursor.execute(
                """INSERT INTO caja_movimientos
                   (sesion_id, tipo, descripcion, monto, fecha, forma_pago)
                   VALUES (?, 'cobro', ?, ?, ?, ?)""",
                (sesion['id'], f"Cobro de fiado - {nombre}", monto, now,
                 forma_pago))
            movimiento_id = self.cursor.lastrowid
        self.cursor.execute(
            """INSERT INTO pagos_cliente
               (cliente_id, monto, forma_pago, fecha, nota, movimiento_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (cliente_id, monto, forma_pago, now, nota, movimiento_id))
        self.connection.commit()
        return movimiento_id is not None

    def delete_pago_cliente(self, pago_id: int) -> bool:
        """Anula un pago cargado por error (la deuda vuelve a subir y, si
        estaba en Caja, se saca de ahí). Si ese cobro quedó en una caja ya
        cerrada no se puede borrar: devuelve False."""
        pago = self.execute_query(
            "SELECT * FROM pagos_cliente WHERE id = ?", (pago_id,))
        if not pago:
            return False
        movimiento_id = pago[0]['movimiento_id']
        if movimiento_id is not None:
            cerrada = self.execute_query(
                """SELECT cs.cerrada FROM caja_movimientos cm
                   JOIN caja_sesiones cs ON cs.id = cm.sesion_id
                   WHERE cm.id = ?""", (movimiento_id,))
            if cerrada and cerrada[0]['cerrada']:
                return False
            self.cursor.execute(
                "DELETE FROM caja_movimientos WHERE id = ?", (movimiento_id,))
        self.cursor.execute(
            "DELETE FROM pagos_cliente WHERE id = ?", (pago_id,))
        self.connection.commit()
        return True

    # ===== Resumen por período =====

    def get_resumen_periodo(self, desde: str, hasta: str) -> dict:
        """Cálculo general de los días entre `desde` y `hasta` (YYYY-MM-DD,
        ambos incluidos), con la misma lógica que Caja: lo vendido no cuenta
        el fiado sin cobrar y suma lo cobrado de fiados; el resultado es
        vendido menos gastos (retiros y bolsillo no son gastos del negocio).

        Devuelve {'dias': [...], 'totales': {...}, 'productos': [...]}, con
        todos los días del rango (también los que no tuvieron movimiento)."""
        from datetime import date, timedelta

        d1 = date.fromisoformat(desde)
        d2 = date.fromisoformat(hasta)
        dias = {}
        d = d1
        while d <= d2:
            dias[d.isoformat()] = {
                'fecha': d.isoformat(), 'efectivo': 0.0,
                'transferencia': 0.0, 'posnet': 0.0, 'fiado': 0.0,
                'cobros': 0.0, 'gastos': 0.0, 'retiros': 0.0,
                'ventas': 0, 'total_ventas': 0.0}
            d += timedelta(days=1)
        rango = (desde, hasta)

        # Ventas de un solo método (las 'mixto' se reparten abajo)
        for r in self.execute_query(
                """SELECT substr(date, 1, 10) AS dia, payment_method,
                          SUM(total) AS total
                   FROM sales
                   WHERE status = 'active' AND payment_method != 'mixto'
                     AND substr(date, 1, 10) BETWEEN ? AND ?
                   GROUP BY dia, payment_method""", rango):
            if r['dia'] in dias and r['payment_method'] in dias[r['dia']]:
                dias[r['dia']][r['payment_method']] += float(r['total'])
        for r in self.execute_query(
                """SELECT substr(s.date, 1, 10) AS dia, sp.payment_method,
                          SUM(sp.amount) AS total
                   FROM sale_payments sp JOIN sales s ON s.id = sp.sale_id
                   WHERE s.status = 'active'
                     AND substr(s.date, 1, 10) BETWEEN ? AND ?
                   GROUP BY dia, sp.payment_method""", rango):
            if r['dia'] in dias and r['payment_method'] in dias[r['dia']]:
                dias[r['dia']][r['payment_method']] += float(r['total'])

        # Cantidad y monto total de las ventas (incluye las fiadas)
        for r in self.execute_query(
                """SELECT substr(date, 1, 10) AS dia, COUNT(*) AS n,
                          SUM(total) AS total
                   FROM sales
                   WHERE status = 'active'
                     AND substr(date, 1, 10) BETWEEN ? AND ?
                   GROUP BY dia""", rango):
            if r['dia'] in dias:
                dias[r['dia']]['ventas'] = int(r['n'])
                dias[r['dia']]['total_ventas'] = float(r['total'])

        # Movimientos de Caja: cobros de fiado, gastos y retiros
        for r in self.execute_query(
                """SELECT cs.fecha AS dia, cm.tipo, SUM(cm.monto) AS total
                   FROM caja_movimientos cm
                   JOIN caja_sesiones cs ON cs.id = cm.sesion_id
                   WHERE cm.tipo IN ('cobro', 'gasto', 'retiro')
                     AND cs.fecha BETWEEN ? AND ?
                   GROUP BY cs.fecha, cm.tipo""", rango):
            clave = {'cobro': 'cobros', 'gasto': 'gastos',
                     'retiro': 'retiros'}[r['tipo']]
            if r['dia'] in dias:
                dias[r['dia']][clave] += float(r['total'])

        lista = []
        for dia in sorted(dias):
            x = dias[dia]
            x['vendido'] = (x['efectivo'] + x['transferencia'] + x['posnet']
                            + x['cobros'])
            x['resultado'] = x['vendido'] - x['gastos']
            lista.append(x)

        claves = ('efectivo', 'transferencia', 'posnet', 'fiado', 'cobros',
                  'gastos', 'retiros', 'ventas', 'total_ventas', 'vendido',
                  'resultado')
        totales = {k: sum(x[k] for x in lista) for k in claves}
        totales['ticket_promedio'] = (
            totales['total_ventas'] / totales['ventas']
            if totales['ventas'] else 0.0)
        totales['dias'] = len(lista)
        totales['fiado_pendiente'] = sum(
            c['saldo'] for c in self.get_clientes() if c['saldo'] > 0.005)

        productos = self.execute_query(
            """SELECT p.name AS producto, SUM(sd.quantity) AS cantidad,
                      SUM(sd.quantity * sd.unit_price) AS monto
               FROM sale_details sd
               JOIN products p ON p.id = sd.product_id
               JOIN sales s ON s.id = sd.sale_id
               WHERE s.status = 'active'
                 AND substr(s.date, 1, 10) BETWEEN ? AND ?
               GROUP BY p.id, p.name
               ORDER BY cantidad DESC, monto DESC
               LIMIT 10""", rango)
        return {'dias': lista, 'totales': totales, 'productos': productos}

    def __del__(self):
        # No cerrar la conexión en el destructor ya que es compartida
        pass
