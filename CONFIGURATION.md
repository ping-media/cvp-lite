# Configuration Guide

## Overview

This project has been simplified to remove AI features and .env file dependencies. The application now only requires MongoDB configuration.

## Required Configuration

### MongoDB Configuration

The application requires a MongoDB connection string. You can set this in one of two ways:

#### Option 1: Environment Variable (Recommended)

Set the `MONGODB_URI` environment variable:

```bash
export MONGODB_URI="mongodb+srv://your_username:your_password@your_cluster.mongodb.net/recipe_db?retryWrites=true&w=majority"
```

#### Option 2: Direct Configuration

Modify the `app/config.py` file directly:

```python
class Settings:
    # MongoDB Configuration
    MONGODB_URI: str = "mongodb+srv://your_username:your_password@your_cluster.mongodb.net/recipe_db?retryWrites=true&w=majority"
    MONGODB_DATABASE: str = "ypd_db"
    MONGODB_COLLECTION: str = "users"

    # FastAPI Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8001

    # Application Configuration
    APP_NAME: str = "CVP Lite"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
```

## Optional Configuration

### Server Configuration

You can optionally set these environment variables:

- `HOST`: Server host (default: "0.0.0.0")
- `PORT`: Server port (default: 8001)

Example:

```bash
export HOST="127.0.0.1"
export PORT="8001"
```

## Removed Features

The following configurations are no longer needed as AI features have been removed:

- ❌ `PINECONE_API_KEY` - Pinecone vector database
- ❌ `PINECONE_INDEX_NAME` - Pinecone index name
- ❌ `OPENAI_API_KEY` - OpenAI API key
- ❌ `.env` files - Environment file loading

## Running the Application

1. **Set MongoDB URI** (see options above)
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python main.py
   ```

The application will start on the configured host and port (default: http://0.0.0.0:8001).

## Available Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /user/setup` - User profile setup
- `GET /user/` - Get all users
- `GET /user/{user_id}` - Get specific user
- `POST /user/` - Create/update user
- `DELETE /user/{user_id}` - Delete user
- `POST /cvp_lite/questions` - Get static questions

## Database Schema

The application uses MongoDB with the following structure:

```javascript
{
  "student_id": "string",
  "name": "string",
  "grade": "string",
  "school_name": "string",
  "email": "string",
  "phone": "string",
  "city": "string",
  "country": "string",
  "subject_stream": "string",
  "hobbies_and_passions": ["string"],
  "dream_job": "string",
  "future_self_info": "string",
  "cvp_lite": {},
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## Troubleshooting

### MongoDB Connection Issues

- Ensure your MongoDB URI is correct
- Check if your MongoDB instance is running
- Verify network connectivity to your MongoDB cluster

### Port Already in Use

- Change the PORT environment variable
- Or kill the process using the current port

### Missing Dependencies

- Run `pip install -r requirements.txt`
- Ensure you're using Python 3.8+
