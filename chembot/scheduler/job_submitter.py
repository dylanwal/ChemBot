
from chembot.rabbitmq.messages import RabbitMessageAction, RabbitMessageReply
from chembot.rabbitmq.rabbit_core import RabbitMQConnection
from chembot.master_controller.master_controller import MasterController
from chembot.scheduler.job import Job


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
        self.rabbit.send(message)
        reply: RabbitMessageReply = self.rabbit.consume(timeout=5)  # ignore type issue
        if reply is not None:
            return reply.value

        raise ValueError("Reply not received from job submission.")

    def delete(self, job: Job):
        raise NotImplementedError
