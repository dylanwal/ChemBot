

def sig_figs(number, significant_figures):
    try:
        return '{:g}'.format(float('{:.{p}g}'.format(number, p=significant_figures)))
    except Exception:
        return number
