from sp.geometry.bbox import BBox
import copy
import math


def create_point_grid(bbox, cell_side):
    x_fraction = cell_side / bbox.x_distance
    cell_width = x_fraction * bbox.width

    y_fraction = cell_side / bbox.y_distance
    cell_height = y_fraction * bbox.height

    columns = math.floor(bbox.width / cell_width)
    rows = math.floor(bbox.height / cell_height)

    delta_x = (bbox.width - columns * cell_width) / 2.0
    delta_y = (bbox.height - rows * cell_height) / 2.0

    points = []
    point = bbox.points[0]

    current_x = bbox.x_min + delta_x
    while current_x <= bbox.x_max:
        current_y = bbox.y_min + delta_y

        while current_y <= bbox.y_max:
            point = copy.deepcopy(point)
            point[BBox.X_INDEX] = current_x
            point[BBox.Y_INDEX] = current_y
            points.append(point)

            current_y += cell_height
        current_x += cell_width

    return points


