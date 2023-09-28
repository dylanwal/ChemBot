import re

import numpy as np
import plotly.graph_objs as go


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


def get_data():
    file_path = r"C:\Users\nicep\Desktop\post_doc_2022\Data\polymerizations\DW2_1\DW2-1-ATIR.csv"
    data = np.loadtxt(file_path, delimiter=",")

    wavenumber = np.flip(data[0, 1:])
    times = data[1:, 0]
    times = times - times[0]
    data = data[1:, 1:]

    data = np.concatenate((data[:171], data[206:]))
    times = np.concatenate((times[:171], times[206:]))

    # remove bad spectra (has fluoronated oil)
    row_min = np.min(data, axis=1)
    mask = row_min >= -0.2
    data = data[mask]
    times = times[mask]

    return times, wavenumber, data


def main():
    times, wavenumber, data = get_data()

    n = 5
    data = data[::n]
    times = times[::n]

    fig = go.Figure()
    n = len(times)
    colors = get_similar_color("(0,0,255)", n+1)
    for i, t in enumerate(times):
        fig.add_trace(
            go.Scatter3d(
                x=wavenumber,
                y=t*np.ones_like(wavenumber),
                z=data[i, :],
                mode="lines",
                line={"color": colors[i]}
            )
        )

    fig.update_layout(scene=dict(
                    xaxis_title='rxn time (sec)',
                    yaxis_title='wavenumber (cm-1)',
                    zaxis_title='signal'),
                showlegend=False
    )

    # fig.update_layout(autosize=False, width=800, height=600, font=dict(family="Arial", size=18, color="black"),
    #                   plot_bgcolor="white", showlegend=False)
    # fig.update_xaxes(title="<b>retention time (min)</b>", tickprefix="<b>", ticksuffix="</b>", showline=True,
    #                  linewidth=5, mirror=True, linecolor='black', ticks="outside", tickwidth=4, showgrid=False,
    #                  gridwidth=1, gridcolor="lightgray", range=[8, 14])
    # fig.update_yaxes(title="<b>normalized signal</b>", tickprefix="<b>", ticksuffix="</b>", showline=True,
    #                  linewidth=5, mirror=True, linecolor='black', ticks="outside", tickwidth=4, showgrid=False,
    #                  gridwidth=1, gridcolor="lightgray", range=[-0.1, 1.1])


    # create gif
    # from plotly_gif import GIF, three_d_scatter_rotate
    # gif = GIF(mode="png")
    # three_d_scatter_rotate(gif, fig)

    fig.show()

from pymcr.constraints import ConstraintNonneg, Constraint
class ConstraintConv(Constraint):
    """
    Conversion constraint. sum(C) = 1

    Parameters
    ----------
    copy : bool
        Make copy of input data, A; otherwise, overwrite (if mutable)
    """
    def __init__(self, copy=False):
        """ A must be non-negative"""
        super().__init__(copy)

    def transform(self, A):
        """ Apply nonnegative constraint"""
        if self.copy:
            B = np.copy(A)
            for i, row in enumerate(B):
                total = np.sum(row)
                B[i] = B[i]/total
            return B
        else:
            for i, row in enumerate(A):
                total = np.sum(row)
                A[i] = A[i] / total
            return A


def analysis():
    """
    https://www.github.com/usnistgov/pyMCR

    """

    import pandas as pd
    import numpy as np
    import plotly.graph_objs as go
    from pymcr.mcr import McrAR
    from pymcr.regressors import OLS, NNLS
    from pymcr.constraints import ConstraintNonneg, ConstraintNorm

    """
    D = CS^T
    
    D = row: spectra, column: is time
    
    C =
    
    S = 
    
    """
    file_path = r"C:\Users\nicep\Desktop\post_doc_2022\Data\polymerizations\ATIR_MA.csv"
    MA = np.loadtxt(file_path, delimiter=",")
    file_path = r"C:\Users\nicep\Desktop\post_doc_2022\Data\polymerizations\ATIR_PMA.csv"
    PMA = np.loadtxt(file_path, delimiter=",")
    file_path = r"C:\Users\nicep\Desktop\post_doc_2022\Data\polymerizations\ATIR_DMSO.csv"
    DMSO = np.loadtxt(file_path, delimiter=",")

    times, wavenumber, data = get_data()
    times = times[44:]
    data = data[44:, 1000:-100]
    wavenumber = wavenumber[1000:-100]

    num_compounds = 2

    D = data
    C = np.ones((D.shape[0], num_compounds)) * .5
    C[0, :] = np.array([1, .10])

    mcrar = McrAR(max_iter=10000,  c_constraints=[ConstraintNonneg(), ConstraintConv()],  # c_regr='NNLS', # st_regr='NNLS', #  ConstraintNonneg(),
                 st_constraints=[], tol_increase=3)

    mcrar.fit(D, C=C, verbose=True)



    fig = go.Figure()
    fig.add_trace(go.Scatter(y=normalize(mcrar.ST_[0, :]), x=wavenumber, name="MA"))
    fig.add_trace(go.Scatter(y=normalize(mcrar.ST_[1, :]), x=wavenumber, name="PMA"))
    # fig.add_trace(go.Scatter(y=mcrar.ST_[2, :], x=wavenumber, name="DMSO"))
    fig.add_trace(go.Scatter(y=normalize(MA[1000:-100, 1]), x=MA[1000:-100, 0], name="MA_pure"))
    fig.add_trace(go.Scatter(y=normalize(PMA[1000:-100, 1]), x=PMA[1000:-100, 0], name="PMA_pure"))
    # fig.add_trace(go.Scatter(y=DMSO[:, 1], x=np.flip(DMSO[:, 0]), name="DMSO_pure"))

    fig.update_layout(autosize=False, width=1200, height=600, font=dict(family="Arial", size=18, color="black"),
                      plot_bgcolor="white", showlegend=True)
    fig.update_xaxes(title="<b>wavenumber (cm-1) (min)</b>", tickprefix="<b>", ticksuffix="</b>", showline=True,
                     linewidth=5, mirror=True, linecolor='black', ticks="outside", tickwidth=4, showgrid=False,
                     gridwidth=1, gridcolor="lightgray", autorange="reversed")
    fig.update_yaxes(title="<b>normalized absorbance</b>", tickprefix="<b>", ticksuffix="</b>", showline=True,
                     linewidth=5, mirror=True, linecolor='black', ticks="outside", tickwidth=4, showgrid=False,
                     gridwidth=1, gridcolor="lightgray")

    fig.show()

    conv = mcrar.C_[:, 1]/(mcrar.C_[:, 0] + mcrar.C_[:, 1])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=conv))
    fig.update_layout(autosize=False, width=800, height=600, font=dict(family="Arial", size=18, color="black"),
                      plot_bgcolor="white", showlegend=False)
    fig.update_xaxes(title="<b>rxn time (min)</b>", tickprefix="<b>", ticksuffix="</b>", showline=True,
                     linewidth=5, mirror=True, linecolor='black', ticks="outside", tickwidth=4, showgrid=False,
                     gridwidth=1, gridcolor="lightgray")
    fig.update_yaxes(title="<b>conversion</b>", tickprefix="<b>", ticksuffix="</b>", showline=True,
                     linewidth=5, mirror=True, linecolor='black', ticks="outside", tickwidth=4, showgrid=False,
                     gridwidth=1, gridcolor="lightgray")
    fig.show()

    for i in range(mcrar.C_.shape[0]):
        print(times[i], conv[i])


def normalize(data):
    return data/ np.max(data)


def analysis2():
    from pymcr.mcr import McrAR
    times, wavenumber, data = get_data()
    times = times[44:]
    data = data[44:]

    file_path = r"C:\Users\nicep\Desktop\post_doc_2022\Data\polymerizations\ATIR_MA.csv"
    MA = np.loadtxt(file_path, delimiter=",")
    file_path = r"C:\Users\nicep\Desktop\post_doc_2022\Data\polymerizations\ATIR_PMA.csv"
    PMA = np.loadtxt(file_path, delimiter=",")
    file_path = r"C:\Users\nicep\Desktop\post_doc_2022\Data\polymerizations\ATIR_DMSO.csv"
    DMSO = np.loadtxt(file_path, delimiter=",")

    D = data
    S = np.ones((3, D.shape[1])) * -.1
    S[0, :] = MA[:, 1]
    S[1, :] = PMA[:, 1]
    S[2, :] = DMSO[:, 1]

    mcrar = McrAR(max_iter=100, c_constraints=[ConstraintConv()], c_regr='NNLS', st_regr='NNLS',
                  st_constraints=[], tol_increase=2)

    mcrar.fit(D, ST=S, verbose=True, st_fix=[0, 1])

    # fig = go.Figure()
    # fig.add_trace(go.Scatter(y=mcrar.ST_[0, :], x=wavenumber, name="MA"))
    # fig.add_trace(go.Scatter(y=mcrar.ST_[1, :], x=wavenumber, name="PMA"))
    # fig.add_trace(go.Scatter(y=mcrar.ST_[2, :], x=wavenumber, name="DMSO"))
    # fig.add_trace(go.Scatter(y=MA[:, 1], x=np.flip(MA[:, 0]), name="MA_pure"))
    # fig.add_trace(go.Scatter(y=PMA[:, 1], x=np.flip(PMA[:, 0]), name="PMA_pure"))
    # fig.add_trace(go.Scatter(y=DMSO[:, 1], x=np.flip(DMSO[:, 0]), name="DMSO_pure"))
    #
    # fig.show()

    conv = mcrar.C_[:, 1]/(mcrar.C_[:, 0] + mcrar.C_[:, 1])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=conv))
    fig.show()

    for i in range(mcrar.C_.shape[0]):
        print(times[i], conv[i])


if __name__ == "__main__":
    main()
    # analysis()
    # analysis2()
