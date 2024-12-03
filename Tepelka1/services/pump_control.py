from typing import List
import base64
import struct
import traceback

from config.parameter_mappings import (
    PARAMETER_GROUPS,
    convert_to_signed,
    PARAMETER_GROUP_CODES,
    STATUS_GROUPS,
    STATUS_GROUPS_CODES,
)


class PumpControl:
    def __init__(self, connection, parameters, debug=False):
        """
        Inicializace kontroleru tepelného čerpadla
        
        Args:
            connection: Objekt pro komunikaci se zařízením
            parameters: Parametry zařízení
            debug (bool): Zapnutí debugovacího módu
        """
        self.connection = connection
        self.parameters = parameters
        self.debug = debug
        #print(f"Debug mode is: {self.debug}")  # Přidejte tento řádek pro kontrolu

    def decode_parameter_groups(self, data: dict, groups_mapping: dict) -> dict:
        """Dekóduje skupiny parametrů podle zadaného mapování, včetně STATUS_GROUPS."""
        if self.debug:
            print(f"Vstupní data před base64 dekódováním: {data}")

        # Dekódování base64 pro každou skupinu
        decoded_data = {}
        for group_key, encoded_values in data.items():
            if not (group_key.startswith('parameter_group_') or group_key.startswith('status_parameter_group_')):
                continue

            try:
                # Zjistíme číslo skupiny
                group_number = int(group_key.replace('parameter_group_', '').replace('status_parameter_group_', ''))
                
                # Převod z base64 na seznam čísel
                decoded_values = self.decode_base64_values(encoded_values)
                
                # Konverze na signed hodnoty
                decoded_values = [convert_to_signed(value) for value in decoded_values]
                decoded_data[group_number] = decoded_values

                if self.debug:
                    print(f"\nDekódovaná skupina {group_number}: {decoded_values}")
            except Exception as e:
                if self.debug:
                    print(f"Chyba při dekódování base64 pro skupinu {group_key}: {str(e)}")
                continue

        if self.debug:
            print(f"\nData po base64 dekódování: {decoded_data}")
            print(f"Použité mapování: {groups_mapping}")

        # Dekódování hodnot podle mapování
        decoded_params = {}
        for group_number, values in decoded_data.items():
            if self.debug:
                print(f"\nZpracovávám skupinu {group_number}")
                print(f"Hodnoty: {values}")

            # Rozhodneme, které mapování použít (PARAMETER_GROUPS nebo STATUS_GROUPS)
                group_mapping = groups_mapping.get(group_number) or STATUS_GROUPS.get(group_number)
            
            if not group_mapping:
                if self.debug:
                    print(f"Nenalezeno mapování pro skupinu {group_number}")
                continue

            try:
                for param_index, value in enumerate(values):
                    if param_index not in group_mapping:
                        if self.debug:
                            print(f"Nenalezen parametr {param_index} ve skupině {group_number}")
                        continue

                    param_name, formatter = group_mapping[param_index]
                    decoded_params[param_name] = formatter(value)

                    if self.debug:
                        print(f"Dekódován parametr: {param_name} = {decoded_params[param_name]}")

            except Exception as e:
                if self.debug:
                    print(f"Chyba při dekódování skupiny {group_number}: {str(e)}")
                    traceback.print_exc()
                continue

        if self.debug:
            print(f"\nVýsledek dekódování: {decoded_params}")

        return decoded_params

    def decode_base64_values(self, encoded_string: str) -> List[int]:
        """Dekóduje base64 řetězec na seznam čísel."""
        try:
            # Dekódování base64
            decoded_bytes = base64.b64decode(encoded_string)
            # Převod na seznam čísel
            return [int.from_bytes(decoded_bytes[i:i+4], byteorder='big') 
                    for i in range(0, len(decoded_bytes), 4)]
        except Exception as e:
            if self.debug:
                print(f"Chyba při dekódování base64: {str(e)}")
            return []

    def get_status(self):
        """
        Získá aktuální stav zařízení
        
        Returns:
            dict: Stav zařízení včetně základních a dekódovaných parametrů
        """
        
        try:
            response = self.connection.get_device_status(self.parameters.device_id)

            if not response or "result" not in response:
                if self.debug:
                    print("Neplatná odpověď ze zařízení")
                return None

            status_data = {
                "device_name": self.parameters.name,
                "raw_status": response,
                "parameters": {},
                "basic_status": {},  # Zde budou základní parametry
                "decoded_parameters": {},
            }

            # Zpracování výsledků
            for item in response.get("result", []):
                if "code" in item and "value" in item:
                    code = item["code"]
                    value = item["value"]
                    
                    # Uložení do parameters
                    status_data["parameters"][code] = value
                    
                    # Zpracování základních parametrů
                    if code == "switch":
                        status_data["basic_status"]["power"] = "ON" if value else "OFF"
                    elif code == "mode":
                        status_data["basic_status"]["mode"] = value
                    elif code == "work_mode":
                        status_data["basic_status"]["work_mode"] = value
                    elif code == "temp_unit_convert":
                        status_data["basic_status"]["temp_unit"] = value.upper()
                    elif code == "fault":
                        status_data["basic_status"]["fault"] = value
                    elif code == "hot_water_set":
                        status_data["basic_status"]["hot_water_temp"] = value
                    elif code == "heating_setting":
                        status_data["basic_status"]["heating_temp"] = value
                    elif code == "cooling_setting":
                        status_data["basic_status"]["cooling_temp"] = value

            # Dekódování parametrů s použitím PARAMETER_GROUPS (ponecháno beze změny)
            status_data["decoded_parameters"] = self.decode_parameter_groups(
                status_data["parameters"],
                PARAMETER_GROUPS
            )

            return status_data

        except Exception as e:
            if self.debug:
                print(f"Chyba při získávání statusu: {str(e)}")
                traceback.print_exc()
            return None
        
    def test_decode(self, data):
        """Testovací metoda pro dekódování dat"""                                            
        print("Testuji dekódování...")
        result = self.decode_parameter_groups(data, PARAMETER_GROUPS)
        print(f"Výsledky dekódování: {result}")
    
            
            
    def get_readable_status(self):
        """
        Vrací zjednodušený a čitelný stav tepelného čerpadla
        
        Returns:
            dict: Formátovaný stav zařízení
        """
        try:
            status = {
                "basic_info": {
                    "power_state": self.status["basic_status"]["power"],
                    "operating_mode": self.status["basic_status"]["mode"],
                    "working_mode": self.status["basic_status"]["work_mode"],
                    "temperature_unit": self.status["basic_status"]["temp_unit"],
                },
                "temperatures": {
                    "hot_water_target": f"{self.status['basic_status']['hot_water_temp']}°C",
                    "heating_target": f"{self.status['basic_status']['heating_temp']}°C",
                    "cooling_target": f"{self.status['basic_status']['cooling_temp']}°C",
                },
                "performance": {
                    "current_power": self.status["decoded_parameters"]["Power of entire machine"],
                    "current_flow_rate": self.status["decoded_parameters"]["Current water flow rate"],
                    "cop": self.status["decoded_parameters"]["COP"],
                    "daily_consumption": self.status["decoded_parameters"]["Daily consumption"],
                },
                "system_health": {
                    "fault_status": "OK" if self.status["basic_status"]["fault"] == 0 else "FAULT",
                    "pump_speed": self.status["decoded_parameters"]["Actual pump speed"],
                }
            }
            
            return status
            
        except KeyError as e:
            return {"error": f"Missing data in status: {str(e)}"}
        except Exception as e:
            return {"error": f"Error getting readable status: {str(e)}"}

    def set_temperature(self, mode, temperature):
        """
        Nastaví požadovanou teplotu pro daný režim
        """
        try:
            code = f"temp_set_{mode}"
            self.connection.set_device_status(
                self.parameters.device_id, code, temperature
            )
            return True
        except Exception as e:
            print(f"Chyba při nastavování teploty: {e}")
            return False

    def set_power(self, state):
        """
        Zapne/vypne čerpadlo
        """
        try:
            self.connection.set_device_status(
                self.parameters.device_id, "switch", state
            )
            return True
        except Exception as e:
            print(f"Chyba při nastavování napájení: {e}")
            return False
