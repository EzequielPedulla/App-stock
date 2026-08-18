class Product:
    def __init__(self, barcode, name, price, stock=0, id=None):
        self.id = id
        self.barcode = barcode
        self.name = name
        self.price = price
        self.stock = stock

    @staticmethod
    def from_db_dict(dict_data):
        return Product(
            id=dict_data['id'],
            barcode=dict_data['barcode'],
            name=dict_data['name'],
            price=float(dict_data['price']),
            stock=dict_data['stock']
        )
