from sp.core.geometry.bound_box import BoundBox
import copy
import math


def create_grid_points(bbox, cell_side):
    """Create list of points in a 2D grid format

    Args:
        bbox (BoundBox): points are generated inside the bound box.
            The generated points use the same coordinate system of the bound box
        cell_side (float): distance between two neighboring points on the grid
    Returns:
        list: list of points
    """
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
            point[BoundBox.X_INDEX] = current_x
            point[BoundBox.Y_INDEX] = current_y
            points.append(point)

            current_y += cell_height
        current_x += cell_width

    return points


