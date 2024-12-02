import json
import os

class TuyaConfig:
    API_KEY = None
    API_SECRET = None
    API_REGION = None

    @classmethod
    def load_config(cls):
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'tuya_config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
                cls.API_KEY = config.get('apiKey')
                cls.API_SECRET = config.get('apiSecret')
                cls.API_REGION = config.get('apiRegion')
                
            print(f"Konfigurace načtena: {config_path}")
        except Exception as e:
            print(f"Chyba při načítání Tuya konfigurace: {str(e)}")
            raise

    @classmethod
    def get_config_dict(cls):
        return {
            'apiKey': cls.API_KEY,
            'apiSecret': cls.API_SECRET,
            'apiRegion': cls.API_REGION
        }