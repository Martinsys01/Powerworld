from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from typing import Dict, Any, List
from datetime import datetime
from retrying import retry
from influxdb_client.client.query_api import QueryApi  # Nový import

from config.parameter_mappings import (
    PARAMETER_GROUPS,
    PARAMETER_GROUP_CODES,  # přidejte tento import, protože ho používáte v create_points
)


class InfluxDBWriter:
    def __init__(self, url: str, token: str, org: str, bucket: str):
        """
        Inicializace InfluxDB klienta

        Args:
            url: URL adresa InfluxDB serveru
            token: Autentizační token
            org: Název organizace
            bucket: Název bucketu pro ukládání dat
        """
        
        self.client = InfluxDBClient(url=url, token=token, org=org)

        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()  # Nový řádek
        self.bucket = bucket
        self.org = org

    def create_points(self, data: Dict[str, Any], device_id: str) -> List[Point]:
        """
        Vytvoření bodů pro zápis do InfluxDB

        Args:
            data: Slovník dat k zápisu ve formátu {'basic_status': {...}, 'decoded_parameters': {...}}
            device_id: ID zařízení

        Returns:
            List bodů pro zápis do InfluxDB
        """
        points = []
        timestamp = datetime.utcnow()
        
        # Zpracování basic_status
        if 'basic_status' in data:
            for param_name, value in data['basic_status'].items():
                try:
                    point = (
                        Point("heat_pump_basic_status")
                        .tag("device_id", device_id)
                        .tag("parameter", param_name)
                    )
                    
                    if isinstance(value, (int, float)):
                        point.field("value", float(value))
                    else:
                        point.field("value_str", str(value))
                    
                    point.time(timestamp)
                    points.append(point)
                except Exception as e:
                    print(f"Error creating point for basic_status {param_name}: {e}")

        # Zpracování decoded_parameters
        if 'decoded_parameters' in data:
            for param_name, value in data['decoded_parameters'].items():
                try:
                    point = (
                        Point("heat_pump_decoded_parameters")
                        .tag("device_id", device_id)
                        .tag("parameter", param_name)
                    )
                    
                    # Pokud je hodnota string s číslem a jednotkou (např. "70°C")
                    if isinstance(value, str):
                        # Extrahujeme číselnou hodnotu
                        numeric_str = ''.join(filter(lambda x: x.isdigit() or x == '.', value))
                        if numeric_str:
                            try:
                                numeric_value = float(numeric_str)
                                point.field("value", numeric_value)
                            except ValueError:
                                pass
                        point.field("value_str", value)
                    elif isinstance(value, (int, float)):
                        point.field("value", float(value))
                    else:
                        point.field("value_str", str(value))
                    
                    point.time(timestamp)
                    points.append(point)
                except Exception as e:
                    print(f"Error creating point for decoded_parameter {param_name}: {e}")

        return points


    


     
     
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def write_data(self, data: Dict[str, Any], device_id: str):
        """
        Zápis dat do InfluxDB

        Args:
            data: Data k zápisu ve formátu {'basic_status': {...}, 'decoded_parameters': {...}}
            device_id: ID zařízení
        """
        try:
            print(f"\nAttempting to write data for device {device_id}")  # Debug log
            points = self.create_points(data, device_id)
            if points:
                self.write_api.write(bucket=self.bucket, org=self.org, record=points)
                print(f"Successfully wrote {len(points)} points to InfluxDB")  # Debug log
            else:
                print("No points created from data")  # Debug log
        except Exception as e:
            print(f"Error writing to InfluxDB: {e}")
            raise

    def check_data(self):
        """
        Kontrolní funkce pro zobrazení posledních dat uložených v InfluxDB
        """
        print("\nChecking recent data in InfluxDB...")
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -1h)
            |> filter(fn: (r) => r["_measurement"] == "heat_pump_basic_status" or r["_measurement"] == "heat_pump_decoded_parameters")
        '''
        
        try:
            result = self.query_api.query(query=query, org=self.org)
            
            if not result:
                print("No data found in the last hour")
                return

            data_count = 0
            for table in result:
                for record in table.records:
                    data_count += 1
                    print("\nRecord:")
                    print(f"Measurement: {record.get_measurement()}")
                    print(f"Field: {record.get_field()}")
                    print(f"Value: {record.get_value()}")
                    print(f"Time: {record.get_time()}")
                    print(f"Tags: {record.values}")
                    print("---")
                    
                    # Omezení výpisu na prvních 10 záznamů
                    if data_count >= 10:
                        print("\nShowing only first 10 records...")
                        return
                        
        except Exception as e:
            print(f"Error checking data: {e}")
    
    
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validace vstupních dat

        Args:
            data: Data k validaci ve formátu slovníku s parametry zařízení

        Returns:
            bool: True pokud jsou data validní
        """
        try:
            # Kontrola, zda je vstup slovník
            if not isinstance(data, dict):
                print(f"Invalid data format: expected dict, got {type(data)}")
                return False

            # Kontrola základní struktury dat
            required_keys = {'basic_status', 'parameters', 'decoded_parameters'}
            if not any(key in data for key in required_keys):
                print(f"Missing required keys. Expected at least one of {required_keys}")
                return False

            # Kontrola parametrů, pokud existují
            if 'parameters' in data:
                for param_name, param_value in data['parameters'].items():
                    # Zde můžete přidat specifickou validaci parametrů podle potřeby
                    if param_value is None:
                        print(f"Parameter {param_name} has None value")
                        continue

            # Kontrola basic_status, pokud existuje
            if 'basic_status' in data:
                if not isinstance(data['basic_status'], dict):
                    print("Invalid basic_status format")
                    return False

            # Kontrola decoded_parameters, pokud existují
            if 'decoded_parameters' in data:
                if not isinstance(data['decoded_parameters'], dict):
                    print("Invalid decoded_parameters format")
                    return False

            return True

        except Exception as e:
            print(f"Error during data validation: {e}")
            return False

    def close(self):
        """Uzavření spojení s InfluxDB"""
        self.client.close()
