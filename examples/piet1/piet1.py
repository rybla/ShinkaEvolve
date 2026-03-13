from typing import Any, List, Literal, Set, Tuple

type Path = Any

type RunOutput = Tuple[List[Path], List[Tuple[Path, str]]]

type Point = tuple[int, int]
"""
A point in a 2D grid as an ordered pair (x, y)
"""

type Direction = Literal[0, 1, 2, 3]
"""
Right = 0
Up = 1
Left = 2
Down = 3
"""

type Segment = Tuple[Point, Point]
"""
A line segment between two points. This segment must be either perfectly horizontal or perfectly vertical.
"""


def check_paths(
    paths: List[Path],
    grid_size: int,
    path_lengths: List[int],
) -> RunOutput:
    valid_paths: List[Path] = []
    problems: List[Tuple[Path, str]] = []

    for path, path_length in zip(paths, path_lengths):
        try:
            check_path(path, grid_size, path_length)
            valid_paths.append(path)
        except Exception as exn:
            problems.append((path, f"{exn}"))

    return valid_paths, problems


def check_path(
    path: Path,
    grid_size: int,
    path_length: int,
):
    start: Point = path.start
    end: Point = path.end
    joints: List[Point] = path.joints

    # check points
    check_point(start, grid_size)
    check_point(end, grid_size)
    for p in joints:
        check_point(p, grid_size)

    # check unique points
    check_unique_points(path)

    # check path_length
    assert (
        len(path.joints) == path_length
    ), f"The path was expected to have path length {path_length} (the expected number of joints), but it actually has length {len(joints)} (the actual number of joints)."

    # check segments
    p0: Point | None = None
    p1 = path.start
    ps_all = set([path.start, path.end]).union(set([p for p, _ in path.joints]))
    for p2 in path.joints:
        s12: Segment = (p1, p2)

        # check the segment is turning the right way, according to the starting joint
        if p0 is not None:

            s01 = (p0, p1)

            d01 = get_direction(s01)
            d12 = get_direction(s12)

            assert (
                (d01 + d12) % 2
            ) == 1, f"The segment {show_segment(s12)} is going in direction {show_direction(d12)} which is NOT orthogonal to the segment immediately before it, {show_segment(s01)}, which is going in direction {show_direction(d01)}."

        # check for bad intersections
        ps_seg = get_points_of_segment(s12)
        ps_inter = ps_all.intersection(ps_seg)
        assert (
            ps_inter != 0
        ), f"There were some joint points that intersected with a segment: {ps_inter}"

        p0 = p1  # type: ignore
        p1 = p2


def show_segment(s: Segment) -> str:
    (p0, p1) = s
    return f"{p0} -> {p1}"


def show_direction(d: Direction) -> str:
    if d == 0:
        return "Right"
    elif d == 1:
        return "Up"
    elif d == 2:
        return "Left"
    elif d == 3:
        return "Down"
    else:
        raise Exception(f"Invalid direction: {d}")


def get_direction(seg: Segment) -> Direction:
    (x0, y0), (x1, y1) = seg

    if (x0 < x1) and (y0 == y1):
        # right
        return 0
    elif (x0 == x1) and (y0 < y1):
        # up
        return 1
    elif (x0 > x1) and (y0 == y1):
        # left
        return 2
    elif (x0 == x1) and (y0 > y1):
        # down
        return 3
    else:
        raise Exception(
            f"Invalid segment: {seg}. Each segment of a path must be either perfectly horizontal (each endpoint has the same y coordinate) or perfectly vertical (each endpoint has the same x coordinate)."
        )


def check_point(p: Point, grid_size: int):
    x, y = p
    assert (
        0 <= x < grid_size
    ), f"Invalid point: {p}. The x coordinate, {x}, is out of bounds in a grid of size {grid_size}."
    assert (
        0 <= y < grid_size
    ), f"Invalid point: {p}. The y coordinate, {y}, is out of bounds in a grid of size {grid_size}."


def check_segment(seg: Segment):
    (x0, y0), (x1, y1) = seg

    assert (x0 == x1) or (
        y0 == y1
    ), f"Invalid segment: {seg}. Each segment of a path must be either perfectly horizontal (each endpoint has the same y coordinate) or perfectly vertical (each endpoint has the same x coordinate)."

    assert (x0, y0) != (
        x1,
        y1,
    ), f"Invalid segment: {seg}. The segment endpoints must be different."


def get_points_of_segment(seg: Segment) -> Set[Point]:
    """
    get points of segment, not including endpoints
    """

    (x0, y0), (x1, y1) = seg

    if x0 < x1 and y0 == y1:
        y = y0
        return set([(x, y) for x in range(x0 + 1, x1)])
    elif x0 > x1 and y0 == y1:
        y = y0
        return set([(x, y) for x in range(x1, x0)])
    elif x0 == x1 and y0 < y1:
        x = x0
        return set([(x, y) for y in range(y0, y1)])
    elif x0 == x1 and y0 > y1:
        x = x0
        return set([(x, y) for y in range(y0, y1)])
    else:
        assert (
            False
        ), f"Invalid segment: {seg}. Each segment of a path must be either perfectly horizontal or perfectly vertical."


def check_unique_points(path: Path):
    start: Point = path.start
    end: Point = path.end
    joints: List[Point] = path.joints

    all_points: Set[Point] = set()

    def check_point(p: Point):
        assert (
            p not in all_points
        ), f"This point appears multiple times in the path: {p}"
        all_points.add(p)

    check_point(start)
    for p in joints:
        check_point(p)

    check_point(end)


def from_path_to_tuple(path: Path):
    start: Point = path.start
    end: Point = path.end
    joints: List[Point] = path.joints

    return (start, tuple(joints), end)
