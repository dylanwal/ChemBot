
from chembot.scheduler.job_submitter import JobSubmitter


def main():
    job_submitter = JobSubmitter()
    result = job_submitter.stop()
    print(result)


if __name__ == "__main__":
    main()
