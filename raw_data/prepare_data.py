import pandas as pd

# считываем данные из файла
data = pd.read_csv("./raw_data/Bakery sales.csv.bak", index_col=0)

# задаём названия столбцов
data.columns = ["date", "time", "transaction_ID", "product", "quantity", "unit_price"]

# переводим колонку transaction_ID в целочисленный тип
data.transaction_ID = data.transaction_ID.astype(int)

# переводим колонку quantity в целочисленный тип
data.quantity = data.quantity.astype(int)

# переводим колонку unit_price в вещественный тип, заменяем , на . и убираем €
data.unit_price = data.unit_price.str.replace(" €", "").str.replace(",", ".").astype(float)

# сохраняем изменённые данные в файл
data.to_csv("./raw_data/Bakery_sales.csv", index=False)
