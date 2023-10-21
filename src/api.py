from peewee import SqliteDatabase
from flask import Flask, jsonify, request, redirect, url_for
from waitress import serve
import time
from datetime import datetime
from moj_licznik import PPETable, MainChartTable

DEBUG = False

app = Flask(__name__)

db = SqliteDatabase('database.sqlite')

@app.route('/', methods=['GET'])
def root_redirect():
    query = PPETable.select().where(PPETable.is_active == True)
    result_ppes = list(query)
    meters = []

    for p in result_ppes:
        meter = {
            'name': p.name,
            'id': p.id
        }

        meters.append(meter)
    if DEBUG:
        print("API: GET /")
    
    return jsonify({'meters': meters})

@app.route('/meters', methods=['GET'])
def meters():
    query = PPETable.select().where(PPETable.is_active == True)
    result_ppes = list(query)
    meters = []

    for p in result_ppes:
        meter = {
            'name': p.name,
            'id': p.id,
            'ppe': p.ppe,
            'number_of_zones': p.number_of_zones,
            'tariffCode': p.tariffCode,
            'first_date': p.first_date,
            'last_update_date': p.last_update_date,
            'measurement_date': p.measurement_date,
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
    if DEBUG:
        print("API: GET /")
    
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


# @app.route('/meters/<int:meter_id>', methods=['GET'])
# def get_meter(meter_id):
#     query = PPETable.select().where((PPETable.is_active == True) & (PPETable.id == meter_id))
#     result_ppes = list(query)

#     if result_ppes:
#         p = result_ppes[0]  # There should be only one matching record

#         meter = {
#             'name': p.name,
#             'id': p.id,
#             'ppe': p.ppe,
#             'number_of_zones': p.number_of_zones,
#             'tariffCode': p.tariffCode,
#             'first_date': p.first_date,
#             'last_update_date': p.last_update_date,
#             'measurement_date': p.measurement_date
#         }

#         for i in range(1, p.number_of_zones + 1):
#             zone_key = f'zone{i}'
#             daily_chart_key = f'zone{i}_daily_chart_sum'

#             meter[zone_key] = getattr(p, zone_key)
#             meter[daily_chart_key] = getattr(p, daily_chart_key)

#         print(f"API: GET /meters/{meter_id}")
#         return jsonify({'meter': meter})
#     else:
#         return jsonify({'error': 'Meter not found'}, 404)

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

    if DEBUG:
        print(f"API: GET / - {start_date} - {end_date}")

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

    if DEBUG:
        print(f"API: GET / - {start_date} - {end_date}")

    return jsonify({'charts': charts})

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8000, threads=8)    