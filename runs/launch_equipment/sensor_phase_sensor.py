import chembot

from runs.launch_equipment.names import NamesSensors

phase_sensor = chembot.equipment.sensors.PhaseSensor(
    name=NamesSensors.PHASE_SENSOR1,
    port="COM14"
)
phase_sensor.activate()
