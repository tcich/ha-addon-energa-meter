import configparser, time, datetime, os
from moj_licznik import MojLicznik
from pathlib import Path

def main():
    username = None
    password = None
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")

    print(f"Inicjacja...")
    mojLicznik = MojLicznik()
    print(f"Logowanie...", username)
    mojLicznik.login(username, password)
    print(f"Aktualizacja liczników...")
    mojLicznik.uppdate_measurments()
    print(f"Wyszukiwanie najstarszych danych...")
    mojLicznik.update_first_date()
    print(f"Pobieranie danych...")
    mojLicznik.download_charts(True)
    mojLicznik.update_last_days()
    mojLicznik.set_daily_zones()
    mojLicznik.logout()

if __name__ == "__main__":
    main()