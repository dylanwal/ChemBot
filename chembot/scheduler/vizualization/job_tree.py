from chembot.scheduler.event import Event
from chembot.scheduler.job import Job, JobConcurrent, JobSequence


class ConfigMermaidFlowchart:
    def __init__(self):
        self.color_event = "#005f73"  # blue
        self.color_job_sequence = "#758E4F"  # green
        self.color_job_concurrent = "#9b2226"  # red
        self.color_background = "#404e4d"
        self.color_arrow = "#ca6702"
        self.color_trigger_arrows = "#758E4F"
        self.trigger_arrow_size = 6

    @property
    def pre_text(self) -> str:
        return "\n".join(
            [
                "%%{",
                "\tinit: {",
                "\t\t'theme': 'base',",
                "\t\t'themeVariables': {",
                f"\t\t\t'background': '{self.color_background}',",
                "\t\t\t'fontFamily': 'arial',",
                "\t\t\t'primaryColor': '#005f73',",
                "\t\t\t'primaryTextColor': '#ffffff',",
                "\t\t\t'primaryBorderColor': '#000000',",
                f"\t\t\t'lineColor': '{self.color_arrow}',",
                "\t\t\t'tertiaryColor': '#fdf0d5',",
                "\t\t\t'tertiaryTextColor': '#000000'",
                "\t\t}",
                "\t}",
                "}%%",
            ]
        )

    @property
    def post_text(self) -> str:
        return "".join(
            [
                f"\tclassDef job_sequence fill:{self.color_job_sequence}\n",
                f"\tclassDef job_concurrent fill:{self.color_job_concurrent}\n",
                f"\tclassDef event fill:{self.color_event}\n"
            ]
        )


class MermaidFlowchartData:
    def __init__(self, depth: int = 1, config: ConfigMermaidFlowchart = None):
        self.depth = depth
        self.config = config if config is not None else ConfigMermaidFlowchart()
        self.index = 0
        self.arrow_index = 0
        self.label_map = {}
        self.text = "graph LR;\n"
        self.text_style = ""
        self.signal_map = {}

    @property
    def final_text(self) -> str:
        return "\n".join((self.config.pre_text, self.text, self.text_style, self.config.post_text))

    def get_label(self, obj: str | Event | Job) -> str:
        if isinstance(obj, str):
            return obj
        if obj.id_ in self.label_map:
            return self.label_map[obj.id_]

        index = self.index
        self.index += 1
        self.label_map[obj.id_] = f"{index}({obj.name})"

        if isinstance(obj, JobConcurrent):
            return f"{index}({obj.name}):::job_concurrent"
        if isinstance(obj, JobSequence):
            return f"{index}({obj.name}):::job_sequence"
        if isinstance(obj, Event):
            return f"{index}({obj.name}):::event"
        return f"{index}({obj.name})"

    def add_arrow(self, obj1: Event | Job | str, obj2: Event | Job | str, text: str = None) -> int:
        self.text += "\t" + self.get_label(obj1) + self.get_arrow_symbol(text) + self.get_label(obj2) + ";\n"
        self.arrow_index += 1
        return self.arrow_index - 1

    def add_line_style(self, arrow_index: int):
        self.text_style += f"\tlinkStyle {arrow_index} stroke:{self.config.color_trigger_arrows}," \
                           f"stroke-width:{self.config.trigger_arrow_size}px;\n"

    def get_arrow_symbol(self, text: str = None):
        if text is None:
            return " --> "
        return f" -- {text} --> "


def generate_job_flowchart(job: Job, depth: int = 5) -> str:
    data = MermaidFlowchartData(depth)
    loop_generate_mermaid_flowchart(job, data)
    return data.final_text


def loop_generate_mermaid_flowchart(job: Job, data: MermaidFlowchartData, depth: int = 0):
    if depth > data.depth:
        return

    for event in job.events:
        data.add_arrow(job, event)

        if hasattr(event, "events"):
            loop_generate_mermaid_flowchart(event, data, depth + 1)
