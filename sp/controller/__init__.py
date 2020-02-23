class Controller:
    def __init__(self):
        self.system = None

    def start(self, system):
        self.system = system
        if self.system is None:
            raise ValueError("System not defined")

    def update(self, time):
        pass

    def stop(self):
        pass
