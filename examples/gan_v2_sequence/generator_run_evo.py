#!/usr/bin/env python3
import argparse

import yaml

from shinka.core import ShinkaEvolveRunner, EvolutionConfig
from shinka.database import DatabaseConfig
from shinka.launch import LocalJobConfig

from dotenv import load_dotenv

from common import train_sequence_length, test_sequence_length, element_min, element_max

load_dotenv()

search_task_sys_msg = f"""
Your task is to design a numeric sequence that uses simple rules but is difficult to recognize. Only the first {train_sequence_length+test_sequence_length} elements of the sequence will be considered. Each element should be in the range {element_min}-{element_max}.

To do this task, you must implement a function that generates each element of the sequence, given its index (ranging frm 0 to {train_sequence_length + test_sequence_length - 1}).

CRITICAL: You are PROHIBITED from using random generation in any way.
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
