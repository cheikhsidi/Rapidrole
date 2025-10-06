# Authentication Guide

## Overview

The Job Copilot API uses JWT (JSON Web Tokens) for authentication. This provides a secure, stateless authentication mechanism.

## Features

- **Secure password hashing** using bcrypt
- **JWT access tokens** (30 minutes expiry)
- **JWT refresh tokens** (7 days expiry)
- **Bearer token authentication**
- **Protected and optional auth endpoints**

## Authentication Endpoints

### Register a New User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Login

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Refresh Token

```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Get Current User

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "account_tier": "free"
}
```

### Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

### Verify Email

```http
GET /api/v1/auth/verify-email?token=<verification_token>
```

**Response:**
```json
{
  "message": "Email verified successfully"
}
```

### Resend Verification Email

```http
POST /api/v1/auth/resend-verification
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Verification email sent"
}
```

### Forgot Password

```http
POST /api/v1/auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "message": "If the email exists, a password reset link has been sent"
}
```

### Reset Password

```http
POST /api/v1/auth/reset-password
Content-Type: application/json

{
  "token": "<reset_token>",
  "new_password": "NewSecurePassword123!"
}
```

**Response:**
```json
{
  "message": "Password reset successfully"
}
```

### Change Password (Authenticated)

```http
POST /api/v1/auth/change-password
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePassword123!"
}
```

**Response:**
```json
{
  "message": "Password changed successfully"
}
```

## Using Authentication in Your Code

### Protecting Endpoints (Required Auth)

```python
from fastapi import APIRouter, Depends
from api.auth import get_current_user
from db.models import User

router = APIRouter()

@router.get("/protected")
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    """This endpoint requires authentication."""
    return {
        "message": f"Hello {current_user.full_name}",
        "user_id": str(current_user.id)
    }
```

### Optional Authentication

```python
from typing import Optional
from fastapi import APIRouter, Depends
from api.auth import get_current_user_optional
from db.models import User

router = APIRouter()

@router.get("/public-or-private")
async def flexible_endpoint(current_user: Optional[User] = Depends(get_current_user_optional)):
    """This endpoint works with or without authentication."""
    if current_user:
        return {"message": f"Hello {current_user.full_name}"}
    else:
        return {"message": "Hello guest"}
```

## Client-Side Usage

### JavaScript/TypeScript Example

```typescript
// Register
const registerResponse = await fetch('http://localhost:8000/api/v1/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePassword123!',
    full_name: 'John Doe'
  })
});

const { access_token, refresh_token } = await registerResponse.json();

// Store tokens securely
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);

// Make authenticated requests
const response = await fetch('http://localhost:8000/api/v1/auth/me', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});

// Refresh token when access token expires
const refreshResponse = await fetch('http://localhost:8000/api/v1/auth/refresh', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${refresh_token}`
  }
});

const { access_token: newAccessToken } = await refreshResponse.json();
localStorage.setItem('access_token', newAccessToken);
```

### Python Example

```python
import httpx

# Register
response = httpx.post(
    "http://localhost:8000/api/v1/auth/register",
    json={
        "email": "user@example.com",
        "password": "SecurePassword123!",
        "full_name": "John Doe"
    }
)
tokens = response.json()
access_token = tokens["access_token"]

# Make authenticated request
response = httpx.get(
    "http://localhost:8000/api/v1/auth/me",
    headers={"Authorization": f"Bearer {access_token}"}
)
user_info = response.json()
```

### cURL Example

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePassword123!","full_name":"John Doe"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePassword123!"}'

# Get current user (replace TOKEN with your access token)
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer TOKEN"
```

## Password Recovery Flow

1. **User requests password reset**
   - POST to `/api/v1/auth/forgot-password` with email
   - System generates secure reset token
   - Email sent with reset link (expires in 1 hour)

2. **User clicks reset link**
   - Link contains reset token as query parameter
   - Frontend shows password reset form

3. **User submits new password**
   - POST to `/api/v1/auth/reset-password` with token and new password
   - Token is validated and password is updated
   - User can now login with new password

## Email Verification Flow

1. **User registers**
   - Verification email sent automatically
   - Contains verification link (expires in 24 hours)

2. **User clicks verification link**
   - GET to `/api/v1/auth/verify-email?token=<token>`
   - Email marked as verified

3. **Resend verification (if needed)**
   - POST to `/api/v1/auth/resend-verification` (requires auth)
   - New verification email sent

## Security Best Practices

1. **Store tokens securely**
   - Use httpOnly cookies for web apps
   - Use secure storage (Keychain/Keystore) for mobile apps
   - Never store tokens in localStorage for production apps

2. **Token expiry**
   - Access tokens expire in 30 minutes
   - Refresh tokens expire in 7 days
   - Verification tokens expire in 24 hours
   - Password reset tokens expire in 1 hour
   - Implement automatic token refresh

3. **Password requirements**
   - Minimum 8 characters required
   - Recommend: mixed case, numbers, and symbols
   - Passwords are hashed with bcrypt (cost factor 12)
   - New password must differ from current password

4. **HTTPS only**
   - Always use HTTPS in production
   - Never send tokens over unencrypted connections

5. **Token revocation**
   - Logout discards tokens client-side
   - Password reset invalidates old tokens
   - Email verification tokens are single-use

6. **Rate limiting**
   - Implement rate limiting on auth endpoints
   - Prevent brute force attacks
   - Use CAPTCHA for sensitive operations

7. **Email enumeration protection**
   - Forgot password always returns success message
   - Prevents attackers from discovering valid emails
   - Actual email only sent if user exists

## Environment Variables

Make sure these are set in your `.env` file:

```bash
# Required
SECRET_KEY=your-secret-key-here-change-in-production

# Optional - SMTP for production email sending
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@jobcopilot.com
```

Generate a secure secret key:
```bash
openssl rand -hex 32
```

### Email Configuration

**Development Mode:**
- Emails are logged to console instead of being sent
- No SMTP configuration needed
- Check logs to see verification/reset links

**Production Mode:**
- Configure SMTP settings in environment variables
- Recommended providers:
  - SendGrid
  - AWS SES
  - Mailgun
  - Gmail (with app password)

**Gmail Setup Example:**
1. Enable 2-factor authentication
2. Generate app password: https://myaccount.google.com/apppasswords
3. Use app password as `SMTP_PASSWORD`

## Migration

Run the migration to add the password field:

```bash
# Docker
docker-compose exec api uv run alembic upgrade head

# Local
uv run alembic upgrade head
```

## Testing Authentication

Use the interactive API docs at `http://localhost:8000/docs`:

1. Click on `/api/v1/auth/register` or `/api/v1/auth/login`
2. Click "Try it out"
3. Enter your credentials
4. Copy the `access_token` from the response
5. Click the "Authorize" button at the top
6. Enter `Bearer <your_access_token>`
7. Now you can test protected endpoints

## Troubleshooting

### "Invalid authentication credentials"
- Token may be expired - use refresh token to get a new one
- Token may be malformed - check the format is `Bearer <token>`

### "User not found"
- User may have been deleted
- Token may be for a different environment

### "Email already registered"
- User already exists - use login instead
- Check if you're using the correct email
