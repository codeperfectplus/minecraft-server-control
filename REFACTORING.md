# Refactored Application Structure

The Flask application has been refactored into a modular structure for better maintainability and organization.

## Directory Structure

```
src/
├── app.py                      # Main Flask application entry point
├── models.py                   # User model for authentication
├── database.py                 # Database connection and initialization
├── config_loader.py            # Configuration file loading utilities
├── rcon_client.py              # RCON client for Minecraft server communication
├── commands.py                 # Command definitions and constants
│
├── services/                   # Business logic layer
│   ├── __init__.py
│   ├── location_service.py     # Location management operations
│   ├── item_service.py         # Item usage tracking
│   ├── error_service.py        # Error logging
│   └── player_service.py       # Player-related operations
│
├── routes/                     # HTTP routes layer (Flask blueprints)
│   ├── __init__.py
│   ├── main_routes.py          # Main pages (dashboard, diagnostics, etc.)
│   ├── auth_routes.py          # Authentication (login, logout, user mgmt)
│   ├── api_routes.py           # API endpoints for AJAX requests
│   └── command_routes.py       # Minecraft command execution routes
│
├── config/                     # JSON configuration files
│   ├── kits.json
│   ├── locations.json
│   └── quick_commands.json
│
└── templates/                  # HTML templates
    └── ...
```

## Module Responsibilities

### Core Modules

- **app.py**: Minimal Flask application setup, blueprint registration, and initialization
- **models.py**: User model for Flask-Login authentication
- **database.py**: Database connection management and table initialization
- **config_loader.py**: Utilities for loading JSON configuration files

### Services Layer

Business logic separated from HTTP concerns:

- **location_service.py**: CRUD operations for saved locations
- **item_service.py**: Item usage tracking, catalog building, top items
- **error_service.py**: Error logging and retrieval
- **player_service.py**: Player stats, inventory, history, location queries

### Routes Layer

Flask blueprints for HTTP endpoints:

- **main_routes.py**: Dashboard, diagnostics, error logs, player pages
- **auth_routes.py**: Login, logout, user management (admin only)
- **api_routes.py**: JSON API endpoints for AJAX requests
- **command_routes.py**: Minecraft command execution (teleport, give, locate, kits, etc.)

## Benefits of This Structure

1. **Separation of Concerns**: Business logic (services) is separated from HTTP handling (routes)
2. **Reusability**: Services can be used from multiple routes or other contexts
3. **Testability**: Each module can be tested independently
4. **Maintainability**: Easier to locate and modify specific functionality
5. **Scalability**: Easy to add new services or routes without cluttering a single file
6. **Code Organization**: Logical grouping of related functionality

## Migration Notes

- All existing routes continue to work with the same URLs
- Database schema remains unchanged
- Configuration files location unchanged
- Templates remain in the same location
- No breaking changes to the API

## Running the Application

The application runs exactly as before:

```bash
python src/app.py
```

Or with Docker:

```bash
docker compose up --build
```
