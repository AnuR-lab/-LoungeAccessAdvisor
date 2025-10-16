"""
Test script for the UserProfileService and updated API client.
This script demonstrates how to use the separated user profile functionality.
"""

import sys
import os

# Add the current directory to the path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from user_profile_service import UserProfileService
from api_client import LoungeAccessClient


def test_user_profile_service():
    """Test the UserProfileService directly."""
    print("=== Testing UserProfileService directly ===")
    
    # Initialize the service
    user_service = UserProfileService()
    
    # Create sample users
    print("Creating sample users...")
    success = user_service.create_sample_users()
    print(f"Sample users created: {success}")
    
    # Test getting a user
    print("\nTesting get_user...")
    user = user_service.get_user("LAA_001")
    if user:
        print(f"Retrieved user: {user}")
    else:
        print("User not found")
    
    # Test getting a non-existent user
    print("\nTesting get_user with non-existent ID...")
    user = user_service.get_user("INVALID_ID")
    if user:
        print(f"Retrieved user: {user}")
    else:
        print("User not found (expected)")


def test_api_client():
    """Test the updated API client."""
    print("\n=== Testing LoungeAccessClient (updated) ===")
    
    # Initialize the client
    client = LoungeAccessClient()
    
    # Test getting a user through the client
    print("Testing get_user through API client...")
    user = client.get_user("LAA_002")
    if user:
        print(f"Retrieved user through client: {user}")
    else:
        print("User not found through client")
    
    # Test creating sample users through the client
    print("\nTesting create_sample_users through API client...")
    success = client.create_sample_users()
    print(f"Sample users created through client: {success}")


def test_crud_operations():
    """Test additional CRUD operations."""
    print("\n=== Testing CRUD Operations ===")
    
    user_service = UserProfileService()
    
    # Test creating a new user
    new_user = {
        "user_id": "LAA_004",
        "name": "Alice Cooper",
        "home_airport": "DEN",
        "memberships": ["delta_skymiles", "priority_pass"]
    }
    
    print("Creating new user...")
    success = user_service.create_user(new_user)
    print(f"User created: {success}")
    
    # Retrieve the new user
    print("Retrieving new user...")
    retrieved_user = user_service.get_user("LAA_004")
    print(f"Retrieved new user: {retrieved_user}")
    
    # Update the user
    print("Updating user...")
    update_data = {
        "name": "Alice Cooper-Smith",
        "memberships": ["delta_skymiles", "priority_pass", "hilton_honors"]
    }
    success = user_service.update_user("LAA_004", update_data)
    print(f"User updated: {success}")
    
    # Retrieve updated user
    print("Retrieving updated user...")
    updated_user = user_service.get_user("LAA_004")
    print(f"Retrieved updated user: {updated_user}")
    
    # Delete the user
    print("Deleting user...")
    success = user_service.delete_user("LAA_004")
    print(f"User deleted: {success}")
    
    # Try to retrieve deleted user
    print("Trying to retrieve deleted user...")
    deleted_user = user_service.get_user("LAA_004")
    print(f"Deleted user (should be None): {deleted_user}")


if __name__ == "__main__":
    print("Starting tests for separated user profile functionality...")
    
    try:
        test_user_profile_service()
        test_api_client() 
        test_crud_operations()
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()