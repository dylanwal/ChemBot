from unitpy import Unit, Quantity

syringe_configs = {
  "hamilton_1001": {
    "volume": 1 * Unit.ml,
    "max_pressure": 13.8 * Unit.bar,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 115 * Unit.degC,
    "min_temperature": 10 * Unit.degC,
    "diameter": 4.61 * Unit.mm,
    "vendor": "hamilton"
  },
  "hamilton_1002": {
    "volume": 2.5 * Unit.ml,
    "max_pressure": 13.8 * Unit.bar,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 115 * Unit.degC,
    "min_temperature": 10 * Unit.degC,
    "diameter": 7.29 * Unit.mm,
    "vendor": "hamilton"
  },
  "hamilton_1005": {
    "volume": 5 * Unit.ml,
    "max_pressure": 13.8 * Unit.bar,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 115 * Unit.degC,
    "min_temperature": 10 * Unit.degC,
    "diameter": 10.3 * Unit.mm,
    "vendor": "hamilton"
  },
  "hamilton_1010": {
    "volume": 10 * Unit.ml,
    "max_pressure": 13.8 * Unit.bar,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 115 * Unit.degC,
    "min_temperature": 10 * Unit.degC,
    "diameter": 14.567 * Unit.mm,
    "vendor": "hamilton"
  },
  "hamilton_1025": {
    "volume": 25 * Unit.ml,
    "max_pressure": 6.9 * Unit.bar,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 85 * Unit.degC,
    "min_temperature": 10 * Unit.degC,
    "diameter": 23.0 * Unit.mm,
    "vendor": "hamilton"
  },
  "KDS_SS_780802": {  # stainless steel syringe  https://www.kdscientific.com/kds-stainless-steel-syringes.html
    "volume": 8 * Unit.ml,
    "max_pressure": 1500 * Unit.psi,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 85 * Unit.degC,
    "min_temperature": 10 * Unit.degC,
    "diameter": 9.525 * Unit.mm,
    "vendor": "kd_scientific"
  },
  "norm_ject_22768": {  # https://www.restek.com/p/22768
    "volume": 5 * Unit.ml,
    "max_pressure": 10 * Unit.psi,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 30 * Unit.degC,
    "min_temperature": 20 * Unit.degC,
    "diameter": 12.45 * Unit.mm,
    "vendor": "norm_ject"
  },
  "norm_ject_22767": {  # https://www.restek.com/p/22768
    "volume": 2 * Unit.ml,
    "max_pressure": 10 * Unit.psi,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 30 * Unit.degC,
    "min_temperature": 20 * Unit.degC,
    "diameter": 9.65 * Unit.mm,
    "vendor": "norm_ject"
  }
}
