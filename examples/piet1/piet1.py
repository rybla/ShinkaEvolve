from typing import Any, Iterable, List, Literal, Set, Tuple

type Path = Any

type RunOutput = Tuple[List[Path], List[Tuple[Path, str]]]

type Point = tuple[int, int]
"""
A point in a 2D grid as an ordered pair (x, y)
"""

type Offset = Tuple[int, int]

type Direction = Literal[0, 1, 2, 3]

# these are the same directions used as the classes for the maze class
direction_up: Direction = 0
direction_down: Direction = 1
direction_left: Direction = 2
direction_right: Direction = 3

type Segment = Tuple[Point, Point]
"""
A line segment between two points. This segment must be either perfectly horizontal or perfectly vertical.
"""


def get_segments(path: Path) -> List[Segment]:
    segs: List[Segment] = []
    p0 = path.start
    for p1 in path.joints + [path.end]:
        segs.append((p0, p1))
        p0 = p1
    return segs


def does_point_intersect_segment(p: Point, seg: Segment) -> bool:
    (x0, y0), (x1, y1) = seg
    x, y = p
    if y0 == y1 == y and ((x0 <= x <= x1) or (x0 >= x >= x1)):
        return True
    elif x0 == x1 == x and ((y0 <= y <= y1) or (y0 >= y >= y1)):
        return True
    return False


def do_points_intersect_segment(ps: Iterable[Point], seg: Segment) -> bool:
    return any([does_point_intersect_segment(p, seg) for p in ps])


def does_point_intersect_segments(p: Point, segs: Iterable[Segment]) -> bool:
    return any([does_point_intersect_segment(p, seg) for seg in segs])


def get_direction(seg: Segment) -> Direction:
    (x0, y0), (x1, y1) = seg

    if (x0 < x1) and (y0 == y1):
        return direction_right
    elif (x0 == x1) and (y0 > y1):
        return direction_up
    elif (x0 > x1) and (y0 == y1):
        return direction_left
    elif (x0 == x1) and (y0 < y1):
        return direction_down
    else:
        raise Exception(
            f"Invalid segment: {seg}. Each segment of a path must be either perfectly horizontal (each endpoint has the same y coordinate) or perfectly vertical (each endpoint has the same x coordinate)."
        )


assert get_direction(((1, 1), (2, 1))) == direction_right
assert get_direction(((1, 1), (1, 0))) == direction_up
assert get_direction(((1, 1), (0, 1))) == direction_left
assert get_direction(((1, 1), (1, 2))) == direction_down


def get_offset(p0: Point, p1: Point) -> Offset:
    (x0, y0), (x1, y1) = p0, p1
    return (x1 - x0, y1 - y0)


def check_paths(
    paths: List[Path],
    grid_size: int,
    path_lengths: List[int],
) -> RunOutput:
    goods: List[Path] = []
    bads: List[Tuple[Path, str]] = []

    for path, path_length in zip(paths, path_lengths):
        try:
            check_path(path, grid_size=grid_size, path_length=path_length)
            goods.append(path)
        except Exception as exn:
            bads.append((path, f"{exn}"))

    return goods, bads


def check_path(
    path: Path,
    grid_size: int,
    path_length: int,
):
    points = set(path.joints).union(set([path.start, path.end]))
    segs = get_segments(path)
    startDirection = get_startDirection(path)
    startDirection_point = get_startDirection_point(path, startDirection)

    # check points
    check_point(path.start, grid_size)
    check_point(path.end, grid_size)
    for p in path.joints:
        check_point(p, grid_size)

    # # make sure no points are right next to start, so that the startDirection
    # # point can be drawn without overlapping an existing point
    # for p in joints + [end]:
    #     o = get_offset(start, joints[0])
    #     assert (
    #         abs(o[0]) > 1 or abs(o[1]) > 1
    #     ), f"There is another point right next to the starting point: {p}"

    assert not does_point_intersect_segments(
        startDirection_point, segs[1:]
    ), f"the startDirection point intersects one of the non-initial segments."
    assert not (
        startDirection_point == segs[0][1]
    ), f"the startDirection point intersects the endpoint of the initial segment."

    # check unique points
    check_unique_points(path)

    # check path_length
    assert (
        len(path.joints) == path_length
    ), f"The path was expected to have path length {path_length} (the expected number of joints), but it actually has length {len(path.joints)} (the actual number of joints)."

    # check segments don't intersect with points
    for seg in segs:
        for p in points.difference(seg):
            assert not does_point_intersect_segment(
                p, seg
            ), f"A point intersects a segment of the path: {p} intersects {seg}"

    # check segments turn orthogonally
    for i0 in range(len(segs) - 1):
        i1 = i0 + 1
        seg0 = segs[i0]
        seg1 = segs[i1]
        d0 = get_direction(seg0)
        d1 = get_direction(seg1)
        assert are_orthogonal_directions(
            d0, d1
        ), f"The segment {show_segment(seg0)} is going in direction {show_direction(d1)} which is NOT orthogonal to the segment immediately before it, {show_segment(seg1)}, which is going in direction {show_direction(d0)}."

    # # check segments
    # p0: Point | None = None
    # p1 = path.start
    # ps_all = set([path.start, path.end]).union(set([p for p, _ in path.joints]))
    # for p2 in path.joints:
    #     s12: Segment = (p1, p2)

    #     # check the segment is turning the right way, according to the starting joint
    #     if p0 is not None:

    #         s01 = (p0, p1)

    #         d01 = get_direction(s01)
    #         d12 = get_direction(s12)

    #         assert (
    #             are_orthogonal_directions(d01, d12)
    #         ) == 1, f"The segment {show_segment(s12)} is going in direction {show_direction(d12)} which is NOT orthogonal to the segment immediately before it, {show_segment(s01)}, which is going in direction {show_direction(d01)}."

    #     # check for bad intersections
    #     ps_seg = get_points_of_segment(s12)
    #     ps_inter = ps_all.intersection(ps_seg)
    #     assert (
    #         ps_inter != 0
    #     ), f"There were some joint points that intersected with a segment: {ps_inter}"

    #     p0 = p1  # type: ignore
    #     p1 = p2

    pass


def show_segment(s: Segment) -> str:
    (p0, p1) = s
    return f"{p0} -> {p1}"


def show_direction(d: Direction) -> str:
    if d == direction_right:
        return "Right"
    elif d == direction_up:
        return "Up"
    elif d == direction_left:
        return "Left"
    elif d == direction_down:
        return "Down"
    else:
        raise Exception(f"Invalid direction: {d}")


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


type Turn = Literal["Left", "Right"]


left_rotations = {
    direction_up: direction_left,
    direction_left: direction_down,
    direction_down: direction_right,
    direction_right: direction_up,
}

right_rotations = {
    direction_up: direction_right,
    direction_right: direction_down,
    direction_down: direction_left,
    direction_left: direction_up,
}


def get_turn_from_directions(d0: Direction, d1: Direction) -> Turn:
    if left_rotations[d0] == d1:
        return "Left"
    elif right_rotations[d0] == d1:
        return "Right"
    else:
        raise Exception(f"Invalid turn: {d0} -> {d1}")


def are_orthogonal_directions(d0: Direction, d1: Direction) -> bool:
    return left_rotations[d0] == d1 or right_rotations[d0] == d1


def length_of_segment(seg: Segment):
    (x0, y0), (x1, y1) = seg

    if x0 < x1 and y0 == y1:
        return x1 - x0
    elif x0 > x1 and y0 == y1:
        return x0 - x1
    elif x0 == x1 and y0 < y1:
        return y1 - y0
    elif x0 == x1 and y0 > y1:
        return y0 - y1
    else:
        raise Exception(f"Invalid segment: {seg}")


def get_stuff(path: Path) -> Tuple[
    Direction,
    List[Turn],
    List[Tuple[Direction, int]],
]:
    steps: List[Tuple[Direction, int]] = []
    turns: List[Turn] = []

    seg0: Segment = path.start, path.joints[0]
    step0 = get_direction(seg0)
    steps.append((step0, length_of_segment(seg0)))

    startDirection = step0

    p0 = path.joints[0]
    for p1 in path.joints[1:] + [path.end]:
        seg1: Segment = p0, p1
        step1 = get_direction(seg1)

        turn1 = get_turn_from_directions(step0, step1)
        turns.append(turn1)

        steps.append((step1, length_of_segment(seg1)))

        p0 = p1
        step0 = step1

    return startDirection, turns, steps


def get_startDirection_offset(path: Path) -> Offset:
    return from_direction_to_offset(get_direction((path.start, path.joints[0])))


def from_direction_to_offset(d: Direction) -> Offset:
    if d == direction_right:
        return 1, 0
    elif d == direction_up:
        return 0, -1
    elif d == direction_left:
        return -1, 0
    elif d == 3:
        return direction_down, 1
    else:
        raise Exception(f"Invalid direction: {d}")


def get_startDirection(path: Path) -> Direction:
    seg0: Segment = path.start, path.joints[0]
    return get_direction(seg0)


def get_startDirection_point(path: Path, startDirection: Direction) -> Point:
    startDirection_offset = from_direction_to_offset(startDirection)
    return apply_offset(path.start, startDirection_offset)


def apply_offset(p: Point, o: Offset) -> Point:
    x, y = p
    ox, oy = o
    return x + ox, y + oy
