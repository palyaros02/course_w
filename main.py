from PyQt5.QtSql import QSqlDatabase, QSqlQuery
import sys

DB_PATH = './db/backery.db'

con = QSqlDatabase.addDatabase('QSQLITE')
con.setDatabaseName(DB_PATH)

if not con.open():
    print("Database Error: ", con.lastError().databaseText())
    sys.exit(1)

createTableQuery = QSqlQuery()

createTableQuery.exec(
    """--sql
    CREATE TABLE IF NOT EXISTS bakeries (
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
        name VARCHAR(40) NOT NULL,
        address VARCHAR(50)
    )
    """
)

createTableQuery.exec(
    """--sql
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
        name VARCHAR(50) NOT NULL,
        price DECIMAL(10, 2) NOT NULL
    )
    """
)

createTableQuery.exec(
    """--sql
    CREATE TABLE IF NOT EXISTS stock (
        bakery_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER,
        FOREIGN KEY (bakery_id) REFERENCES bakeries (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    """
)

createTableQuery.exec(
    """--sql
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
        date DATE NOT NULL,
        time TIME NOT NULL
    )
    """
)

createTableQuery.exec(
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

createTableQuery.exec(
    """--sql
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
        bakery_id INTEGER,
        role_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        FOREIGN KEY (bakery_id) REFERENCES bakeries (id),
        FOREIGN KEY (role_id) REFERENCES roles (id)
    )
    """
)

createTableQuery.exec(
    """--sql
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
        name TEXT NOT NULL
    )
    """
)