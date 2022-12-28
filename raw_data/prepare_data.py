import pandas as pd


def clear_data():
    # считываем данные из файла
    data = pd.read_csv("./raw_data/Bakery sales.csv.bak", index_col=0)

    # задаём названия столбцов
    data.columns = ["date", "time", "order_ID", "product", "quantity", "unit_price"]

    # переводим колонку transaction_ID в целочисленный тип
    data.order_ID = data.order_ID.astype(int)

    # переводим колонку quantity в целочисленный тип
    data.quantity = data.quantity.astype(int)

    # переводим колонку unit_price в вещественный тип, заменяем , на . и убираем €
    data.unit_price = data.unit_price.str.replace(" €", "").str.replace(",", ".").astype(float)

    # сохраняем изменённые данные в файл
    data.to_csv("./raw_data/Bakery_sales.csv", index=False)



class DF:
    def __init__(self):
        data = pd.read_csv("./raw_data/Bakery_sales.csv")
        data.drop(data[data['unit_price'] == 0].index, inplace=True)
        data.drop(data[data['product'].str.contains("DIVERS")].index, inplace=True)
        data.drop(data[data['product'] == "TRAITEUR"].index, inplace=True)
        self.data = data


    def get_products(self):
        most_popular_prices = self.data.groupby('product')['unit_price'].agg(lambda x: x.value_counts().index[0])
        return most_popular_prices.to_dict()

    def get_orders(self):
        return self.data.groupby(['order_ID', 'date', 'time'])['product', 'quantity', 'unit_price'].apply(lambda x: x.to_dict(orient='list')).to_dict()