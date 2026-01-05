# Error Logging System

## Overview
Comprehensive error logging system that tracks all failed RCON commands with detailed information for debugging and monitoring.

## Features

### 1. Database Storage
- **Table**: `error_logs`
- **Columns**:
  - `id`: Auto-incrementing primary key
  - `timestamp`: When the error occurred
  - `command_type`: Type of command (e.g., "give_item", "teleport", "quick_command")
  - `command`: The actual RCON command that failed
  - `error_message`: Error message from RCON or system
  - `player`: Player associated with the command (if applicable)
  - `endpoint`: API endpoint where error occurred (e.g., "/give", "/tp")

### 2. Automatic Error Logging
Errors are automatically logged from all command execution routes:
- **Give Item** (`/give`)
- **Teleport** (`/tp` and `/tp/coordinates`)
- **Locate Village** (`/locate`)
- **Quick Commands** (`/quick-command`)
- **Kits** (`/kit/<kit_id>`)

### 3. Error Detection
Uses `is_rcon_error()` function to detect:
- "Unknown command"
- "No player was found"
- "Unable to modify"
- "Invalid"
- "Incorrect argument"
- "Expected"
- "Cannot"
- "Failed"
- "Error:" prefix

### 4. API Endpoint
**GET** `/api/error-logs?limit=50`

Returns JSON with recent error logs:
```json
{
  "success": true,
  "logs": [
    {
      "id": 1,
      "timestamp": "2026-01-05 12:34:56",
      "command_type": "give_item",
      "command": "/give Player123 minecraft:diamond_sword 1",
      "error_message": "No player was found",
      "player": "Player123",
      "endpoint": "/give"
    }
  ]
}
```

### 5. Diagnostics UI
Visit `/diagnostics` to view:
- RCON connection status
- **Recent Error Logs** section showing:
  - Command type and timestamp
  - Player name (if applicable)
  - Error message
  - Full command that failed
  - API endpoint
- Auto-refreshes on page load
- Manual refresh button

## Usage

### View Logs in UI
1. Navigate to `http://localhost:5000/diagnostics`
2. Scroll to "Recent Error Logs" section
3. Click "Refresh" to update

### Query Logs via API
```bash
# Get last 50 errors
curl http://localhost:5000/api/error-logs

# Get last 100 errors
curl http://localhost:5000/api/error-logs?limit=100
```

### Check Database Directly
```bash
# Connect to SQLite database
sqlite3 /app/data/data.db

# View all errors
SELECT * FROM error_logs ORDER BY timestamp DESC LIMIT 10;

# Count errors by type
SELECT command_type, COUNT(*) as count 
FROM error_logs 
GROUP BY command_type 
ORDER BY count DESC;

# Errors for specific player
SELECT * FROM error_logs WHERE player = 'PlayerName';
```

## Benefits

1. **Debugging**: Quickly identify why commands are failing
2. **Monitoring**: Track system health and error patterns
3. **User Support**: Help players understand what went wrong
4. **Analytics**: Identify most common errors to improve UX
5. **Audit Trail**: Complete history of all failed operations

## Examples

### Successful Command (Not Logged)
```
Player: Steve
Command: /give Steve minecraft:diamond 64
Result: Gave 64 [Diamond] to Steve
```

### Failed Command (Logged)
```
Player: NonExistentPlayer
Command: /give NonExistentPlayer minecraft:diamond 64
Error: No player was found
Logged: Yes ✓
```

## Console Output
All logged errors also print to console:
```
[ERROR_LOG] give_item: No player was found
```

## Maintenance

### Clear Old Logs
```sql
-- Delete logs older than 30 days
DELETE FROM error_logs 
WHERE timestamp < datetime('now', '-30 days');

-- Keep only last 1000 logs
DELETE FROM error_logs 
WHERE id NOT IN (
  SELECT id FROM error_logs 
  ORDER BY timestamp DESC 
  LIMIT 1000
);
```

### Backup Logs
```bash
# Export to CSV
sqlite3 /app/data/data.db \
  "SELECT * FROM error_logs" \
  -header -csv > error_logs_backup.csv
```
