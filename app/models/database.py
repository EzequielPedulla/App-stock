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
        self.connection.commit()

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

    def add_sale(self, date: str, total: float, paid: float, change: float, commit=True) -> int:
        self.cursor.execute(
            '''INSERT INTO sales (date, total, paid, `change`) VALUES (?, ?, ?, ?)''',
            (date, total, paid, change)
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

    def __del__(self):
        # No cerrar la conexión en el destructor ya que es compartida
        pass
