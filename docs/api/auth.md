# Authentication API

Base URL: `/api/v1`

All timestamps are ISO-8601 UTC. All error responses use:

```json
{
    "error": "machine_readable_code",
    "message": "Human-readable description"
}
```

## Authorization

Protected endpoints require a bearer token:

```
Authorization: Bearer <token>
```

| HTTP | Error code        | When                                         |
| ---- | ----------------- | -------------------------------------------- |
| 401  | `unauthenticated` | Missing, invalid, or expired token           |
| 403  | `forbidden`       | Authenticated user lacks required permission |

### Permissions (MVP 0)

| Permission         | Allowed roles               |
| ------------------ | --------------------------- |
| `list_users`       | `admin`                     |
| `view_own_account` | `admin`, `coach`, `athlete` |

---

## POST /auth/register

Register a coach or athlete account.

**Request**

```json
{
    "email": "coach@example.com",
    "password": "secure-password",
    "role": "coach"
}
```

| Field      | Type   | Rules                                                   |
| ---------- | ------ | ------------------------------------------------------- |
| `email`    | string | Valid email, unique                                     |
| `password` | string | Min 8 chars, max 128, at least one letter and one digit |
| `role`     | string | `coach` or `athlete` only                               |

**Response `201 Created`**

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "coach@example.com",
    "role": "coach",
    "created_at": "2026-06-26T12:00:00Z"
}
```

**Errors**

| Status | Code                   | When                             |
| ------ | ---------------------- | -------------------------------- |
| 400    | `validation_error`     | Invalid email, password, or role |
| 409    | `email_already_exists` | Email is already registered      |

---

## POST /auth/login

Authenticate and open a session.

**Request**

```json
{
    "email": "coach@example.com",
    "password": "secure-password"
}
```

**Response `200 OK`**

```json
{
    "token": "opaque-session-token",
    "expires_at": "2026-07-26T12:00:00Z",
    "user": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "coach@example.com",
        "role": "coach"
    }
}
```

The client sends the token in the `Authorization` header:

```
Authorization: Bearer <token>
```

**Errors**

| Status | Code                  | When                        |
| ------ | --------------------- | --------------------------- |
| 400    | `validation_error`    | Missing or malformed fields |
| 401    | `invalid_credentials` | Email or password is wrong  |

---

## POST /auth/logout

Terminate the current session.

**Headers**

```
Authorization: Bearer <token>
```

**Response `204 No Content`**

**Errors**

| Status | Code              | When                     |
| ------ | ----------------- | ------------------------ |
| 401    | `unauthenticated` | Missing or invalid token |

---

## GET /auth/me

Return the authenticated user.

**Headers**

```
Authorization: Bearer <token>
```

**Response `200 OK`**

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "coach@example.com",
    "role": "coach",
    "created_at": "2026-06-26T12:00:00Z"
}
```

**Errors**

| Status | Code              | When                     |
| ------ | ----------------- | ------------------------ |
| 401    | `unauthenticated` | Missing or invalid token |

---

## GET /admin/users

List all users. **Admin only.**

**Headers**

```
Authorization: Bearer <admin-token>
```

**Query parameters**

| Parameter | Type    | Default | Rules        |
| --------- | ------- | ------- | ------------ |
| `offset`  | integer | `0`     | Non-negative |
| `limit`   | integer | `20`    | 1–100        |

**Response `200 OK`**

```json
{
    "items": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "coach@example.com",
            "role": "coach",
            "created_at": "2026-06-26T12:00:00Z"
        }
    ],
    "total": 1
}
```

**Errors**

| Status | Code              | When                     |
| ------ | ----------------- | ------------------------ |
| 401    | `unauthenticated` | Missing or invalid token |
| 403    | `forbidden`       | User is not an admin     |
