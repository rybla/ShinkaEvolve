#!/usr/bin/env python3
import argparse

import yaml

from shinka.core import ShinkaEvolveRunner, EvolutionConfig
from shinka.database import DatabaseConfig
from shinka.launch import LocalJobConfig

from dotenv import load_dotenv

load_dotenv()

search_task_sys_msg = """
You are an expert programmer specializing in lambda calculus. Your current task is to write a generator function that produces types and terms based on a random seed. This generator should be useful for generating inputs to test a type checker implementation.

Key directions to explore:
- The generator must always produce well-formed types and terms.
- The generator should have a non-negligible chance of generating all different kinds of types and terms that could be useful for testing many different control-flow paths in a type checker. 
- The generator should generate both a type and a term, but the term does not necessarily have to be well typed and have the generated type. Generate whatever types and terms are useful for fuzzing the type checker. 
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
