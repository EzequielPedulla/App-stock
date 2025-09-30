import pymysql
from .product import Product
from config import MYSQL_CONFIG


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
            Database._connection = pymysql.connect(
                host=MYSQL_CONFIG['host'],
                port=MYSQL_CONFIG['port'],
                user=MYSQL_CONFIG['user'],
                password=MYSQL_CONFIG['password'],
                database=MYSQL_CONFIG['database'],
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False  # Control manual de transacciones
            )
            self.connection = Database._connection
            self.cursor = self.connection.cursor()
            self.create_tables()
        else:
            self.connection = Database._connection
            self.cursor = self.connection.cursor()

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
                `change` DECIMAL(10,2) NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                cancelled_at DATETIME NULL,
                cancellation_reason TEXT NULL
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

    def execute_query(self, query, params=None):
        """Ejecuta una consulta SELECT y retorna los resultados como lista de diccionarios"""
        try:
            # Crear un nuevo cursor para asegurar datos frescos
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
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
            from datetime import datetime

            # Verificar que la venta existe y está activa
            query = "SELECT status FROM sales WHERE id = %s"
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
                WHERE sale_id = %s
            """
            details = self.execute_query(query, (sale_id,))

            # Reintegrar stock de cada producto (excepto VARIOS)
            for detail in details:
                product = self.get_product_by_id(detail['product_id'])
                if product and not product.barcode.startswith('VAR'):
                    product.stock += detail['quantity']
                    self.update_product(product)

            # Marcar venta como anulada
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            update_query = """
                UPDATE sales 
                SET status = 'cancelled',
                    cancelled_at = %s,
                    cancellation_reason = %s
                WHERE id = %s
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
