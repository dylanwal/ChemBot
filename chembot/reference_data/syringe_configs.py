from unitpy import Unit, Quantity

syringe_configs = {
  "hamilton_1001": {
    "volume": 1 * Unit.ml,
    "max_pressure": 13.8 * Unit.bar,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 115 * Unit.degC,
    "min_temperature": 10 * Unit.degC,
    "diameter": 4.61 * Unit.mm,
    "vendor": "hamilton",
    "force": 50
  },
  "hamilton_1002": {
    "volume": 2.5 * Unit.ml,
    "max_pressure": 13.8 * Unit.bar,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 115 * Unit.degC,
    "min_temperature": 10 * Unit.degC,
    "diameter": 7.29 * Unit.mm,
    "vendor": "hamilton",
    "force": 50
  },
  "hamilton_1005": {
    "volume": 5 * Unit.ml,
    "max_pressure": 13.8 * Unit.bar,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 115 * Unit.degC,
    "min_temperature": 10 * Unit.degC,
    "diameter": 10.3 * Unit.mm,
    "vendor": "hamilton",
    "force": 50
  },
  "hamilton_1010": {
    "volume": 10 * Unit.ml,
    "max_pressure": 13.8 * Unit.bar,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 115 * Unit.degC,
    "min_temperature": 10 * Unit.degC,
    "diameter": 14.567 * Unit.mm,
    "vendor": "hamilton",
    "force": 50
  },
  "hamilton_1025": {
    "volume": 25 * Unit.ml,
    "max_pressure": 6.9 * Unit.bar,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 85 * Unit.degC,
    "min_temperature": 10 * Unit.degC,
    "diameter": 23.0 * Unit.mm,
    "vendor": "hamilton",
    "force": 50
  },
  "KDS_SS_780802": {  # stainless steel syringe  https://www.kdscientific.com/kds-stainless-steel-syringes.html
    "volume": 8 * Unit.ml,
    "max_pressure": 1500 * Unit.psi,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 85 * Unit.degC,
    "min_temperature": 10 * Unit.degC,
    "diameter": 9.525 * Unit.mm,
    "vendor": "kd_scientific",
    "force": 100
  },
  "norm_ject_5ml": {  # https://www.restek.com/p/22768
    "volume": 5 * Unit.ml,
    "max_pressure": 10 * Unit.psi,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 30 * Unit.degC,
    "min_temperature": 20 * Unit.degC,
    "diameter": 12.2 * Unit.mm,  # 12.45
    "vendor": "norm_ject",
    "force": 30
  },
  "norm_ject_2ml": {  # https://www.restek.com/p/22768
    "volume": 2 * Unit.ml,
    "max_pressure": 10 * Unit.psi,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 30 * Unit.degC,
    "min_temperature": 20 * Unit.degC,
    "diameter": 9.65 * Unit.mm,
    "vendor": "norm_ject",
    "force": 30
  },
  "norm_ject_20ml": {  # https://www.restek.com/p/22768
    "volume": 20 * Unit.ml,
    "max_pressure": 10 * Unit.psi,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 30 * Unit.degC,
    "min_temperature": 20 * Unit.degC,
    "diameter": 20.05 * Unit.mm,
    "vendor": "norm_ject",
    "force": 30
  },
  "norm_ject_10ml": {  # https://www.restek.com/p/22768
    "volume": 10 * Unit.ml,
    "max_pressure": 10 * Unit.psi,
    "min_pressure": 0 * Unit.bar,
    "max_temperature": 30 * Unit.degC,
    "min_temperature": 20 * Unit.degC,
    "diameter": 15.90 * Unit.mm,
    "vendor": "norm_ject",
    "force": 30
  }
}
