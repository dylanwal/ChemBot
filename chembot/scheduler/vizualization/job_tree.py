
from chembot.scheduler.job import Job


class ConfigMermaidFlowchart:
    def __init__(self):
        self.color_event = ""
        self.color_job = ""
        self.color_background = ""
        self.color_arrow = ""
        self.color_trigger_arrows = ""


def generate_mermaid_flowchart(job: Job) -> str:
    flowchart_code = "graph LR;"

    return flowchart_code + loop_generate_mermaid_flowchart(job, "0.")


def loop_generate_mermaid_flowchart(job: Job, prefix: str) -> str:
    output = "\n"
    for i, event in enumerate(job.events):
        if isinstance(event, Job):
            prefix_ = prefix + f"{i}."
            output += f"\t{prefix}({job.name}) --> {prefix_}({event.name});\n"
            output += loop_generate_mermaid_flowchart(event, prefix_)
        else:
            output += f"\t{prefix}({job.name}) --> {prefix}{i}.({event.name});\n"
    return output
