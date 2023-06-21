from datetime import datetime


class JobSubmitResult:

    def __init__(self, job_id: int):
        self.job_id = job_id
        self.success: bool = False
        self.validation_success: bool = False
        self.time_start: datetime | None = None
        self.position_in_queue: int | None = None
        self.length_of_queue: int | None = None
        self.errors: list[Exception] = []

    def __str__(self):
        if self.success:
            return f"Success || validation success: {self.validation_success}," \
                   f" start: {self.time_start} ({self.position_in_queue}/{self.length_of_queue})"
        return f"Unsuccessful || validation success: {self.validation_success}, # errors: {len(self.errors)}"

    def register_error(self, error: Exception):
        self.success = False
        self.errors.append(error)
