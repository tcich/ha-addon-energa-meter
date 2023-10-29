from peewee import SqliteDatabase
from flask import Flask, jsonify, request, redirect, url_for
from waitress import serve
import time, os, logging
from moj_licznik import PPETable, MeterTable, CounterTable, MainChartTable

logger = logging.getLogger("energaMeter.api")


path = os.path.dirname(os.path.abspath(__file__))
db_file = 'database.sqlite'
db = SqliteDatabase(os.path.join(path, db_file))

app = Flask(__name__)

@app.route('/', methods=['GET'])
def root_redirect():
    query = PPETable.select() #.where(PPETable.is_active == True)
    result_ppes = list(query)
    ppes = []
    for p in result_ppes:
        meters_query = MeterTable.select().where(MeterTable.ppe_id == p.id)
        meter_result = meters_query.execute()
        meters = []
        for meter in meter_result:
            countners_query = CounterTable.select().where(CounterTable.meter_id == meter.id)
            countners_result = countners_query.execute()
            countners = []
            for countner in countners_result:
                countner = {
                    'tariff': countner.tariff,
                    'measurement_date': countner.measurement_date,
                    'meter_value': countner.meter_value
                }
                countners.append(countner)

            meter = {
                'meter_type': meter.meter_type,
                'last_update_date': meter.last_update_date,
                'first_date': meter.first_date,
                'countners': countners
            }
            meters.append(meter)

        ppe = {
            'name': p.name,
            'id': p.id,
            'type': p.type,
            'isActive': p.is_active,
            'meters': meters
        }
        ppes.append(ppe)
    logger.debug("API: GET /")
    
    return jsonify({'ppes': ppes})

@app.route('/meters', methods=['GET'])
def meters():
    query = PPETable.select() #.where(PPETable.is_active == True)
    result_ppes = list(query)
    meters = []

    for p in result_ppes:
        meter = {
            'name': p.name,
            'id': p.id,
            'ppe': p.ppe,
            'number_of_zones': '',#p.number_of_zones,
            'tariffCode': p.tariffCode,
            # 'first_date': p.first_date,
            'last_update_date': p.last_update_date,
            # 'measurement_date': p.measurement_date,
        }

        for i in range(1, p.number_of_zones + 1):
            zone_key = f'zone{i}'
            daily_chart_key = f'zone{i}_daily_chart_sum'

            zone_value = getattr(p, zone_key)
            daily_chart_value = getattr(p, daily_chart_key)

            # Zamień None na zero podczas obliczania sumy
            zone_value = float(zone_value) if zone_value is not None else 0
            daily_chart_value = float(daily_chart_value) if daily_chart_value is not None else 0

            meter[zone_key] = {
                'meter': zone_value,
                'daily_chart': daily_chart_value,
                'sum': zone_value + daily_chart_value
            }

        meters.append(meter)
    logger.debug("GET /meters")
    
    return jsonify({'meters': meters})

@app.route('/meters/<int:meter_id>', methods=['GET'])
def get_meter(meter_id):
    query = PPETable.select().where((PPETable.is_active == True) & (PPETable.id == meter_id))
    result_ppes = list(query)

    if result_ppes:
        p = result_ppes[0]  # There should be only one matching record

        meter = {
            'name': p.name,
            'id': p.id,
            'ppe': p.ppe,
            'number_of_zones': p.number_of_zones,
            'tariffCode': p.tariffCode,
            'first_date': p.first_date,
            'last_update_date': p.last_update_date,
            'measurement_date': p.measurement_date
        }

        for i in range(1, p.number_of_zones + 1):
            zone_key = f'zone{i}'
            daily_chart_key = f'zone{i}_daily_chart_sum'

            zone_value = getattr(p, zone_key)
            daily_chart_value = getattr(p, daily_chart_key)

            # Zamień None na zero podczas obliczania sumy
            zone_value = float(zone_value) if zone_value is not None else 0
            daily_chart_value = float(daily_chart_value) if daily_chart_value is not None else 0

            meter[zone_key] = {
                'meter': zone_value,
                'daily_chart': daily_chart_value,
                'sum': zone_value + daily_chart_value
            }

        print(f"API: GET /meters/{meter_id}")
        return jsonify({'meter': meter})
    else:
        return jsonify({'error': 'Meter not found'}, 404)

@app.route('/<int:ppe_id>', methods=['GET'])
def get_ppe(ppe_id):
    query = PPETable.select().where((PPETable.is_active == True) & (PPETable.id == ppe_id))
    result_ppes = list(query)

    if result_ppes:
        p = result_ppes[0]  # There should be only one matching record

        meter = {
            'name': p.name,
            'id': p.id,
            'ppe': p.ppe,
            'tariffCode': p.tariffCode,
            'last_update_date': p.last_update_date,
            'is_active': p.is_active
        }

        logger.debug(f"API: GET /meters/{ppe_id}")
        return jsonify({'meter': meter})
    else:
        return jsonify({'error': 'Meter not found'}, 404)


@app.route('/charts/<mp>', methods=['GET'])
def charts(mp):
    start_time = time.time()
    current_time = time.localtime()
    start_date = request.args.get('start_date', (time.mktime(current_time) - 864000))
    end_date = request.args.get('end_date', (time.mktime(current_time)))
    query = MainChartTable.select().where((MainChartTable.mp == mp) & (MainChartTable.tm >= start_date) & (MainChartTable.tm <= end_date))
    result_ppes = list(query)
    charts = []

    for p in result_ppes:
        czas = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.tm/1000))

        chart = {
            'mp': p.mp,
            'zone': p.zone,
            'tm': p.tm,
            'czas': czas,
            'value': p.value
        }
        charts.append(chart)
    end_time = time.time()
    logger.debug(f"API: GET / - {start_date} - {end_date}")

    return jsonify({'charts': charts})

@app.route('/<mp>/<zone>', methods=['GET'])
def charts_zone(mp, zone):
    start_time = time.time()
    current_time = time.localtime()
    start_date = request.args.get('start_date', (time.mktime(current_time) - 864000))
    end_date = request.args.get('end_date', (time.mktime(current_time)))
    query = MainChartTable.select().where((MainChartTable.mp == mp) & (MainChartTable.tm >= start_date) & (MainChartTable.tm <= end_date) & (MainChartTable.zone == zone))
    result_ppes = list(query)
    charts = []

    for p in result_ppes:
        czas = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.tm/1000))

        chart = {
            'mp': p.mp,
            'zone': p.zone,
            'tm': p.tm,
            'czas': czas,
            'value': p.value
        }
        charts.append(chart)
    end_time = time.time()

    logger.debug(f"API: GET / - {start_date} - {end_date}")

    return jsonify({'charts': charts})

