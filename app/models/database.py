import sqlite3
from datetime import datetime
from .product import Product
from config import DB_PATH


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

        self._migrate_add_payment_method_column()
        self._migrate_add_forma_pago_column()
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
                 payment_method: str = 'efectivo', commit=True) -> int:
        self.cursor.execute(
            '''INSERT INTO sales (date, total, paid, `change`, payment_method)
               VALUES (?, ?, ?, ?, ?)''',
            (date, total, paid, change, payment_method)
        )
        if commit:
            self.connection.commit()
        return self.cursor.lastrowid

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
        return self.execute_query(
            "SELECT * FROM caja_movimientos WHERE sesion_id = ? ORDER BY id",
            (sesion_id,)
        )

    def delete_caja_movimiento(self, movimiento_id: int) -> None:
        self.cursor.execute(
            "DELETE FROM caja_movimientos WHERE id = ?", (movimiento_id,))
        self.connection.commit()

    def get_ventas_totales_por_metodo(self, fecha: str) -> dict:
        """Suma el total de ventas activas de un día, por método de pago.
        Usa `total` (no `paid`): en efectivo es lo que efectivamente queda
        en el cajón (lo que se recibe menos el vuelto que sale del mismo
        cajón, neto = total); en fiado no entra nada de plata todavía.
        """
        result = self.execute_query(
            """SELECT payment_method, COALESCE(SUM(total), 0) as total
               FROM sales
               WHERE status = 'active' AND date LIKE ?
               GROUP BY payment_method""",
            (f"{fecha}%",)
        )
        totales = {'efectivo': 0.0, 'transferencia': 0.0,
                  'posnet': 0.0, 'fiado': 0.0}
        for row in result:
            totales[row['payment_method']] = float(row['total'])
        return totales

    def __del__(self):
        # No cerrar la conexión en el destructor ya que es compartida
        pass
