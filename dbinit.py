import os
from peewee import AutoField, Model, CharField, IntegerField, DateField, BooleanField, CompositeKey, DecimalField, ForeignKeyField, SQL, SqliteDatabase

path = os.path.dirname(os.path.abspath(__file__))
db_file = 'database.sqlite'

db = SqliteDatabase(os.path.join(path, db_file))

path = os.path.dirname(os.path.abspath(__file__))
db_file = 'database_empty.sqlite'
db = SqliteDatabase(os.path.join(path, db_file))

# class ChartType(Enum):
#     DAY = "DAY"
#     MONTH = "MONTH"
#     YEAR = "YEAR"

class PPETable(Model):
    id = CharField(primary_key=True)
    ppe = CharField(unique=True)
    tariffCode = CharField()
    type = CharField()
    name = CharField()
    last_update_date = DateField(null=True)
    is_active = BooleanField(default=True)

    class Meta:
        database = db
        table_name = 'PPE'
        constraints = [SQL('UNIQUE (ppe, tariffCode)')]

class MeterTable(Model):
    id = AutoField() # Meter point
    ppe_id = ForeignKeyField(PPETable, backref='zones')
    meter_type = CharField()
    last_update_date = DateField(null=True)
    first_date = DateField(null=True)

    class Meta:
        database = db
        table_name = 'METER'
        constraints = [SQL('UNIQUE (ppe_id, meter_type)')]

class CounterTable(Model):
    id = AutoField()
    meter_id = ForeignKeyField(MeterTable, backref='meter')
    tariff = CharField()
    measurement_date = DateField(null=True)
    meter_value = DecimalField(max_digits=15, decimal_places=5, null=True)

    class Meta:
        database = db
        table_name = 'COUNTER'

class ChartTable(Model):
    id = IntegerField()
    meter_type = CharField() 
    year = IntegerField()
    month = IntegerField(null=True)
    day = IntegerField(null=True)
    value =CharField()

    class Meta:
        database = db
        table_name = 'CHART_CACHE'
        primary_key = CompositeKey('id', 'year', 'month', 'day')    

class MainChartTable(Model):
    mp = CharField()
    meter_type = CharField() 
    zone = IntegerField()
    tm = IntegerField()
    value = DecimalField(max_digits=20, decimal_places=16, null=True)
    tarAvg = DecimalField(max_digits=20, decimal_places=16, null=True)
    est = BooleanField(default=False)
    cplt = BooleanField(default=False)

    class Meta:
        database = db
        table_name = 'CHART'
        primary_key = CompositeKey('mp', 'meter_type', 'zone', 'tm')  





def databaseInit():
    db.create_tables([PPETable], safe=True)
    db.create_tables([MeterTable], safe=True)
    db.create_tables([CounterTable], safe=True)
    db.create_tables([ChartTable], safe=True)
    db.create_tables([MainChartTable], safe=True)


if __name__ == "__main__":
    databaseInit()    