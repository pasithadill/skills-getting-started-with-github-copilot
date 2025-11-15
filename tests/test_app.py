"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities(client):
    """Reset activities to initial state before each test"""
    # Get activities and reset participants
    response = client.get("/activities")
    activities = response.json()
    
    # We'll work with a fresh state in each test
    yield


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_activities(self, client):
        """Test that activities include expected ones"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Basketball Team",
            "Art Studio",
            "Drama Club"
        ]
        
        for activity in expected_activities:
            assert activity in activities
    
    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"{activity_name} missing {field}"
    
    def test_participants_is_list(self, client):
        """Test that participants field is a list"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert isinstance(activity_data["participants"], list), \
                f"{activity_name} participants is not a list"


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant_returns_200(self, client):
        """Test signing up a new participant returns 200"""
        response = client.post(
            "/activities/Tennis Club/signup?email=newstudent1@mergington.edu"
        )
        assert response.status_code == 200
    
    def test_signup_new_participant_returns_success_message(self, client):
        """Test signup returns appropriate message"""
        response = client.post(
            "/activities/Tennis Club/signup?email=newstudent2@mergington.edu"
        )
        data = response.json()
        assert "message" in data
        assert "newstudent2@mergington.edu" in data["message"]
        assert "Tennis Club" in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant"""
        email = "teststudent@mergington.edu"
        
        # Signup
        client.post(f"/activities/Science Club/signup?email={email}")
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Science Club"]["participants"]
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test signup to nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_duplicate_participant_returns_400(self, client):
        """Test signing up same student twice returns 400"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(f"/activities/Debate Team/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/Debate Team/signup?email={email}")
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant_returns_200(self, client):
        """Test unregistering an existing participant returns 200"""
        email = "unregister@mergington.edu"
        
        # First signup
        client.post(f"/activities/Programming Class/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Programming Class/unregister?email={email}"
        )
        assert response.status_code == 200
    
    def test_unregister_returns_success_message(self, client):
        """Test unregister returns appropriate message"""
        email = "unregister2@mergington.edu"
        
        # First signup
        client.post(f"/activities/Programming Class/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Programming Class/unregister?email={email}"
        )
        data = response.json()
        assert "message" in data
        assert email in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "remove@mergington.edu"
        
        # Signup
        client.post(f"/activities/Drama Club/signup?email={email}")
        
        # Verify participant was added
        response = client.get("/activities")
        assert email in response.json()["Drama Club"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Drama Club/unregister?email={email}")
        
        # Verify participant was removed
        response = client.get("/activities")
        assert email not in response.json()["Drama Club"]["participants"]
    
    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Test unregister from nonexistent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
    
    def test_unregister_nonexistent_participant_returns_400(self, client):
        """Test unregistering nonexistent participant returns 400"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()


class TestRootRedirect:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static files"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
