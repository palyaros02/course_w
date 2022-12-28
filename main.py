from cProfile import label
from turtle import right
from PyQt5.QtSql import QSqlQuery, QSqlDatabase
from PyQt5.QtWidgets import (QApplication, QWidget,
                             QVBoxLayout, QPushButton,
                             QHBoxLayout, QListWidget, QLineEdit, QTextEdit,
                             QListWidgetItem, QLabel, QMessageBox, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt
import sys

from db import DBRepo
from raw_data import DF

repo = DBRepo()
data = DF()

con = repo.get_connection()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.new_order_btn = QPushButton('Новый заказ')
        self.exit_btn = QPushButton('Выход из системы')
        self.export_data_btn = QPushButton('Выгрузка данных')
        self.price = QLabel('0')
        self.initUI()
        self.bind_events()
        self.get_data()


    def initUI(self):
        self.setWindowTitle('Управление пекарней')
        self.resize(900, 600)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        top_hbox = QHBoxLayout()
        left_vbox = QVBoxLayout()
        left_vbox.addWidget(QLabel('Пекарня: Le Fournil de Pierre'))
        left_vbox.addWidget(QLabel('Пользователь: Кассир Pierre'))
        top_hbox.addLayout(left_vbox)

        right_vbox = QVBoxLayout()
        right_vbox.addWidget(self.new_order_btn)
        right_vbox.addWidget(self.exit_btn)
        right_vbox.addWidget(self.export_data_btn)
        top_hbox.addLayout(right_vbox)
        self.main_layout.addLayout(top_hbox)

        bottom_hbox = QHBoxLayout()
        orders_vbox = QVBoxLayout()
        label = QLabel('Заказы:')
        orders_vbox.addWidget(label)
        orders_list = QTableWidget()
        orders_list.setColumnCount(3)
        orders_list.setRowCount(200000)
        orders_list.setHorizontalHeaderLabels(['Номер заказа', 'Дата', 'Время'])
        self.orders_list = orders_list
        orders_vbox.addWidget(orders_list)
        bottom_hbox.addLayout(orders_vbox)

        bottom_vbox = QVBoxLayout()
        order_hbox = QVBoxLayout()
        label = QLabel('Заказ:')
        order_hbox.addWidget(label)
        order_table = QTableWidget()
        order_table.setColumnCount(3)
        order_table.setRowCount(50)
        order_table.setHorizontalHeaderLabels(['Название', 'Количество', 'Сумма'])
        self.order_table = order_table
        order_hbox.addWidget(self.order_table)

        price_hbox = QHBoxLayout()
        price_label = QLabel('Сумма заказа')
        price_label.setAlignment(Qt.AlignRight)
        price_hbox.addWidget(price_label)
        price_hbox.setAlignment(Qt.AlignRight)
        price_hbox.addWidget(self.price)
        order_hbox.addLayout(price_hbox)
        bottom_vbox.addLayout(order_hbox)

        stock_hbox = QVBoxLayout()
        label = QLabel('Наличие:')
        stock_hbox.addWidget(label)
        stock_table = QTableWidget()
        stock_table.setColumnCount(3)
        stock_table.setRowCount(140)
        stock_table.setHorizontalHeaderLabels(['ID', 'Название', 'Количество'])
        self.stock_table = stock_table
        stock_hbox.addWidget(self.stock_table)
        bottom_vbox.addLayout(stock_hbox)
        bottom_hbox.addLayout(bottom_vbox)
        self.main_layout.addLayout(bottom_hbox)

    def get_data(self):
        self.orders_list.setRowCount(0)
        self.order_table.setRowCount(0)
        self.price.setText('0')
        orders = repo.get_orders()
        i = 0
        for order in orders:
            if order == 150141:
                break
            order = orders[order]
            self.orders_list.insertRow(i)
            self.orders_list.setItem(i, 0, QTableWidgetItem(str(order["id"])))
            self.orders_list.setItem(i, 1, QTableWidgetItem(str(order["date"])))
            self.orders_list.setItem(i, 2, QTableWidgetItem(str(order["time"])))
            i += 1

        stock = repo.get_stock()
        i = 0
        for item in stock:
            item = stock[item]
            self.stock_table.insertRow(i)
            self.stock_table.setItem(i, 0, QTableWidgetItem(str(item["id"])))
            self.stock_table.setItem(i, 1, QTableWidgetItem(str(item["name"])))
            self.stock_table.setItem(i, 2, QTableWidgetItem(str(item["quantity"])))
            i += 1

    def get_order(self):
        self.order_table.setRowCount(0)
        order_id = self.orders_list.item(self.orders_list.currentRow(), 0).text()
        order = repo.get_order(order_id)
        i = 0
        for item in order:
            item = order[item]
            self.order_table.insertRow(i)
            self.order_table.setItem(i, 0, QTableWidgetItem(str(item["name"])))
            self.order_table.setItem(i, 1, QTableWidgetItem(str(item["quantity"])))
            self.order_table.setItem(i, 2, QTableWidgetItem(str(item["price"])))
            i += 1
        # self.order_table.resizeColumnsToContents()
        self.price.setText(str(repo.get_order_price(order_id)))

    def bind_events(self):
        # self.new_order_btn.clicked.connect(self.new_order)
        # self.exit_btn.clicked.connect(self.exit)
        # self.get_data_btn.clicked.connect(self.get_data)
        self.orders_list.itemClicked.connect(self.get_order)



if __name__ == '__main__':
    con = repo.get_connection()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()