# Smooth Lights for Home Assistant

Automatically adds smooth fade-up transitions to all lights in Home Assistant without modifying individual automations or scripts.

## Features

- **Universal**: Works with ALL `light.turn_on` calls automatically
- **Configurable transition time**: Set your preferred fade duration (default: 4 seconds)
- **Exclude specific lights**: Opt-out individual entities that shouldn't have transitions
- **Lightweight**: Simple service interceptor with minimal overhead
- **Non-invasive**: Respects existing transition parameters in your automations

## How It Works

This component intercepts `light.turn_on` service calls before they execute. If no transition is specified, it automatically adds your configured transition time. If a transition is already present, it leaves it unchanged.

## Installation

### Manual Installation

1. Copy the `smooth_lights` folder to your Home Assistant `custom_components` directory:
   ```
   <config>/custom_components/smooth_lights/
   ```

2. Restart Home Assistant

3. Go to **Settings** → **Devices & Services** → **Add Integration**

4. Search for "Smooth Lights" and follow the setup wizard

### Configuration

During setup, you can configure:

- **Transition time**: Duration in seconds (0-60, default: 4)
- **Exclude entities**: List of light entity IDs to skip (optional)

### Changing Settings

To modify settings after installation:

1. Go to **Settings** → **Devices & Services**
2. Find "Smooth Lights" in your integrations
3. Click **Configure**
4. Update your settings and save

## Examples

### Before (instant on)
```yaml
service: light.turn_on
target:
  entity_id: light.living_room
```

### After (4 second fade-up)
```yaml
# Same call, but now fades up automatically!
service: light.turn_on
target:
  entity_id: light.living_room
```

### Custom transition still works
```yaml
# This will use 2 seconds instead of the default
service: light.turn_on
target:
  entity_id: light.living_room
data:
  transition: 2
```

## Troubleshooting

**Lights still turning on instantly**
- Check that the light supports transitions
- Verify the integration is enabled in Settings → Devices & Services
- Check Home Assistant logs for any errors

**Some lights shouldn't have transitions**
- Add them to the "Exclude entities" list in the configuration

**Want different transition times for different lights**
- Use the exclude list for those lights
- Manually specify transition in your automations for excluded lights

## Uninstallation

1. Go to **Settings** → **Devices & Services**
2. Find "Smooth Lights" in your integrations
3. Click the three dots menu → **Delete**
4. Restart Home Assistant
5. Remove the `custom_components/smooth_lights` folder

## Technical Details

- Uses service call interception pattern (similar to Adaptive Lighting)
- Does not modify Home Assistant core code
- Minimal performance impact
- Compatible with all light integrations that support transitions

## Credits

Inspired by [Adaptive Lighting](https://github.com/basnijholt/adaptive-lighting) by @basnijholt

Created by Greg Schwartz (@gregschwartz)

## License

MIT
