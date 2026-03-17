from datetime import datetime
from math import inf
import subprocess
from typing import Any, Dict
import yaml
import json
import sqlite3
import os
import os.path as path
from pathlib import Path

from shinka.database.dbase import DatabaseConfig, ProgramDatabase


# ------------------------------------------------------------------------------
# config


suffix = f"v001"

manager_generations_count = 1
generator_generations_per_manager_generation = 2
critic_generations_per_manager_generation = 4


# ------------------------------------------------------------------------------
# constants

now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

generator_config_filepath = Path(f"generator_config_{suffix}.yaml")
critic_config_filepath = Path(f"critic_config_{suffix}.yaml")

generator_config_tmp_filepath = Path(f"tmp_generator_config.yaml")
critic_config_tmp_filepath = Path(f"tmp_critic_config.yaml")

generator_results_dirpath = Path(
    "generator_results",
    f"results_{suffix}_{now}",
)
critic_results_dirpath = Path(
    "critic_results",
    f"results_{suffix}_{now}",
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

generator_view_of_critic_best_filepath = Path(f"critic_best.py")
critic_view_of_generator_best_filepath = Path(f"generator_best.py")

generator_initial_filepath = Path(f"generator_initial.py")
critic_initial_filepath = Path(f"critic_initial.py")


def generator_evaluation_results_dirpath(program_generation: int):
    return Path(
        generator_results_dirpath,
        f"gen_{program_generation}",
        "results",
    )


def critic_evaluation_results(program_generation: int):
    return Path(
        critic_results_dirpath,
        f"gen_{program_generation}",
        "results",
    )


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

        # update generator with new stuff from critic
        (
            critic_best_filepath
            if critic_best_filepath.exists()
            else critic_initial_filepath
        ).copy(generator_view_of_critic_best_filepath)

        # read original config
        config = yaml.safe_load(generator_config_filepath.read_text(encoding="utf-8"))

        # adjust config
        target_generator_generation = (
            self.generator_generation + generator_generations_per_manager_generation
        )
        self.log(f"target_generator_generation = {target_generator_generation}")
        config["evo_config"]["num_generations"] = target_generator_generation
        config["evo_config"]["results_dir"] = generator_results_dirpath.as_posix()

        # write tmp config
        generator_config_tmp_filepath.write_text(
            yaml.safe_dump(config), encoding="utf-8"
        )

        subprocess.run(
            args=[
                "/Users/henry/Documents/ShinkaEvolve/.venv/bin/python",
                "generator_run_evo.py",
                "--config_path",
                generator_config_tmp_filepath.name,
            ],
            check=True,
        )

        self.update_generator_best_score()

        self.generator_generation = target_generator_generation

        # cleanup
        generator_config_tmp_filepath.unlink()
        # NOTE: we don't remove generator_view_of_critic_best_filepath so that the generator_evaluate module can pretend to import it for the sake of type-checking

    def run_critic(self):
        self.log(
            f"run critic for {critic_generations_per_manager_generation} generations"
        )

        # update the critic with new stuff from generator
        (
            generator_best_filepath
            if generator_best_filepath.exists()
            else generator_initial_filepath
        ).copy(critic_view_of_generator_best_filepath)

        # read original config
        # config = read_yaml(critic_config_filepath)
        config = yaml.safe_load(critic_config_filepath.read_text(encoding="utf-8"))

        # adjust config
        target_critic_generation = (
            self.critic_generation + critic_generations_per_manager_generation
        )
        self.log(f"target_critic_generation = {target_critic_generation}")
        config["evo_config"]["num_generations"] = target_critic_generation
        config["evo_config"]["results_dir"] = critic_results_dirpath.as_posix()

        # write tmp config
        critic_config_tmp_filepath.write_text(yaml.safe_dump(config), encoding="utf-8")

        subprocess.run(
            args=[
                "/Users/henry/Documents/ShinkaEvolve/.venv/bin/python",
                "critic_run_evo.py",
                "--config_path",
                critic_config_tmp_filepath.name,
            ],
            check=True,
        )

        self.update_critic_best_score()

        self.critic_generation = target_critic_generation

        # cleanup
        critic_config_tmp_filepath.unlink()
        # NOTE: we don't remove critic_view_of_generator_best_filepath so that the critic_evaluate module can pretend to import it for the sake of type-checking

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
            cursor.execute("SELECT program_id, code, generation FROM programs")
            program_rows = cursor.fetchall()

            self.log(f"updating generator metrics for {len(program_rows)} programs")
            for row in program_rows:
                program_id = row["program_id"]
                program_code = row["code"]
                program_generation: int = row["generation"]

                # write program code to temporary program file to evaluate
                tmp_program_filepath = Path(f"generator_tmp_main.py")
                tmp_program_filepath.write_text(program_code, encoding="utf-8")

                tmp_program_evaluation_results_dirpath = (
                    generator_evaluation_results_dirpath(program_generation)
                )

                # evaluate program file
                subprocess.run(
                    args=[
                        "/Users/henry/Documents/ShinkaEvolve/.venv/bin/python",
                        "generator_evaluate.py",
                        "--program_path",
                        tmp_program_filepath.as_posix(),
                        "--results_dir",
                        tmp_program_evaluation_results_dirpath.as_posix(),
                    ],
                    check=True,
                )

                try:
                    metrics: Dict = json.loads(
                        Path(
                            tmp_program_evaluation_results_dirpath, "metrics.json"
                        ).read_text(encoding="utf-8")
                    )
                    correctness: Dict = json.loads(
                        Path(
                            tmp_program_evaluation_results_dirpath, "correct.json"
                        ).read_text(encoding="utf-8")
                    )
                    new_score = (
                        metrics.get("combined_score", 0.0)
                        if correctness["correct"]
                        else None
                    )
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
                        (new_score, public_json, private_json, correctness, program_id),
                    )
                    conn.commit()

                except Exception as e:
                    self.log(f"exception when updating generator program metrics: {e}")

                # cleanup
                tmp_program_filepath.unlink()

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
            cursor.execute("SELECT program_id, code, generation FROM programs")
            program_rows = cursor.fetchall()

            self.log(f"updating critic metrics for {len(program_rows)} programs")
            for row in program_rows:
                program_id = row["program_id"]
                program_code = row["code"]
                program_generation: int = row["generation"]

                # write program code to temporary program file to evaluate
                tmp_program_path = Path(f"critic_tmp_main.py")
                tmp_program_path.write_text(program_code, encoding="utf-8")

                tmp_program_evaluation_results_dirpath = (
                    generator_evaluation_results_dirpath(program_generation)
                )

                # evaluate program file
                subprocess.run(
                    args=[
                        "/Users/henry/Documents/ShinkaEvolve/.venv/bin/python",
                        "critic_evaluate.py",
                        "--program_path",
                        tmp_program_path.as_posix(),
                        "--results_dir",
                        tmp_program_evaluation_results_dirpath.as_posix(),
                    ],
                    check=True,
                )

                try:
                    metrics: Dict = json.loads(
                        Path(
                            tmp_program_evaluation_results_dirpath, "metrics.json"
                        ).read_text(encoding="utf-8")
                    )
                    correctness: Dict = json.loads(
                        Path(
                            tmp_program_evaluation_results_dirpath, "correct.json"
                        ).read_text(encoding="utf-8")
                    )
                    new_score = (
                        metrics.get("combined_score", 0.0)
                        if correctness["correct"]
                        else None
                    )
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
                        (new_score, public_json, private_json, correctness, program_id),
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
