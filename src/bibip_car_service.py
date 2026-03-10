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

    def _find_object(self, dir: str, key: str) -> int | None:
        with open(dir, 'r') as f:
            for line in f:
                if key == line.strip().split(';')[0]:
                    pos = int(line.strip().split(';')[1])
                    return pos
        return


    # Задание 1. Сохранение автомобилей и моделей
    def add_model(self, model: Model) -> Model:
        index = SortedDict()
        with open(self.model_dir, 'a') as f:
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
        with open(self.car_dir, 'a') as f:
            f.write(f'{car.vin};{car.model};{car.price};{car.date_start};{car.status}'.ljust(500) + '\n')

        if os.path.exists(self.car_idx_dir):
            with open(self.car_idx_dir, 'r') as f:
                for line in f:
                    # key, pos = line.split(';')
                    index[line.split(';')[0]] = line.strip().split(';')[1]

        index[car.vin] = str(len(index))
        with open(self.car_idx_dir, 'w') as f:
            for key, pos in index.items():
                f.write(f'{key};{pos}\n')
        return car

    # Задание 2. Сохранение продаж.
    def sell_car(self, sale: Sale) -> Car:
        index = SortedDict()
        with open(self.sale_dir, 'a') as f:
            f.write(f'{sale.sales_number};{sale.car_vin};{sale.sales_date};{sale.cost}'.ljust(500) + '\n')

        if os.path.exists(self.sale_idx_dir):
            with open(self.sale_idx_dir, 'r') as f:
                for line in f:
                    index[line.split(';')[0]] = line.strip().split(';')[1]

        index[sale.sales_number] = str(len(index))
        with open(self.sale_idx_dir, 'w') as f:
            for key, pos in index.items():
                f.write(f'{key};{pos}\n')

        with open(self.car_idx_dir, 'r') as f:
            for line in f:
                if sale.car_vin == line.split(';')[0]:
                    car_pos = int(line.split(';')[1])
                    break
        
        with open(self.car_dir, 'r+') as f:
            f.seek(car_pos * 501)
            vin, model, price, date_start = f.read(500).rstrip().split(';')[:-1]
            f.seek(car_pos * 501)
            f.write(f'{vin};{model};{price};{date_start};sold'.ljust(500))

        return Car(vin=vin, model=int(model), price=Decimal(price), date_start=date_start, status=CarStatus.sold)

    # Задание 3. Доступные к продаже
    def get_cars(self, status: CarStatus) -> list[Car]:
        available_cars = []
        with open(self.car_dir, 'r') as f:
            for line in f:
                vin, model, price, date_start, status = line.strip().split(';')
                if status == 'available':
                    available_cars.append(Car(vin=vin, model=int(model), price=Decimal(price), date_start=date_start, status=CarStatus(status)))
        
        # available_cars.sort(key=lambda x: x.vin) нужно же сортировать было
        return available_cars

    # Задание 4. Детальная информация
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        car_pos = self._find_object(self.car_idx_dir, vin)
        if car_pos is None:
            return

        with open(self.car_dir, 'r') as f:
            f.seek(car_pos * 501)
            model_id, price, date_start, status = f.read(500).rstrip().split(';')[1:]
        
        model_pos = self._find_object(self.model_idx_dir, model_id)
        if model_pos is None:
            return

        with open(self.model_dir, 'r') as f:
            f.seek(model_pos * 501)
            model, brand = f.read(500).rstrip().split(';')[1:]

        if status == 'sold':
            with open(self.sale_dir, 'r') as f:
                for line in f:
                    sales_vin, sales_date, cost = line.rstrip().split(';')[1:]
                    cost = Decimal(cost)
                    if vin == sales_vin:
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
            sales_cost=cost)
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

        with open(self.car_dir, 'r+') as f:
            f.seek(pos * 501)
            model, price, date_start, status = f.read(500).rstrip().split(';')[1:]
            f.seek(pos * 501)
            f.write(f'{new_vin};{model};{price};{date_start};{status}')

        return Car(vin=new_vin, model=model, date_start=date_start, price=Decimal(price), status=CarStatus(status))

    # Задание 6. Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        # sale_pos = self._find_object(self.sale_idx_dir, sales_number)
        # if sale_pos is None:
        #     return
        # with open(self.sale_dir, 'r+') as f:
        #     f.seek(sale_pos * 501)
        #     sale = f.read(500).rstrip().split(';')[:-1]
        #     f.seek(501)
        #     f.write(';'.join(sale) + 'False')
        raise NotImplementedError

    # Задание 7. Самые продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        raise NotImplementedError
