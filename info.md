# Smooth Lights

Automatically adds smooth fade-up transitions to ALL lights in Home Assistant.

## Features

✨ **Universal** - Works with all `light.turn_on` calls automatically
⚙️ **Configurable** - Set your preferred fade duration (default: 4 seconds)
🎯 **Smart** - Respects existing transitions in your automations
🚫 **Excludable** - Opt-out specific lights that shouldn't fade
🪶 **Lightweight** - Minimal overhead, maximum smoothness

## Quick Start

1. Install via HACS
2. Restart Home Assistant
3. Add the integration via Settings → Devices & Services
4. Configure your transition time
5. Enjoy smooth lighting!

## How It Works

Intercepts `light.turn_on` service calls and automatically adds your configured transition time when none is specified. Existing transitions are never overridden.

**No configuration of individual lights needed** - it just works!

## Configuration

- **Transition time**: 0-60 seconds (default: 4)
- **Exclude entities**: List of lights to skip (optional)

Settings can be changed anytime via the integration's configuration page.
