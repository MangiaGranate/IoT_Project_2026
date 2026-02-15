from Edge.model.SenML import SenMLRecord, SenMLPack
from Edge.iot_devices import SensTemp 
import time


MySensor1 = SensTemp(version=1, name="TempSensor", id="TS-001", manufacturer="SensorCo", value=20, thresholds=(40, 80))
MySensor2 = SensTemp(version=1, name="TempSensor", id="TS-002", manufacturer="SensorCo", value=20, thresholds=(40, 80))
MySensor3 = SensTemp(version=1, name="TempSensor", id="TS-003", manufacturer="SensorCo", value=20, thresholds=(40, 80))

for i in range(15):
    start_timer = time.time()

    Record1 = SenMLRecord(name=MySensor1.name, value=MySensor1.read(), unit="°C", time=time.time())
    Record2 = SenMLRecord(name=MySensor2.name, value=MySensor2.read(), unit="°C", time=time.time())
    Record3 = SenMLRecord(name=MySensor3.name, value=MySensor3.read(), unit="°C", time=time.time())

    Pack = SenMLPack(records=[Record1, Record2, Record3], base_name="Sensors/Temperature/", base_time=start_timer, base_unit="°C", base_version=1)

    print(Pack.get_list())

end_timer = time.time()
print("Time taken: ", end_timer - start_timer, "seconds")






