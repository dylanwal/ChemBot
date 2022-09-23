
from chembot.errors import PumpFlowRateError


class PumpFlowProfile:

    def __init__(self, flow_rate_profile: list | tuple):
        """
        Parameters
        ----------
        flow_rate_profile: list[tuple[float, float]]
            flow rate profile
            [
                [time (min), flow_rate (ml/min)],
                [time (min), flow_rate (ml/min)],
            ]

            * time must start at 0
            * time is absolute

        """
        self._flow_rate_profile = None
        self.flow_rate_profile = flow_rate_profile

    def __repr__(self) -> str:
        return f"steps: {self.number_steps} | volume_added: {self.total_volume} ml | total_time: {self.total_time} min"

    @property
    def flow_rate_profile(self):
        return self._flow_rate_profile

    @flow_rate_profile.setter
    def flow_rate_profile(self, flow_rate_profile: list | tuple):
        if not isinstance(flow_rate_profile, (list, tuple)) or not isinstance(flow_rate_profile[0], (list, tuple)) or \
                not len(flow_rate_profile[0]) == 2:
            raise PumpFlowRateError("'flow_rate' must have the following structure:"
                                    "\n[\n\t[time (min), flow_rate (ml/min)],\n\t[time (min), "
                                    "flow_rate (ml/min)],\n\t...\n]")

        if flow_rate_profile[0][0] != 0:
            raise PumpFlowRateError("First 'flow_rate' time must be zero.")

        self._flow_rate_profile = flow_rate_profile

    @property
    def number_steps(self):
        return len(self.flow_rate_profile)

    @property
    def total_volume(self):
        """ volume in ml """
        volume = 0
        for i in range(1, len(self.flow_rate_profile)):
            volume += 0.5 * (self.flow_rate_profile[i][1] + self.flow_rate_profile[i - 1][1]) * \
                      (self.flow_rate_profile[i][0] - self.flow_rate_profile[i - 1][0])

        return volume

    @property
    def total_time(self) -> float:
        """ time in minutes """
        return self.flow_rate_profile[-1][0]

    def plot(self):
        try:
            import plotly
            return self._plot_plotly()
        except ImportError as e:
            pass  # module doesn't exist

        try:
            import matplotlib
            raise NotImplemented
        except ImportError as e:
            pass  # module doesn't exist

        raise ImportError("Install plotly or matplotlib to view plots. "
                          "('pip install plotly' or 'pip install matplotlib'")

    def _plot_plotly(self):
        import numpy as np
        import plotly.graph_objs as go

        data = np.array(self.flow_rate_profile)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data[:, 0], y=data[:, 1]))
        fig.update_layout(autosize=False, width=800, height=600, font=dict(family="Arial", size=18, color="black"),
                          plot_bgcolor="white", showlegend=False, legend=dict(x=.5, y=.95))
        fig.update_xaxes(title="<b>time (min)</b>", tickprefix="<b>", ticksuffix="</b>", showline=True,
                         linewidth=5, mirror=True, linecolor='black', ticks="outside", tickwidth=4, showgrid=False,
                         gridwidth=1, gridcolor="lightgray", range=[0, np.max(data[:, 0]) * 1.1])
        fig.update_yaxes(title="<b>flow rate (ml/min) </b>", tickprefix="<b>", ticksuffix="</b>", showline=True,
                         linewidth=5, mirror=True, linecolor='black', ticks="outside", tickwidth=4, showgrid=False,
                         gridwidth=1, gridcolor="lightgray", range=[0, np.max(data[:, 1]) * 1.1])

        return fig


def run_local():
    flow_profile = PumpFlowProfile(
        (
            (0, 0),
            (1, 1),
            (2, 1),
            (3, 2),
            (4, 0)
        )
    )
    print(flow_profile)
    fig = flow_profile.plot()
    fig.write_html("temp.html", auto_open=True)


if __name__ == '__main__':
    run_local()
