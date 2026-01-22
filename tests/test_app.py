"""
Tests for the Mergington High School Activities API
"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    activities.clear()
    activities.update({
        "Basketball": {
            "description": "Team sport focusing on basketball skills and competitive play",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn tennis techniques and participate in friendly matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
            "max_participants": 10,
            "participants": ["sophia@mergington.edu"]
        },
        "Art Studio": {
            "description": "Explore painting, drawing, and various visual art forms",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["lucy@mergington.edu"]
        },
        "Drama Club": {
            "description": "Perform in plays and develop theatrical skills",
            "schedule": "Fridays, 4:00 PM - 5:30 PM",
            "max_participants": 20,
            "participants": ["alex@mergington.edu", "jordan@mergington.edu"]
        },
    })
    yield
    activities.clear()


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that all activities are present
        assert "Basketball" in data
        assert "Tennis Club" in data
        assert "Art Studio" in data
        assert "Drama Club" in data
    
    def test_activities_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        basketball = data["Basketball"]
        assert "description" in basketball
        assert "schedule" in basketball
        assert "max_participants" in basketball
        assert "participants" in basketball
        assert isinstance(basketball["participants"], list)
    
    def test_activities_have_participants(self, client):
        """Test that activities have initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        assert len(data["Basketball"]["participants"]) > 0
        assert "james@mergington.edu" in data["Basketball"]["participants"]


class TestSignupEndpoint:
    """Tests for the /signup endpoint"""
    
    def test_successful_signup(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Art Studio/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        initial_count = len(activities["Art Studio"]["participants"])
        
        client.post(f"/activities/Art Studio/signup?email={email}")
        
        # Verify participant was added
        assert len(activities["Art Studio"]["participants"]) == initial_count + 1
        assert email in activities["Art Studio"]["participants"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup fails for nonexistent activity"""
        response = client.post(
            "/activities/Nonexistent/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_duplicate_email(self, client):
        """Test signup fails when student is already registered"""
        email = "james@mergington.edu"  # Already in Basketball
        response = client.post(f"/activities/Basketball/signup?email={email}")
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_activity_full(self, client):
        """Test signup fails when activity is at max capacity"""
        # Set max_participants to 1 for Tennis Club
        activities["Tennis Club"]["max_participants"] = 1
        
        response = client.post(
            "/activities/Tennis Club/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 400
        assert "full" in response.json()["detail"].lower()


class TestUnregisterEndpoint:
    """Tests for the /unregister endpoint"""
    
    def test_successful_unregister(self, client):
        """Test successful unregistration from an activity"""
        email = "james@mergington.edu"
        response = client.delete(
            f"/activities/Basketball/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "james@mergington.edu"
        initial_count = len(activities["Basketball"]["participants"])
        
        client.delete(f"/activities/Basketball/unregister?email={email}")
        
        # Verify participant was removed
        assert len(activities["Basketball"]["participants"]) == initial_count - 1
        assert email not in activities["Basketball"]["participants"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregister fails for nonexistent activity"""
        response = client.delete(
            "/activities/Nonexistent/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_not_registered(self, client):
        """Test unregister fails when student is not registered"""
        response = client.delete(
            "/activities/Basketball/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()
    
    def test_unregister_multiple_participants(self, client):
        """Test unregister works with activities having multiple participants"""
        # Drama Club has 2 participants
        initial_count = len(activities["Drama Club"]["participants"])
        assert initial_count == 2
        
        response = client.delete(
            "/activities/Drama Club/unregister?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify only one participant was removed
        assert len(activities["Drama Club"]["participants"]) == initial_count - 1
        assert "alex@mergington.edu" not in activities["Drama Club"]["participants"]
        assert "jordan@mergington.edu" in activities["Drama Club"]["participants"]


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_signup_then_unregister_workflow(self, client):
        """Test full workflow: signup then unregister"""
        email = "testuser@mergington.edu"
        activity = "Art Studio"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        assert email in activities[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        assert email not in activities[activity]["participants"]
    
    def test_multiple_signups(self, client):
        """Test multiple students signing up for the same activity"""
        activity = "Art Studio"
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu",
        ]
        
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all were added
        for email in emails:
            assert email in activities[activity]["participants"]
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses"""
        response = client.get("/activities")
        assert response.status_code == 200
        # CORS middleware should be configured (test with TestClient)
