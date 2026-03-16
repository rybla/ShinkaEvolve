import subprocess
from typing import Any
import yaml
import json
import os
import os.path as path
from pathlib import Path


# ------------------------------------------------------------------------------
# config


suffix = "v001"

manager_generations_count = 2
generator_generations_per_manager_generation = 4
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
    generator_dirpath, "results", f"results_generator_{suffix}"
)
critic_results_dirpath = Path(critic_dirpath, "results", f"results_critic_{suffix}")

generator_best_result_metrics_filepath = Path(
    generator_results_dirpath, "best", "results", "metrics.json"
)
critic_best_result_metrics_filepath = Path(
    critic_results_dirpath, "best", "results", "metrics.json"
)

generator_best_filepath = Path(generator_results_dirpath, "best", "main.py")
critic_best_filepath = Path(critic_results_dirpath, "best", "main.py")

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
        self.generator_best_score = 0.0
        self.critic_best_score = 0.0

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

            # beat best score
            checkpoint_generator_best_score = self.generator_best_score
            generator_i = 1
            while not (self.generator_best_score > checkpoint_generator_best_score):
                self.log(f"generator attempt #{generator_i} to beat best score")
                self.run_generator()
                generator_i += 1
            self.log(f"generator beat best score after {generator_i} attempts")

            # run one more time
            self.run_generator()

            # critic turn

            # beat best score
            checkpoint_critic_best_score = self.critic_best_score
            critic_i = 1
            while not (self.critic_best_score > checkpoint_critic_best_score):
                self.log(f"critic attempt #{critic_i} to beat best score")
                self.run_critic()
                critic_i += 1
            self.log(f"critic beat best score after {critic_i} attempts")

            # run one more time
            self.run_critic()

            # upkeep

            self.generation += 1

    def run_generator(self):
        self.log("run generator")

        if self.generation > 0:
            # update generator with new stuff from critic
            critic_best_filepath.copy(generator_view_of_critic_best_filepath)

        # read original config
        config = read_yaml(generator_config_filepath)

        # adjust config
        config["db_config"]["num_generations"] = (
            generator_generations_per_manager_generation * (self.generation + 1) + 1
        )
        config["evo_config"]["results_dir"] = generator_results_dirpath.relative_to(
            generator_dirpath
        ).as_posix()

        # write tmp config
        write_yaml(generator_config_tmp_filepath, config)

        subprocess.run(
            cwd=generator_dirpath,
            args=[
                "/Users/henry/Documents/ShinkaEvolve/.venv/bin/python",
                "run_evo.py",
                "--config_path",
                generator_config_filepath.name,
            ],
            check=True,
        )

        self.update_generator_best_score()

    def run_critic(self):
        self.log("run critic")

        # update the critic with new stuff from generator
        generator_best_filepath.copy(critic_view_of_generator_best_filepath)

        # read original config
        config = read_yaml(critic_config_filepath)

        # adjust config
        config["db_config"]["num_generations"] = (
            critic_generations_per_manager_generation * (self.generation + 1) + 1
        )
        config["evo_config"]["results_dir"] = critic_results_dirpath.relative_to(
            critic_dirpath
        ).as_posix()

        # write tmp config
        write_yaml(critic_config_tmp_filepath, config)

        subprocess.run(
            cwd=critic_dirpath,
            args=[
                "/Users/henry/Documents/ShinkaEvolve/.venv/bin/python",
                "run_evo.py",
                "--config_path",
                critic_config_filepath.name,
            ],
            check=True,
        )

        self.update_critic_best_score()

    def update_generator_best_score(self):
        if not generator_best_result_metrics_filepath.exists():
            return

        metrics = read_json(generator_best_result_metrics_filepath)
        self.generator_best_score = metrics["combined_score"]

    def update_critic_best_score(self):
        if not critic_best_result_metrics_filepath.exists():
            return

        metrics = read_json(critic_best_result_metrics_filepath)
        self.critic_best_score = metrics["combined_score"]


# ------------------------------------------------------------------------------
# main


def main():
    manager = Manager()
    manager.run()


# ------------------------------------------------------------------------------
# utilities


def read_yaml(filepath: Path) -> Any:
    with open(filepath, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return data


def write_yaml(filepath: Path, data: Any):
    with open(filepath, "w", encoding="utf-8") as file:
        yaml.safe_dump(data, file)


def read_json(filepath: Path) -> Any:
    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    main()
