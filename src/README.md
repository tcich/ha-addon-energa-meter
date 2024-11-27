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



[kawa-logo]: https://github.com/tcich/ha-addon-energa-meter/blob/main/img/buycoffeeto-btn-primary-outline.png
[kawa]: https://buycoffee.to/tcich

## O dodatku

To jest dodatek dla [Home Assistant](https://www.home-assistant.io/). Instalacja dodatku [Energa meter](https://github.com/tcich/ha-addon-energa-meter) umożliwia cykliczne pobieranie danych z aplikacji [Mój Licznik - Energa](https://mojlicznik.energa-operator.pl) udostępnianej klientom Operatora energetycznego Energa.

## Instalacja
1) Dodaj repozytorium do repozytoriów dodatków swojego HA za pomocą poniższego przycisku

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Ftcich%2Fha-addon-energa-meter)

Lub zainstaluj manualnie z Ustawienia -> Dodatki -> Sklep z dodatkami -> ⁞ (Menu) -> Repozytoria -> Wpisz `https://github.com/tcich/hassio-mojlicznik` -> Dodaj. Następnie w ⁞ (Menu) -> Sprawdź aktualizacje (może być konieczne przeładowanie strony)

2) Odszukaj dodatek na liście dodatków w sklepie z dodatkami i zainstaluj go.

3) W zakładce konfiguracja uzupełnij nazwę użytkownika oraz hasło do aplikacji Mój Licznik, jeżeli potrzebujesz to zmień udostępniany port dla API

4) Przejdź do zakładki informacje i uruchom dodatek (pierwsze uruchomienie może trwać kilkanaście minut), jeżeli w logu pojawi się informacja *INFO: Czekam...* oznacza to, że pierwsze inicjalne pobieranie danych zostało ukończone.


## Wersja Docker
Aby ruchomić wersję docker należy skorzystać z polecenia poniżej

```
docker run -p 8000:8000 -e ENERGA_USERNAME=LoginEnerga  -e ENERGA_PASSWORD=HasloEnerga tomcic/energa-meter:v1.0.0
```

Wymagane parametry:

* ENERGA_USERNAME - nazwa użytkownika w aplikacji Energa Mój licznik
* ENERGA_PASSWORD - hasło użytkownika w aplikacji Energa Mój licznik

Opcjonalne parametry:

* POSTGRESQL_CONNSTRING - namiar na bazę PostgreSQL do przechowywania odczytów;
format opisany w [dokumentacji PGSQL](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING-URIS)
(przykładowo `postgresql://uzytkownik:haslo@serwer/mojlicznik`)

## Konfiguracja sensorów
Do HA możesz dodać sensory, które zawierają informacje udostępniane przez API

Poniższa instrukcja zawiera założenia:
* dodatek jest dostępny pod adresem *localhost* na porcie *8000*
* ID Twojego licznika to *123456789*

1) Ustal ID Twoich liczników, w tym celu przejdź do adresu Twojego HA na porcie 8000 lub innym jeźeli zmieniłeś go w konfiguracji, np. http://192.168.1.10:8000 wyświetli się w formacie json lista dostępnych liczników.
2) W pliku configuration.yaml w HA dodaj następującą konfigurację np.:

```
sensor:
  - platform: rest
    resource: http://localhost:8000/123456789/A%2B/1
    name: "A+ Taryfa 1"
    unique_id: 123456789_apt1
    unit_of_measurement: "kWh"
    value_template: "{{ value_json.countner.meter_value | round(2) }}"
  - platform: rest
    resource: http://localhost:8000/123456789/A-/1
    name: "A- Taryfa 1"
    unique_id: 123456789_aot1
    unit_of_measurement: "kWh"
    value_template: "{{ value_json.countner.meter_value | round(2) }}"       
  - platform: rest
    resource: http://localhost:8000/123456789/A%2B/2
    name: "A+ Taryfa 2"
    unique_id: 123456789_apt2
    unit_of_measurement: "kWh"
    value_template: "{{ value_json.countner.meter_value | round(2) }}"       
```    
## Suma liczników, bilans
W celu uzyskania sumy liczników, bilansu, itp należy użyć templates:
```
template:
  - sensor:
      - name: "Suma liczników"
        unit_of_measurement: "kWh"
        state: "{{ states('sensor.123456789_apt1') | float + states('sensor.123456789_apt2') | float | round(2) }}"
  - sensor:
      - name: "Bilans/różnica liczników"
        unit_of_measurement: "kWh"
        state: "{{ states('sensor.123456789_apt1') | float - states('sensor.123456789_apt2') | float | round(2) }}"        
```


### Opis konfiguracji
| element konfiguracji | Opis |
|-------------------|-------------------|
| resource: http://localhost:8000/123456789/A%2B/1     | Adres API z danymi konkretnego licznika, podajemy **localhost** lub nazwę instancji dockera (**Nazwa hosta** z okna dodatku), port, id licznika, rodzaj pomiaru, taryfa|
| name: "A+ Taryfa 1"    | Nazwa sensora, wpisz dowolną|
| unique_id   | Unikalny ID sensora, nie mogą być w systemie dwa sensory z tym samym ID|
| unit_of_measurement: "kWh"   | Jednostka miary, nie zmieniaj chyba, że wiesz co robisz|
| value_template: "{{ value_json.countner.meter_value \| round(2) }}"   | Zaokrąglony do dwóch miejsc po przecinku stan sensora|

## API dla wykresów, np. Grafana
Aby pobrać dane z API w formacie JSON należy użyć adresu http://home_assistant:8000/charts/12729?start_date=1695332400129&end_date=1697924583285&mp=123456789&zone=1

### Opis konfiguracji
| element konfiguracji | Opis |
|-------------------|-------------------|
| resource: http://localhost:8000/charts     | Adres API z danymi do wykresów, podajemy **localhost** lub nazwę instancji dockera (**Nazwa hosta** z okna dodatku), port, id licznika, rodzaj pomiaru, taryfa|
| start_date | data początkowa danych w formacie epoch (ms), domyślnie czas bieżący |
| end_date | data końcowa danych w formacie epoch (ms), domyślnie czas bieżący - 1 dzień |
| mp | numer licznika |
| meter_type_url | typ licznika (np. A+: A%2B, A-: A- ) |
| zone | numer strefy (np. 1, 2) |


## Grafana
Instrukcja konfiguracji dla Grafana znajduje się tutaj [link](https://github.com/tcich/ha-addon-energa-meter/blob/main/src/INSTALL.md)


## Znane problemy
Czasami w aplikacji Mój Licznik włącza się captha (jeżeli masz dużo danych historycznych lub wielokrotnie instalujesz dodatek)

## Uwagi
Dostęp do aktualnej wersji API nie jest zabezpieczony tokenem
Każde przeinstalowanie dodatku pobiera ponownie dane z aplikacji Mój Licznik
