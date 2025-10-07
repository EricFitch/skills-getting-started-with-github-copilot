"""
Tests for the High School Management System API.
Tests cover all endpoints: root redirect, activities listing, signup, and unregister.
"""
import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that root path redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_200(self, client):
        """Test that getting activities returns 200 OK."""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that activities endpoint returns a dictionary."""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_activities_has_required_fields(self, client):
        """Test that each activity has required fields."""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, details in data.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)
    
    def test_get_activities_includes_default_activities(self, client):
        """Test that default activities are present."""
        response = client.get("/activities")
        data = response.json()
        
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds participant to the list."""
        email = "teststudent@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
    
    def test_signup_duplicate_fails(self, client):
        """Test that signing up twice for same activity fails."""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for non-existent activity fails."""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_existing_participants_unchanged(self, client):
        """Test that existing participants remain after new signup."""
        response = client.get("/activities")
        original_participants = response.json()["Chess Club"]["participants"].copy()
        
        # Add new participant
        client.post("/activities/Chess Club/signup?email=newperson@mergington.edu")
        
        # Check original participants are still there
        response = client.get("/activities")
        current_participants = response.json()["Chess Club"]["participants"]
        
        for participant in original_participants:
            assert participant in current_participants


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity."""
        # Chess Club has michael@mergington.edu by default
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes participant from the list."""
        email = "michael@mergington.edu"
        
        # Verify participant exists
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Chess Club/unregister?email={email}")
        
        # Verify participant was removed
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
    
    def test_unregister_not_signed_up_fails(self, client):
        """Test that unregistering when not signed up fails."""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregistering from non-existent activity fails."""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_other_participants_unchanged(self, client):
        """Test that other participants remain after one unregisters."""
        # Chess Club has michael and daniel by default
        client.delete("/activities/Chess Club/unregister?email=michael@mergington.edu")
        
        # Check daniel is still there
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in participants
        assert "michael@mergington.edu" not in participants


class TestIntegrationScenarios:
    """Integration tests for complete user flows."""
    
    def test_signup_and_unregister_flow(self, client):
        """Test complete flow of signing up and then unregistering."""
        email = "flowtest@mergington.edu"
        activity = "Programming Class"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify count increased
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count + 1
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify count back to original
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count
        assert email not in response.json()[activity]["participants"]
    
    def test_multiple_signups_different_activities(self, client):
        """Test that a student can sign up for multiple different activities."""
        email = "multisport@mergington.edu"
        
        # Sign up for multiple activities
        activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in activities:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify student is in all activities
        response = client.get("/activities")
        data = response.json()
        for activity in activities:
            assert email in data[activity]["participants"]
