# Project Code Styles

## Docstrings

Every module, class, and function must have a docstring.

### Format

```python
"""Short description ending with a period."""
```

### Rules

1. Use triple double quotes `"""`
2. Single line description
3. End with a period
4. One blank line after docstring before code

### Examples

**Module:**
```python
"""PostgreSQL Database models."""

from pydantic import BaseModel
```

**Class:**
```python
class UserService:
    """Service for user operations."""

    def __init__(self, app: "Application"):
        """Initialize service with application."""

        self.app = app
```

**Function:**
```python
async def get_user(self, user_id: int) -> User | None:
    """Get user by ID."""

    user = await self.repo.get_by_id(user_id)
    return user
```

**Multi-line function signature:**
```python
async def create_user(
    self,
    username: str,
    password_hash: str,
    display_name: str
) -> int:
    """Create new user and return ID."""

    user_id = await self.repo.create(username, password_hash, display_name)
    return user_id
```

## Type Hints

Use modern Python 3.10+ syntax:

```python
# Good
def get_user(self, user_id: int) -> User | None:
    ...

def get_users(self) -> list[User]:
    ...

# Bad (old style)
def get_user(self, user_id: int) -> Optional[User]:
    ...

def get_users(self) -> List[User]:
    ...
```

## Imports

Order:
1. Standard library
2. Third-party packages
3. Local imports

```python
"""Module description."""

import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel

from src.common.base_repos import BaseDBRepository
from src.models.db_models import UserDB

if TYPE_CHECKING:
    from src.app import Application
```

## Error Handling

Never raise exceptions for client errors. Always return `Result`:

```python
from src.models.api_models import Result

async def get_user(self, token: str, user_id: int) -> Result[User]:
    """Get user by ID."""

    # Validation error - return Result
    if not user_id:
        return Result(success=False, error="User ID required", error_code="VALIDATION_ERROR")

    user = await self.repo.get_by_id(user_id)
    if not user:
        return Result(success=False, error="User not found", error_code="NOT_FOUND")

    return Result(success=True, data=user)
```

## Naming Conventions

| Type            | Convention       | Example                         |
|-----------------|------------------|---------------------------------|
| Class           | PascalCase       | `UserService`, `ChatRepository` |
| Function/Method | snake_case       | `get_user`, `create_chat`       |
| Variable        | snake_case       | `user_id`, `chat_name`          |
| Constant        | UPPER_SNAKE_CASE | `MAX_CONNECTIONS`, `UTC_PLUS_3` |
| Private         | _prefix          | `_handle_client`, `_running`    |

## Database Column Names

Use snake_case with descriptive suffixes:

| Column      | Convention                       |
|-------------|----------------------------------|
| Primary key | `id`                             |
| Foreign key | `{table}_id` or `{role}_user_id` |
| Timestamp   | `created_at`, `last_online_at`   |
| Boolean     | `is_read`, `account_is_active`   |

Examples:
- `user_id` - FK to users
- `owner_user_id` - FK to users (owner role)
- `sender_user_id` - FK to users (sender role)
- `chat_id` - FK to chats
