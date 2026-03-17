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
Your task is to infer the pattern of a numeric sequence from the first {train_sequence_length} in order to predict the next {test_sequence_length} numbers. Assume that each number in the sequence must be in the range {element_min}-{element_max}.

To do this task, you must implement a function that takes as input the initial sequence of {train_sequence_length} elements to analyze, and outputs a function that predicts each element of the full {train_sequence_length+test_sequence_length} sequence by taking as input that elements index and returning the element at that index. Your implementation will be evaluated on both correctly predicting elements in the given {train_sequence_length}-element sequence as well as the next {test_sequence_length} elements of the sequence.
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
