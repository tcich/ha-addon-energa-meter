[![ha_badge](https://img.shields.io/badge/Home%20Assistant-Add%20On-blue.svg)](https://www.home-assistant.io/)
# [Energa meter](https://github.com/tcich/ha-addon-energa-meter) Home Assistant add-on

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armv6-shield]: https://img.shields.io/badge/armv6-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
![aarch64-shield]
![amd64-shield]
![armv6-shield]
![armv7-shield]
![i386-shield]


[![Postaw kawę][kawa-logo]][kawa]

[kawa-logo]: https://github.com/tcich/ha-addon-energa-meter/blob/main/img/buycoffeeto-btn-primary-outline.png
[kawa]: https://buycoffee.to/tcich



## O dodatku

To jest dodatek dla [Home Assistant](https://www.home-assistant.io/). Instalacja dodatku [Energa meter](https://github.com/tcich/ha-addon-energa-meter) umożliwia cykliczne pobieranie danych z aplikacji [Mój Licznik - Energa](https://mojlicznik.energa-operator.pl) udostępnianej klientom Operatora energetycznego Energa

## Instalacja
1) Dodaj repozytorium do repozytoriów dodatków swojego HA za pomocą poniższego przycisku

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Ftcich%2Fha-addon-energa-meter)

Lub zainstaluj manualnie z Ustawienia -> Dodatki -> Sklep z dodatkami -> ⁞ (Menu) -> Repozytoria -> Wpisz `https://github.com/tcich/hassio-mojlicznik` -> Dodaj. Następnie w ⁞ (Menu) -> Sprawdź aktualizacje (może być konieczne przeładowanie strony)

2) Odszukaj dodatek na liście dodatków w sklepie z dodatkami i zainstaluj go.

3) W zakładce konfiguracja uzupełnij nazwę użytkownika oraz hasło do aplikacji Mój Licznik, jeżeli potrzebujesz to zmień udostępniany port dla API

4) Przejdź do zakładki informacje i uruchom dodatek (pierwsze uruchomienie może trwać kilkanaście minut), jeżeli w logu pojawi się informacja *INFO: Czekam...* oznacza to, że pierwsze inicjalne pobieranie danych zostało ukończone.


## Wersja Docker
```
docker run -p 8000:8000 -e ENERGA_USERNAME=LoginEnerga  -e ENERGA_PASSWORD=HasloEnerga tomcic/energa-meter:v0.1.0
```

## Konfiguracja sensorów
1) Ustal ID Twoich liczników, w tym celu przejdź do adresu Twojego HA na porcie 8000 lub innym jeźeli zmieniłeś go w konfiguracji, np. http://192.168.1.10:8000 wyświetli się w formacie json lista dostępnych liczników, możesz również odszukać ID w logu: *Licznik 12335379 istnieje w systemie*
2) W pliku configuration.yaml w HA dodaj następującą konfigurację np.:

```
sensor:
  - platform: rest
    resource: http://localhost:8000/meters/12335379
    name: "Energia aktualna T1"
    unique_id: 12335379_sumz1
    unit_of_measurement: "kWh"
    value_template: "{{ value_json.meter.zone1.meter | round(2) }}"   
  - platform: rest
    resource: http://localhost:8000/meters/12335379
    name: "Dzienny odczyt licznika"
    unique_id: 12335379_meterz1
    unit_of_measurement: "kWh"
    value_template: "{{ value_json.meter.zone1.sum | round(2) }}"
  - platform: rest
    resource: http://localhost:8000/meters/12335379
    name: "Energia aktualna T2"
    unique_id: 12335379_sumz2
    unit_of_measurement: "kWh"
    value_template: "{{ value_json.meter.zone2.meter | round(2) }}"   
  - platform: rest
    resource: http://localhost:8000/meters/12335379
    name: "Dzienny odczyt licznika"
    unique_id: 12335379_meterz2
    unit_of_measurement: "kWh"
    value_template: "{{ value_json.meter.zone2.sum | round(2) }}" 
```    

# Opis konfiguracji
| element konfiguracji | Opis |
|-------------------|-------------------|
| resource: http://localhost:8000/meters/12335379     | Adres API z danymi konkretnego licznika, podajemy nazwę instancji dockera (**Nazwa hosta** z okna dodatku) lub localhost|
| name: "Energia aktualna"    | Nazwa sensora, wpisz dowolną|
| unique_id   | Unikalny ID sensora, nie mogą być w systemie dwa sensory z tym samym ID|
| unit_of_measurement: "kWh"   | Jednostka miary, nie zmieniaj chyba, że wiesz co robisz|
| value_template: "{{ value_json.meter.zone2.meter \| round(2) }}"   | Zaokrąglony do dwóch miejsc po przecinku stan sensora|

# Opis konfiguracji cd
| value_template | Opis |
|-------------------|-------------------|
| value_json.meter.zone1.sum     | Suma licznika oraz dziennego zużycia dla tartfy1 (dostępne są: zone1, zone2, zone3)|
| value_json.meter.zone2.meter     | Stan licznika dziennego dla taryfy1 (dostępne są: zone1, zone2, zone3)|


## API dla wykresów, np. Grafana
Aby pobrać dane z API w formacie JSON należy użyć adresu http://home_assistant:8000/charts/12729?start_date=1695332400129&end_date=1697924583285

gdzie: 
* 12729 - jest to ID licznika
* start_date - początek okresu w milisekundach wg. standardu EPOCH (timestamp)
* end_date - koniec okresu w milisekundach wg. standardu EPOCH (timestamp)

## Jak dodać wykres do Grafana
### Źródło danych
1) Dodajemy źródło danych Home -> Data sources - Add new datasources: Wyszukujemy JSON API (jeżeli nie ma to musimy dodać)
2) NAME: ENERGA (1)
3) URL: http://twoj_addon:8000 (2)
4) Klikamy Save&test (3)
5) Uwaga: Jeżeli Grafana jest addonem w HA użyj właściwej nazwy hosta dostępnej w docker.

![Addon](https://github.com/tcich/ha-addon-energa-meter/blob/main/img/addon.png "Nazwa hosta")

![Żródło danych](https://github.com/tcich/ha-addon-energa-meter/blob/main/img/grafana_01.png "Grafana źródło danych")

### Dashboard
1) Przechodzimy do Dashboards
2) Klikamy New -> New dashboard -> Add visualization
3) Wskazujemy Data source: ENERGA
4) W **Path** wpisujemy: GET: /charts/12335379 (id Twojego licznika)
5) W **Fields** wpisujemy \$.charts\[\*\].czas typu Time oraz $.charts[*].value typu number z aliasem kWh
5) W **Params** wpisujemy Key: start_date Value: $__from
6) W **Params** wpisujemy Key: end_date Value: $__to

![Grafana path](https://github.com/tcich/ha-addon-energa-meter/blob/main/img/grafana_06.png "Grafana")

![Grafana path](https://github.com/tcich/ha-addon-energa-meter/blob/main/img/grafana_02.png "Grafana")

![Grafana Params](https://github.com/tcich/ha-addon-energa-meter/blob/main/img/grafana_03.png "Grafana")

![Grafana Params](https://github.com/tcich/ha-addon-energa-meter/blob/main/img/grafana_04.png "Grafana")

![Grafana Params](https://github.com/tcich/ha-addon-energa-meter/blob/main/img/grafana_05.png "Grafana")


## Znane problemy
Czasami w aplikacji Mój Licznik włącza się captha (jeżeli masz dużo danych historycznych lub wielokrotnie instalujesz dodatek)
Dane wytwórcy (energia oddana oraz bilans) nie są dostępne, prace w tym zakresie trwają.

## Uwagi
Dostęp do aktualnej wersji API nie jest zabezpieczony tokenem
Każde przeinstalowanie dodatku pobiera ponownie dane z aplikacji Mój Licznik

[![Postaw kawę][kawa-logo]][kawa]

