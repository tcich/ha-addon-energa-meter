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


<a href="https://buycoffee.to/tcich"><img src="img/logo-buycoffee-wide.jpg" width=200 alt="Postaw kawę"></a>


## O dodatku

To jest dodatek dla [Home Assistant](https://www.home-assistant.io/). Instalacja dodatku [Energa meter](https://github.com/tcich/ha-addon-energa-meter) umożliwia cykliczne pobieranie danych z aplikacji [Mój Licznik - Energa](https://mojlicznik.energa-operator.pl) udostępnianej klientom Operatora energetycznego Energa.
* Udostępnia dane o aktualnym stanie licznika dla sensorów
* Udostępnia dane historyczne dla wykresów

### Wersja podstawowa
Jest to głowna wersja. Więcej informacji [tutaj](src/README.md)

### Wersja dev
Wersja dev jest wersją developeską, nie należy jej używać w produkcyjnej wersji HA, może powodować różne problemy, może nie działać. Więcej informacji [tutaj](src.dev/README.md)

## Wersja Docker
Aby ruchomić wersję docker należy skorzystać z polecenia poniżej

```
docker run -p 8000:8000 -e ENERGA_USERNAME=LoginEnerga  -e ENERGA_PASSWORD=HasloEnerga tomcic/energa-meter:v0.1.0
```

Wymagane parametry:

* ENERGA_USERNAME - nazwa użytkownika w aplikacji Energa Mój licznik
* ENERGA_PASSWORD - hasło użytkownika w aplikacji Energa Mój licznik

## Znane problemy
* Czasami w aplikacji Mój Licznik włącza się captha (jeżeli masz dużo danych historycznych lub wielokrotnie instalujesz dodatek)
* Dane wytwórcy (energia oddana oraz bilans) nie są dostępne, prace w tym zakresie trwają.

## Uwagi
Dostęp do aktualnej wersji API nie jest zabezpieczony tokenem
Każde przeinstalowanie dodatku pobiera ponownie dane z aplikacji Mój Licznik

## Uwagi
Błędy można zgłaszać przez https://github.com/tcich/ha-addon-energa-meter/issues 

<a href="https://buycoffee.to/tcich"><img src="img/logo-buycoffee-wide.jpg" width=200 alt="Postaw kawę"></a>

