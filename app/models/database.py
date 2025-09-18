import pymysql
from .product import Product
from config import MYSQL_CONFIG


class Database:
    def __init__(self):
        self.connection = pymysql.connect(
            host=MYSQL_CONFIG['host'],
            port=MYSQL_CONFIG['port'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            database=MYSQL_CONFIG['database'],
            cursorclass=pymysql.cursors.DictCursor
        )
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                barcode VARCHAR(13) UNIQUE,
                name VARCHAR(255) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                stock INT DEFAULT 0
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATETIME NOT NULL,
                total DECIMAL(10,2) NOT NULL,
                paid DECIMAL(10,2) NOT NULL,
                `change` DECIMAL(10,2) NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sale_details (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sale_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')
        self.connection.commit()

    @staticmethod
    def from_db_dict(data):
        return Product(
            id=data.get('id'),
            barcode=data.get('barcode'),
            name=data.get('name'),
            price=float(data.get('price')),
            stock=int(data.get('stock', 0))
        )

    def add_product(self, product):
        self.cursor.execute('''
            INSERT INTO products (barcode, name, price, stock)
            VALUES (%s, %s, %s, %s)
        ''', (product.barcode, product.name, product.price, product.stock))
        self.connection.commit()

    def get_all_products(self):
        self.cursor.execute('SELECT * FROM products')
        rows = self.cursor.fetchall()
        return [Product.from_db_dict(row) for row in rows]

    def update_product(self, product):
        self.cursor.execute('''
            UPDATE products 
            SET barcode=%s, name=%s, price=%s, stock=%s
            WHERE id=%s
        ''', (product.barcode, product.name, product.price, product.stock, product.id))
        self.connection.commit()

    def delete_product(self, product_id):
        self.cursor.execute('DELETE FROM products WHERE id=%s', (product_id,))
        self.connection.commit()

    def get_product_by_id(self, product_id):
        self.cursor.execute(
            'SELECT * FROM products WHERE id=%s', (product_id,))
        row = self.cursor.fetchone()
        return Product.from_db_dict(row) if row else None

    def get_product_by_barcode(self, barcode):
        self.cursor.execute(
            'SELECT * FROM products WHERE barcode=%s', (barcode,))
        row = self.cursor.fetchone()
        return Product.from_db_dict(row) if row else None

    def add_sale(self, date: str, total: float, paid: float, change: float) -> int:
        self.cursor.execute(
            '''INSERT INTO sales (date, total, paid, `change`) VALUES (%s, %s, %s, %s)''',
            (date, total, paid, change)
        )
        self.connection.commit()
        return self.cursor.lastrowid

    def add_sale_detail(self, sale_id: int, product_id: int, quantity: int, unit_price: float) -> None:
        self.cursor.execute(
            '''INSERT INTO sale_details (sale_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)''',
            (sale_id, product_id, quantity, unit_price)
        )
        self.connection.commit()

    def __del__(self):
        self.connection.close()
