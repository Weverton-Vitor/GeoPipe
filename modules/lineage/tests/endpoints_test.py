from fastapi.testclient import TestClient
from main import app
from pathlib import Path

client = TestClient(app)


def test_list_runs():
    response = client.get("/runs/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 2
    assert response.json() == [
        "argemiro_reservatorio",
        "engenheiro_avidos_reservatorio",
    ]


def test_get_volume_temporal_serie():
    response = client.get(
        "/timeseries/volume?segmentation_method=watnet&run_name=argemiro_reservatorio"
    )
    # print(response.json())

    import json

    with open(
        f"{Path(__file__).parent.resolve()}/data/volume_argemiro.json",
        "r",
    ) as f:
        expected_response = json.load(f)

    assert response.json() == expected_response
    assert response.status_code == 200


def test_get_image():
    response = client.get(
        "/images/get_for_month?run_name=argemiro_reservatorio&year=2020&month=06"
    )
    print(response.json())

    assert response.status_code == 200
