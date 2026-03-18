#!/usr/bin/env python3
import argparse

import yaml

from shinka.core import ShinkaEvolveRunner, EvolutionConfig
from shinka.database import DatabaseConfig
from shinka.launch import LocalJobConfig

from dotenv import load_dotenv

from common import grid_size, update_cell_doc, grid_std_min
import critic_best

load_dotenv()

search_task_sys_msg = f"""
Your task is to find an interesting set of parameters for a novel cellular automaton. 

{update_cell_doc}

Your task is to find a set of parameters for the cellular automaton that yields interesting behaviors. The interestingness of the cellular automaton is measured by the longest period (the number of steps required for a state to repeat) and the minimum standard deviation of the cell values over the simulation. Note that the grid must always have a cell value standard deviation above {grid_std_min}

Your cellular automaton configuration will be evaluated on an initial grid where these are the first two rows:

    {critic_best.generate_initial_grid(grid_size=grid_size)[0:2]}

Important notes:
- maximize steps
- bonus points for avoiding period detection
- minimize grid cell values standard deviation
- minimize grid cell value change velocity
- design a configuration that leads to interesting life-like behavior
""".strip()


def main(config_path: str):
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    config["evo_config"]["task_sys_msg"] = search_task_sys_msg
    evo_config = EvolutionConfig(**config["evo_config"])
    job_config = LocalJobConfig(
        eval_program_path="generator_evaluate.py",
        time="00:05:00",
    )
    db_config = DatabaseConfig(**config["db_config"])

    runner = ShinkaEvolveRunner(
        evo_config=evo_config,
        job_config=job_config,
        db_config=db_config,
        max_evaluation_jobs=config.get("max_evaluation_jobs"),
        max_proposal_jobs=config.get("max_proposal_jobs"),
        max_db_workers=config.get("max_db_workers"),
        debug=False,
        verbose=True,
    )
    runner.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", type=str)
    args = parser.parse_args()
    main(args.config_path)
