from dataclasses import dataclass
from typing import List, Literal, Tuple
import random
import tqdm


type Point = tuple[int, int]
"""
A point in a 2D grid as an ordered pair (x, y)
"""

type Segment = Tuple[Point, Point]
"""
A line segment between two points. 
"""


@dataclass
class Path:
    """
    A path in a grid.
    """

    start: Point
    """
    The starting point for the path
    """

    end: Point
    """
    The 
    """

    joints: List[Point]
    """
    The joint points, in order, that make up the path.
    """


# EVOLVE-BLOCK-START


def generate_path(
    rng: random.Random,
    grid_size: int,
    path_length: int,
) -> Path:
    """
    Generates a random path with a number of joints equal to path_length that is
    contained within a grid_size*grid_size grid with these boundary points:

        - (0, 0)
        - (0, grid_size)
        - (grid_size, 0)
        - (grid_size, grid_size)

    So, every point (x, y) in the path must satisfy these constraints:

        0 <= x < grid_size
        0 <= y < grid_size.
    """

    def randomCoord():
        return rng.randrange(0, grid_size)

    coords = set(range(0, grid_size))

    def randomPoint():
        return (randomCoord(), randomCoord())

    start = randomPoint()

    joints: List[Point] = []

    point = start

    orientation = rng.choice([0, 1])
    """
    Vertical = 0
    Horizontal = 1
    """

    for i in range(path_length + 1):
        x, y = point

        if orientation == 0:
            y = rng.choice(list(coords.difference(set([y]))))
            point = (x, y)
        else:
            x = rng.choice(list(coords.difference(set([x]))))
            point = (x, y)

        if i < path_length:
            joints.append(point)
        else:
            end = point

        orientation = (orientation + 1) % 2

    return Path(
        start=start,
        end=end,  # type: ignore
        joints=joints,
    )


# EVOLVE-BLOCK-END


from piet1 import RunOutput, check_paths


# This part remains fixed (not evolved)
def run_piet1() -> RunOutput:
    """Run the path generator"""

    rng = random.Random(3478237)
    samples_count = 1000
    grid_size = 8
    # path_lengths = [rng.randrange(4, 6) for _ in range(samples_count)]
    path_lengths = [rng.randrange(2, 3) for _ in range(samples_count)]
    paths = [
        generate_path(
            rng=rng,
            grid_size=grid_size,
            path_length=path_length,
        )
        for path_length in tqdm.tqdm(path_lengths, desc="Generating samples")
    ]

    return check_paths(paths, grid_size, path_lengths)


if __name__ == "__main__":
    paths, bads = run_piet1()
    print("=" * 16)
    print("Good paths:")
    for path in paths:
        print(path)

    print("=" * 16)
    print("Problematic paths:")
    for path, problem in bads:
        print(path)
        print(f"  [!] {problem}")

    print(f"goods = {len(paths)}")
    print(f"bads = {len(bads)}")
