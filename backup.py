import yaml
import subprocess
import os
import tarfile
import shutil
from datetime import datetime

with open("config.yml", "r") as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

docker_dir = config["docker-dir"]
target_backup_dir = config["target-dir"]

if not os.path.isdir(target_backup_dir):
    print(f"Target '{target_backup_dir}' directory is not valid.")
    exit(1)

DATETIME = datetime.now().strftime(format="%Y%m%dT%H%M")
COMPRESS = config["options"]["compress"]
COMPRESS_LEVEL = int(config["options"]["compress-level"])
RETENTION = int(config["options"]["retention"])

if COMPRESS not in ["gz", "xz"]:
    raise ValueError("Compression setting must be gz or xz")

if not (1 <= COMPRESS_LEVEL <= 9):
    raise ValueError("Compression level has to be between 1 to 9.")

if not RETENTION >= 1:
    raise ValueError("Retention has to be at least 1 day.")

target_dir = os.path.join(target_backup_dir, DATETIME)
os.mkdir(target_dir)


def backup_docker_dir(docker_dir: str, ignore: list[str], target_dir: str):
    if not os.path.isdir(docker_dir):
        raise FileNotFoundError(f"No such file or directory: {docker_dir}")

    target_dir = os.path.join(target_dir, "docker")
    os.mkdir(target_dir)
    print(f"Backup up Docker Compose stacks in {docker_dir}")

    stacks = os.listdir(docker_dir)

    for stack in stacks:
        stack_path = os.path.join(docker_dir, stack)
        if stack in ignore:
            print(f"Ignoring {stack}")
            continue
        print(f"Shutting down {stack}.")
        
        subprocess.run(["docker", "compose", "down"], cwd=stack_path)

        print(f"Backing up {stack}.")

        backup_path = os.path.join(target_dir, f"{stack}.tar.{COMPRESS}")
        print(backup_path)
        with tarfile.open(backup_path, f"w:{COMPRESS}", compresslevel=COMPRESS_LEVEL) as tar:
            tar.add(stack_path)

        print(f"Starting up {stack}")

        subprocess.run(["docker", "compose", "up", "-d"], cwd=stack_path)


if docker_dir:
    backup_docker_dir(docker_dir, config["docker-backup-ignore"], target_dir)
else:
    print("No docker directory given, skipping.")


for dir_name, path in config["backup-dirs"].items():
    path = os.path.expanduser(path)
    if not os.path.isdir(path):
        raise FileNotFoundError(f"{path} is not a directory.")

    backup_path = os.path.join(target_dir, f"{dir_name}.tar.{COMPRESS}")

    with tarfile.open(backup_path, f"w:{COMPRESS}") as tar:
        tar.add(path)


for file in os.listdir(target_backup_dir):
    path = os.path.join(target_dir, file)
    backup_time = datetime.strptime(file, "%Y%m%dT%H%M")

    current_time = datetime.now()

    time_difference = current_time - backup_time

    if time_difference.days > 1:
        print(f"Backup from {backup_time} exceeds retention. Deleting it.")
        shutil.rmtree(path)

