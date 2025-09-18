class Product:
    def __init__(self, barcode, name, price, stock=0, id=None):
        self.id = id
        self.barcode = barcode
        self.name = name
        self.price = price
        self.stock = stock

    def to_tuple(self):
        return (self.barcode, self.name, self.price, self.stock)

    @staticmethod
    def from_db_dict(dict_data):
        return Product(
            id=dict_data['id'],
            barcode=dict_data['barcode'],
            name=dict_data['name'],
            price=float(dict_data['price']),
            stock=dict_data['stock']
        )

    @staticmethod
    def get_sample_products():
        return [
            Product("123456789012", "Caldo", 1.50, 40),
            Product("987654322108", "Pan", 2.00, 25),
            Product("456789012345", "Jugo", 1.00, 50),
            Product("654321098765", "Galletas", 3.00, 30)
        ]
