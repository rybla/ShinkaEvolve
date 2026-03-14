#!/usr/bin/env python3
import argparse

import yaml

from shinka.core import ShinkaEvolveRunner, EvolutionConfig
from shinka.database import DatabaseConfig
from shinka.launch import LocalJobConfig

from dotenv import load_dotenv

load_dotenv()

search_task_sys_msg = """
Your task is to develop a better implementation of `generate_path`, which is a function that generates a path on a grid from a random seed.

The path must satisfy these requirements:
- Each point of the path must lie within the grid specified by the grid_size
- Each point of the path must be unique
- Each line segment of the path is perfectly horizontal or perfectly vertical
- Each line segment of the path must be orthogonal ot the segment immediately before it and the segment immediately after it
- The path length must exactly match the specified path_length, where a path's length is measured as the number of joint points of the path
- Each endpoint of each line segment of the path must NOT intersect with any other line segments, however line segments are allowed to intersect
""".strip()


def main(config_path: str):
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    config["evo_config"]["task_sys_msg"] = search_task_sys_msg
    evo_config = EvolutionConfig(**config["evo_config"])
    job_config = LocalJobConfig(
        eval_program_path="evaluate.py",
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
