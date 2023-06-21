
from chembot.rabbitmq.messages import RabbitMessageAction
from chembot.rabbitmq.rabbit_core import RabbitMQConnection
from chembot.master_controller.master_controller import MasterController
from chembot.scheduler.job import Job
from chembot.scheduler.schedular import Schedular
from chembot.equipment.equipment_interface import EquipmentRegistry
from chembot.scheduler.submit_result import JobSubmitResult


class JobSubmitter:
    name = "job_submitter"

    def __init__(self):
        self.rabbit = RabbitMQConnection(self.name)

    def validate(self, job: Job) -> JobSubmitResult:
        message = RabbitMessageAction(
            destination=MasterController.name,
            source=self.name,
            action=MasterController.write_validate_job,
            kwargs={"job": job}
        )
        return self.rabbit.send_and_consume(message, timeout=1, error_out=True).value

    def submit(self, job: Job) -> JobSubmitResult:
        message = RabbitMessageAction(
            destination=MasterController.name,
            source=self.name,
            action=MasterController.write_add_job,
            kwargs={"job": job}
        )
        return self.rabbit.send_and_consume(message, timeout=1, error_out=True).value

    def delete(self, job: Job):
        raise NotImplementedError

    def get_schedule(self) -> Schedular:
        message = RabbitMessageAction(
            destination=MasterController.name,
            source=self.name,
            action=MasterController.read_schedule,
        )
        return self.rabbit.send_and_consume(message, timeout=1, error_out=True).value

    def get_equipment_registry(self) -> EquipmentRegistry:
        message = RabbitMessageAction(
            destination=MasterController.name,
            source=self.name,
            action=MasterController.read_equipment_registry,
        )
        return self.rabbit.send_and_consume(message, timeout=1, error_out=True).value

    def stop(self):
        message = RabbitMessageAction(
            destination=MasterController.name,
            source=self.name,
            action=MasterController.write_stop,
        )
        self.rabbit.send(message)
