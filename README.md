
TODO List API

A Flask-based REST API for managing tasks with user authentication, validation, and SQLite database persistence.

## Features

- ✅ **User Authentication** (Basic Auth)
- 🔒 **Password Validation** (8+ characters)
- 📝 **Task Management** (CRUD operations)
- ✂️ **Description Validation** (max 16 chars)
- 🗃️ **SQLite Database** with proper schema
- 🛡️ **Secure Password Hashing**

## API Endpoints

### Authentication

| Method | Endpoint   | Description                     |
|--------|------------|---------------------------------|
| POST   | `/register`| Register new user               |

### Tasks

| Method | Endpoint    | Description                     |
|--------|-------------|---------------------------------|
| GET    | `/tasks`    | Get all tasks for current user  |
| POST   | `/tasks`    | Create new task                 |
| GET    | `/tasks/:id`| Get specific task               |
| PUT    | `/tasks/:id`| Update task                     |
| DELETE | `/tasks/:id`| Delete task                     |

## Request/Response Examples

### Register User
```bash
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser", "password":"testpass123"}'
Success Response (201):

json
{
  "message": "User registered successfully",
  "username": "testuser"
}
Create Task
bash
curl -u admin:admin123 -X POST http://localhost:5000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy groceries", "description":"Milk, eggs"}'
Validation Errors (400):

json
{
  "error": "Password must be at least 8 characters"
}
json
{
  "error": "Description cannot exceed 16 characters"
}
Database Schema
Users Table
Column	Type	Description
username	TEXT	Primary key
password_hash	TEXT	Hashed password
Tasks Table
Column	Type	Description
id	INTEGER	Primary key
title	TEXT	Task title (required)
description	TEXT	Optional details
done	BOOLEAN	Completion status
user	TEXT	Owner username (foreign key)
