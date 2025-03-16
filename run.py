import subprocess

command = [
    "kedro",
    "docker",
    "cmd",
    "--docker-args=--cpus=4.0 --privileged -v ./key.json:/home/kedro_docker/key.json -e GOOGLE_APPLICATION_CREDENTIALS=/home/kedro_docker/key.json",
    "kedro",
    "run",
    "--pipeline=coastline_cfmask_landsat_deepwatermap",
]


subprocess.run(
    'kedro docker cmd --docker-args="--cpus=4.0 --privileged -v ./key.json:/home/kedro_docker/key.json -e GOOGLE_APPLICATION_CREDENTIALS=/home/kedro_docker/key.json" kedro run --pipeline=coastline_cfmask_landsat_deepwatermap"',
    shell=True,
    check=True,
)
