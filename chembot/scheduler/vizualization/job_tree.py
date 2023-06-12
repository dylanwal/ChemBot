from chembot.scheduler.triggers import TriggerNow, TriggerSignal, TriggerOr, TriggerAnd, \
    TriggerTimeRelative, TriggerTimeAbsolute
from chembot.scheduler.event import Event
from chembot.scheduler.job import Job


class ConfigMermaidFlowchart:
    def __init__(self):
        self.color_event = "#005f73"
        self.color_job = "#758E4F"
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
                f"\tclassDef job fill:{self.color_job}\n",
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

        if isinstance(obj, Job):
            return f"{index}({obj.name}):::job"
        if isinstance(obj, Job):
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

    def add_signal_trigger_arrow(self, obj):
        trigger: TriggerSignal = obj.trigger
        if trigger.signal in self.signal_map:
            for obj_ in self.signal_map[trigger.signal]:
                arrow_index = self.add_arrow(obj_, obj, "signal")
                if isinstance(obj_, Job) and isinstance(obj, Job):
                    self.add_line_style(arrow_index)
        else:
            self.add_arrow("signal_out_scope", obj)  # zero is invalid id_ and will return out of scope

    def register_signal(self, obj):
        if obj.completion_signal in self.signal_map:
            self.signal_map[obj.completion_signal.signal].append(obj)
        else:
            self.signal_map[obj.completion_signal] = [obj]


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


def generate_trigger_flowchart(job: Job, depth: int = 5) -> str:
    data = MermaidFlowchartData(depth)
    loop_generate_trigger_arrows(job, data)
    return data.final_text


def loop_generate_trigger_arrows(job: Job, data: MermaidFlowchartData, depth: int = 0):
    if depth > data.depth:
        return

    for i, event in enumerate(job.events):
        if isinstance(event.trigger, TriggerNow):
            data.add_arrow(event.parent, event)
        if isinstance(event.trigger, TriggerTimeRelative):
            data.add_arrow(event.parent, event, text=str(event.trigger.trigger_time))
        if isinstance(event.trigger, TriggerSignal):
            data.add_signal_trigger_arrow(event)

        if event.completion_signal:
            data.register_signal(event)

        if hasattr(event, "events"):
            loop_generate_trigger_arrows(event, data, depth + 1)
