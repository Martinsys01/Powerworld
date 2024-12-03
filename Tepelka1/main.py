from config.tuya_config import TuyaConfig
from config.pump_config import HeatPumpParameters
from services.tuya_connection import TuyaConnection
from services.pump_control import PumpControl
from main_v2 import process_pump_data
import time
DEBUG_MODE = True  # nebo načíst z konfigurace


def create_tuya_connection(config):
    return TuyaConnection(
        api_key=config.API_KEY,
        api_secret=config.API_SECRET,
        api_region=config.API_REGION
    )

def main():
    try:
        # Načtení konfigurace
        print("Načítám Tuya konfiguraci...")
        TuyaConfig.load_config()
        print("Načítám konfiguraci čerpadel...")
        HeatPumpParameters.load_config()
        
        if DEBUG_MODE:
            print("\nKontrolní výpis konfigurace:")
            print(f"API Key: {TuyaConfig.API_KEY}")
            print(f"API Secret: {TuyaConfig.API_SECRET}")
            print(f"API Region: {TuyaConfig.API_REGION}")
            print(f"Pump1 ID: {HeatPumpParameters.DEVICE_ID_PUMP1}")
            print(f"Pump2 ID: {HeatPumpParameters.DEVICE_ID_PUMP2}")
            print("Načtené parametry čerpadel:")
            print(f"Pump1 ID: {HeatPumpParameters.DEVICE_ID_PUMP1}")
            print(f"Pump1 Name: {HeatPumpParameters.PUMP1_NAME}")
            print(f"Pump2 ID: {HeatPumpParameters.DEVICE_ID_PUMP2}")
            print(f"Pump2 Name: {HeatPumpParameters.PUMP2_NAME}")

        # Inicializace připojení k Tuya
        tuya_connection = create_tuya_connection(TuyaConfig)
        
        # Kontrola připojení
        if not tuya_connection.connect():
            raise Exception("Nepodařilo se připojit k Tuya API")

        # Vytvoření ovladačů pro čerpadla
        pump1 = PumpControl(tuya_connection, HeatPumpParameters.create_pump1(), debug=DEBUG_MODE)
        pump2 = PumpControl(tuya_connection, HeatPumpParameters.create_pump2(), debug=DEBUG_MODE)

        while True:
            try:
                # Získání statusu čerpadel
                status1 = pump1.get_status()
                status2 = pump2.get_status()

                print("\nStatus čerpadla 1:")
                print(status1)
                print("\nStatus čerpadla 2:")
                print(status2)
                
                # Zpracování a zápis dat do InfluxDB
                if status1:
                    process_pump_data(status1, HeatPumpParameters.DEVICE_ID_PUMP1)
                if status2:
                    process_pump_data(status2, HeatPumpParameters.DEVICE_ID_PUMP2)

                time.sleep(60)  # Čekání 60 sekund před dalším dotazem

            except Exception as e:
                print(f"Chyba v hlavní smyčce: {str(e)}")
                time.sleep(10)  # Při chybě čekáme kratší dobu

    except Exception as e:
        print(f"Kritická chyba: {str(e)}")

if __name__ == "__main__":
    main()