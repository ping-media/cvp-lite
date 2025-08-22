from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
from typing import Optional, Dict, Any, List
from .config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.connect()
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            if not settings.MONGODB_URI:
                raise ValueError("MONGODB_URI not configured")
            
            self.client = MongoClient(settings.MONGODB_URI)
            # Test the connection
            self.client.admin.command('ping')
            
            self.db = self.client[settings.MONGODB_DATABASE]
            self.collection = self.db[settings.MONGODB_COLLECTION]
            
            logger.info("Successfully connected to MongoDB")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            raise
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile by student_id"""
        try:
            user = self.collection.find_one({"student_id": user_id})
            
            # Handle migration from favorite_food to favorite_foods
            if user and 'favorite_food' in user and 'favorite_foods' not in user:
                user['favorite_foods'] = [user['favorite_food']]
                del user['favorite_food']
                # Update the user in database
                self.create_or_update_user(user)
                logger.info(f"Migrated user {user_id} from favorite_food to favorite_foods")
            
            return user
        except Exception as e:
            logger.error(f"Error retrieving user {user_id}: {e}")
            return None
    
    def create_or_update_user(self, user_data: Dict[str, Any]) -> bool:
        """Create or update user profile"""
        try:
            # Add timestamps
            now = datetime.utcnow()
            user_data["updated_at"] = now
            
            # Use upsert to create or update
            result = self.collection.update_one(
                {"student_id": user_data["student_id"]},
                {
                    "$set": user_data,
                    "$setOnInsert": {"created_at": now}
                },
                upsert=True
            )
            
            logger.info(f"User {user_data['student_id']} {'created' if result.upserted_id else 'updated'}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating/updating user: {e}")
            return False
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Retrieve all user profiles"""
        try:
            users = list(self.collection.find({}))
            
            # Handle migration for all users
            migrated_count = 0
            for user in users:
                if 'favorite_food' in user and 'favorite_foods' not in user:
                    user['favorite_foods'] = [user['favorite_food']]
                    del user['favorite_food']
                    # Update the user in database
                    self.create_or_update_user(user)
                    migrated_count += 1
            
            if migrated_count > 0:
                logger.info(f"Migrated {migrated_count} users from favorite_food to favorite_foods")
            
            return users
        except Exception as e:
            logger.error(f"Error retrieving all users: {e}")
            return []
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user by student_id. Returns True if a document was deleted."""
        try:
            result = self.collection.delete_one({"student_id": user_id})
            if result.deleted_count > 0:
                logger.info(f"Deleted user {user_id}")
                return True
            logger.warning(f"No user deleted for id {user_id} (not found)")
            return False
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    # def store_conversation_history(self, user_id: str, recipe_data: Dict[str, Any], conversation_id: str = None) -> str:
    #     """
    #     Store recipe conversation history in MongoDB
    #     
    #     Args:
    #         user_id (str): User's student ID
    #         recipe_data (Dict[str, Any]): Generated recipe data
    #         conversation_id (str, optional): Existing conversation ID for grouping
    #         
    #     Returns:
    #         str: Conversation ID (new or existing)
    #     """
    #     # Removed AI features - conversation history was for recipe generation
    #     pass
    
    # def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    #     """
    #     Retrieve conversation history for a user
    #     
    #     Args:
    #         user_id (str): User's student ID
    #         limit (int): Maximum number of conversations to retrieve
    #         
    #     Returns:
    #         List[Dict[str, Any]]: List of conversation entries
    #     """
    #     # Removed AI features - conversation history was for recipe generation
    #     pass
    
    # def get_conversation_by_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
    #     """
    #     Retrieve a specific conversation by ID
    #         
    #     Args:
    #         conversation_id (str): Conversation ID
    #             
    #     Returns:
    #         Optional[Dict[str, Any]]: Conversation data or None
    #     """
    #     # Removed AI features - conversation history was for recipe generation
    #     pass
    
    # def get_user_conversations_summary(self, user_id: str) -> Dict[str, Any]:
    #     """
    #     Get summary of user's conversation history
    #         
    #     Args:
    #         user_id (str): User's student ID
    #             
    #     Returns:
    #         List[Dict[str, Any]]: Summary including total conversations, recent recipes, etc.
    #     """
    #     # Removed AI features - conversation history was for recipe generation
    #     pass
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Create global MongoDB instance
mongodb = MongoDB() 