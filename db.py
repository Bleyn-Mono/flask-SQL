from peewee import SqliteDatabase, Model, TextField, DateTimeField, ForeignKeyField, TimeField


db = SqliteDatabase('my_database.db')  # Файл базы данных


class BaseModel(Model):
    class Meta:
        database = db


class DriverModel(BaseModel):
    """
    Model representing a driver.

    Fields:
        code (TextField): The unique code for the driver.
        name (TextField): The name of the driver.
        team (TextField): The team the driver belongs to.
        result_time (TimeField, optional): The result time of the driver. Can be null.
    """
    code = TextField()
    name = TextField()
    team = TextField()
    result_time = TimeField(null=True)


class StartLogModel(BaseModel):
    """
    Model representing a start log entry.

    Fields:
        datetime (DateTimeField): The date and time when the start log entry was recorded.
        driver (ForeignKeyField): Foreign key to the DriverModel, indicating which driver the start log belongs to.
    """
    datetime = DateTimeField()
    driver = ForeignKeyField(DriverModel, backref='start_time')


class EndLogModel(BaseModel):
    """
    Model representing an end log entry.

    Fields:
        datetime (DateTimeField): The date and time when the end log entry was recorded.
        driver (ForeignKeyField): Foreign key to the DriverModel, indicating which driver the end log belongs to.
    """
    datetime = DateTimeField()
    driver = ForeignKeyField(DriverModel, backref='end_time')
