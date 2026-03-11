from datetime import datetime
from decimal import Decimal
import os
from sortedcontainers import SortedDict

from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale


class CarService:
    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = root_directory_path
        self.model_dir = f'{self.root_directory_path}/model.txt'
        self.model_idx_dir = f'{self.root_directory_path}/model_index.txt'
        self.car_dir = f'{self.root_directory_path}/car.txt'
        self.car_idx_dir = f'{self.root_directory_path}/car_index.txt'
        self.sale_dir = f'{self.root_directory_path}/sale.txt'
        self.sale_idx_dir = f'{self.root_directory_path}/sale_index.txt'

    def _find_object(self, dir: str, idx: str) -> int | None:
        with open(dir, 'r') as f:
            for line in f:
                key, val = line.strip().split(';')
                if idx == key:
                    pos = int(val)
                    return pos
        return

    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        index = SortedDict()
        with open(self.model_dir, 'a', newline='\n') as f:
            f.write(f'{model.id};{model.name};{model.brand}'.ljust(500) + '\n')

        if os.path.exists(self.model_idx_dir):
            with open(self.model_idx_dir, 'r') as f:
                for line in f:
                    index[int(line.split(';')[0])] = line.strip().split(';')[1]

        index[model.id] = str(len(index))
        with open(self.model_idx_dir, 'w') as f:
            for key, pos in index.items():
                f.write(f'{key};{pos}\n')
        return model

    # Задание 1. Сохранение автомобилей и моделей
    def add_car(self, car: Car) -> Car:
        index = SortedDict()
        with open(self.car_dir, 'a', newline='\n') as f:
            f.write(f'{car.vin};{car.model};{car.price};{car.date_start};{car.status}'.ljust(500) + '\n')

        if os.path.exists(self.car_idx_dir):
            with open(self.car_idx_dir, 'r') as f:
                for line in f:
                    index[line.split(';')[0]] = line.strip().split(';')[1]

        index[car.vin] = str(len(index))
        with open(self.car_idx_dir, 'w') as f:
            for key, pos in index.items():
                f.write(f'{key};{pos}\n')
        return car

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        index = SortedDict()
        with open(self.sale_dir, 'a', newline='\n') as f:
            f.write(f'{sale.sales_number};{sale.car_vin};{sale.sales_date};{sale.cost};False'.ljust(500) + '\n')

        if os.path.exists(self.sale_idx_dir):
            with open(self.sale_idx_dir, 'r') as f:
                for line in f:
                    index[line.split(';')[0]] = line.strip().split(';')[1]

        index[sale.sales_number] = str(len(index))
        with open(self.sale_idx_dir, 'w') as f:
            for key, pos in index.items():
                f.write(f'{key};{pos}\n')

        car_pos = self._find_object(self.car_idx_dir, sale.car_vin)
        if car_pos is None:
            raise ValueError(f"VIN {sale.car_vin} not found")
        
        with open(self.car_dir, 'r+', newline='\n') as f:
            f.seek(car_pos * 501)
            vin, model, price, date_start, _ = f.read(500).rstrip().split(';')
            f.seek(car_pos * 501)
            f.write(f'{vin};{model};{price};{date_start};sold'.ljust(500) + '\n')

        return Car(vin=vin, model=int(model), price=Decimal(price), date_start=date_start, status=CarStatus.sold)

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        available_cars = []
        with open(self.car_dir, 'r') as f:
            for line in f:
                vin, model, price, date_start, status = line.strip().split(';')
                if status == 'available':
                    available_cars.append(Car(vin=vin, model=int(model), price=Decimal(price), date_start=date_start, status=CarStatus(status)))
        
        return available_cars

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        car_pos = self._find_object(self.car_idx_dir, vin)
        if car_pos is None:
            return

        with open(self.car_dir, 'r') as f:
            f.seek(car_pos * 501)
            _, model_id, price, date_start, status = f.read(500).rstrip().split(';')
        
        model_pos = self._find_object(self.model_idx_dir, model_id)
        if model_pos is None:
            raise ValueError(f"Model id {model_id} not found")

        with open(self.model_dir, 'r') as f:
            f.seek(model_pos * 501)
            _, model, brand = f.read(500).rstrip().split(';')

        if status == 'sold':
            with open(self.sale_dir, 'r') as f:
                for line in f:
                    _, sales_vin, sales_date, cost, _ = line.rstrip().split(';')
                    if vin == sales_vin:
                        cost = Decimal(cost)
                        break
        else:
            sales_date = cost = None

        car_info = CarFullInfo(
            vin=vin,
            car_model_name=model, 
            car_model_brand=brand, 
            price=Decimal(price),
            date_start=date_start,
            status=CarStatus(status),
            sales_date=sales_date,
            sales_cost=cost
            )
        return car_info

    # Задание 5. Обновление ключевого поля
    def update_vin(self, vin: str, new_vin: str) -> Car:
        index = SortedDict()
        with open(self.car_idx_dir, 'r+') as f:
            for line in f:
                index[line.split(';')[0]] = line.strip().split(';')[1]
            f.seek(0)
            pos = int(index[vin])
            del index[vin]
            index[new_vin] = pos
            for key, val in index.items():
                f.write(f'{key};{val}\n')

        with open(self.car_dir, 'r+', newline='\n') as f:
            f.seek(pos * 501)
            _, model, price, date_start, status = f.read(500).rstrip().split(';')
            f.seek(pos * 501)
            f.write(f'{new_vin};{model};{price};{date_start};{status}')

        return Car(vin=new_vin, model=model, date_start=date_start, price=Decimal(price), status=CarStatus(status))

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        sale_pos = self._find_object(self.sale_idx_dir, sales_number)
        if sale_pos is None:
            raise ValueError(f"Sale number {sales_number} not found")
        with open(self.sale_dir, 'r+', newline='\n') as f:
            f.seek(sale_pos * 501)
            sale = f.read(500).rstrip().split(';')[:-1]
            vin = sale[1]
            f.seek(sale_pos * 501)
            f.write((';'.join(sale) + ';True').ljust(500) + '\n')
        
        car_pos = self._find_object(self.car_idx_dir, vin)
        if car_pos is None:
            raise ValueError(f"VIN {vin} not found")
        
        with open(self.car_dir, 'r+', newline='\n') as f:
            f.seek(car_pos * 501)
            _, model, price, date_start, _ = f.read(500).rstrip().split(';')
            f.seek(car_pos * 501)
            f.write(f'{vin};{model};{price};{date_start};available'.ljust(500) + '\n')

        return Car(vin=vin, model=model, price=price, date_start=date_start, status=CarStatus.available)

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        sold_vins = []
        with open(self.sale_dir, 'r') as f:
            for line in f:
                sale = line.strip().split(';')
                if sale[-1] == False:
                    sold_vins.append(sale[1])

        vin_model = {}
        model_price = {}
        with open(self.car_dir, 'r') as f:
            for line in f:
                vin, model_id, price, _, status = line.strip().split(';')
                if status == 'sold':
                    vin_model[vin] = model_id
                    model_price[model_id] = Decimal(price)
        
        models_sale_count = {}
        with open(self.model_dir, 'r') as f:
            for line in f:
                id, name, brand = line.strip().split(';')
                if id in set(vin_model.values()):
                    models_sale_count[(name, brand)] = [list(vin_model.values()).count(id), model_price[id]]

        top_models = []
        for (model, brand), [sale_amt, price] in sorted(models_sale_count.items(), key=lambda x: (x[1][0], x[1][1]), reverse=True)[:3]:
            top_models.append(ModelSaleStats(
                car_model_name=model,
                brand=brand,
                sales_number=sale_amt
            ))
        
        return top_models