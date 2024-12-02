from typing import Dict, Any, Optional, Tuple
import base64
from config.parameter_mappings import (
    PARAMETER_GROUPS,
    PARAMETER_GROUP_CODES,
    STATUS_GROUPS,
    STATUS_GROUPS_CODES,
)
from services.validation_functions import VALIDATION_FUNCTIONS

class HeatPumpDataProcessor:
    """Třída pro zpracování a validaci dat z tepelného čerpadla"""

    def __init__(self):
        """Inicializace procesoru"""
        self.last_valid_data: Dict[int, Dict[int, Any]] = {}
        self.error_count = 0
        self.MAX_ERRORS = 3

    def process_data(self, raw_data: Dict[int, Dict[int, Any]]) -> Tuple[bool, Optional[Dict[int, Dict[int, Any]]]]:
        """
        Zpracování a validace surových dat
        """
        try:
            # Validace struktury dat
            if not self._validate_data_structure(raw_data):
                print("Diagnostika: Neplatná struktura dat.")
                return False, None

            # Validace hodnot
            if not self._validate_values(raw_data):
                self.error_count += 1
                print(f"Diagnostika: Neplatné hodnoty, počet chyb: {self.error_count}")
                if self.error_count >= self.MAX_ERRORS:
                    print("Diagnostika: Překročen maximální počet chyb.")
                    return False, None
                return False, self.last_valid_data

            # Reset chyb
            self.error_count = 0
            self.last_valid_data = raw_data.copy()

            # Formátování dat
            processed_data = self._format_data(raw_data)

            print("Diagnostika: Data byla úspěšně zpracována.")
            return True, processed_data

        except Exception as e:
            print(f"Diagnostika: Chyba při zpracování dat: {e}")
            return False, None

    def _validate_data_structure(self, data: Dict[str, Any]) -> bool:
        """
        Validace struktury dat, včetně speciálních sekcí.
        """
        if not isinstance(data, dict):
            print("Diagnostika: Vstupní data musí být slovník.")
            return False

        # Povolené klíče (např. basic_status, decoded_parameters)
        valid_sections = {"basic_status", "decoded_parameters"}
        found_valid_section = False

        for key, value in data.items():
            if key in valid_sections:
                if not isinstance(value, dict):
                    print(f"Diagnostika: Sekce {key} musí být slovník.")
                    return False
                found_valid_section = True
            elif isinstance(key, int):  # Číselné klíče pro parametrické skupiny
                if key in PARAMETER_GROUPS or key in STATUS_GROUPS:
                    found_valid_section = True
                else:
                    print(f"DEBUG: Ignoring unknown parameter group {key}.")
            else:
                print(f"DEBUG: Ignoring unexpected key: {key} (type: {type(key)})")

        if not found_valid_section:
            print("Diagnostika: Nebyly nalezeny žádné platné sekce nebo parametry.")
            return False

        return True

    def _validate_values(self, data: Dict[str, Any]) -> bool:
        """
        Validace hodnot parametrů včetně STATUS_GROUPS.
        """
        for key, value in data.items():
            if isinstance(key, int):  # Parametrické nebo stavové skupiny
                validation_func = VALIDATION_FUNCTIONS.get(key)
                if validation_func:
                    for param_id, param_value in value.items():
                        if not validation_func(param_value):
                            print(f"Diagnostika: Neplatná hodnota {param_value} pro parametr ID {param_id}.")
                            return False

        return True

    def _format_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formátování dat, včetně parametrických a stavových skupin.
        """
        formatted_data = {}

        for key, value in data.items():
            if isinstance(key, int):  # Parametrické nebo stavové skupiny
                group_mapping = PARAMETER_GROUPS.get(key, STATUS_GROUPS.get(key, {}))
                formatted_data[key] = {}
                for param_id, param_value in value.items():
                    if param_id in group_mapping:
                        param_name, formatter = group_mapping[param_id]
                        formatted_data[key][param_name] = formatter(param_value)
                    else:
                        formatted_data[key][f"Unknown Param {param_id}"] = param_value

        print(f"Diagnostika: Formátovaná data: {formatted_data}")
        return formatted_data
    
    def test_processing(self, raw_data):
        print("Testuji zpracování dat...")
        success, processed_data = self.process_data(raw_data)
        print(f"Zpracování úspěšné: {success}, Data: {processed_data}")

