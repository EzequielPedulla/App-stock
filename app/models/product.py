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
    def from_db_tuple(tuple_data):
        return Product(
            id=tuple_data[0],
            barcode=tuple_data[1],
            name=tuple_data[2],
            price=tuple_data[3],
            stock=tuple_data[4]
        )

    @staticmethod
    def get_sample_products():
        return [
            Product("123456789012", "Caldo", 1.50, 40),
            Product("987654322108", "Pan", 2.00, 25),
            Product("456789012345", "Jugo", 1.00, 50),
            Product("654321098765", "Galletas", 3.00, 30)
        ]
