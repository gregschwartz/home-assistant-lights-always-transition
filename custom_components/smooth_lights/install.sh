#!/bin/bash
# Installation script for Smooth Lights

# Default Home Assistant config directory
HA_CONFIG="${1:-/config}"

echo "Installing Smooth Lights to $HA_CONFIG/custom_components/"

# Create custom_components directory if it doesn't exist
mkdir -p "$HA_CONFIG/custom_components"

# Copy the component
cp -r "$(dirname "$0")" "$HA_CONFIG/custom_components/"

# Remove the install script from the destination
rm -f "$HA_CONFIG/custom_components/smooth_lights/install.sh"

echo "✅ Smooth Lights installed successfully!"
echo ""
echo "Next steps:"
echo "1. Restart Home Assistant"
echo "2. Go to Settings → Devices & Services"
echo "3. Click 'Add Integration'"
echo "4. Search for 'Smooth Lights'"
echo "5. Configure your transition time"
