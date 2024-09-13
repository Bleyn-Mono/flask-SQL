from pathlib import Path
from datetime import datetime
from db import db, DriverModel, StartLogModel, EndLogModel

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
ABBR_FILE = DATA_DIR / "abbreviations.txt"
STARTLOG_FILE = DATA_DIR / "start.log"
ENDLOG_FILE = DATA_DIR / "end.log"
DATETIME_FORMAT = '%Y-%m-%d_%H:%M:%S.%f'
STRTIME_FORMAT = '%M:%S.%f'
TOP_DELIMITER = 15


def read_data_file(file_path: Path) -> list:
    """This function reads data from files located in the data folder,
         called for files of race times and abbreviations of racers"""
    with open(file_path, 'r') as fp:
        content = [line.strip() for line in fp if line.strip()]
        return content


def get_all_racer(order):
    # Определяем порядок сортировки в зависимости от значения параметра order
    """
    Retrieve and return a list of all racers with their details, sorted by their result time.

    Args:
        order (str): The order in which to sort the racers.
                     Accepts 'asc' for ascending order and 'desc' for descending order.

    Returns:
        list: A list of dictionaries, each containing the following keys:
            - 'code': The code of the racer.
            - 'name': The name of the racer.
            - 'team': The team of the racer.
            - 'result_time': The result time of the racer in the format '%H:%M:%S.%f'.

    Raises:
        ValueError: If the order parameter is not 'asc' or 'desc'.
    """
    if order == 'asc':
        sort_order = DriverModel.result_time.asc()
    elif order == 'desc':
        sort_order = DriverModel.result_time.desc()
    else:
        raise ValueError("Invalid order parameter. Use 'asc' or 'desc'.")
    query = (
        DriverModel .select(
            DriverModel, StartLogModel.datetime.alias('start_time'), EndLogModel.datetime.alias('end_time')) .join(
            StartLogModel, on=(
                StartLogModel.driver_id == DriverModel.id)) .join(
                    EndLogModel, on=(
                        EndLogModel.driver_id == DriverModel.id)) .order_by(sort_order))  # сортировка
    data_list = []
    for driver in query:
        data_list.append({
            'code': driver.code,
            'name': driver.name,
            'team': driver.team,
            'result_time': driver.result_time.strftime('%H:%M:%S.%f')
        })
    return data_list


def swap_times(code):
    """
    Swap the start and end times for a driver if the start time is after the end time.

    This function retrieves the driver with the given code and checks if their start time
    is after their end time. If so, it swaps the times and saves the updated records to the database.

    Args:
        code (str): The code of the driver whose times need to be swapped.

    Raises:
        Exception: If there is an error during the process, an exception is caught and
                   an error message is printed to the console.
    """
    try:
        driver = DriverModel.get(DriverModel.code == code)
        start_log = StartLogModel.get(StartLogModel.driver == driver.id)
        end_log = EndLogModel.get(EndLogModel.driver == driver.id)
        if start_log.datetime > end_log.datetime:
            start_datetime = start_log.datetime
            end_datetime = end_log.datetime

            start_log.datetime = end_datetime
            end_log.datetime = start_datetime

            start_log.save()
            end_log.save()
    except Exception as e:
        print(f"Error swap data {e}")


def result_update():
    """
    Update the result times for all drivers.

    This function iterates over all drivers in the database and calculates the result time
    as the difference between the end log and start log times. It then updates the
    driver's result time in the database.

    The updates are performed within an atomic transaction. If an error occurs during the
    process, the transaction is rolled back and an error message is printed to the console.

    Raises:
        Exception: If there is an error during the process, the transaction is rolled back
                   and an error message is printed to the console.
    """
    drivers = DriverModel.select()
    with db.atomic() as transaction:
        try:
            for driver in drivers:
                start_log = StartLogModel.get_or_none(
                    StartLogModel.driver == driver)
                end_log = EndLogModel.get_or_none(EndLogModel.driver == driver)
                if start_log and end_log:
                    result_time = (end_log.datetime - start_log.datetime)
                    driver.result_time = result_time
                    driver.save()
        except Exception as e:
            transaction.rollback()
            print(f"Error updating result times {e}")


def get_racer_by_code(name):
    """
    Retrieve a racer's details by their code.

    This function fetches a driver from the database based on the provided code.
    It then constructs a dictionary containing the driver's code, name, team, and
    formatted result time.

    Args:
        name (str): The code of the driver to retrieve.

    Returns:
        list: A list containing a single dictionary with the driver's details:
            - code (str): The driver's code.
            - name (str): The driver's name.
            - team (str): The driver's team.
            - result_time (str): The driver's result time formatted as '%H:%M:%S.%f'.

    Raises:
        peewee.DoesNotExist: If no driver with the given code exists in the database.
    """
    query = DriverModel.get(DriverModel.code == name)
    racer_by_code = [{
        'code': query.code,
        'name': query.name,
        'team': query.team,
        'result_time': query.result_time.strftime('%H:%M:%S.%f')
    }]
    return racer_by_code


def store_data_from_files_to_db():
    """
    Read data from files and store it in the database.

    This function reads abbreviation, start log, and end log data from respective files.
    It then populates the database with this data, ensuring that drivers and their logs
    are correctly stored. If a driver already exists, their information is updated.
    It also ensures that the start and end times are correctly ordered by swapping if necessary.

    Reads data from:
        - ABBR_FILE: Contains driver abbreviations, names, and teams.
        - STARTLOG_FILE: Contains start log times.
        - ENDLOG_FILE: Contains end log times.

    Uses transactions to ensure atomicity, rolling back if any error occurs.

    Raises:
        Exception: If any error occurs during the database operations, the transaction is rolled back
                   and the error message is printed.
    """
    abbr_data = read_data_file(ABBR_FILE)
    start_data = read_data_file(STARTLOG_FILE)
    end_data = read_data_file(ENDLOG_FILE)
    with db.atomic() as transaction:
        try:
            drivers = {}
            for abbr in abbr_data:
                code, name, team = abbr.split('_', 2)
                driver, created = DriverModel.get_or_create(
                    code=code, defaults={'name': name, 'team': team})
                if not created:
                    driver.name = name
                    driver.team = team
                    driver.save()
                drivers[code] = driver
            for start_time in start_data:
                code = start_time[:3]
                data_time = datetime.strptime(start_time[3:], DATETIME_FORMAT)
                if not StartLogModel.get_or_none(
                        driver=drivers[code], datetime=data_time):
                    StartLogModel.create(
                        driver=drivers[code], datetime=data_time)
            for end_time in end_data:
                code = end_time[:3]
                data_time = datetime.strptime(end_time[3:], DATETIME_FORMAT)
                if not EndLogModel.get_or_none(
                        driver=drivers[code], datetime=data_time):
                    EndLogModel.create(
                        driver=drivers[code], datetime=data_time)
                swap_times(code)
        except Exception as e:
            transaction.rollback()
            print(f"Error saving data {e}")
