
from chembot.scheduler.vizualization.gantt_chart import GanttChart, Row, TimeBlock
from chembot.scheduler.schedule import Schedule


def schedule_to_gantt_chart(schedule: Schedule) -> GanttChart:
    gantt_chart = GanttChart()

    for resource in schedule.resources:
        row = Row(resource.name)
        for event in resource.events:
            row.add_time_block(
                TimeBlock(
                    time_start=event.time_start,
                    time_end=event.time_end,
                    name=event.name,
                    hover_text=event.hover_text()
                )
            )
        gantt_chart.add_row(row)

    return gantt_chart
