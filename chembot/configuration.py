
class GlobalIDs:
    objects = dict()

    def __init__(self):
        self.next_id = 0

    def get_id(self, obj) -> int:
        id_ = self.next_id
        self.objects[id_] = obj
        self.next_id += 1
        return id_


global_ids = GlobalIDs()


class Configurations:
    def __init__(self):
        self.encoding = "UTF-8"
        self.sig_fig_pump = 3


configuration = Configurations()
