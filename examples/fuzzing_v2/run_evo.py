#!/usr/bin/env python3
import argparse

import yaml

from shinka.core import ShinkaEvolveRunner, EvolutionConfig
from shinka.database import DatabaseConfig
from shinka.launch import LocalJobConfig

from dotenv import load_dotenv

load_dotenv()

search_task_sys_msg = """
You are an expert programmer specializing in lambda-calculus. Your current task is to write a generator that produces types and terms of the simply-typed lambda-calculus from a random seed. This generator should be useful for testing a lambda-calculus compiler (which includes type checking, evaluation, and compilation).

Requirements:
- The generator must ALWAYS produce well-formed types and terms 
- The generator must ALWAYS produce well-typed terms, and where the term's type matches the generated type.

Key directions to explore:
- A generated type is better the bigger it is, where its size is measured by the number of nodes in its AST. The maximum allowed number of nodes in the generated type's AST is 10.
- A generated term is better the bigger it is, where its size is measured by the number of nodes in its AST. The maximum allowed number of nodes in the generated term's AST is 100.
- A generated term is better the more it uses its variables (which are introduced by lambdas), by applying those variables to arguments or using them as arguments in applications.
- A generated term is better the more it applies its lambdas to arguments.
- A generated term is better the more unique sub-terms it has. Only application and lambda sub-terms count toward this.
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
