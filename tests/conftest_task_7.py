from datetime import datetime

import unittest
from unittest.mock import mock_open, patch
from pathlib import Path

from peewee import SqliteDatabase

import report_racers
from main import app
from db import DriverModel, StartLogModel, EndLogModel

import xml.etree.ElementTree as ET
from lxml import etree

# Создаем тестовую базу данных
test_db = SqliteDatabase(':memory:')


class TestDataFromFileToDb(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        test_db.bind([DriverModel, StartLogModel, EndLogModel],
                     bind_refs=False, bind_backrefs=False)
        test_db.connect()
        test_db.create_tables([DriverModel, StartLogModel, EndLogModel])

    @classmethod
    def tearDownClass(cls):
        # Закрываем соединение с тестовой базой данных и удаляем таблицы
        test_db.drop_tables([DriverModel, StartLogModel, EndLogModel])
        test_db.close()

    def setUp(self):
        # Подготавливаем данные для тестов
        self.driver1 = DriverModel.create(
            code='DR1', name='Driver One', team='Team A')
        self.driver2 = DriverModel.create(
            code='DR2', name='Driver Two', team='Team B')
        StartLogModel.create(
            driver=self.driver1, datetime=datetime(
                2023, 1, 1, 12, 0, 0))
        EndLogModel.create(
            driver=self.driver1, datetime=datetime(
                2023, 1, 1, 12, 1, 0))
        StartLogModel.create(
            driver=self.driver2, datetime=datetime(
                2023, 1, 1, 12, 0, 0))
        EndLogModel.create(
            driver=self.driver2, datetime=datetime(
                2023, 1, 1, 12, 2, 0))

    def tearDown(self):
        # Очищаем таблицы после каждого теста
        DriverModel.delete().execute()
        StartLogModel.delete().execute()
        EndLogModel.delete().execute()

    def test_store_data_from_files_to_db(self):
        drivers = DriverModel.select()
        self.assertGreater(
            len(drivers),
            0,
            "Должны быть сохранены записи о водителях")

    def test_swap_times(self):

        start_log = StartLogModel.get(StartLogModel.driver == self.driver2)
        end_log = EndLogModel.get(EndLogModel.driver == self.driver2)

        start_log.datetime = datetime(2023, 1, 1, 12, 2, 0)
        end_log.datetime = datetime(2023, 1, 1, 12, 0, 0)
        start_log.save()
        end_log.save()

        report_racers.swap_times('DR2')

        start_log = StartLogModel.get(StartLogModel.driver == self.driver2)
        end_log = EndLogModel.get(EndLogModel.driver == self.driver2)

        # Проверяем, что даты поменялись местами
        self.assertEqual(start_log.datetime, datetime(2023, 1, 1, 12, 0, 0))
        self.assertEqual(end_log.datetime, datetime(2023, 1, 1, 12, 2, 0))

    def test_result_update(self):
        report_racers.result_update()
        drivers = DriverModel.select()
        for driver in drivers:
            self.assertIsNotNone(
                driver.result_time,
                "Результатное время должно быть обновлено")

    def test_get_all_racer(self):
        report_racers.result_update()
        racers = report_racers.get_all_racer('asc')
        self.assertGreater(
            len(racers),
            0,
            "Должны быть возвращены записи о водителях")
        self.assertTrue(all('result_time' in racer for racer in racers),
                        "Каждая запись должна содержать result_time")

    def test_get_racer_by_code(self):
        report_racers.result_update()
        driver = DriverModel.select().first()
        racer = report_racers.get_racer_by_code(driver.code)
        self.assertIsNotNone(racer, "Должна быть возвращена запись о водителе")
        self.assertEqual(
            racer[0]['code'],
            driver.code,
            "Код водителя должен совпадать")


class TestMonacoFileFlask(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()
        with app.app_context():
            # Создание всех таблиц
            test_db.bind([DriverModel, StartLogModel, EndLogModel],
                         bind_refs=False, bind_backrefs=False)
            test_db.connect()
            test_db.create_tables([DriverModel, StartLogModel, EndLogModel])

    @classmethod
    def tearDownClass(cls):
        try:
            # Удаление всех таблиц
            test_db.drop_tables([DriverModel, StartLogModel, EndLogModel])
        except Exception as e:
            print(f"Error dropping tables: {e}")
        finally:
            test_db.close()

    def setUp(self):
        with app.app_context():
            driver1 = DriverModel.create(
                code='DR1', name='Driver One', team='Team A')
            driver2 = DriverModel.create(
                code='DR2', name='Driver Two', team='Team B')
            StartLogModel.create(
                driver=driver1, datetime=datetime(
                    2023, 1, 1, 12, 0, 0))
            EndLogModel.create(
                driver=driver1, datetime=datetime(
                    2023, 1, 1, 12, 1, 0))
            StartLogModel.create(
                driver=driver2, datetime=datetime(
                    2023, 1, 1, 12, 0, 0))
            EndLogModel.create(
                driver=driver2, datetime=datetime(
                    2023, 1, 1, 12, 2, 0))

    def tearDown(self):
        with app.app_context():
            # Очистка таблиц после каждого теста
            DriverModel.delete().execute()
            StartLogModel.delete().execute()
            EndLogModel.delete().execute()

    def test_read_file(self):
        with patch("builtins.open", new_callable=mock_open, read_data="line1\nline2\nline3") as mock_file_open:
            file_path = Path("test_data.txt")
            expected_content = ["line1", "line2", "line3"]
            mock_content = report_racers.read_data_file(file_path)
            self.assertEqual(mock_content, expected_content)

    def test_index(self):
        report_racers.result_update()
        response = self.client.get('/report')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Driver One', response.data)
        self.assertIn(b'Driver Two', response.data)

    def test_info_in_drivers(self):
        report_racers.result_update()
        response = self.client.get('/report/drivers/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'DR1', response.data)
        self.assertIn(b'DR2', response.data)
        self.assertIn(b'<a href="/report/drivers/DR1">DR1 </a>', response.data)
        self.assertIn(b'<a href="/report/drivers/DR2">DR2 </a>', response.data)

    def test_name_page(self):
        report_racers.result_update()
        response = self.client.get('/report/drivers/DR1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Result DR1', response.data)
        self.assertIn(b'Rider data : Driver One', response.data)
        self.assertIn(b'Comand data : Team A', response.data)
        self.assertIn(b'Time : 00:01:00.000000', response.data)

    def test_index_api(self):
        report_racers.result_update()
        response = self.client.get('/api/v1/report/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json,
                         [{'code': 'DR1',
                           'name': 'Driver One',
                           'team': 'Team A',
                           'result_time': '00:01:00.000000'},
                          {'code': 'DR2',
                           'name': 'Driver Two',
                             'team': 'Team B',
                             'result_time': '00:02:00.000000'}])

    def test_index_api_xml(self):
        expected_data = [{'time': '00:01:00.000000',
                          'code': 'DR1',
                          'name': 'Driver One',
                          'team': 'Team A'},
                         {'time': '00:02:00.000000',
                          'code': 'DR2',
                          'name': 'Driver Two',
                          'team': 'Team B'}]
        report_racers.result_update()
        response = self.client.get('/api/v1/report/?format=xml')
        self.assertEqual(response.status_code, 200)

        root = etree.fromstring(response.data)
        self.assertEqual(root.tag, 'drivers')
        # Проверяем содержимое
        for index, driver in enumerate(root.findall('driver')):
            # Проверяем наличие и содержимое тега <time>
            time_element = driver.find('time')
            self.assertIsNotNone(time_element)
            self.assertEqual(time_element.text, expected_data[index]['time'])

            data_element = driver.find('data')
            self.assertIsNotNone(data_element)

            code_element = data_element.find('code')
            self.assertIsNotNone(code_element)
            self.assertEqual(code_element.text, expected_data[index]['code'])

            name_element = data_element.find('name')
            self.assertIsNotNone(name_element)
            self.assertEqual(name_element.text, expected_data[index]['name'])

            team_element = data_element.find('team')
            self.assertIsNotNone(team_element)
            self.assertEqual(team_element.text, expected_data[index]['team'])

    def test_info_driver_api(self):
        report_racers.result_update()
        response = self.client.get('/api/v1/report/drivers/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('/api/v1/report/drivers/DR1/', response.json[0]['code'])
        self.assertIn('/api/v1/report/drivers/DR2/', response.json[1]['code'])

    def test_info_driver_api_xml(self):
        expected_data = [{'time': '00:01:00.000000',
                          'code': 'http://localhost/api/v1/report/drivers/DR1/',
                          'name': 'Driver One',
                          'team': 'Team A'},
                         {'time': '00:02:00.000000',
                          'code': 'http://localhost/api/v1/report/drivers/DR2/',
                          'name': 'Driver Two',
                          'team': 'Team B'}]
        report_racers.result_update()
        response = self.client.get('/api/v1/report/drivers/?format=xml')
        self.assertEqual(response.status_code, 200)

        root = etree.fromstring(response.data)
        self.assertEqual(root.tag, 'drivers')
        # Проверяем содержимое
        for index, driver in enumerate(root.findall('driver')):
            # Проверяем наличие и содержимое тега <time>
            time_element = driver.find('time')
            self.assertIsNotNone(time_element)
            self.assertEqual(time_element.text, expected_data[index]['time'])

            data_element = driver.find('data')
            self.assertIsNotNone(data_element)

            code_element = data_element.find('code')
            self.assertIsNotNone(code_element)
            self.assertEqual(code_element.text, expected_data[index]['code'])

            name_element = data_element.find('name')
            self.assertIsNotNone(name_element)
            self.assertEqual(name_element.text, expected_data[index]['name'])

            team_element = data_element.find('team')
            self.assertIsNotNone(team_element)
            self.assertEqual(team_element.text, expected_data[index]['team'])

    def test_name_page_api(self):
        report_racers.result_update()
        response = self.client.get('/api/v1/report/drivers/DR1/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json,
                         [{'code': 'DR1',
                           'name': 'Driver One',
                           'team': 'Team A',
                           'result_time': '00:01:00.000000'}])

    def test_name_page_api_xml(self):
        report_racers.result_update()
        response = self.client.get('/api/v1/report/drivers/DR1/?format=xml')
        self.assertEqual(response.status_code, 200)

        root = etree.fromstring(response.data)
        self.assertEqual(root.tag, 'drivers')
        # Проверяем содержимое
        driver = root.findall('driver')
        time_element = driver[0].find('time')
        self.assertIsNotNone(time_element)
        self.assertEqual(time_element.text, '00:01:00.000000')

        data_element = driver[0].find('data')
        self.assertIsNotNone(data_element)

        code_element = data_element.find('code')
        self.assertIsNotNone(code_element)
        self.assertEqual(code_element.text, 'DR1')

        name_element = data_element.find('name')
        self.assertIsNotNone(name_element)
        self.assertEqual(name_element.text, 'Driver One')

        team_element = data_element.find('team')
        self.assertIsNotNone(team_element)
        self.assertEqual(team_element.text, 'Team A')


if __name__ == '__main__':
    unittest.main()
