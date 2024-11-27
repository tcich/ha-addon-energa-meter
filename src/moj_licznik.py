from peewee import SqliteDatabase, PostgresqlDatabase
from playhouse.shortcuts import ReconnectMixin
from datetime import datetime, timedelta, date
import calendar, requests, re, time, json, os, logging
import http.cookiejar as cookiejar
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
from enum import Enum
from peewee import AutoField, Model, CharField, IntegerField, DateField, BooleanField, CompositeKey, DecimalField, ForeignKeyField, SQL, TextField, TimestampField
import urllib.parse

logger = logging.getLogger("energaMeter")

class ReconnectPostgresqlDatabase(ReconnectMixin, PostgresqlDatabase):
    pass

if postgresql_connstring := os.getenv("POSTGRESQL_CONNSTRING"):
    from psycopg2.extensions import parse_dsn
    db_name = parse_dsn(postgresql_connstring)['dbname']
    db_host = parse_dsn(postgresql_connstring)['host']
    db = ReconnectPostgresqlDatabase(db_name, dsn=postgresql_connstring)
    logger.info(f"Używam bazy PostgreSQL „{db_name}” na {db_host}")
else:
    path = os.path.dirname(os.path.abspath(__file__))
    db_file = 'data/database.sqlite'
    db = SqliteDatabase(os.path.join(path, db_file))

class ChartType(Enum):
    DAY = "DAY"
    MONTH = "MONTH"
    YEAR = "YEAR"

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
        constraints = [SQL('UNIQUE ("ppe", "tariffCode")')]

class MeterTable(Model):
    id = AutoField() # Meter point
    ppe_id = ForeignKeyField(PPETable, backref='zones')
    meter_type = CharField()
    last_update_date = DateField(null=True)
    first_date = DateField(null=True)

    class Meta:
        database = db
        table_name = 'METER'
        constraints = [SQL('UNIQUE ("ppe_id", "meter_type")')]

class CounterTable(Model):
    id = AutoField()
    meter_id = ForeignKeyField(MeterTable, backref='meter')
    tariff = CharField()
    measurement_date = DateField(null=True)
    meter_value = DecimalField(max_digits=15, decimal_places=5, null=True)

    class Meta:
        database = db
        table_name = 'COUNTER'

# class CounterTable(Model):
#     meter_id = ForeignKeyField(MeterTable, backref='zones')
#     measurement_date = DateField(null=True)
#     meter_value = DecimalField(max_digits=15, decimal_places=5, null=True)

#     class Meta:
#         database = db


class ChartTable(Model):
    id = IntegerField()
    meter_type = CharField() 
    year = IntegerField()
    month = IntegerField(null=True)
    day = IntegerField(null=True)
    value = TextField()

    class Meta:
        database = db
        table_name = 'CHART_CACHE'
        primary_key = CompositeKey('id', 'year', 'month', 'day')    

class MainChartTable(Model):
    mp = CharField()
    meter_type = CharField() 
    zone = IntegerField()
    tm = TimestampField()
    value = DecimalField(max_digits=20, decimal_places=16, null=True)
    tarAvg = DecimalField(max_digits=20, decimal_places=16, null=True)
    est = BooleanField(default=False)
    cplt = BooleanField(default=False)

    class Meta:
        database = db
        table_name = 'CHART'
        primary_key = CompositeKey('mp', 'meter_type', 'zone', 'tm')  

def znajdz_typ_odbiorcy(element):
    typ_odbiorcy = ''
    div_elements = element.find_all('div', recursive=False)
    for div_element in div_elements:
        typ_span = div_element.find('span', text='Typ')
        if typ_span:
            typ_odbiorcy = typ_span.next_sibling.strip()
            return typ_odbiorcy
        typ_odbiorcy = znajdz_typ_odbiorcy(div_element)  # Rekurencyjne przeszukiwanie zagnieżdżonych div
    return typ_odbiorcy

def findCountners(page):
    table = page.find('table')
    countner_type_list = ["A-", "A+"]
    data_list = []

    # Jeśli znaleźliśmy tabelę, możemy przeszukać jej wiersze i komórki
    if table:
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) > 1:
                # Pobieramy opis z pierwszej komórki
                description = cells[0].text.strip()
                
                # Pomijamy, jeśli rodzaj_licznika jest pusty
                if not description:
                    continue

                # Usuwamy datę z opisu
                description_parts = description.split('\n')
                meter_type = description_parts[0][:2].strip()
                
                if meter_type not in countner_type_list:
                    continue

                tariff0 = description_parts[0][2:].strip()
                tariff = ''.join(filter(str.isdigit, tariff0))
                measurement_date = description_parts[1].strip()
                
                # Pobieramy dane liczbowe z drugiej komórki
                data = cells[1].text.strip()
                
                # Usuwamy znaki nowej linii i spacje z danych
                data = data.replace('\n', '').replace(' ', '')
                
                data = data.replace(',', '.')
                
                # Dzielimy dane na część całkowitą i część dziesiętną
                parts = data.split('.')
                if len(parts) == 2:
                    integer_part = parts[0]
                    decimal_part = parts[1]
                else:
                    integer_part = parts[0]
                    decimal_part = '0'
                
                data_dict = {
                    "meter_type": meter_type,
                    "tariff": tariff,
                    "measurement_date": measurement_date,
                    "meter_value": f"{integer_part}.{decimal_part}"
                }
                
                data_list.append(data_dict)
    return data_list

class MojLicznik:

    session = requests.Session()
    session.cookies = cookiejar.LWPCookieJar(filename='cookies.txt')

    meter_url = "https://mojlicznik.energa-operator.pl"



    def databaseInit(self):
        db.create_tables([PPETable], safe=True)
        db.create_tables([MeterTable], safe=True)
        db.create_tables([CounterTable], safe=True)
        db.create_tables([ChartTable], safe=True)
        db.create_tables([MainChartTable], safe=True)
        

    def __init__(self):
        self.username = None
        self.password = None
        self.loginStatus = False
        self.data = []  # Change self.data to a list
        self.ppes = []
        self.databaseInit()       

    def login(self, _username, _password):
        
        self.username = _username
        self.password = _password        

        login_url = f"{self.meter_url}/dp/UserLogin.do"

        self.loginStatus = False

        try:
            logger.debug("Pobieram formularz logowania.")
            response = self.session.get(login_url)
            response.raise_for_status() 
            if response.url == 'https://mojlicznik.energa-operator.pl/maintenance.html':
                logger.critical("Trwają prace serwisowe w Mój Licznik. Logowanie nie jest możliwe, spróbuj później.")
                return

        except HTTPError as e:
            logger.error(f"Wystąpił błąd HTTP: {e}")

        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': '_antixsrf'})['value']

        login_data = {
            'j_username': self.username,
            'j_password': self.password,
            'selectedForm': '1',
            'save': 'save',
            'clientOS': 'web',
            '_antixsrf': csrf_token 
        }

        try:
            response = self.session.post(login_url, data=login_data)
            response.raise_for_status()
            
            
        except HTTPError as e:
            logger.error(f"Wystąpił błąd HTTP: {e}")     

        soup = BeautifulSoup(response.text, 'html.parser')

        login_error_text = 'Użytkownik lub hasło niepoprawne'
        login_error = soup.find('div', text=login_error_text)

        if login_error:
            logger.critical(login_error_text)
            return
        else:
            self.loginStatus = True
            logger.info(f"Zalogowano")

            body = soup.find('body')
            type_value = znajdz_typ_odbiorcy(body)

            logger.debug(f"Typ umowy: {type_value}.")
            select_elements = soup.find_all('script', type='text/javascript')
            meter_isd = []
            for el in select_elements:
                pattern = r"id:\s+(\d+),[\s\S]*?ppe:\s+'([\d\s]+)',[\s\S]*?tariffCode:\s+'([^']+)',[\s\S]*?name:\s+'([^']+)'"
                matches = re.search(pattern, el.text)
                if matches:
                    id_value = matches.group(1)
                    ppe_value = matches.group(2)
                    tariffCode_value = matches.group(3)
                    name_value = matches.group(4)
                    meter_isd.append(id_value)
                    retrieved_record = PPETable.get_or_none(id=id_value)
                    if retrieved_record:
                        logger.info(f"Licznik {id_value} istnieje w systemie.")
                        if not retrieved_record.is_active:
                            retrieved_record.is_active = True
                            retrieved_record.save()                   
                    else:
                        logger.info(f"Licznik {id_value} nie istnieje w systemie, zostanie dodany.")
                        data = PPETable.create(
                                id=id_value,
                                ppe=ppe_value,
                                tariffCode=tariffCode_value,
                                type=type_value,
                                name=name_value
                            )                    
            update_query = PPETable.update(is_active=0).where(PPETable.id.not_in(meter_isd))
            update_query.execute()       

    def logout(self):
        logout_url = f"{self.meter_url}/dp/MainLogout.go"
        try:
            response = self.session.get(logout_url)
            response.raise_for_status()
            self.loginStatus = False
            logger.info(f"Wylogowano.")
        except HTTPError as e:
            logger.error(f"Wystąpił błąd HTTP: {e}")

    def update_countners(self):

        query = PPETable.select().where(PPETable.is_active == True)
        result_ppes = query.execute()
        for p in result_ppes:
            meter_url = f"{self.meter_url}/dp/UserData.do?mpc={p.id}&ppe={p.ppe}"
            try:
                response = self.session.get(meter_url)
                response.raise_for_status()  
                soup = BeautifulSoup(response.text, 'html.parser')
                countners_dict = findCountners(soup)

                for c in countners_dict:
                    mn, mu = MeterTable.get_or_create(ppe_id=p.id, meter_type=c['meter_type'])
                    mn.last_update_date = datetime.now()
                    mn.save()
                    cn, cu = CounterTable.get_or_create(
                        meter_id = mn.id,
                        tariff=c['tariff']
                    )
                                                    
                    cn.meter_value = c['meter_value']
                    cn.measurement_date = c['measurement_date']
                    cn.save()
                    
                    logger.info(f"Zapisano stan licznika {p.id} {c['meter_type']} taryfa {c['tariff']} z dnia: {c['measurement_date']} : {c['meter_value']}")
            except HTTPError as e:
                logger.error(f"Wystąpił błąd HTTP: {e}")

    def update_first_date(self):
        ppes_query = PPETable.select().where(PPETable.is_active == True)
        result_ppes = ppes_query.execute()
        for p in result_ppes:
            meters_query = MeterTable.select().where((MeterTable.ppe_id == p.id) & (MeterTable.first_date.is_null(True)))
            meters_result = meters_query.execute()

            for meter in meters_result:
                meter_type = meter.meter_type

                print(f"Szukam najstarsze dane historyczne licznika {p.name} (PPE: {p.ppe}, {p.id}) typ: {meter_type}") 
                meter_point = p.id
                max_years_back = 5
                start_date = datetime.now()
                last_chart_year = None
                for n in range(max_years_back + 1):
                    first_day_of_year = datetime(start_date.year-n, 1, 1)
                    data_json = self.download_chart(ChartType.YEAR, first_day_of_year, meter_point, meter_type)
                    if data_json:
                        data = json.loads(data_json)    
                        if data and data.get("mainChart") and len(data["mainChart"]) > 0:                    
                            last_chart_year = first_day_of_year.year
                last_chart_month = None
                max_month = 12
                for n in range(max_month, 0, -1):
                    first_day_of_month = datetime(last_chart_year, n, 1)
                    data_json = self.download_chart(ChartType.MONTH, first_day_of_month, meter_point, meter_type)
                    if data_json:
                        data = json.loads(data_json)  
                        if data and data.get("mainChart") and len(data["mainChart"]) > 0:
                            last_chart_month = n    
                last_chart_day = None
                max_day = 31
                first_day_of_day = datetime(last_chart_year, last_chart_month, 1)
                _, max_day = calendar.monthrange(first_day_of_day.year, first_day_of_day.month)
                for n in range(max_day, 0, -1):
                    first_day_of_day = datetime(last_chart_year, last_chart_month, n)
                    data_json = self.download_chart(ChartType.DAY, first_day_of_day, meter_point, meter_type)
                    if data_json:
                        data = json.loads(data_json)        
                        if data and data.get("mainChart") and len(data["mainChart"]) > 0:
                            last_chart_day = n
                first_date = datetime(last_chart_year, last_chart_month, last_chart_day).date()
                print(f"Najstarsze dane historyczne dla licznika {p.name} (PPE: {p.ppe}, {p.id}) typ: {meter_type}: {first_date}")    
                meter.first_date = first_date
                meter.save()

    def save_main_charts(self, mp, vals, m_type):
        for val in vals:
            try:
                logger.debug(f"save_main_charts: mp: {mp}, val: {val}, meter_type: {m_type}")
                z = val["zones"]
                tm = int(val["tm"]) / 1000 # convert JS timestamp (milliseconds) to unix (seconds)
                if z[0]:
                    # MainChartTable.get_or_create(tm = val["tm"], zone = 1, value = z[0], tarAvg=val["tarAvg"], est=val["est"], cplt=val["cplt"])
                    try:
                        existing_record = MainChartTable.get((MainChartTable.meter_type == m_type) & (MainChartTable.mp == mp) & (MainChartTable.tm == tm) & (MainChartTable.zone == 1))
                    except MainChartTable.DoesNotExist:
                        # Jeśli rekord nie istnieje, utwórz nowy
                        MainChartTable.create(
                            mp=mp,
                            meter_type=m_type,
                            tm=tm,
                            zone=1,
                            value=z[0],
                            tarAvg=val["tarAvg"],
                            est=val["est"],
                            cplt=val["cplt"]
                        )
                
                if z[1]:
                    try:
                        existing_record = MainChartTable.get((MainChartTable.meter_type == m_type) & (MainChartTable.mp == mp) & (MainChartTable.tm == tm) & (MainChartTable.zone == 2))
                    except MainChartTable.DoesNotExist:
                        # Jeśli rekord nie istnieje, utwórz nowy
                        MainChartTable.create(
                            mp=mp,
                            meter_type=m_type,
                            tm=tm,
                            zone=2,
                            value=z[1],
                            tarAvg=val["tarAvg"],
                            est=val["est"],
                            cplt=val["cplt"]
                        )                
                
                if z[2]:
                    try:
                        existing_record = MainChartTable.get((MainChartTable.meter_type == m_type) & (MainChartTable.mp == mp) & (MainChartTable.tm == tm) & (MainChartTable.zone == 3))
                    except MainChartTable.DoesNotExist:
                        # Jeśli rekord nie istnieje, utwórz nowy
                        MainChartTable.create(
                            mp=mp,
                            meter_type=m_type,
                            tm=tm,
                            zone=3,
                            value=z[2],
                            tarAvg=val["tarAvg"],
                            est=val["est"],
                            cplt=val["cplt"]
                        )
                                                        
            except Exception as e:
                logger.error(f"Wystąpił błąd: {str(e)}")

        return None
    
    def download_chart(self, type, date, meter_point, meter_type, update_mode=False):

        if type == ChartType.DAY:
            chart_type = "DAY"
            first_day = datetime(date.year, date.month, date.day)
            tsm_date = int(time.mktime(first_day.timetuple()) * 1000)            

        if type == ChartType.MONTH:
            chart_type = "MONTH"
            first_day = datetime(date.year, date.month, 1)
            tsm_date = int(time.mktime(first_day.timetuple()) * 1000)

        if type == ChartType.YEAR:
            chart_type = "YEAR"
            first_day = datetime(date.year, 1, 1)
            tsm_date = int(time.mktime(first_day.timetuple()) * 1000)

        # meter_type = 'A+'
        chart_url = f"{self.meter_url}/dp/resources/chart?mainChartDate={tsm_date}&type={chart_type}&meterPoint={meter_point}&mo={urllib.parse.quote_plus(meter_type)}"
        logger.debug(f"chart_url: {chart_url}")
        try:
            response = self.session.get(chart_url)
            data = json.loads(response.text)
            response.raise_for_status()
            if data["response"]:
                id = data["response"]["meterPoint"]
                mainChartDate = data["response"]["mainChartDate"]
                mainChart = data["response"]["mainChart"]
                if type == ChartType.DAY:
                    self.save_main_charts(meter_point, mainChart, meter_type)
                
                date = int(mainChartDate) / 1000
                month = None
                day = None
                dt = datetime.fromtimestamp(date)                       
                year = dt.year
                if type == ChartType.MONTH:
                    month = dt.month
                if type == ChartType.DAY:
                    month = dt.month
                    day = dt.day          
                json_dump = json.dumps(data["response"], ensure_ascii=False)
                if update_mode:
                    try:
                        chart_record = ChartTable.get(id=id,year=year, month=month, day=day)
                        chart_record.value = json_dump
                        chart_record.save()
                    except ChartTable.DoesNotExist:
                        chart_record = ChartTable.create(id=id, meter_type=meter_type, value=json_dump, year=year, month=month, day=day)

                else:
                    try:
                        ChartTable.create(id=id, meter_type=meter_type, value=json_dump, year=year, month=month, day=day)
                    except:
                        pass
                return json_dump
            return None 
        except HTTPError as e:
            logger.error(f"Wystąpił błąd HTTP: {e}")

    def download_charts(self, full_mode=False):
        query = PPETable.select().where(PPETable.is_active == True)
        result_ppes = query.execute()
        for p in result_ppes:
            meters_query = MeterTable.select().where((MeterTable.ppe_id == p.id)) # // & (MeterTable.first_date.is_null(True)))
            meters_result = meters_query.execute()

            for meter in meters_result:
                meter_type = meter.meter_type

                logger.info(f"Pobieram dane historyczne dla {p.name} ({p.id}) typ: {meter_type}")
                current_date = meter.first_date
                if not full_mode:
                    current_date = meter.last_update_date - timedelta(days=1)
                
                while current_date <= date.today():
                    try:    
                        if full_mode:                   
                            record = ChartTable.get(id=p.id, meter_type=meter_type, year=current_date.year, month=current_date.month, day=current_date.day)
                            logger.debug(f"Posiadam dane historyczne dla {p.name} ({p.id}) typ: {meter_type} na dzień: {current_date}")
                        else:
                            self.download_chart(ChartType.DAY, current_date, p.id, meter_type) 
                            logger.debug(f"Aktualizuję dane dla {p.name} ({p.id}) typ: {meter_type} na dzień: {current_date}")


                    except ChartTable.DoesNotExist:
                        self.download_chart(ChartType.DAY, current_date, p.id, meter_type) 
                        logger.debug(f"Pobieram dane historyczne dla {p.name} ({p.id}) typ: {meter_type} na dzień: {current_date}")
                    current_date += timedelta(days=1)

    def update_last_days(self):
        today = datetime.today().date()
        query = PPETable.select().where(PPETable.is_active == True)
        result_ppes = query.execute()
        
        for p in result_ppes:
            meters_query = MeterTable.select().where((MeterTable.ppe_id == p.id) & (MeterTable.first_date.is_null(True)))
            meters_result = meters_query.execute()

            for meter in meters_result:
                meter_type = meter.meter_type

                logger.info(f"Aktualizacja danych bieżących dla {p.name} ({p.id}) typ: {meter_type}")
                if not p.last_update_date:
                    p.last_update_date = today - timedelta(days=5)
                    p.save()
                last_update_date = p.last_update_date - timedelta(days=1)
                while last_update_date <= today:
                    logger.debug(f"Aktualizacja danych dla {p.name} ({p.id}) typ: {meter_type} na dzień: {last_update_date}")
                    self.download_chart(ChartType.DAY, last_update_date, p.id, meter_type, True)
                    p.last_update_date = last_update_date
                    p.save()
                    last_update_date += timedelta(days=1)

    def get_current_meters(self, add_daily_char_data=False):

        query = PPETable.select().where(PPETable.is_active == True)
        result_ppes = query.execute()
        for p in result_ppes:
            if add_daily_char_data:
                    query = ChartTable.select().where((ChartTable.id == p.id) & (ChartTable.year == p.measurement_date.year) & (ChartTable.month == p.measurement_date.month) & (ChartTable.day == p.measurement_date.day))
                    query_count = query.count()
                    if (query_count > 0):
                        query_first = query.first()
                        value_json = json.loads(query_first.value)
                        print(query_first.value)
                        zones = value_json.get("zones", [])
                        if zones:
                            zone1_data = zones[0]
                            zone1_main_chart = zone1_data.get("mainChart", [])

    # def set_daily_zones(self):
    #     query = PPETable.select().where(PPETable.is_active == True)
    #     result_ppes = query.execute()

    #     for p in result_ppes:
    #         query = ChartTable.select().where(
    #             (ChartTable.id == p.id) &
    #             ((ChartTable.year > p.measurement_date.year) |
    #             ((ChartTable.year == p.measurement_date.year) &
    #             (ChartTable.month > p.measurement_date.month)) |
    #             ((ChartTable.year == p.measurement_date.year) &
    #             (ChartTable.month == p.measurement_date.month) &
    #             (ChartTable.day >= p.measurement_date.day))
    #         ))

    #         zones_sums = {f"zone{i+1}_daily_chart_sum": 0.0 for i in range(3)}

    #         for chart_entry in query:
    #             value_json = json.loads(chart_entry.value)
    #             main_chart = value_json.get("mainChart", [])

    #             for entry in main_chart:
    #                 zones = entry.get("zones", [])

    #                 for i, value in enumerate(zones):
    #                     if value is not None:
    #                         zones_sums[f"zone{i+1}_daily_chart_sum"] += value
            
    #         for key, value in zones_sums.items():
    #             setattr(p, key, value)
    #         p.save()


    def print_summary_zones(self):
        query = PPETable.select().where(PPETable.is_active == True)
        result_ppes = query.execute()
        for p in result_ppes:
            zon1 = (p.zone1 if p.zone1 is not None else 0 ) + (p.zone1_daily_chart_sum if p.zone1_daily_chart_sum is not None else 0)
            zon2 = (p.zone2 if p.zone2 is not None else 0 ) + (p.zone2_daily_chart_sum if p.zone2_daily_chart_sum is not None else 0)
            zon3 = (p.zone3 if p.zone3 is not None else 0 ) + (p.zone3_daily_chart_sum if p.zone3_daily_chart_sum is not None else 0)
            print(f"{p.name} : {round(zon1, 5)} "
              f"{round(zon2,5)} "
              f"{round(zon3,5)}")

    def get_current_meters_list(self):
        query = PPETable.select().where(PPETable.is_active == True)
        return query.execute()

    def get_current_meter_value(self, meter_id, zone):
        if zone == "zone1":
            pPETable = PPETable.get(PPETable.id == meter_id)
            return pPETable.zone1
        if zone == "zone2":
            pPETable = PPETable.get(PPETable.id == meter_id)
            return pPETable.zone2
        if zone == "zone3":
            pPETable = PPETable.get(PPETable.id == meter_id)
            return pPETable.zone3
        return None                
