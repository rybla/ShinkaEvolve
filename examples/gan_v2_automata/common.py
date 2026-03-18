from datetime import datetime
import math
from typing import Any, Dict, List, Literal, Tuple
import PIL.Image as Image
import os


# ------------------------------------------------------------------------------
# constants


grid_size = 32
max_steps = 1000
min_diff = 0.05


# ------------------------------------------------------------------------------
# utilities

type Cell = float
type Grid = List[List[Cell]]

type RRR = Tuple[Literal[False], str] | Tuple[Literal[True], None]


def validate_cell(cell: Cell) -> RRR:
    if not (-1.0 <= cell <= 1.0):
        return False, f"Invalid cell value: {cell}"
    return True, None


def validate_grid(grid: Grid) -> RRR:
    msgs = []

    for row in grid:
        for cell in row:
            result = validate_cell(cell)
            if result[0] == False:
                msgs.append(result[1])

    if len(msgs) != 0:
        return False, f"Invalid grid:\n{"\n".join([ f"- {msg}" for msg in msgs  ])}"

    return True, None


def validate_param(name: str, param: float) -> RRR:
    # if not (-1.0 <= param <= 1.0):
    #     return (
    #         False,
    #         f"The param {name}={param} is invalid since it is outside the range -1.0 to 1.0",
    #     )

    return True, None


def validate_params(params: Dict) -> RRR:
    msgs = []

    for k, v in params.items():
        validate_param_result = validate_param(k, v)
        if not validate_param_result[0]:
            msgs.append(validate_param_result[1])

    return True, None


def mean_squared_differences_of_grids(grid0: Grid, grid1: Grid) -> float:
    i_max = len(grid0)
    j_max = len(grid0[0])

    total = 0
    for i in range(i_max):
        for j in range(j_max):
            total += (grid0[i][j] - grid1[i][j]) ** 2

    return total / (i_max * j_max)


right_di_dj = [(d, 1) for d in [-1, 0, 1]]
left_di_dj = [(d, -1) for d in [-1, 0, 1]]
up_di_dj = [(1, d) for d in [-1, 0, 1]]
down_di_dj = [(-1, d) for d in [-1, 0, 1]]


def update_grid(params: Dict, grid: Grid) -> Grid:
    i_max = len(grid)
    j_max = len(grid[0])

    new_grid = [[0.0 for _ in row] for row in grid]

    def get_cell(i: int, j: int) -> Cell:
        return grid[i % i_max][j % j_max]

    def get_neighborhood(i: int, j: int, all_di_dj: List[Tuple[int, int]]):
        return sum([get_cell(i + di, j + dj) for di, dj in all_di_dj]) / len(all_di_dj)

    for i in range(i_max):
        for j in range(j_max):
            new_grid[i][j] = update_cell(
                params,
                x=j / j_max,
                y=i / i_max,
                cell=get_cell(i, j),
                right_neighborhood=get_neighborhood(i, j, right_di_dj),
                up_neighborhood=get_neighborhood(i, j, up_di_dj),
                left_neighborhood=get_neighborhood(i, j, left_di_dj),
                down_neighborhood=get_neighborhood(i, j, down_di_dj),
            )

    return new_grid


def calculate_period(params: Dict, grid: Grid):
    grids = [grid]

    diff = math.inf

    for step in range(max_steps):
        grids.append(update_grid(params=params, grid=grids[-1]))
        diff = min(mean_squared_differences_of_grids(grids[0], grids[-1]), diff)

        # terminate if repetition is detected
        if diff <= min_diff:
            render_gif(
                params=params,
                grids=grids,
            )

            return {
                "stop_reason": "The simulation was stopped early because a repeated state was detected.",
                "period_detected": True,
                "period_length": step,
                "period_diff": diff,
            }

    render_gif(
        params=params,
        grids=grids,
    )

    return {
        "stop_reason": "The simulation ran for its maximum duration without detecting a repeated state.",
        "period_detected": False,
        "period_length": max_steps,
        "period_diff": None,
    }


def generator_score(calculate_period_result: Dict) -> float:
    return sum(
        [
            calculate_period_result["period_length"],
            (
                # Bonus if period was not detected
                0.0
                if calculate_period_result["period_detected"]
                else (5.0 / 100.0) * max_steps
            ),
        ]
    )


def update_cell(
    params: Dict,
    cell: Cell,
    x: float,
    y: float,
    right_neighborhood: Cell,
    up_neighborhood: Cell,
    left_neighborhood: Cell,
    down_neighborhood: Cell,
) -> float:
    vals = [
        math.sin(params["cx"] * cell * 2.0 * math.pi + x),
        math.cos(params["cy"] * cell * 2.0 * math.pi + y),
        math.sin(params["r"] * right_neighborhood * 2.0 * math.pi),
        math.sin(params["u"] * up_neighborhood * 2.0 * math.pi),
        math.sin(params["l"] * left_neighborhood * 2.0 * math.pi),
        math.sin(params["d"] * down_neighborhood * 2.0 * math.pi),
    ]

    return sum(vals) / len(vals)


params_names = ["cx", "cy", "r", "u", "l", "d"]

update_cell_doc: str = (
    f"""
This cellular automata operates on a grid of cells (with torus wrapping), where each cell always has a value in the range -1 to 1. Each cell in the grid is updated every step according to this formula:

    new_cell = sin(cx * cell * 2 * pi + x) + sin(cy * cell * pi + y) + sin(r * right_neighborhood * 2 * pi) + sin(u * up_neighborhood * 2 * pi) + sin(l * left_neighborhood * 2 * pi) + sin(c * down_neighborhood * 2 * pi)

where:

- `cell` is the current value of the cell
- `x` is the normalized x-coordinate of the cell
- `y` is the normalized y-coordinate of the cell
- `right_neighborhood` is the average value of the 3 closest cells to the right of the cell
- `up_neighborhood` is the average value of the 3 closest cells above this cell
- `left_neighborhood` is the average value of the 3 closest cells to the left of this cell
- `down_neighborhood` is the average value of the 3 closest cells below this cell

The parameters of this cellular automaton are: cx, cy, r, u, l, d.
    """.strip()
)


def value_to_color(val: float) -> tuple[int, int, int]:
    val = max(-1.0, min(1.0, val))

    if val < 0:
        r = g = int(255 * (1 + val))
        b = 255
    else:
        r = 255
        g = b = int(255 * (1 - val))

    return (r, g, b)


def render_gif(
    params: Dict,
    grids: List[Grid],
    scale_factor: int = 20,
    duration_ms: int = 100,
) -> None:
    os.makedirs("artifacts", exist_ok=True)
    output_path = f"artifacts/simulation_{ "_".join([ f"{k}={v}" for k,v in params.items()  ]) }_timestamp={datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.gif"
    print(f"rendering simulation gif to '{output_path}'")

    if not grids or not grids[0]:
        raise ValueError("Cannot render: The grids list is empty or malformed.")

    rows = len(grids[0])
    cols = len(grids[0][0])

    if rows == 0 or cols == 0:
        raise ValueError("Cannot render: Grid dimensions must be greater than 0.")

    frames: List[Image.Image] = []

    for grid in grids:
        img = Image.new("RGB", (cols, rows))
        pixels: Any = img.load()

        for r in range(rows):
            for c in range(cols):
                pixels[c, r] = value_to_color(grid[r][c])

        if scale_factor > 1:
            img = img.resize(
                (cols * scale_factor, rows * scale_factor), Image.Resampling.NEAREST
            )

        frames.append(img)

    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
    )
