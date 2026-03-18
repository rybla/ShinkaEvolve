from datetime import datetime
import math
from typing import Any, Dict, List, Literal, Tuple
import PIL.Image as Image
import os
import numpy as np


# ------------------------------------------------------------------------------
# constants


grid_size = 64
max_steps = 256
grid_diff_min = 0.2
grid_std_min = 0.2
initial_grid_min_std = 0.4


# ------------------------------------------------------------------------------
# utilities


def max_velocity(steps: int):
    return ((1 - (-1)) ** 2) * (grid_size**2) * (steps + 1)


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


def validate_initial_grid(grid: Grid) -> RRR:
    validate_grid_result = validate_grid(grid)
    if validate_grid_result[0] == False:
        return validate_grid_result

    grid_np = np.array(grid)
    std = np.std(grid_np.flatten())

    print(f"std = {std}")

    if not (initial_grid_min_std <= std):
        return (
            False,
            f"The standard deviation of values in the grid, which is {std}, is too small. The minimum acceptable value is {initial_grid_min_std}.",
        )

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
            new_cell = update_cell(
                params,
                cell=get_cell(i, j),
                right_neighborhood=get_neighborhood(i, j, right_di_dj),
                up_neighborhood=get_neighborhood(i, j, up_di_dj),
                left_neighborhood=get_neighborhood(i, j, left_di_dj),
                down_neighborhood=get_neighborhood(i, j, down_di_dj),
            )
            new_grid[i][j] = new_cell

    return new_grid


def analyze_simulation(params: Dict, grid: Grid):
    grids = [grid]

    diff = math.inf
    std = math.inf
    velocity = 0.0

    for step in range(max_steps):
        grids.append(update_grid(params=params, grid=grids[-1]))

        grid0_np = np.array(grids[0]).flatten()
        grid1_np = np.array(grids[-1]).flatten()

        diff = min(np.mean((grid0_np - grid1_np) ** 2), diff)

        velocity += np.sum((grid0_np - grid1_np) ** 2)

        std = min(np.std(grid1_np), std)

        # terminate if repetition is detected
        if diff <= grid_diff_min:
            render_gif(
                params=params,
                grids=grids,
            )

            return {
                "stop_reason": "The simulation was stopped early because a repeated state was detected.",
                "period_detected": True,
                "steps": step,
                "period_diff": diff,
                "grid_std": std,
                "velocity": velocity / max_velocity(step),
            }

        if std < grid_std_min:
            render_gif(
                params=params,
                grids=grids,
            )

            return {
                "stop_reason": "The simulation was stopped early because a grid's cell values had too small of a standard deviation.",
                "period_detected": True,
                "steps": step,
                "period_diff": diff,
                "grid_std": std,
                "velocity": velocity / max_velocity(step),
            }

    render_gif(
        params=params,
        grids=grids,
    )

    return {
        "stop_reason": "The simulation ran for its maximum duration without detecting a repeated state.",
        "period_detected": False,
        "steps": max_steps,
        "period_diff": diff,
        "grid_std": std,
        "velocity": velocity / max_velocity(max_steps),
    }


def generator_score(analysis: Dict) -> float:
    return sum(
        [
            2.0 * (analysis["steps"] / max_steps),
            # Bonus if period was not detected
            0.5 * (0.0 if analysis["period_detected"] else 1.0),
            -1.0 * analysis["grid_std"],
            -1.0 * analysis["velocity"],
        ]
    )


def critic_score(analysis: Dict) -> float:
    return sum(
        [
            -2.0 * (analysis["steps"] / max_steps),
            # Penalty if period was not detected
            -0.5 * (0.0 if analysis["period_detected"] else 1.0),
            -1.0 * analysis["grid_std"],
            -1.0 * analysis["velocity"],
        ]
    )


def update_cell(
    params: Dict,
    cell: Cell,
    right_neighborhood: Cell,
    up_neighborhood: Cell,
    left_neighborhood: Cell,
    down_neighborhood: Cell,
) -> float:
    vals = [
        math.sin(params["c"] * cell * 2.0 * math.pi),
        math.sin(params["r"] * right_neighborhood * 2.0 * math.pi),
        math.sin(params["u"] * up_neighborhood * 2.0 * math.pi),
        math.sin(params["l"] * left_neighborhood * 2.0 * math.pi),
        math.sin(params["d"] * down_neighborhood * 2.0 * math.pi),
    ]

    return sum(vals) / len(vals)


params_names = ["c", "r", "u", "l", "d"]

update_cell_doc: str = (
    f"""
This cellular automata operates on a grid of cells (with torus wrapping), where each cell always has a value in the range -1 to 1. Each cell in the grid is updated every step according to this formula:

    new_cell = sin(x * cell * 2 * pi) + sin(r * right_neighborhood * 2 * pi) + sin(u * up_neighborhood * 2 * pi) + sin(l * left_neighborhood * 2 * pi) + sin(c * down_neighborhood * 2 * pi)

where:

- `cell` is the current value of the cell
- `right_neighborhood` is the average value of the 3 closest cells to the right of the cell
- `up_neighborhood` is the average value of the 3 closest cells above this cell
- `left_neighborhood` is the average value of the 3 closest cells to the left of this cell
- `down_neighborhood` is the average value of the 3 closest cells below this cell

The parameters of this cellular automaton are: {", ".join(params_names)}.
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
