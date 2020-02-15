from .resource import Resource


class Application:
    K1 = "a"  # Slope constant of a linear function f(x) = ax + b
    K2 = "b"  # Intercept constant of a linear function f(x) = ax + b

    def __init__(self):
        self._id = -1
        self._type = ""
        self._deadline = 0
        self._work_size = 0
        self._data_size = 0
        self._request_rate = 0
        self._max_instances = 0
        self._availability = 0
        self._demand = {}

        self.test = 0

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = int(value)

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = str(value).upper()

    @property
    def deadline(self):
        return self._deadline

    @deadline.setter
    def deadline(self, value):
        self._deadline = float(value)

    @property
    def work_size(self):
        return self._work_size

    @work_size.setter
    def work_size(self, value):
        self._work_size = float(value)

    @property
    def data_size(self):
        return self._data_size

    @data_size.setter
    def data_size(self, value):
        self._data_size = float(value)

    @property
    def request_rate(self):
        return self._request_rate

    @request_rate.setter
    def request_rate(self, value):
        self._request_rate = float(value)

    @property
    def max_instances(self):
        return self._max_instances

    @max_instances.setter
    def max_instances(self, value):
        self._max_instances = int(value)

    @property
    def availability(self):
        return self._availability

    @availability.setter
    def availability(self, value):
        self._availability = float(value)

    def get_demand(self, resource_name):
        value = self._demand[resource_name]
        return value[self.K1], value[self.K2]

    def set_demand(self, resource_name, value):
        if isinstance(value, list) or isinstance(value, tuple):
            self._demand[resource_name] = {
                self.K1: float(value[0]),
                self.K2: float(value[1])
            }
        elif isinstance(value, dict):
            self._demand[resource_name] = {
                self.K1: float(value[self.K1]),
                self.K2: float(value[self.K2])
            }
        else:
            raise TypeError

    def get_demand_k1(self, resource_name):
        return self._demand[resource_name][self.K1]

    def get_demand_k2(self, resource_name):
        return self._demand[resource_name][self.K2]

    def get_cpu_demand(self):
        return self.get_demand(Resource.CPU)

    def get_cpu_demand_k1(self):
        return self.get_demand_k1(Resource.CPU)

    def get_cpu_demand_k2(self):
        return self.get_demand_k2(Resource.CPU)
