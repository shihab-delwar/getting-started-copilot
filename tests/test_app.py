import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = copy.deepcopy(app_module.activities)
    yield
    app_module.activities = original_activities


def test_get_activities_returns_payload():
    # Arrange
    expected_keys = ["Chess Club", "Programming Class", "Gym Class"]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    for key in expected_keys:
        assert key in data


def test_root_redirects_to_static_page():
    # Arrange

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_signup_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "signup-test@mergington.edu"
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.post(f"/activities/{activity_path}/signup?email={quote(email, safe='')}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}

    activity = client.get("/activities").json()[activity_name]
    assert email in activity["participants"]


def test_duplicate_signup_returns_400():
    # Arrange
    activity_name = "Programming Class"
    email = "duplicate-test@mergington.edu"
    activity_path = quote(activity_name, safe="")

    client.post(f"/activities/{activity_path}/signup?email={quote(email, safe='')}")

    # Act
    response = client.post(f"/activities/{activity_path}/signup?email={quote(email, safe='')}")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"

    participants = client.get("/activities").json()[activity_name]["participants"]
    assert participants.count(email) == 1


def test_remove_participant():
    # Arrange
    activity_name = "Gym Class"
    email = "remove-test@mergington.edu"
    activity_path = quote(activity_name, safe="")

    client.post(f"/activities/{activity_path}/signup?email={quote(email, safe='')}")

    # Act
    response = client.delete(f"/activities/{activity_path}/participants?email={quote(email, safe='')}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}

    participants = client.get("/activities").json()[activity_name]["participants"]
    assert email not in participants


def test_remove_missing_participant_returns_404():
    # Arrange
    activity_name = "Drama Club"
    email = "missing-test@mergington.edu"
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.delete(f"/activities/{activity_path}/participants?email={quote(email, safe='')}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
