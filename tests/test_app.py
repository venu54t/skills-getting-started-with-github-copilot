"""
FastAPI backend tests for Mergington High School Activities API
Uses AAA (Arrange-Act-Assert) testing pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Fixture to provide a test client for the FastAPI app"""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities"""
        # Arrange
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Swimming Club",
            "Art Studio",
            "Drama Club",
            "Science Club",
            "Robotics Club",
        ]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == len(expected_activities)
        for activity_name in expected_activities:
            assert activity_name in activities

    def test_get_activities_returns_correct_structure(self, client):
        """Test that each activity has the correct data structure"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities = response.json()
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_adds_new_participant(self, client):
        """Test that a new participant can sign up for an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "new_student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

    def test_signup_rejects_duplicate_participant(self, client):
        """Test that a student cannot sign up twice for the same activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "already signed up" in result["detail"].lower()

    def test_signup_rejects_nonexistent_activity(self, client):
        """Test that signup fails for an activity that doesn't exist"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "not found" in result["detail"].lower()


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_removes_participant(self, client):
        """Test that a participant can be unregistered from an activity"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]

    def test_unregister_nonexistent_participant_returns_404(self, client):
        """Test that unregistering a non-participant returns 404"""
        # Arrange
        activity_name = "Chess Club"
        email = "nonexistent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "not found" in result["detail"].lower()

    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        """Test that unregistering from a non-existent activity returns 404"""
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "michael@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "not found" in result["detail"].lower()


class TestIntegrationScenarios:
    """Integration tests combining multiple operations"""

    def test_signup_and_unregister_flow(self, client):
        """Test complete flow of signing up and then unregistering"""
        # Arrange
        activity_name = "Programming Class"
        email = "integration_test@mergington.edu"

        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            params={"email": email},
        )

        # Assert - Sign up successful
        assert signup_response.status_code == 200

        # Verify participant is in the list
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]

        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister?email={email}",
            params={"email": email},
        )

        # Assert - Unregister successful
        assert unregister_response.status_code == 200

        # Verify participant is removed
        final_activities_response = client.get("/activities")
        final_activities = final_activities_response.json()
        assert email not in final_activities[activity_name]["participants"]

    def test_multiple_participants_signup_and_unregister(self, client):
        """Test that multiple participants can sign up and be managed independently"""
        # Arrange
        activity_name = "Art Studio"
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu",
        ]

        # Act - Multiple sign-ups
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}",
                params={"email": email},
            )
            assert response.status_code == 200

        # Assert - All are signed up
        activities_response = client.get("/activities")
        activities = activities_response.json()
        for email in emails:
            assert email in activities[activity_name]["participants"]

        # Act - Remove middle participant
        middle_response = client.delete(
            f"/activities/{activity_name}/unregister?email={emails[1]}",
            params={"email": emails[1]},
        )

        # Assert - Middle participant removed, others remain
        assert middle_response.status_code == 200
        final_activities_response = client.get("/activities")
        final_activities = final_activities_response.json()
        assert emails[0] in final_activities[activity_name]["participants"]
        assert emails[1] not in final_activities[activity_name]["participants"]
        assert emails[2] in final_activities[activity_name]["participants"]