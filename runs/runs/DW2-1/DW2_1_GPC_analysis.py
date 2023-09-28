import logging
import re

import numpy as np
import pandas as pd
import plotly.graph_objs as go

import chem_analysis.analysis as chem
import chem_analysis.algorithms.baseline_correction as chem_bc
from unitpy import U

chem.logger_analysis.setLevel(logging.CRITICAL)


def RI_calibration_curve(time: np.ndarray):
    return 10 ** (-0.6 * time + 10.644)


cal_RI = chem.Cal(RI_calibration_curve, lb=160, ub=1_000_000, name="RI calibration")


def get_similar_color(color_in: str, num_colors: int, mode: str = "dark") -> list[str]:
    rgb = re.findall("[0-9]{1,3}", color_in)
    rgb = [int(i) for i in rgb]
    if mode == "dark":
        change_rgb = [i > 120 for i in rgb]
        jump_amount = [-int((i - 10) / num_colors) for i in rgb]
        jump_amount = [v if i else 0 for i, v in zip(change_rgb, jump_amount)]

    elif mode == "light":
        jump_amount = [int(100 / num_colors) if i < 100 else int((245 - i) / num_colors) for i in rgb]

    else:
        raise ValueError(f"Invalid 'mode'; only 'light' or 'dark'. (mode: {mode})")

    colors = []
    for i in range(num_colors):
        r = rgb[0] + jump_amount[0] * (i + 1)
        g = rgb[1] + jump_amount[1] * (i + 1)
        b = rgb[2] + jump_amount[2] * (i + 1)
        colors.append(f"rgb({r},{g},{b})")

    return colors


def single_analysis(path: str):
    df: pd.DataFrame = pd.read_csv(path, header=0, index_col=0)
    df.index.names = ["time (min)"]
    df = df.apply(pd.to_numeric, errors='coerce')

    filtered_df = df.loc[10:13]
    max_values = []
    for col in df.columns:
        max_values.append(max([filtered_df[col].max(), 3.8]))

    max_values[0] = 10
    max_values[1] = 10
    max_values[2] = 2.9
    max_values[-1] = 5


    ################################################################################
    fig = go.Figure()
    colors = get_similar_color("(0,0,255)", len(max_values))
    for i, col in enumerate(df.columns):
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df[col]/max_values[i],
                mode="lines",
                name=col,
                line={"color": colors[i]}
            )
        )

    fig.update_layout(autosize=False, width=800, height=600, font=dict(family="Arial", size=18, color="black"),
                      plot_bgcolor="white", showlegend=True, )
    fig.update_xaxes(title="<b>retention time (min)</b>", tickprefix="<b>", ticksuffix="</b>", showline=True,
                     linewidth=5, mirror=True, linecolor='black', ticks="outside", tickwidth=4, showgrid=False,
                     gridwidth=1, gridcolor="lightgray", range=[8, 14])
    fig.update_yaxes(title="<b>normalized signal</b>", tickprefix="<b>", ticksuffix="</b>", showline=True,
                     linewidth=5, mirror=True, linecolor='black', ticks="outside", tickwidth=4, showgrid=False,
                     gridwidth=1, gridcolor="lightgray", range=[-0.1, 1.1])

    # fig.show()

    ################################################################################
    df = df.loc[8:14]
    for i, col in enumerate(df.columns):
        df[col] = df[col]/max_values[i]

    x = []
    for col in df.columns:
        x.append(int(col[:2]))

    fig = go.Figure()
    fig.add_trace(
        go.Surface(
            z=df.values,
            x=x,
            y=df.index.values
        )
    )
    # fig.update_traces(contours_z=dict(show=True, usecolormap=True, highlightcolor="limegreen", project_z=True))
    fig.update_layout(font=dict(family="Arial", size=18, color="black"),
                      plot_bgcolor="white")
    fig.update_xaxes(title="<b>rxn time (min)</b>", tickprefix="<b>", ticksuffix="</b>", showline=True,
                     linewidth=5, mirror=True, linecolor='black', ticks="outside", tickwidth=4, showgrid=False,
                     gridwidth=1, gridcolor="lightgray")
    fig.update_yaxes(title="<b>retention time (min)</b>", tickprefix="<b>", ticksuffix="</b>", showline=True,
                     linewidth=5, mirror=True, linecolor='black', ticks="outside", tickwidth=4, showgrid=False,
                     gridwidth=1, gridcolor="lightgray")

    # fig.show()

    ################################################################################
    fig = go.Figure()
    for i, col in enumerate(df.columns):
        fig.add_trace(
            go.Scatter3d(
                x=x[i]*np.ones_like(df.index.values),
                y=df.index.values,
                z=df[col].values,
                mode="lines",
                line={"color": colors[i]}
            )
        )

    fig.update_layout(autosize=False, width=800, height=600, font=dict(family="Arial", size=18, color="black"),
                      plot_bgcolor="white", showlegend=False)
    fig.update_xaxes(title="<b>retention time (min)</b>", tickprefix="<b>", ticksuffix="</b>", showline=True,
                     linewidth=5, mirror=True, linecolor='black', ticks="outside", tickwidth=4, showgrid=False,
                     gridwidth=1, gridcolor="lightgray", range=[8, 14])
    fig.update_yaxes(title="<b>normalized signal</b>", tickprefix="<b>", ticksuffix="</b>", showline=True,
                     linewidth=5, mirror=True, linecolor='black', ticks="outside", tickwidth=4, showgrid=False,
                     gridwidth=1, gridcolor="lightgray", range=[-0.1, 1.1])
    fig.show()

    # single
    # sig = chem.SECSignal(ser=df["59 min"], cal=cal_RI)
    # sig.pipeline.add(chem_bc.adaptive_polynomial_baseline, remove_amount=0.7)
    # sig.peak_picking(lb=10, ub=12)   # lb=10.85, ub=12.2
    # sig.plot(title=path)
    # sig.stats()


def main():
    path = r"C:\Users\nicep\Desktop\post_doc_2022\Data\polymerizations\DW2_1\DW2-1-GPC.csv"
    single_analysis(path)


if __name__ == '__main__':
    main()
