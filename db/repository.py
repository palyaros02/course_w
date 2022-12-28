import datetime
import sys
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from decimal import Decimal

from anyio import start_blocking_portal

from config import DB_PATH

from raw_data import DF
from traitlets import default

class DBRepo:
    def __init__(self, con=None) -> None:
        if con:
            self.con = con
        else:
            self.con = QSqlDatabase.addDatabase('QSQLITE')
            self.con.setDatabaseName(DB_PATH)

        if self.con.open():
            print('Database connection successful')
        else:
            print(f'Database connection FAILED: {self.con.lastError().text()}')
            sys.exit(1)

        self.con.open()
        self.query = QSqlQuery() if con is None else QSqlQuery(con)

    def open(self)-> bool:
        return self.con.open()

    def close(self) -> bool:
        return self.con.close()

    def get_connection(self) -> QSqlDatabase:
        return self.con

    def create_tables(self) -> None:
        self.query.exec(
            """--sql
            CREATE TABLE IF NOT EXISTS bakeries (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                name VARCHAR(40) NOT NULL,
                address VARCHAR(100) NOT NULL
            )
            """
        )

        self.query.exec(
            """--sql
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                name VARCHAR(50) NOT NULL,
                price DECIMAL(10, 2) NOT NULL
            )
            """
        )

        self.query.exec(
            """--sql
            CREATE TABLE IF NOT EXISTS stock (
                bakery_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER,
                FOREIGN KEY (bakery_id) REFERENCES bakeries (id) ON UPDATE CASCADE ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (id) ON UPDATE CASCADE ON DELETE NO ACTION,
                PRIMARY KEY (bakery_id, product_id)
            )
            """
        )

        self.query.exec(
            """--sql
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                bakery_id INTEGER NOT NULL,
                date DATE NOT NULL,
                time TIME NOT NULL,
                FOREIGN KEY (bakery_id) REFERENCES bakeries (id) ON UPDATE CASCADE ON DELETE CASCADE
            )
            """
        )

        self.query.exec(
            """--sql
            CREATE TABLE IF NOT EXISTS order_product (
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER,
                price_change DECIMAL(10, 2),
                FOREIGN KEY (order_id) REFERENCES orders (id) ON UPDATE CASCADE ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products (id) ON UPDATE CASCADE ON DELETE NO ACTION,
                PRIMARY KEY (order_id, product_id)
                )
            """
        )

        self.query.exec(
            """--sql
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                bakery_id INTEGER,
                role_id INTEGER,
                name VARCHAR(40) NOT NULL,
                login VARCHAR(16) NOT NULL UNIQUE,
                password VARCHAR(20) NOT NULL,
                FOREIGN KEY (bakery_id) REFERENCES bakeries (id) ON UPDATE CASCADE ON DELETE SET NULL,
                FOREIGN KEY (role_id) REFERENCES roles (id) ON UPDATE CASCADE ON DELETE SET NULL
            )
            """
        )

        self.query.exec(
            """--sql
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                name VARCHAR(20) NOT NULL
            )
            """
        )

        self.query.exec(
            """--sql
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                change_date TIMESTAMP NOT NULL,
                op_type VARCHAR(20) NOT NULL,
                table_name VARCHAR(20) NOT NULL
            )
            """
        )
        print('Tables created')

    def drop_tables(self) -> None:
        self.query.exec("DROP TABLE IF EXISTS bakeries")
        self.query.exec("DROP TABLE IF EXISTS products")
        self.query.exec("DROP TABLE IF EXISTS stock")
        self.query.exec("DROP TABLE IF EXISTS orders")
        self.query.exec("DROP TABLE IF EXISTS order_product")
        self.query.exec("DROP TABLE IF EXISTS users")
        self.query.exec("DROP TABLE IF EXISTS roles")
        self.query.exec("DROP TABLE IF EXISTS logs")
        print('Tables dropped')

    def _add_log_triggers(self) -> None:
        tables = ['bakeries', 'products', 'stock', 'orders', 'order_product', 'users', 'roles']
        for table in tables:
            for op in ['INSERT', 'UPDATE', 'DELETE']:
                self.query.exec(
                    f"""--sql
                    CREATE TRIGGER IF NOT EXISTS {table}_{op.lower()}_log
                    AFTER {op} ON {table}
                    BEGIN
                        INSERT INTO logs (change_date, op_type, table_name)
                        VALUES (datetime('now'), '{op}', '{table}');
                    END
                    """
                )
        print('Log triggers added')

    def add_triggers(self) -> None:

        self.query.exec( # Проверка на наличие продукта в заказе и добавление его в случае наличия
            """--sql
            CREATE TRIGGER IF NOT EXISTS order_product_insert
            BEFORE INSERT ON order_product
            WHEN EXISTS (
                SELECT * FROM order_product
                WHERE order_id = NEW.order_id AND product_id = NEW.product_id
            )
            BEGIN
                UPDATE order_product
                SET quantity = quantity + NEW.quantity
                WHERE order_id = NEW.order_id AND product_id = NEW.product_id;
                SELECT RAISE(IGNORE);
            END
            """
        )


        self.query.exec( # Проверка на наличие продукта на складе
            """--sql
            CREATE TRIGGER stock_update
            BEFORE UPDATE ON order_product
            BEGIN
                UPDATE stock
                SET quantity =
                CASE WHEN (
                    SELECT quantity
                    FROM stock
                    WHERE product_id = NEW.product_id
                    AND bakery_id = (
                        SELECT bakery_id
                        FROM orders
                        WHERE id = NEW.order_id
                    )
                )>= NEW.quantity THEN
                    quantity + OLD.quantity - NEW.quantity
                    WHERE product_id = NEW.product_id
                    AND bakery_id = ( SELECT bakery_id FROM orders WHERE id = NEW.order_id );
                ELSE
                    RAISE(ABORT, "Not enough products in stock")
                END;
            END;
            """
        )

        self.query.exec(
            """--sql
            CREATE TRIGGER stock_insert
            BEFORE INSERT ON order_product
            WHEN NOT EXISTS (
                SELECT * FROM order_product
                WHERE order_id = NEW.order_id AND product_id = NEW.product_id
            )
            BEGIN
                UPDATE stock
                SET quantity =
                CASE WHEN (
                    SELECT quantity
                    FROM stock
                    WHERE product_id = NEW.product_id
                    AND bakery_id = (
                        SELECT bakery_id
                        FROM orders
                        WHERE id = NEW.order_id
                    )
                )>= NEW.quantity THEN
                    quantity - NEW.quantity
                    WHERE product_id = NEW.product_id
                    AND bakery_id = (SELECT bakery_id FROM orders WHERE id = NEW.order_id);
                ELSE
                    RAISE(ABORT, "Not enough products in stock")
                END;
            END;
            """
        )

        self.query.exec(
            """--sql
            CREATE TRIGGER stock_delete
            AFTER DELETE ON order_product
            BEGIN
                UPDATE stock
                SET quantity = quantity + OLD.quantity
                WHERE product_id = OLD.product_id
                AND bakery_id = ( SELECT bakery_id FROM orders WHERE id = OLD.order_id );
            END
            """
        )

        # триггер после обновления склада, который удаляет запись о продукте со склада, если его количество равно 0
        # self.query.exec(
        #     """--sql
        #     CREATE TRIGGER stock_clear
        #     AFTER UPDATE ON stock
        #     FOR EACH ROW
        #     BEGIN
        #     DELETE FROM stock
        #         WHERE quantity = 0;
        #     END;
        #     """
        # )
        print('Triggers added')

    def add_bakery(self, name: str, addr: str) -> None:
        self.query.prepare("INSERT INTO bakeries (name, address) VALUES (:name, :addr)")
        self.query.bindValue(":name", name)
        self.query.bindValue(":addr", addr)
        self.query.exec()

    def add_role(self, name: str) -> None:
        self.query.prepare("INSERT INTO roles (name) VALUES (:name)")
        self.query.bindValue(":name", name)
        self.query.exec()

    def add_user(self, bakery_id: int, role_id: int, name: str, login: str, password: str) -> None:
        self.query.prepare("INSERT INTO users (bakery_id, role_id, name, login, password) VALUES (:bakery_id, :role_id, :name, :login, :password)")
        self.query.bindValue(":bakery_id", bakery_id)
        self.query.bindValue(":role_id", role_id)
        self.query.bindValue(":name", name)
        self.query.bindValue(":login", login)
        self.query.bindValue(":password", str(hash(password)))
        self.query.exec()

    def add_product(self, name: str, price: Decimal, id: int=None) -> int:
        if id is None:
            self.query.prepare("INSERT INTO products (name, price) VALUES (:name, :price)")
            self.query.bindValue(":name", name)
            self.query.bindValue(":price", price)
            self.query.exec()
            id = self.query.lastInsertId()
        else:
            self.query.prepare("INSERT INTO products (id, name, price) VALUES (:id, :name, :price)")
            self.query.bindValue(":id", id)
            self.query.bindValue(":name", name)
            self.query.bindValue(":price", price)
            self.query.exec()
        return id

    def add_order(self, bakery_id: int, date: str=None, time: str=None, id: int=None) -> int:
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        if time is None:
            time = datetime.now().strftime('%H:%M')
        if id is None:
            self.query.prepare("INSERT INTO orders (bakery_id, date, time) VALUES (:bakery_id, :date, :time)")
            self.query.bindValue(":bakery_id", bakery_id)
            self.query.bindValue(":date", date)
            self.query.bindValue(":time", time)
            self.query.exec()
            id = self.query.lastInsertId()
        else:
            self.query.prepare("INSERT INTO orders (id, bakery_id, date, time) VALUES (:id, :bakery_id, :date, :time)")
            self.query.bindValue(":id", id)
            self.query.bindValue(":bakery_id", bakery_id)
            self.query.bindValue(":date", date)
            self.query.bindValue(":time", time)
            self.query.exec()
        return id

    def add_order_product(self, order_id: int, product_id: int, quantity: int, price_change: int=None) -> None:
        if price_change is None:
            self.query.prepare("INSERT INTO order_product (order_id, product_id, quantity) VALUES (:order_id, :product_id, :quantity)")
            self.query.bindValue(":order_id", order_id)
            self.query.bindValue(":product_id", product_id)
            self.query.bindValue(":quantity", quantity)
            self.query.exec()
        else:
            self.query.prepare("INSERT INTO order_product (order_id, product_id, quantity, price_change) VALUES (:order_id, :product_id, :quantity, :price_change)")
            self.query.bindValue(":order_id", order_id)
            self.query.bindValue(":product_id", product_id)
            self.query.bindValue(":quantity", quantity)
            self.query.bindValue(":price_change", price_change)
            self.query.exec()

    def add_stock(self, product_id: int, quantity: int, bakery_id: int=1) -> None:
        self.query.prepare("INSERT INTO stock (bakery_id, product_id, quantity) VALUES (:bakery_id, :product_id, :quantity)")
        self.query.bindValue(":bakery_id", bakery_id)
        self.query.bindValue(":product_id", product_id)
        self.query.bindValue(":quantity", quantity)
        self.query.exec()

    def set_stock(self, product_id: int, quantity: int, bakery_id: int=1) -> None:
        self.query.prepare("UPDATE stock SET quantity=:quantity WHERE bakery_id=:bakery_id AND product_id=:product_id")
        self.query.bindValue(":bakery_id", bakery_id)
        self.query.bindValue(":product_id", product_id)
        self.query.bindValue(":quantity", quantity)
        self.query.exec()

    def get_product(self, name: str) -> dict:
        self.query.prepare("SELECT * FROM products WHERE name=:name")
        self.query.bindValue(":name", name)
        self.query.exec()
        self.query.next()
        return {'id': self.query.value(0), 'name': self.query.value(1), 'price': self.query.value(2)}

    # МБ НЕ РАБОТАЕТ def get_order_id(self, bakery_id: int, date: str, time: str) -> dict:
    #     self.query.prepare("SELECT * FROM orders WHERE bakery_id=:bakery_id AND date=:date AND time=:time")
    #     self.query.bindValue(":bakery_id", bakery_id)
    #     self.query.bindValue(":date", date)
    #     self.query.bindValue(":time", time)
    #     self.query.exec()
    #     self.query.next()
    #     return {'id': self.query.value(0), 'bakery_id': self.query.value(1), 'date': self.query.value(2), 'time': self.query.value(3)}

    def get_orders(self, bakery_id=1) -> list:
        self.query.prepare("SELECT * FROM orders WHERE bakery_id=:bakery_id")
        self.query.bindValue(":bakery_id", bakery_id)
        self.query.exec()
        orders = {}
        while self.query.next():
            orders[self.query.value(0)] = {'id': self.query.value(0), 'bakery_id': self.query.value(1), 'date': self.query.value(2), 'time': self.query.value(3)}
        return orders

    def get_order(self, order_id: int) -> dict:
        self.query.prepare("SELECT (SELECT name FROM products WHERE id=product_id), quantity, (SELECT price FROM products WHERE id=product_id), price_change FROM order_product WHERE order_id=:order_id")
        self.query.bindValue(":order_id", order_id)
        self.query.exec()
        order = {}
        while self.query.next():
            price = self.query.value(3) if self.query.value(3) else self.query.value(2)
            order[self.query.value(0)] = {'name': self.query.value(0), 'quantity': self.query.value(1), 'price': price}
        return order

    def get_order_price(self, order_id: int) -> int:
        self.query.prepare("SELECT (SELECT price FROM products WHERE id=product_id), quantity, price_change FROM order_product WHERE order_id=:order_id")
        self.query.bindValue(":order_id", order_id)
        self.query.exec()
        order_price = 0
        while self.query.next():
            price = self.query.value(2) if self.query.value(2) else self.query.value(0)
            order_price += price * self.query.value(1)
        return order_price

    def get_stock(self, bakery_id=1) -> dict:
        # select product id, product name, quantity from stock
        self.query.prepare("SELECT product_id, (SELECT name FROM products WHERE id=product_id), quantity FROM stock WHERE bakery_id=:bakery_id")
        self.query.bindValue(":bakery_id", bakery_id)
        self.query.exec()
        stock = {}
        while self.query.next():
            stock[self.query.value(0)] = {'id': self.query.value(0), 'name': self.query.value(1), 'quantity': self.query.value(2)}
        return stock

    def __insert_data(self) -> None:
        for role in ['admin', 'cashier', 'cook']:
            self.add_role(role)
        print('Roles added')

        self.add_bakery('Le Fournil de Pierre', '2 Rue de la Paix, 75002 Paris')
        print('Bakery added')
        self.add_user(1, 1, 'admin', 'admin', 'admin')
        print('Admin added')

        print('Parsing products...')
        data = DF()
        products = data.get_products()
        print('Done. Adding products...')
        for name, price in products.items():
            self.add_product(name, price)

        # get all products from db and make a dict {name: (id, price)}
        self.query.exec("SELECT * FROM products")
        products = {}
        while self.query.next():
            products[self.query.value(1)] = (self.query.value(0), self.query.value(2))

        print('Products added')

        print('Parsing orders...')
        orders = data.get_orders()
        print('Done. Foming orders queries...')
        # orders = {
        # (150040, '2021-01-02', '08:38'): {'product': ['BAGUETTE', 'PAIN AU CHOCOLAT'],
        #   'quantity': [1, 3],
        #   'unit_price': [0.9, 1.2]},
        # (150041, '2021-01-02', '09:14'): {'product': ['PAIN AU CHOCOLAT', 'PAIN'],
        #   'quantity': [2, 1],
        #   'unit_price': [1.2, 1.15]},
        #  ...}

        query_order = "INSERT INTO orders (bakery_id, date, time, id) VALUES "
        query_order_list = []
        query_order_product = "INSERT INTO order_product (order_id, product_id, quantity, price_change) VALUES "
        query_order_product_list = []

        for (order_id, date, time), order in orders.items():
            query_order_list.append(f"({1}, '{date}', '{time}', {order_id}),")
            for product, quantity, unit_price in zip(order['product'], order['quantity'], order['unit_price']):
                product_id = products[product][0]
                self.add_stock(product_id, 100000, 1)
                default_price = products[product][1]
                if unit_price != default_price:
                    query_order_product_list.append(f"({order_id}, {product_id}, {quantity}, {unit_price}),")
                else:
                    query_order_product_list.append(f"({order_id}, {product_id}, {quantity}, NULL),")
        print('Orders queries formed')

        # print('Adding orders...')
        # query_order_list = ''.join(query_order_list)
        # print('Orders queries joined')
        # query_order_product_list = ''.join(query_order_product_list)
        # print('Order_product queries joined')
        # query_order += query_order_list
        # query_order_product += query_order_product_list
        # open('query_order.txt', 'w').write(query_order)
        # open('query_order_product.txt', 'w').write(query_order_product)
        # self.query.exec(query_order)
        # self.query.exec(query_order_product)
        # print('Orders added')
        print('Adding orders...')
        for i in range(0, len(query_order_list), 100):
            l = query_order_list[i:i+100]
            l[-1] = l[-1][:-1] + ';'
            if self.query.exec(query_order + ''.join(l)) == False:
                print(self.query.lastError().text())
                break
            l2 = query_order_product_list[i:i+100]
            l2[-1] = l2[-1][:-1] + ';'
            if self.query.exec(query_order_product + ''.join(l2)) == False:
                print(self.query.lastError().text())
                print(l2)
                break



    def _reset(self) -> None:
        ans = input('Are you sure you want to reset the database? (y/n) ')
        if ans == 'y':
            self.drop_tables()
            self.create_tables()
            self.add_triggers()
            self.__insert_data()
            self._add_log_triggers()