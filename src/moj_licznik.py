from peewee import SqliteDatabase
from datetime import datetime, timedelta, date
import calendar, requests, re, time, json
import http.cookiejar as cookiejar
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup
from enum import Enum
from peewee import Model, CharField, IntegerField, DateField, BooleanField, CompositeKey, DecimalField

db = SqliteDatabase('database.sqlite')

class ChartType(Enum):
    DAY = "DAY"
    MONTH = "MONTH"
    YEAR = "YEAR"

class PPETable(Model):
    ppe = CharField()
    tariffCode = CharField()
    name = CharField()
    zone1 = DecimalField(max_digits=15, decimal_places=5, null=True)
    zone2 = DecimalField(max_digits=15, decimal_places=5, null=True)
    zone3 = DecimalField(max_digits=15, decimal_places=5, null=True)
    zone1_daily_chart_sum = DecimalField(max_digits=10, decimal_places=5, null=True)
    zone2_daily_chart_sum = DecimalField(max_digits=10, decimal_places=5, null=True)
    zone3_daily_chart_sum = DecimalField(max_digits=10, decimal_places=5, null=True)    
    number_of_zones = IntegerField(default=0)
    is_active = BooleanField(default=True)
    measurement_date = DateField(null=True)
    first_date = DateField(null=True)
    last_update_date = DateField(null=True) 

    class Meta:
        database = db

class ChartTable(Model):
    id = IntegerField()    
    year = IntegerField()
    month = IntegerField(null=True)
    day = IntegerField(null=True)
    value =CharField()

    class Meta:
        database = db
        primary_key = CompositeKey('id', 'year', 'month', 'day')    

class MainChartTable(Model):
    mp = CharField()
    zone = IntegerField()
    tm = IntegerField()
    value = DecimalField(max_digits=20, decimal_places=16, null=True)
    tarAvg = DecimalField(max_digits=20, decimal_places=16, null=True)
    est = BooleanField(default=False)
    cplt = BooleanField(default=False)

    class Meta:
        database = db
        primary_key = CompositeKey('mp', 'zone', 'tm')  



class MojLicznik:

    session = requests.Session()
    session.cookies = cookiejar.LWPCookieJar(filename='cookies.txt')

    meter_url = "https://mojlicznik.energa-operator.pl"

    def databaseInit(self):
        db.create_tables([ChartTable], safe=True)
        db.create_tables([PPETable], safe=True)
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

        try:
            response = self.session.get(login_url)
            response.raise_for_status() 
            print(f"Logowanie rozpoczęte.")

        except HTTPError as e:
            print(f"Wystąpił błąd HTTP: {e}")

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
            print(f"Wystąpił błąd HTTP: {e}")        

        soup = BeautifulSoup(response.text, 'html.parser')

        login_error_text = 'Użytkownik lub hasło niepoprawne'
        login_error = soup.find('div', text=login_error_text)

        if login_error:
            self.loginStatus = False
            print(login_error_text)
        else:
            self.loginStatus = True
            print(f"Zalogowano")

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
                        print(f"Licznik {id_value} istnieje w systemie.")
                        if not retrieved_record.is_active:
                            retrieved_record.is_active = True
                            retrieved_record.save()                   
                    else:
                        print(f"Licznik {id_value} nie istnieje w systemie.")
                        data = PPETable.create(
                                id=id_value,
                                ppe=ppe_value,
                                tariffCode=tariffCode_value,
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
            print(f"Wylogowano.")
        except HTTPError as e:
            print(f"Wystąpił błąd HTTP: {e}")

    def uppdate_measurments(self):

        query = PPETable.select().where(PPETable.is_active == True)
        result_ppes = query.execute()
        for p in result_ppes:
            meter_url = f"{self.meter_url}/dp/UserData.do?mpc={p.id}&ppe={p.ppe}"
            try:
                response = self.session.get(meter_url)
                response.raise_for_status()  
                soup = BeautifulSoup(response.text, 'html.parser')
                td_elements = soup.find_all('td', class_='last')
                date_divs = soup.find_all("div", style="font-size: 10px")

                for div in date_divs:
                    p.measurement_date = datetime.strptime(div.text.strip(), "%Y-%m-%d %H:%M").date()
                i = 0

                for td in td_elements:
                    text = td.get_text()
                    cleaned_text = re.sub(r'[^\d,]', '', text)
                    cleaned_number_str = cleaned_text.lstrip('0').replace(',', '.')
                    i = i + 1
                    if i == 1:
                        p.zone1 = float(cleaned_number_str)
                        p.number_of_zones = 1
                    elif i == 2:
                        p.zone2 = float(cleaned_number_str)
                        p.number_of_zones = 2
                    elif i == 3:
                        p.zone3 = float(cleaned_number_str)
                        p.number_of_zones = 1
                p.last_update_date = datetime.now()
                p.save()
                print(f"Zapisano stan licznika {p.name} na dzień: {p.measurement_date}")
            except HTTPError as e:
                print(f"Wystąpił błąd HTTP: {e}")

    def update_first_date(self):
        query = PPETable.select().where(PPETable.first_date.is_null(True) & (PPETable.is_active == True))
        result_ppes = query.execute()
        for p in result_ppes:
            print(f"Szukam najstarsze dane historyczne licznika {p.name}") 
            meter_point = p.id
            max_years_back = 5
            start_date = datetime.now()
            last_chart_year = None
            for n in range(max_years_back + 1):
                first_day_of_year = datetime(start_date.year-n, 1, 1)
                data_json = self.download_chart(ChartType.YEAR, first_day_of_year, meter_point)
                if data_json:
                    data = json.loads(data_json)    
                    if data and data.get("mainChart") and len(data["mainChart"]) > 0:                    
                        last_chart_year = first_day_of_year.year
            last_chart_month = None
            max_month = 12
            for n in range(max_month, 0, -1):
                first_day_of_month = datetime(last_chart_year, n, 1)
                data_json = self.download_chart(ChartType.MONTH, first_day_of_month, meter_point)
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
                data_json = self.download_chart(ChartType.DAY, first_day_of_day, meter_point)
                if data_json:
                    data = json.loads(data_json)        
                    if data and data.get("mainChart") and len(data["mainChart"]) > 0:
                        last_chart_day = n
            first_date = datetime(last_chart_year, last_chart_month, last_chart_day).date()
            print(f"Najstarsze dane historyczne dla licznika {p.name}: {first_date}")    
            p.first_date = first_date
            p.save()

    def save_main_charts(self, mp, vals):
        for val in vals:
            #try:
                z = val["zones"]
                # {"tm": "1690412400000", "tarAvg": 0.3899153269199055, "zones": [null, 0.232, null], "est": false, "cplt": true}, 
                if z[0]:
                    # MainChartTable.get_or_create(tm = val["tm"], zone = 1, value = z[0], tarAvg=val["tarAvg"], est=val["est"], cplt=val["cplt"])
                    try:
                        existing_record = MainChartTable.get((MainChartTable.mp == mp) & (MainChartTable.tm == val["tm"]) & (MainChartTable.zone == 1))
                    except MainChartTable.DoesNotExist:
                        # Jeśli rekord nie istnieje, utwórz nowy
                        MainChartTable.create(
                            mp=mp,
                            tm=val["tm"],
                            zone=1,
                            value=z[0],
                            tarAvg=val["tarAvg"],
                            est=val["est"],
                            cplt=val["cplt"]
                        )
                
                if z[1]:
                    try:
                        existing_record = MainChartTable.get((MainChartTable.mp == mp) & (MainChartTable.tm == val["tm"]) & (MainChartTable.zone == 2))
                    except MainChartTable.DoesNotExist:
                        # Jeśli rekord nie istnieje, utwórz nowy
                        MainChartTable.create(
                            mp=mp,
                            tm=val["tm"],
                            zone=2,
                            value=z[1],
                            tarAvg=val["tarAvg"],
                            est=val["est"],
                            cplt=val["cplt"]
                        )                
                
                if z[2]:
                    try:
                        existing_record = MainChartTable.get((MainChartTable.mp == mp) & (MainChartTable.tm == val["tm"]) & (MainChartTable.zone == 1))
                    except MainChartTable.DoesNotExist:
                        # Jeśli rekord nie istnieje, utwórz nowy
                        MainChartTable.create(
                            mp=mp,
                            tm=val["tm"],
                            zone=3,
                            value=z[2],
                            tarAvg=val["tarAvg"],
                            est=val["est"],
                            cplt=val["cplt"]
                        )
                                                        
            #except:
            #    pass

        return None
    
    def download_chart(self, type, date, meter_point, update_mode=False):

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

        chart_url = f"{self.meter_url}/dp/resources/chart?mainChartDate={tsm_date}&type={chart_type}&meterPoint={meter_point}&mo=A%2B"
        try:
            response = self.session.get(chart_url)
            data = json.loads(response.text)
            response.raise_for_status()
            if data["response"]:
                id = data["response"]["meterPoint"]
                mainChartDate = data["response"]["mainChartDate"]
                mainChart = data["response"]["mainChart"]
                if type == ChartType.DAY:
                    self.save_main_charts(meter_point, mainChart)
                
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
                        chart_record = ChartTable.create(id=id, value=json_dump, year=year, month=month, day=day)

                else:
                    try:
                        ChartTable.create(id=id, value=json_dump, year=year, month=month, day=day)
                    except:
                        pass
                return json_dump
            return None 
        except HTTPError as e:
            print(f"Wystąpił błąd HTTP: {e}")

    def download_charts(self, full_mode=False):
        query = PPETable.select().where(PPETable.is_active == True)
        result_ppes = query.execute()
        for p in result_ppes:
            current_date = p.first_date
            if not full_mode:
                current_date = p.measurement_date - timedelta(days=1)
            
            while current_date <= date.today():
                try:
                    record = ChartTable.get(id=p.id, year=current_date.year, month=current_date.month, day=current_date.day)
                    # Jeśli rekord o określonych wartościach klucza głównego istnieje, zostanie pobrany.
                    print(f"Posiadam dane historyczne dla {p.name} na dzień: {current_date}")
                except ChartTable.DoesNotExist:
                    self.download_chart(ChartType.DAY, current_date, p.id) 
                    print(f"Pobieram dane historyczne dla {p.name} na dzień: {current_date}")
                current_date += timedelta(days=1)

    def update_last_days(self):
        today = datetime.today().date()
        query = PPETable.select().where(PPETable.is_active == True)
        result_ppes = query.execute()
        
        for p in result_ppes:
            if not p.last_update_date:
                p.last_update_date = today - timedelta(days=5)
                p.save()
            last_update_date = p.last_update_date - timedelta(days=1)
            while last_update_date <= today:
                print(f"Aktualizacja danych dla {p.name} na dzień: {last_update_date}")
                self.download_chart(ChartType.DAY, last_update_date, p.id, True)
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
                            #print(zone1_data)
                    #else:
                        #print(f"{p.name} ({p.measurement_date}) : {p.zone1}, {p.zone2}, {p.zone3}")

            #else:
                #print(f"{p.name} ({p.measurement_date}) : {p.zone1}, {p.zone2}, {p.zone3}")

    def set_daily_zones(self):
        query = PPETable.select().where(PPETable.is_active == True)
        result_ppes = query.execute()

        for p in result_ppes:
            query = ChartTable.select().where(
                (ChartTable.id == p.id) &
                ((ChartTable.year > p.measurement_date.year) |
                ((ChartTable.year == p.measurement_date.year) &
                (ChartTable.month > p.measurement_date.month)) |
                ((ChartTable.year == p.measurement_date.year) &
                (ChartTable.month == p.measurement_date.month) &
                (ChartTable.day >= p.measurement_date.day))
            ))

            zones_sums = {f"zone{i+1}_daily_chart_sum": 0.0 for i in range(3)}

            for chart_entry in query:
                value_json = json.loads(chart_entry.value)
                main_chart = value_json.get("mainChart", [])

                for entry in main_chart:
                    zones = entry.get("zones", [])

                    for i, value in enumerate(zones):
                        if value is not None:
                            zones_sums[f"zone{i+1}_daily_chart_sum"] += value
            
            for key, value in zones_sums.items():
                setattr(p, key, value)
            
            p.save()


    # def set_daily_zones(self):
    #     query = PPETable.select().where(PPETable.is_active == True)
    #     result_ppes = query.execute()

    #     for p in result_ppes:
    #         query = ChartTable.select().where((ChartTable.id == p.id) & (ChartTable.year >= p.measurement_date.year) & (ChartTable.month >= p.measurement_date.month) & (ChartTable.day >= p.measurement_date.day))
    #         query_count = query.count()
    #         if (query_count > 0):
    #             query_first = query.first()
    #             value_json = json.loads(query_first.value)
    #             main_chart = value_json.get("mainChart", [])

    #             # Inicjalizacja słownika do przechowywania sum dla każdej sekcji zones
    #             zones_sums = {f"zone{i+1}": 0.0 for i in range(len(main_chart[0].get("zones", [])))}

    #             for entry in main_chart:
    #                 zones = entry.get("zones", [])

    #                 for i, value in enumerate(zones):
    #                     if value is not None:
    #                         zones_sums[f"zone{i+1}"] += value
    #             if (zones_sums["zone1"] > 0):
    #                 p.zone1_daily_chart_sum = zones_sums["zone1"]
    #             else:
    #                 p.zone1_daily_chart_sum = None
    #             if (zones_sums["zone2"] > 0):
    #                 p.zone2_daily_chart_sum = zones_sums["zone2"]
    #             else:
    #                 p.zone2_daily_chart_sum = None
    #             if (zones_sums["zone3"]):
    #                 p.zone3_daily_chart_sum = zones_sums["zone3"]
    #             else:
    #                 p.zone3_daily_chart_sum = None
    #             p.save()


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