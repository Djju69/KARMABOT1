# KarmaBot Partner API

This document describes the RESTful API endpoints available for the KarmaBot Partner Cabinet.

## Base URL

All API endpoints are prefixed with `/api/v1/partner`.

## Authentication

All endpoints require authentication using JWT tokens. Include the token in the `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### Cards

#### Get All Cards

```
GET /cards/
```

**Query Parameters:**
- `status` (optional): Filter cards by status (draft, pending_review, approved, rejected, archived)
- `q` (optional): Search query string
- `category_id` (optional): Filter by category ID
- `after_id` (optional): Pagination - get cards after this ID
- `limit` (optional, default=20): Number of cards to return per page

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "category_id": 1,
      "title": "Sample Card",
      "description": "This is a sample card",
      "status": "approved",
      "is_active": true,
      "created_at": "2023-01-01T00:00:00",
      "updated_at": "2023-01-01T00:00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

#### Get Single Card

```
GET /cards/{card_id}
```

**Response:**
```json
{
  "id": 1,
  "category_id": 1,
  "title": "Sample Card",
  "description": "This is a sample card",
  "status": "approved",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00"
}
```

#### Create Card

```
POST /cards/
```

**Request Body:**
```json
{
  "category_id": 1,
  "title": "New Card",
  "description": "This is a new card",
  "status": "draft"
}
```

**Response (201 Created):**
```json
{
  "id": 2,
  "category_id": 1,
  "title": "New Card",
  "description": "This is a new card",
  "status": "draft",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T00:00:00"
}
```

#### Update Card

```
PUT /cards/{card_id}
```

**Request Body:**
```json
{
  "title": "Updated Card Title",
  "description": "Updated description"
}
```

**Response:**
```json
{
  "id": 2,
  "category_id": 1,
  "title": "Updated Card Title",
  "description": "Updated description",
  "status": "draft",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00",
  "updated_at": "2023-01-01T01:00:00"
}
```

#### Delete Card

```
DELETE /cards/{card_id}
```

**Response:**
- `204 No Content` on success

### Card Images

#### Get Card Images

```
GET /cards/{card_id}/images
```

**Response:**
```json
[
  {
    "id": 1,
    "card_id": 1,
    "url": "https://example.com/images/1.jpg",
    "position": 0,
    "created_at": "2023-01-01T00:00:00"
  }
]
```

#### Upload Card Images

```
POST /cards/{card_id}/images
```

**Request:**
- Content-Type: `multipart/form-data`
- Body: One or more image files

**Response:**
```json
[
  {
    "id": 2,
    "card_id": 1,
    "url": "https://example.com/images/2.jpg",
    "position": 1,
    "created_at": "2023-01-01T01:00:00"
  }
]
```

#### Delete Card Image

```
DELETE /cards/{card_id}/images/{image_id}
```

**Response:**
- `204 No Content` on success

### Card Delete Requests

#### Request Card Deletion

```
POST /cards/{card_id}/delete-request
```

**Request Body (optional):**
```json
{
  "reason": "No longer relevant"
}
```

**Response:**
- `202 Accepted` on success

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Card not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```
