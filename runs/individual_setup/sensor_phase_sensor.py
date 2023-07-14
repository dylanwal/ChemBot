
import chembot

from runs.individual_setup.names import NamesSensors

phase_sensor = chembot.equipment.sensors.PhaseSensor(
    name=NamesSensors.PHASE_SENSOR1,
    port="COM6"
)
phase_sensor.activate()
