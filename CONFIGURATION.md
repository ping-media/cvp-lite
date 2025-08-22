# Configuration Guide

## Overview

This project has been simplified to remove AI features, .env file dependencies, and database requirements. The application now uses in-memory storage and requires no external configuration.

## Required Configuration

**No configuration required!** The application uses in-memory storage and works out of the box.

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

The following configurations are no longer needed:

- ❌ `MONGODB_URI` - MongoDB database connection
- ❌ `PINECONE_API_KEY` - Pinecone vector database
- ❌ `PINECONE_INDEX_NAME` - Pinecone index name
- ❌ `OPENAI_API_KEY` - OpenAI API key
- ❌ `.env` files - Environment file loading

## Running the Application

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the application**:
   ```bash
   python main.py
   ```

The application will start on the configured host and port (default: http://0.0.0.0:8001).

## Available Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /cvp_lite/questions` - Get static questions

## Data Storage

**No data storage required!** The application is completely stateless and returns static questions without any user management or data persistence.

## Troubleshooting

### Port Already in Use

- Change the PORT environment variable
- Or kill the process using the current port

### Missing Dependencies

- Run `pip install -r requirements.txt`
- Ensure you're using Python 3.8+

### Data Loss

- No data storage means no data loss concerns
- The application is completely stateless
