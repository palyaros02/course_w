from PyQt5.QtSql import QSqlDatabase, QSqlQuery
import sys

DB_PATH = './db/backery.db'

con = QSqlDatabase.addDatabase('QSQLITE')
con.setDatabaseName(DB_PATH)

if not con.open():
    print("Database Error: ", con.lastError().databaseText())
    sys.exit(1)
else:
    print("Connected")

tableQuery = QSqlQuery()

def create_tables():
    tableQuery.exec(
        """--sql
        CREATE TABLE IF NOT EXISTS bakeries (
            id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
            name VARCHAR(40) NOT NULL,
            address VARCHAR(50)
        )
        """
    )

    tableQuery.exec(
        """--sql
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
            name VARCHAR(50) NOT NULL,
            price DECIMAL(10, 2) NOT NULL
        )
        """
    )

    tableQuery.exec(
        """--sql
        CREATE TABLE IF NOT EXISTS stock (
            bakery_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER,
            FOREIGN KEY (bakery_id) REFERENCES bakeries (id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
            PRIMARY KEY (bakery_id, product_id)

        )
        """
    )

    tableQuery.exec(
        """--sql
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL
        )
        """
    )

    tableQuery.exec(
        """--sql
        CREATE TABLE IF NOT EXISTS transactions (
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id),
            FOREIGN KEY (product_id) REFERENCES products (id),
            PRIMARY KEY (order_id, product_id)
            )
        """
    )

    tableQuery.exec(
        """--sql
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
            bakery_id INTEGER,
            role_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            login TEXT NOT NULL,
            password TEXT NOT NULL,
            FOREIGN KEY (bakery_id) REFERENCES bakeries (id),
            FOREIGN KEY (role_id) REFERENCES roles (id)
        )
        """
    )

    tableQuery.exec(
        """--sql
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
            name TEXT NOT NULL
        )
        """
    )

    tableQuery.exec(
        """--sql
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
            change_date TIMESTAMP NOT NULL,
            op_type TEXT NOT NULL,
            table_name TEXT NOT NULL
        )
        """
    )

def drop_tables():
    tableQuery.exec("DROP TABLE IF EXISTS bakeries")
    tableQuery.exec("DROP TABLE IF EXISTS products")
    tableQuery.exec("DROP TABLE IF EXISTS stock")
    tableQuery.exec("DROP TABLE IF EXISTS orders")
    tableQuery.exec("DROP TABLE IF EXISTS transactions")
    tableQuery.exec("DROP TABLE IF EXISTS users")
    tableQuery.exec("DROP TABLE IF EXISTS roles")

def add_triggers():

    tableQuery.exec(
        """--sql
        CREATE TRIGGER IF NOT EXISTS bakeries_insert_log AFTER INSERT ON bakeries
        BEGIN
            INSERT INTO logs (change_date, op_type, table_name) VALUES (datetime('now'), 'INSERT', 'bakeries');
        END
        """
    )

    tableQuery.exec(
        """--sql
        CREATE TRIGGER IF NOT EXISTS bakeries_update_log AFTER UPDATE ON bakeries
        BEGIN
            INSERT INTO logs (change_date, op_type, table_name) VALUES (datetime('now'), 'UPDATE', 'bakeries');
        END
        """
    )

    tableQuery.exec(
        """--sql
        CREATE TRIGGER IF NOT EXISTS bakeries_delete_log AFTER DELETE ON bakeries
        BEGIN
            INSERT INTO logs (change_date, op_type, table_name) VALUES (datetime('now'), 'DELETE', 'bakeries');
        END
        """
    )



def reset_tables():
    drop_tables()
    create_tables()
    add_triggers()

reset_tables()
print(con.tables())
