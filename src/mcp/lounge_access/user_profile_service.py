"""
User Profile Service for DynamoDB operations.
Handles all user profile related database operations.
"""

import json
import boto3
from botocore.exceptions import ClientError


class UserProfileService:
    """
    Service class for managing user profiles in DynamoDB.
    """
    
    def __init__(self, table_name='UserProfile'):
        """
        Initialize the UserProfileService.
        
        Args:
            table_name (str): Name of the DynamoDB table (default: 'UserProfile')
        """
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = table_name
        self.user_profile_table = self.dynamodb.Table(table_name)
        # Ensure table exists
        self._ensure_table_exists()

    def get_user(self, user_id: str):
        """
        Retrieves user information by user_id from DynamoDB UserProfile table.
        
        Args:
            user_id (str): The unique identifier for the user
            
        Returns:
            dict: User information containing user_id, name, home_airport, and memberships
                 Returns None if user not found or error occurs
        """
        try:
            # Query DynamoDB UserProfile table
            response = self.user_profile_table.get_item(
                Key={
                    'user_id': user_id
                }
            )
            
            # Check if item was found
            if 'Item' in response:
                user_item = response['Item']
                
                # Return user data in the expected format
                return {
                    "user_id": user_item.get('user_id'),
                    "name": user_item.get('name'),
                    "home_airport": user_item.get('home_airport'),
                    "memberships": user_item.get('memberships', [])
                }
            else:
                # User not found in DynamoDB
                return None
                
        except ClientError as e:
            # Log the error and return None
            print(f"Error retrieving user {user_id} from DynamoDB: {e.response['Error']['Message']}")
            return None
        except Exception as e:
            # Handle any other unexpected errors
            print(f"Unexpected error retrieving user {user_id}: {str(e)}")
            return None

    def create_sample_users(self):
        """
        Creates sample users in the DynamoDB UserProfile table for testing.
        This method can be used to populate the table with initial data.
        
        Returns:
            bool: True if successful, False otherwise
        """
        sample_users = [
            {
                "user_id": "LAA_001",
                "name": "John Doe",
                "home_airport": "JFK",
                "memberships": ["priority_pass", "amex_platinum"]
            },
            {
                "user_id": "LAA_002",
                "name": "Jane Smith",
                "home_airport": "LAX",
                "memberships": ["chase_sapphire", "priority_pass"]
            },
            {
                "user_id": "LAA_003",
                "name": "Mike Johnson",
                "home_airport": "ORD",
                "memberships": ["amex_gold", "united_club"]
            }
        ]
        
        try:
            # Insert sample users into DynamoDB
            with self.user_profile_table.batch_writer() as batch:
                for user in sample_users:
                    batch.put_item(Item=user)
            
            print("Successfully created sample users in UserProfile table")
            return True
            
        except ClientError as e:
            print(f"Error creating sample users: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            print(f"Unexpected error creating sample users: {str(e)}")
            return False

    def create_user(self, user_data):
        """
        Creates a new user in the DynamoDB UserProfile table.
        
        Args:
            user_data (dict): User information containing user_id, name, home_airport, and memberships
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.user_profile_table.put_item(Item=user_data)
            print(f"Successfully created user {user_data.get('user_id')}")
            return True
            
        except ClientError as e:
            print(f"Error creating user: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            print(f"Unexpected error creating user: {str(e)}")
            return False

    def update_user(self, user_id, update_data):
        """
        Updates an existing user in the DynamoDB UserProfile table.
        
        Args:
            user_id (str): The unique identifier for the user
            update_data (dict): Dictionary of attributes to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Build update expression
            update_expression = "SET "
            expression_attribute_values = {}
            
            for key, value in update_data.items():
                if key != 'user_id':  # Don't update the primary key
                    update_expression += f"{key} = :{key}, "
                    expression_attribute_values[f":{key}"] = value
            
            # Remove trailing comma and space
            update_expression = update_expression.rstrip(', ')
            
            if expression_attribute_values:
                self.user_profile_table.update_item(
                    Key={'user_id': user_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values
                )
                print(f"Successfully updated user {user_id}")
                return True
            else:
                print("No valid update data provided")
                return False
                
        except ClientError as e:
            print(f"Error updating user {user_id}: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            print(f"Unexpected error updating user {user_id}: {str(e)}")
            return False

    def delete_user(self, user_id):
        """
        Deletes a user from the DynamoDB UserProfile table.
        
        Args:
            user_id (str): The unique identifier for the user
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.user_profile_table.delete_item(
                Key={'user_id': user_id}
            )
            print(f"Successfully deleted user {user_id}")
            return True
            
        except ClientError as e:
            print(f"Error deleting user {user_id}: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            print(f"Unexpected error deleting user {user_id}: {str(e)}")
            return False

    def _ensure_table_exists(self):
        """
        Ensures the UserProfile DynamoDB table exists, creates it if it doesn't.
        """
        try:
            # Try to load the table to check if it exists
            self.user_profile_table.load()
            print(f"{self.table_name} table already exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Table doesn't exist, create it
                print(f"{self.table_name} table not found, creating it...")
                self._create_user_profile_table()
            else:
                print(f"Error checking table existence: {e.response['Error']['Message']}")
        except Exception as e:
            print(f"Unexpected error checking table: {str(e)}")

    def _create_user_profile_table(self):
        """
        Creates the UserProfile DynamoDB table with the required schema.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create the DynamoDB table
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'user_id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'user_id',
                        'AttributeType': 'S'  # String
                    }
                ],
                BillingMode='PAY_PER_REQUEST'  # On-demand billing
            )
            
            # Wait for table to be created
            print(f"Creating {self.table_name} table...")
            table.wait_until_exists()
            print(f"{self.table_name} table created successfully")
            
            # Update the table reference
            self.user_profile_table = table
            
            return True
            
        except ClientError as e:
            print(f"Error creating {self.table_name} table: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            print(f"Unexpected error creating table: {str(e)}")
            return False