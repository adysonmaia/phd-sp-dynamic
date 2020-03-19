from sp.core.model import Scenario
import json


def main():
    filename = 'input/san_francisco/scenario.json'
    scenario = None
    with open(filename) as json_file:
        data = json.load(json_file)
        scenario = Scenario.from_json(data)
    print(scenario)


if __name__ == '__main__':
    main()
