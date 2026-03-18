#!/usr/bin/env python3
import argparse

import yaml

from shinka.core import ShinkaEvolveRunner, EvolutionConfig
from shinka.database import DatabaseConfig
from shinka.launch import LocalJobConfig

from dotenv import load_dotenv

import generator_best
from common import update_cell_doc, initial_grid_min_std

load_dotenv()

search_task_sys_msg = f"""
Your task is to define an initial configuration for a cellular automaton that yields the shortest possible period, where the period is the number of steps that it takes for the initial state to repeat. 

    {update_cell_doc.strip()}

The parameters have been set to these specific values that yield interesting behavior.

{"\n".join([ f"    {k} = {v}" for k,v in generator_best.params.items() ])}

Your task is to find an initial grid for the grid that the cellular automaton works over that leads to the shortest possible period and smallest minimum standard deviation over the simulation. Note that the initial grid must have a cell value standard deviation of at least {initial_grid_min_std}.

Important notes:
- minimize steps
- penalty for missing period detection
- minimize grid cell values standard deviation
- minimize grid cell value change velocity
- design an initial that leads to life-like behavior with a very short period
""".strip()


def main(config_path: str):
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    config["evo_config"]["task_sys_msg"] = search_task_sys_msg
    evo_config = EvolutionConfig(**config["evo_config"])
    job_config = LocalJobConfig(
        eval_program_path="critic_evaluate.py",
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
