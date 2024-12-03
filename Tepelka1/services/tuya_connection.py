from tuya_connector import TuyaOpenAPI, TUYA_LOGGER
import logging


class TuyaConnection:
    def __init__(self, api_key, api_secret, api_region):
        """Inicializace připojení k Tuya API"""
        endpoint = f"https://openapi.tuya{api_region}.com"
        self.openapi = TuyaOpenAPI(
            endpoint,
            api_key,
            api_secret
        )
        self.connect()

    def connect(self):
        """Připojení k Tuya API"""
        try:
            is_connected = self.openapi.connect()
            if not is_connected:
                raise Exception("Nepodařilo se připojit k Tuya API")
            return True
        except Exception as e:
            print(f"Chyba při připojování k Tuya API: {str(e)}")
            return False

    def get_device_status(self, device_id):
        """Získání stavu zařízení"""
        try:
            # Nová cesta API pro získání stavu zařízení
            response = self.openapi.get(f'/v1.0/iot-03/devices/{device_id}/status')
            if not response.get('success', False):
                raise Exception(response.get('msg', 'Unknown error'))
            return response
        except Exception as e:
            return {"success": False, "msg": str(e)}

    def control_device(self, device_id, commands):
        """Ovládání zařízení"""
        try:
            endpoint = f'/v1.0/iot-03/devices/{device_id}/commands'
            response = self.openapi.post(endpoint, commands)
            if not response.get('success', False):
                raise Exception(response.get('msg', 'Unknown error'))
            return response
        except Exception as e:
            return {"success": False, "msg": str(e)}