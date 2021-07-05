
import numpy as np


def sig_figs(number: float, significant_figures: int = 3) -> str:
    """
    Given a number return a string rounded to the desired significant digits.
    :param number:
    :param significant_figures:
    :return:
    """
    try:
        return '{:g}'.format(float('{:.{p}g}'.format(number, p=significant_figures)))
    except Exception:
        return str(number)


def sig_figs_array(array: np.ndarray, significant_figures: int = 3) -> str:
    """
    Given a array return a string rounded to the desired significant digits.
    :param array:
    :param significant_figures:
    :return:
    """
    try:
        out = ""
        for number in array:
            out = out + '{:g}'.format(float('{:.{p}g}'.format(number, p=significant_figures))) + " ,"
        return out[:-2]
    except Exception:
        return str(np.array)


if __name__ == '__main__':
    # for testing purposes
    a = 12.3049030934
    print(sig_figs(a, 5))
    print(sig_figs(a, 1))
    
    b = np.array([1.234, 123124, 21312, 123])
    print(sig_figs_array(b, 2))
