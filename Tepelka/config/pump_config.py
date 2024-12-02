import json
import os

class HeatPumpParameters:
    DEVICE_ID_PUMP1 = None
    DEVICE_ID_PUMP2 = None
    PUMP1_NAME = None
    PUMP2_NAME = None

    @classmethod
    def load_config(cls):
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'pump_config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
                pump1_config = config.get('pump1', {})
                pump2_config = config.get('pump2', {})
                
                cls.DEVICE_ID_PUMP1 = pump1_config.get('deviceId')
                cls.PUMP1_NAME = pump1_config.get('name')
                cls.DEVICE_ID_PUMP2 = pump2_config.get('deviceId')
                cls.PUMP2_NAME = pump2_config.get('name')
                
            print(f"Konfigurace čerpadel načtena: {config_path}")
        except Exception as e:
            print(f"Chyba při načítání konfigurace čerpadel: {str(e)}")
            raise

    @classmethod
    def create_pump1(cls):
        return cls(cls.DEVICE_ID_PUMP1, cls.PUMP1_NAME)

    @classmethod
    def create_pump2(cls):
        return cls(cls.DEVICE_ID_PUMP2, cls.PUMP2_NAME)

    def __init__(self, device_id, name):
        self.device_id = device_id
        self.name = name