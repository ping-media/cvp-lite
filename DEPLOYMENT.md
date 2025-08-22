# Deployment Guide

## Overview

This guide provides commands to deploy the CVP Lite application on a server using Docker.

## Prerequisites

- Docker installed on the server
- Docker Compose installed (optional, for easier deployment)
- Git (to clone the repository)

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Clone the repository**:

   ```bash
   git clone <your-repository-url>
   cd cvp-lite
   ```

2. **Build and run with Docker Compose**:

   ```bash
   docker-compose up -d
   ```

3. **Check if the application is running**:

   ```bash
   docker-compose ps
   curl http://localhost:8001/health
   ```

4. **View logs**:

   ```bash
   docker-compose logs -f cvp-lite
   ```

5. **Stop the application**:
   ```bash
   docker-compose down
   ```

### Option 2: Using Docker directly

1. **Clone the repository**:

   ```bash
   git clone <your-repository-url>
   cd cvp-lite
   ```

2. **Build the Docker image**:

   ```bash
   docker build -t cvp-lite .
   ```

3. **Run the container**:

   ```bash
   docker run -d \
     --name cvp-lite-api \
     -p 8001:8001 \
     -e HOST=0.0.0.0 \
     -e PORT=8001 \
     --restart unless-stopped \
     cvp-lite
   ```

4. **Check if the application is running**:

   ```bash
   docker ps
   curl http://localhost:8001/health
   ```

5. **View logs**:

   ```bash
   docker logs -f cvp-lite-api
   ```

6. **Stop the container**:
   ```bash
   docker stop cvp-lite-api
   docker rm cvp-lite-api
   ```

## Production Deployment

### Using Docker Compose with Production Settings

1. **Create a production docker-compose file**:

   ```bash
   cp docker-compose.yml docker-compose.prod.yml
   ```

2. **Edit docker-compose.prod.yml** to add production settings:

   ```yaml
   version: "3.8"

   services:
     cvp-lite:
       build: .
       container_name: cvp-lite-api
       ports:
         - "8001:8001"
       environment:
         - HOST=0.0.0.0
         - PORT=8001
       restart: unless-stopped
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
         interval: 30s
         timeout: 10s
         retries: 3
         start_period: 40s
       # Add resource limits for production
       deploy:
         resources:
           limits:
             memory: 512M
             cpus: "0.5"
           reservations:
             memory: 256M
             cpus: "0.25"
   ```

3. **Deploy with production settings**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Using Nginx as Reverse Proxy (Optional)

1. **Create nginx.conf**:

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

2. **Run with nginx**:

   ```bash
   # Start the application
   docker-compose up -d

   # Start nginx (assuming nginx is installed)
   sudo nginx -c /path/to/your/nginx.conf
   ```

## Monitoring and Maintenance

### Check Application Status

```bash
# Check if container is running
docker ps | grep cvp-lite

# Check health endpoint
curl http://localhost:8001/health

# Check application logs
docker logs cvp-lite-api
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Backup and Restore

```bash
# Since this is a stateless application, no data backup is needed
# Just ensure your code is in version control
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs cvp-lite-api

# Check if port is already in use
netstat -tulpn | grep 8001

# Kill process using port 8001
sudo kill -9 $(lsof -t -i:8001)
```

### Health Check Failing

```bash
# Check if application is responding
curl -v http://localhost:8001/health

# Check container resources
docker stats cvp-lite-api
```

### Memory Issues

```bash
# Check memory usage
docker stats cvp-lite-api

# Restart container if needed
docker restart cvp-lite-api
```

## Environment Variables

The application supports the following environment variables:

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8001)

## API Endpoints

Once deployed, the following endpoints will be available:

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /cvp_lite/questions` - Get static questions

## Example Usage

```bash
# Test the questions endpoint
curl -X POST "http://your-server:8001/cvp_lite/questions" \
  -H "Content-Type: application/json" \
  -d '{"page": 1, "page_size": 10}'
```
