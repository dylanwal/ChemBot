from datetime import datetime

from scheduler.vizualization.gantt_chart import Row, TimeBlock, GanttChart
from chembot.scheduler.vizualization.gantt_chart_app import create_app


def run():
    data = GanttChart(
        [
            Row("LED (red)",
                [
                    TimeBlock(
                        time_start=datetime(year=2023, month=6, day=1, hour=13, minute=15, second=0),
                        time_end=datetime(year=2023, month=6, day=1, hour=13, minute=16, second=0),
                        name="ON",
                        hover_text=str({"power": 50})
                    )
                ]
                ),
            Row("LED (blue)",
                [
                    TimeBlock(
                        time_start=datetime(year=2023, month=6, day=1, hour=13, minute=15, second=0),
                        time_end=datetime(year=2023, month=6, day=1, hour=13, minute=18, second=0),
                        name="ON",
                        hover_text=str({"power": 50})
                    )
                ]
                ),
            Row("LED (green)",
                [
                    TimeBlock(
                        time_start=datetime(year=2023, month=6, day=1, hour=13, minute=16, second=0),
                        time_end=datetime(year=2023, month=6, day=1, hour=13, minute=18, second=0),
                        name="ON",
                        hover_text=str({"power": 50})
                    )
                ]
                ),
            Row("LED (cyan)",
                [
                    TimeBlock(
                        time_start=datetime(year=2023, month=6, day=1, hour=13, minute=17, second=6),
                        name="ON",
                        hover_text=str({"power": 50})
                    )
                ]
                ),
            Row("LED (mint)",
                [
                    TimeBlock(
                        time_start=datetime(year=2023, month=6, day=1, hour=13, minute=17, second=6),
                        name="ON",
                        hover_text=str({"power": 50})
                    )
                ]
                ),
            Row("LED (violet)",
                [
                    TimeBlock(
                        time_start=datetime(year=2023, month=6, day=1, hour=13, minute=22, second=36),
                        name="ON",
                        hover_text=str({"power": 50})
                    )
                ]
                ),
            Row("Pico (serial)",
                [
                    TimeBlock(
                        time_start=datetime(year=2023, month=6, day=1, hour=13, minute=23, second=6),
                        time_end=datetime(year=2023, month=6, day=1, hour=13, minute=25, second=0),
                        name="ON",
                        hover_text=str({"power": 50})
                    )
                ]
                ),
            Row("Pump1 (serial)",
                [
                    TimeBlock(
                        time_start=datetime(year=2023, month=6, day=1, hour=13, minute=23, second=6),
                        time_end=datetime(year=2023, month=6, day=1, hour=13, minute=25, second=0),
                        name="ON",
                        hover_text=str({"power": 50})
                    )
                ]
                ),
            Row("Pump2 (serial)",
                [
                    TimeBlock(
                        time_start=datetime(year=2023, month=6, day=1, hour=13, minute=23, second=6),
                        time_end=datetime(year=2023, month=6, day=1, hour=13, minute=25, second=0),
                        name="ON",
                        hover_text=str({"power": 50})
                    )
                ]
                ),
            Row("Pump3 (serial)",
                [
                    TimeBlock(
                        time_start=datetime(year=2023, month=6, day=1, hour=13, minute=23, second=6),
                        time_end=datetime(year=2023, month=6, day=1, hour=13, minute=25, second=0),
                        name="ON",
                        hover_text=str({"power": 50})
                    )
                ]
                ),
        ])

    data.current_time = datetime(year=2023, month=6, day=1, hour=13, minute=20, second=6)

    # fig = create_gantt_chart(data)
    # fig.write_html("temp.html", auto_open=True)

    app = create_app(data)
    app.run(debug=True)


if __name__ == "__main__":
    run()
