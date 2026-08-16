# E-Commerce Backend

Backend API for an e-commerce platform built with FastAPI.

## Project Objective

Build a production-oriented backend for an e-commerce website.

The project is being developed step by step with testing, documentation, and Git version control.

## Technology Stack

- Python
- FastAPI
- Uvicorn
- PostgreSQL
- SQLAlchemy
- Redis
- JWT Authentication
- Alembic
- Docker / Docker Compose

## Current Features

- FastAPI application
- PostgreSQL database connection
- User registration
- Password hashing
- User login
- JWT access token generation
- Invalid credential handling
- Basic API health check
- Swagger API documentation
- PostgreSQL running with Docker Compose

## Running the Application

Activate the virtual environment:

```bash
source venv/bin/activate

*****************************************************************************
Start PostgreSQL:
docker compose up -d db
Run the API:
uvicorn main:app --reload
Swagger

After starting the API, open:
http://127.0.0.1:8000/docs


Swagger is currently the main tool used for manual API testing.

Current API
Health Check
GET /
Register User
POST /users/
Login
POST /users/login

Login returns a JWT access token for valid credentials.

Invalid credentials return HTTP 401.

Testing Status

The following tests have been completed successfully:

PostgreSQL Docker container startup
Python database connection
Database table creation
FastAPI application startup
Health check
User registration
Duplicate email detection
User login
JWT generation
Invalid password handling
Development Workflow

Every development step follows this process:

Implement the required change.
Test the change.
Update documentation.
Review Git changes.
Commit the completed step.
Push the commit to GitHub.
Only then start the next step.
Project State

See PROJECT_STATE.md for the complete current project state and instructions for continuing development in a future session.
