from datetime import datetime

from chembot.scheduler.vizualization.gantt_chart import Row, TimeBlock, create_gantt_chart
from chembot.scheduler.vizualization.gantt_chart_app import create_app


def run():
    data = [
        Row("LED (red)",
            [
              TimeBlock(
                  start=datetime(year=2023, month=6, day=1, hour=13, minute=15, second=0),
                  end=datetime(year=2023, month=6, day=1, hour=13, minute=16, second=0),
                  name="ON",
                  hover_text=str({"power": 50})
              )
            ]
            ),
        Row("LED (blue)",
            [
                TimeBlock(
                    start=datetime(year=2023, month=6, day=1, hour=13, minute=15, second=0),
                    end=datetime(year=2023, month=6, day=1, hour=13, minute=18, second=0),
                    name="ON",
                    hover_text=str({"power": 50})
                )
            ]
            ),
        Row("LED (green)",
            [
                TimeBlock(
                    start=datetime(year=2023, month=6, day=1, hour=13, minute=16, second=0),
                    end=datetime(year=2023, month=6, day=1, hour=13, minute=18, second=0),
                    name="ON",
                    hover_text=str({"power": 50})
                )
            ]
            ),
        Row("LED (cyan)",
            [
                TimeBlock(
                    start=datetime(year=2023, month=6, day=1, hour=13, minute=17, second=6),
                    name="ON",
                    hover_text=str({"power": 50})
                )
            ]
            ),
        Row("LED (mint)",
            [
                TimeBlock(
                    start=datetime(year=2023, month=6, day=1, hour=13, minute=17, second=6),
                    name="ON",
                    hover_text=str({"power": 50})
                )
            ]
            ),
        Row("LED (violet)",
            [
                TimeBlock(
                    start=datetime(year=2023, month=6, day=1, hour=13, minute=22, second=36),
                    name="ON",
                    hover_text=str({"power": 50})
                )
            ]
            ),
        Row("LED (serial)",
            [
                TimeBlock(
                    start=datetime(year=2023, month=6, day=1, hour=13, minute=23, second=6),
                    end=datetime(year=2023, month=6, day=1, hour=13, minute=25, second=0),
                    name="ON",
                    hover_text=str({"power": 50})
                )
            ]
            ),
        Row("LED2 (serial)",
            [
                TimeBlock(
                    start=datetime(year=2023, month=6, day=1, hour=13, minute=23, second=6),
                    end=datetime(year=2023, month=6, day=1, hour=13, minute=25, second=0),
                    name="ON",
                    hover_text=str({"power": 50})
                )
            ]
            ),
                Row("LED3 (serial)",
            [
                TimeBlock(
                    start=datetime(year=2023, month=6, day=1, hour=13, minute=23, second=6),
                    end=datetime(year=2023, month=6, day=1, hour=13, minute=25, second=0),
                    name="ON",
                    hover_text=str({"power": 50})
                )
            ]
            ),
                Row("LED4 (serial)",
            [
                TimeBlock(
                    start=datetime(year=2023, month=6, day=1, hour=13, minute=23, second=6),
                    end=datetime(year=2023, month=6, day=1, hour=13, minute=25, second=0),
                    name="ON",
                    hover_text=str({"power": 50})
                )
            ]
            ),
    ]

    # fig = create_gantt_chart(data)
    # fig.write_html("temp.html", auto_open=True)

    app = create_app(data)
    app.run(debug=True)


if __name__ == "__main__":
    run()
