#!/bin/bash

echo "🎮 Minecraft RCON Setup Helper"
echo "================================"
echo ""

# Function to find Minecraft server
find_minecraft_server() {
    echo "🔍 Looking for Minecraft server files..."
    
    # Common locations
    locations=(
        "$HOME/minecraft"
        "$HOME/minecraft-server"
        "$HOME/server"
        "$HOME/.minecraft/server"
        "/opt/minecraft"
        "$(pwd)/../minecraft"
    )
    
    for loc in "${locations[@]}"; do
        if [ -f "$loc/server.properties" ]; then
            echo "✅ Found Minecraft server at: $loc"
            return 0
        fi
    done
    
    # Search in home directory
    found=$(find "$HOME" -name "server.properties" -type f 2>/dev/null | head -1)
    if [ -n "$found" ]; then
        echo "✅ Found server.properties at: $(dirname "$found")"
        return 0
    fi
    
    echo "❌ No Minecraft server found"
    return 1
}

# Function to check RCON status
check_rcon() {
    local server_props="$1"
    
    if [ -f "$server_props" ]; then
        echo ""
        echo "📋 Current RCON Configuration:"
        echo "--------------------------------"
        grep -E "enable-rcon|rcon\." "$server_props" || echo "No RCON settings found"
        echo ""
        
        # Check if RCON is enabled
        rcon_enabled=$(grep "^enable-rcon=" "$server_props" | cut -d'=' -f2)
        rcon_port=$(grep "^rcon.port=" "$server_props" | cut -d'=' -f2)
        rcon_password=$(grep "^rcon.password=" "$server_props" | cut -d'=' -f2)
        
        if [ "$rcon_enabled" = "true" ]; then
            echo "✅ RCON is enabled"
            echo "📍 Port: ${rcon_port:-25575}"
            if [ -n "$rcon_password" ] && [ "$rcon_password" != "" ]; then
                echo "🔑 Password is set: ${rcon_password}"
            else
                echo "⚠️  WARNING: No RCON password set!"
            fi
        else
            echo "❌ RCON is NOT enabled"
            echo ""
            echo "To enable RCON, add these lines to $server_props:"
            echo ""
            echo "enable-rcon=true"
            echo "rcon.port=25575"
            echo "rcon.password=your_secure_password_here"
            echo "broadcast-rcon-to-ops=true"
        fi
    fi
}

# Main execution
echo ""
find_minecraft_server

echo ""
echo "Where is your Minecraft server.properties file?"
read -p "Enter full path (or press Enter to search): " server_path

if [ -z "$server_path" ]; then
    # Auto-search
    server_path=$(find "$HOME" -name "server.properties" -type f 2>/dev/null | head -1)
fi

if [ -f "$server_path" ]; then
    check_rcon "$server_path"
    
    echo ""
    read -p "Would you like to enable/update RCON? (y/n): " enable_rcon
    
    if [ "$enable_rcon" = "y" ] || [ "$enable_rcon" = "Y" ]; then
        read -p "Enter RCON password (leave empty for 'minecraft'): " new_password
        new_password=${new_password:-minecraft}
        
        # Backup original file
        cp "$server_path" "$server_path.backup"
        echo "📦 Backed up to: $server_path.backup"
        
        # Update or add RCON settings
        if grep -q "^enable-rcon=" "$server_path"; then
            sed -i "s/^enable-rcon=.*/enable-rcon=true/" "$server_path"
        else
            echo "enable-rcon=true" >> "$server_path"
        fi
        
        if grep -q "^rcon.port=" "$server_path"; then
            sed -i "s/^rcon.port=.*/rcon.port=25575/" "$server_path"
        else
            echo "rcon.port=25575" >> "$server_path"
        fi
        
        if grep -q "^rcon.password=" "$server_path"; then
            sed -i "s/^rcon.password=.*/rcon.password=$new_password/" "$server_path"
        else
            echo "rcon.password=$new_password" >> "$server_path"
        fi
        
        if grep -q "^broadcast-rcon-to-ops=" "$server_path"; then
            sed -i "s/^broadcast-rcon-to-ops=.*/broadcast-rcon-to-ops=true/" "$server_path"
        else
            echo "broadcast-rcon-to-ops=true" >> "$server_path"
        fi
        
        echo ""
        echo "✅ RCON configuration updated!"
        echo ""
        echo "📝 Update your .env file with:"
        echo "RCON_HOST=localhost"
        echo "RCON_PORT=25575"
        echo "RCON_PASSWORD=$new_password"
        echo ""
        echo "⚠️  You MUST restart your Minecraft server for changes to take effect!"
    fi
else
    echo ""
    echo "❌ Could not find server.properties"
    echo ""
    echo "📝 Manual setup instructions:"
    echo "1. Find your Minecraft server folder"
    echo "2. Open server.properties"
    echo "3. Add or update these lines:"
    echo "   enable-rcon=true"
    echo "   rcon.port=25575"
    echo "   rcon.password=your_password"
    echo "   broadcast-rcon-to-ops=true"
    echo "4. Restart your Minecraft server"
    echo "5. Update your .env file in this app folder"
fi

echo ""
echo "🔍 Testing RCON connection..."
cd "$(dirname "$0")"
python3 -c "
from rcon_client import run_command
result = run_command('list')
if 'Error' in result:
    print('❌ RCON connection failed:', result)
    print('')
    print('Troubleshooting:')
    print('1. Make sure Minecraft server is running')
    print('2. Check that RCON is enabled in server.properties')
    print('3. Verify the password in .env matches server.properties')
    print('4. Check if port 25575 is open (no firewall blocking)')
else:
    print('✅ RCON connection successful!')
    print('Server response:', result)
" 2>/dev/null || echo "❌ Could not test connection (Python dependencies may be missing)"

echo ""
echo "Done! 🎉"
