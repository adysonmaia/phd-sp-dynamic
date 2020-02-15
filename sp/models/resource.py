class Resource:
    CPU = "CPU"

    def __init__(self):
        self.name = ""
        self.unit = ""
        self.type = "int"
        self.precision = 4

    @property
    def id(self):
        return self.name
