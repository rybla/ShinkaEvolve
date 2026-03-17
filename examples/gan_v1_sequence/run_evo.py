from datetime import datetime
from math import inf
import subprocess
from typing import Any
import yaml
import json
import sqlite3
import os
import os.path as path
from pathlib import Path

import generator.evaluate
import critic.evaluate
from shinka.database.dbase import DatabaseConfig, ProgramDatabase


# ------------------------------------------------------------------------------
# config


suffix = f"v001"

manager_generations_count = 1
generator_generations_per_manager_generation = 2
critic_generations_per_manager_generation = 4


# ------------------------------------------------------------------------------
# constants


generator_dirpath = Path("generator")
critic_dirpath = Path("critic")

generator_config_filepath = Path(generator_dirpath, f"config_{suffix}.yaml")
critic_config_filepath = Path(critic_dirpath, f"config_{suffix}.yaml")

generator_config_tmp_filepath = Path(generator_dirpath, "config_tmp.yaml")
critic_config_tmp_filepath = Path(critic_dirpath, "config_tmp.yaml")

generator_results_dirpath = Path(
    generator_dirpath,
    "results",
    f"results_generator_{suffix}_{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}",
)
critic_results_dirpath = Path(
    critic_dirpath,
    "results",
    f"results_critic_{suffix}_{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}",
)

generator_best_result_metrics_filepath = Path(
    generator_results_dirpath, "best", "results", "metrics.json"
)
critic_best_result_metrics_filepath = Path(
    critic_results_dirpath, "best", "results", "metrics.json"
)

generator_best_filepath = Path(generator_results_dirpath, "best", "main.py")
critic_best_filepath = Path(critic_results_dirpath, "best", "main.py")

generator_db_filepath = Path(generator_results_dirpath, "programs.sqlite")
critic_db_filepath = Path(critic_results_dirpath, "programs.sqlite")

generator_view_of_critic_best_filepath = Path(generator_dirpath, "critic_best.py")
critic_view_of_generator_best_filepath = Path(critic_dirpath, "generator_best.py")

generator_initial_filepath = Path(generator_dirpath, "initial.py")
critic_initial_filepath = Path(critic_dirpath, "initial.py")


# ------------------------------------------------------------------------------
# initialization


def assert_filepath_exists(filepath: Path):
    assert filepath.exists(), f"File DOES NOT exist: {filepath}"


def assert_filepath_not_exist(filepath: Path):
    assert not filepath.exists(), f"File ALREADY exists: {filepath}"


# check file existences
# config
assert_filepath_exists(generator_config_filepath)
assert_filepath_exists(critic_config_filepath)
# initial
assert_filepath_exists(generator_initial_filepath)
assert_filepath_exists(critic_initial_filepath)

# make results directories
os.makedirs(generator_results_dirpath, exist_ok=False)
os.makedirs(critic_results_dirpath, exist_ok=False)


# ------------------------------------------------------------------------------
# Manager


class Manager:
    def __init__(self):
        self.generation = 0
        self.generator_generation = 0
        self.critic_generation = 0
        self.generator_best_score = -inf
        self.critic_best_score = -inf

    def log(self, *msgs: str):
        print(f"[ gan.manager #{self.generation} ] ", *msgs)

    def run(self):
        self.log("initialization")
        generator_initial_filepath.copy(critic_view_of_generator_best_filepath)
        critic_initial_filepath.copy(generator_view_of_critic_best_filepath)

        self.log("begin loop")
        while self.generation < manager_generations_count:
            self.log("begin loop iteration")

            # generator turn

            self.run_generator()
            self.update_critic_metrics()

            # critic turn

            self.run_critic()
            self.update_generator_metrics()

            # upkeep

            self.generation += 1

    def run_generator(self):
        self.log("run generator")

        if self.generation > 0:
            # update generator with new stuff from critic
            critic_best_filepath.copy(generator_view_of_critic_best_filepath)

        # read original config
        config = yaml.safe_load(generator_config_filepath.read_text(encoding="utf-8"))

        # adjust config
        target_generator_generation = (
            self.generator_generation + generator_generations_per_manager_generation
        )
        self.log(f"target_generator_generation = {target_generator_generation}")
        config["evo_config"]["num_generations"] = target_generator_generation
        config["evo_config"]["results_dir"] = generator_results_dirpath.relative_to(
            generator_dirpath
        ).as_posix()

        # write tmp config
        generator_config_tmp_filepath.write_text(
            yaml.safe_dump(config), encoding="utf-8"
        )

        subprocess.run(
            cwd=generator_dirpath,
            args=[
                "/Users/henry/Documents/ShinkaEvolve/.venv/bin/python",
                "run_evo.py",
                "--config_path",
                generator_config_tmp_filepath.name,
            ],
            check=True,
        )

        self.update_generator_best_score()

        self.generator_generation = target_generator_generation

        # cleanup
        generator_config_tmp_filepath.unlink()

    def run_critic(self):
        self.log(
            f"run critic for {critic_generations_per_manager_generation} generations"
        )

        # update the critic with new stuff from generator
        generator_best_filepath.copy(critic_view_of_generator_best_filepath)

        # read original config
        # config = read_yaml(critic_config_filepath)
        config = yaml.safe_load(critic_config_filepath.read_text(encoding="utf-8"))

        # adjust config
        target_critic_generation = (
            self.critic_generation + critic_generations_per_manager_generation
        )
        self.log(f"target_critic_generation = {target_critic_generation}")
        config["evo_config"]["num_generations"] = target_critic_generation
        config["evo_config"]["results_dir"] = critic_results_dirpath.relative_to(
            critic_dirpath
        ).as_posix()

        # write tmp config
        critic_config_tmp_filepath.write_text(yaml.safe_dump(config), encoding="utf-8")

        subprocess.run(
            cwd=critic_dirpath,
            args=[
                "/Users/henry/Documents/ShinkaEvolve/.venv/bin/python",
                "run_evo.py",
                "--config_path",
                critic_config_tmp_filepath.name,
            ],
            check=True,
        )

        self.update_critic_best_score()

        self.critic_generation = target_critic_generation

        # cleanup
        critic_config_tmp_filepath.unlink()

    def update_generator_metrics(self):
        if not generator_db_filepath.exists():
            return

        def update_local_metrics():
            """
            update metrics per-program
            """

            conn = sqlite3.connect(generator_db_filepath)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT program_id, code FROM programs")
            program_rows = cursor.fetchall()

            self.log(f"updating generator metrics for {len(program_rows)} programs")
            for row in program_rows:
                program_id = row["program_id"]
                code = row["code"]

                # write program code to temporary program file to evaluate
                tmp_program_path = Path(generator_dirpath, "tmp_main.py")
                tmp_program_path.write_text(code, encoding="utf-8")

                # evaluate program file
                subprocess.run(
                    cwd=generator_dirpath,
                    args=[
                        "/Users/henry/Documents/ShinkaEvolve/.venv/bin/python",
                        "evaluate.py",
                        "--program_path",
                        tmp_program_path.as_posix(),
                        "--results_dir",
                        generator_results_dirpath.as_posix(),
                    ],
                    check=True,
                )

                try:
                    metrics, correct, error_msg = generator.evaluate.evaluate(
                        program_path=tmp_program_path.as_posix(),
                        results_dir=generator_results_dirpath.as_posix(),
                    )
                    new_score = metrics.get("combined_score", 0.0) if correct else None
                    public_json = json.dumps(metrics.get("public", {}))
                    private_json = json.dumps(metrics.get("private", {}))
                    cursor.execute(
                        """
                        UPDATE programs 
                        SET
                            combined_score = ?,
                            public_metrics = ?,
                            private_metrics = ?,
                            correct = ?
                        WHERE id = ?
                    """,
                        (new_score, public_json, private_json, correct, program_id),
                    )
                    conn.commit()

                except Exception as e:
                    self.log(f"exception when updating generator program metrics: {e}")

                # cleanup
                tmp_program_path.unlink()

            # cleanup
            conn.close()

        def update_global_metrics():
            """
            update database-wide metrics
            """

            db_config = DatabaseConfig(db_path=generator_db_filepath.as_posix())
            db = ProgramDatabase(config=db_config)

            all_programs = db.get_all_programs()
            for program in all_programs:
                if program.correct:
                    db._update_best_program(program)
                    db._update_archive(program)

        update_local_metrics()
        update_global_metrics()

    def update_critic_metrics(self):
        if not critic_db_filepath.exists():
            return

        def update_local_metrics():
            """
            update metrics per-program
            """

            conn = sqlite3.connect(critic_db_filepath)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT program_id, code FROM programs")
            program_rows = cursor.fetchall()

            self.log(f"updating critic metrics for {len(program_rows)} programs")
            for row in program_rows:
                program_id = row["program_id"]
                code = row["code"]

                # write program code to temporary program file to evaluate
                tmp_program_path = Path(critic_dirpath, "tmp_main.py")
                tmp_program_path.write_text(code, encoding="utf-8")

                # evaluate program file
                subprocess.run(
                    cwd=critic_dirpath,
                    args=[
                        "/Users/henry/Documents/ShinkaEvolve/.venv/bin/python",
                        "evaluate.py",
                        "--program_path",
                        tmp_program_path.as_posix(),
                        "--results_dir",
                        critic_results_dirpath.as_posix(),
                    ],
                    check=True,
                )

                try:
                    metrics, correct, error_msg = critic.evaluate.evaluate(
                        program_path=tmp_program_path.as_posix(),
                        results_dir=critic_results_dirpath.as_posix(),
                    )
                    new_score = metrics.get("combined_score", 0.0) if correct else None
                    public_json = json.dumps(metrics.get("public", {}))
                    private_json = json.dumps(metrics.get("private", {}))
                    cursor.execute(
                        """
                        UPDATE programs 
                        SET
                            combined_score = ?,
                            public_metrics = ?,
                            private_metrics = ?,
                            correct = ?
                        WHERE id = ?
                    """,
                        (new_score, public_json, private_json, correct, program_id),
                    )
                    conn.commit()

                except Exception as e:
                    self.log(f"exception when updating critic program metrics: {e}")

                # cleanup
                tmp_program_path.unlink()

            # cleanup
            conn.close()

        def update_global_metrics():
            """
            update database-wide metrics
            """

            db_config = DatabaseConfig(db_path=critic_db_filepath.as_posix())
            db = ProgramDatabase(config=db_config)

            all_programs = db.get_all_programs()
            for program in all_programs:
                if program.correct:
                    db._update_best_program(program)
                    db._update_archive(program)

        update_local_metrics()
        update_global_metrics()

    def update_generator_best_score(self):
        if not generator_best_result_metrics_filepath.exists():
            return

        metrics = json.loads(
            generator_best_result_metrics_filepath.read_text(encoding="utf-8")
        )
        self.generator_best_score = metrics["combined_score"]

    def update_critic_best_score(self):
        if not critic_best_result_metrics_filepath.exists():
            return

        metrics = yaml.safe_load(
            critic_best_result_metrics_filepath.read_text(encoding="utf-8")
        )
        self.critic_best_score = metrics["combined_score"]


# ------------------------------------------------------------------------------
# main


def main():
    manager = Manager()
    manager.run()


# ------------------------------------------------------------------------------
# utilities


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    main()
