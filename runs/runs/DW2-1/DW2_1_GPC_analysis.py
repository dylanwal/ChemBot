import logging

import numpy as np
import pandas as pd

import chem_analysis.analysis as chem
import chem_analysis.algorithms.baseline_correction as chem_bc
from unitpy import U

chem.logger_analysis.setLevel(logging.CRITICAL)


def RI_calibration_curve(time: np.ndarray):
    return 10 ** (-0.6 * time + 10.644)


cal_RI = chem.Cal(RI_calibration_curve, lb=160, ub=1_000_000, name="RI calibration")


def single_analysis(path: str):
    df: pd.DataFrame = pd.read_csv(path, header=0, index_col=0)
    df.index.names = ["time (min)"]
    df = df.apply(pd.to_numeric, errors='coerce')

    sig = chem.SECSignal(ser=df["59 min"], cal=cal_RI)
    sig.pipeline.add(chem_bc.adaptive_polynomial_baseline, remove_amount=0.7)
    sig.peak_picking(lb=10, ub=12)   # lb=10.85, ub=12.2
    # mask = np.ones_like(sig_RI.result.index.to_numpy())
    # mask_index = np.argmin(np.abs(sig_RI.result.index.to_numpy() - 10))
    # mask[mask_index:] = False
    # sig_RI.baseline(mask=mask, deg=1)
    # sig_RI.auto_peak_picking()
    # sig.auto_peak_baseline(deg=1, iterations=3)
    sig.plot(title=path)
    sig.stats()


def main():
    path = r"C:\Users\nicep\Desktop\post_doc_2022\Data\polymerizations\DW2_1\DW2-1-GPC.csv"
    single_analysis(path)


if __name__ == '__main__':
    main()
