
class IDData:
    REFRESH_REGISTRY = "data_refresh_registry"
    EQUIPMENT_REGISTRY = "data_equipment_registry"
    EQUIPMENT_UPDATE = "data_equipment_update"
    EQUIPMENT_ATTRIBUTES = "data_equipment_attributes"
    TIMELINE = "data_timeline"


class GUIData:
    name = "GUI"
    pulse = 0.01
    LOGO = "assets/icon-research-catalysis-white.svg"
    navbar_title = "chembot"
    default_refresh_rate = 30
    refresh_rates = (1, 2, 5, 10, 30)
