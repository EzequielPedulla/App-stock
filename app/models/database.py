import sqlite3
from .product import Product


class Database:
    def __init__(self):
        self.connection = sqlite3.connect('inventory.db')
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total REAL NOT NULL,
                paid REAL NOT NULL,
                change REAL NOT NULL
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

    def add_product(self, product):
        self.cursor.execute('''
            INSERT INTO products (barcode, name, price, stock)
            VALUES (?, ?, ?, ?)
        ''', (product.barcode, product.name, product.price, product.stock))
        self.connection.commit()

    def get_all_products(self):
        self.cursor.execute('SELECT * FROM products')
        return [Product.from_db_tuple(row) for row in self.cursor.fetchall()]

    def update_product(self, product):
        self.cursor.execute('''
            UPDATE products 
            SET barcode=?, name=?, price=?, stock=?
            WHERE id=?
        ''', (product.barcode, product.name, product.price, product.stock, product.id))
        self.connection.commit()

    def delete_product(self, product_id):
        self.cursor.execute('DELETE FROM products WHERE id=?', (product_id,))
        self.connection.commit()

    def get_product_by_id(self, product_id):
        self.cursor.execute('SELECT * FROM products WHERE id=?', (product_id,))
        row = self.cursor.fetchone()
        return Product.from_db_tuple(row) if row else None

    def get_product_by_barcode(self, barcode):
        self.cursor.execute(
            'SELECT * FROM products WHERE barcode=?', (barcode,))
        row = self.cursor.fetchone()
        return Product.from_db_tuple(row) if row else None

    def add_sale(self, date: str, total: float, paid: float, change: float) -> int:
        """Registra una venta en la base de datos.

        Args:
            date: Fecha y hora de la venta en formato ISO.
            total: Total de la venta.
            paid: Monto pagado por el cliente.
            change: Vuelto entregado al cliente.

        Returns:
            int: ID de la venta registrada.
        """
        self.cursor.execute(
            '''INSERT INTO sales (date, total, paid, change) VALUES (?, ?, ?, ?)''',
            (date, total, paid, change)
        )
        self.connection.commit()
        return self.cursor.lastrowid

    def add_sale_detail(self, sale_id: int, product_id: int, quantity: int, unit_price: float) -> None:
        """Registra un detalle de venta en la base de datos.

        Args:
            sale_id: ID de la venta a la que pertenece el detalle.
            product_id: ID del producto vendido.
            quantity: Cantidad vendida.
            unit_price: Precio unitario del producto.
        """
        self.cursor.execute(
            '''INSERT INTO sale_details (sale_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)''',
            (sale_id, product_id, quantity, unit_price)
        )
        self.connection.commit()

    def __del__(self):
        self.connection.close()
