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
    "diameter": 14.6 * Unit.mm,
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
  }
}
