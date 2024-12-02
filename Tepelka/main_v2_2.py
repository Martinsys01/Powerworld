from services.measurements import InfluxDBWriter
from services.data_processor import HeatPumpDataProcessor
from config.influxdb_config import INFLUXDB_CONFIG



def process_pump_data(pump_data, device_id):
    """
    Zpracování dat z čerpadla a zápis do InfluxDB
    
    Args:
        pump_data: Data z čerpadla
        device_id: Identifikátor čerpadla
    """
    processor = HeatPumpDataProcessor()
    writer = InfluxDBWriter(
        url=INFLUXDB_CONFIG['url'],
        token=INFLUXDB_CONFIG['token'],
        org=INFLUXDB_CONFIG['org'],
        bucket=INFLUXDB_CONFIG['bucket']
    )
    
    try:
        success, processed_data = processor.process_data(pump_data)
        if success:
            print("Processed data ready to send:", processed_data)  # Debug výpis
            writer.write_data(processed_data, device_id=device_id)
    except Exception as e:
        print(f"Error processing/writing pump data: {e}")
    finally:
        writer.close()


def test_run():
    """Testovací funkce pro ověření základní funkcionality"""
    print("=== Starting Test Run ===")

    # Test data
    test_data = {
        1: {  # Temperatures
            0: 22.5,  # Outside temp
            1: 45.0,  # Flow temp
        },
        2: {  # Pressures
            0: 25.5,  # High pressure
        },
        23: {  # Performance
            0: 4.2,   # COP
        }
    }

    print("\nTest data:")
    print(test_data)

    # Inicializace komponent
    processor = HeatPumpDataProcessor()
    
    # Test zpracování dat
    print("\nProcessing data...")
    success, processed_data = processor.process_data(test_data)
    
    print(f"Processing success: {success}")
    print("Processed data:")
    print(processed_data)

    if success:
        print("\nFormatted structure:")
        structured_data = processor.get_formatted_structure()
        print(structured_data)

        # Test zápisu do InfluxDB
        print("\nTrying to write to InfluxDB...")
        writer = InfluxDBWriter(
            url=INFLUXDB_CONFIG['url'],
            token=INFLUXDB_CONFIG['token'],
            org=INFLUXDB_CONFIG['org'],
            bucket=INFLUXDB_CONFIG['bucket']
        )
        try:
            writer.write_data(processed_data, device_id="heat_pump_test")
            print("Data successfully written to InfluxDB")
        except Exception as e:
            print(f"Error writing to InfluxDB: {e}")
        finally:
            writer.close()

    print("\n=== Test Run Completed ===")

if __name__ == "__main__":
    test_run()