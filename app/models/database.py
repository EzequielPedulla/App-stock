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

    def __del__(self):
        self.connection.close()
