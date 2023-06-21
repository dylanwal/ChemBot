
from chembot.rabbitmq.messages import RabbitMessageAction
from chembot.rabbitmq.rabbit_core import RabbitMQConnection
from chembot.master_controller.master_controller import MasterController
from chembot.scheduler.job import Job
from chembot.scheduler.schedule import Schedule


class JobSubmitter:
    name = "job_submitter"

    def __init__(self):
        self.rabbit = RabbitMQConnection(self.name)

    # def validate(self, job: Job):
    #     pass
    #
    def submit(self, job: Job):
        message = RabbitMessageAction(
            destination=MasterController.name,
            source=self.name,
            action=MasterController.write_add_job,
            kwargs={"job": job}
        )
        return self.rabbit.send_and_consume(message, timeout=1, error_out=True)

    def delete(self, job: Job):
        raise NotImplementedError

    def get_schedule(self) -> Schedule:
        message = RabbitMessageAction(
            destination=MasterController.name,
            source=self.name,
            action=MasterController.read_schedule,
        )
        reply = self.rabbit.send_and_consume(message, timeout=1, error_out=True)
        return reply.value

    def stop(self):
        message = RabbitMessageAction(
            destination=MasterController.name,
            source=self.name,
            action=MasterController.write_stop,
        )
        self.rabbit.send(message)
