# Product Requirements Document: Lights Always Transition

## Overview

**Product Name:** Lights Always Transition
**Version:** 1.0
**Author:** Greg Schwartz (greg@gregschwartz.net)
**Last Updated:** 2025-11-25

## Problem Statement

Home Assistant lights turn on/off instantly by default, creating jarring lighting changes. While transition parameters exist, they must be manually specified in every automation, script, and UI interaction. Users want smooth, natural lighting transitions without modifying existing automations or infrastructure.

Further, some lights don't support transitions, so this integration patches that functionality.

## Solution

A custom Home Assistant integration that automatically applies smooth fade transitions to all light operations by intercepting `light.turn_on` and `light.turn_off` service calls.

## Core Requirements

### 1. Universal Light Interception

**Requirement:** Intercept ALL `light.turn_on` and `light.turn_off` service calls before execution.

**Behavior:**
- Hook into Home Assistant service registry
- Process calls before they reach the light integration
- Support both single and multiple entity targets

### 2. Dual-Mode Transition Support 

**Requirement:** Support both native transitions and manual step-based transitions.

**2.1 Native Transition Mode**

For lights that support the `transition` parameter:
- Add `transition` parameter if not already present
- Use the configured default transition time
- Let the light hardware handle the fade

**2.2 Manual Transition Mode**

For lights that DON'T support transitions:
- Detect lack of transition support via light capabilities
- Implement manual brightness stepping
- Step brightness from current → target over configured duration

**Step Calculation Algorithm:**

Steps are derived from brightness delta, not duration, to prevent API overload and respect HA's integer brightness constraint (0-255).

```
brightness_delta = abs(target - current)
max_steps = 60  # Cap to prevent excessive API calls
steps = min(brightness_delta, max_steps)
interval = duration / steps
interval = max(interval, min_step_interval)  # Enforce minimum interval
```

**Constraints:**
- Minimum step interval: **1 second** (configurable)
- Maximum steps per transition: **60** (prevents long transitions from flooding APIs)
- Minimum brightness delta per step: **1%** (HA integer constraint)

**Examples:**

| Transition | Brightness Change | Steps | Interval | Delta/Step |
|------------|-------------------|-------|----------|------------|
| 0→100% in 4s | 100% | 4 | 1s | 25% |
| 0→100% in 60s | 100% | 60 | 1s | ~1.7% |
| 0→100% in 600s (10min) | 100% | 60 (capped) | 10s | ~1.7% |
| 0→10% in 4s | 10% | 10 | 1s* | 1% |
| 50→60% in 4s | 10% | 10 | 1s* | 1% |

*When calculated interval < min_step_interval, actual duration extends beyond requested duration to maintain smooth steps.

**2.3 Transition Parameter Passthrough**

For lights that DON'T support transitions but receive a `transition` parameter (e.g., from a script or automation):
- Detect the incoming `transition` value before stripping it
- Use that duration for manual stepping instead of the default
- This allows scripts to specify custom durations even for non-transition lights

**Example:**
```yaml
# Script calls:
service: light.turn_on
target:
  entity_id: light.non_transition_bulb
data:
  transition: 10  # Use 10 seconds, not default 4
```

### 3. Proportional Transition Scaling

**Requirement:** Scale transition duration based on brightness change magnitude.

**Formula:**
```
actual_duration = configured_duration * (abs(target - current) / 100)
```

**Examples:**
- Default Transition: 4 seconds
- 0% brightness → 100%: 4 seconds (100% change)
- If a light is at 25% brightness → 0%: 1 second (25% change)
- 50% brightness → 100%: 2 seconds (50% change)
- 75% brightness → 25%: 2 seconds (50% change)

**Constraints:**
- Minimum duration: 1 second (even for small changes)
- Round to nearest second
- Minimum brightness delta is 1%

### 4. Rate Limit Awareness (Govee Integration)

**Requirement:** Respect API rate limits for cloud-based integrations.

**Detection:**
Check if light entity has `rate_limit_remaining` attribute (e.g., Govee lights).

**Behavior:**
- Read current `rate_limit_remaining` value
- Calculate safe step count to leave ≥10 remaining
- Adjust step interval accordingly

**Formula:**
```
safe_steps = rate_limit_remaining - 10
step_interval = max(1, configured_duration / safe_steps)
```

**Example:**
```
Rate limit remaining: 45
Safe steps: 35
Configured duration: 4 seconds
Step interval: max(1, 4/35) = 1 second
Adjusted steps: 4 (use fewer steps to respect rate limit)
```

**Fallback:** If rate limit < 2, skip transition and execute command immediately.

### 5. Manual Control Detection

**Requirement:** Stop ongoing transitions when user manually changes light state.

**Triggers for Cancellation:**
If a light that is currently having a manual transition applied gets:
- A `light.turn_on` call
- A `light.turn_off` call
- A state change from external source (physical switch, other automation)

**Implementation:**
- Listen to `state_changed` events for lights in transition
- Compare event context to transition context
- If contexts differ → cancel transition
- Similar to Adaptive Lighting's "manual control" detection

**Behavior:**
```
1. User calls light.turn_on (no brightness)
2. Transition starts: 0% → 100% over 4s
3. At 2 seconds (50% brightness):
   - User manually sets brightness to 75%
4. Transition immediately stops
5. Light remains at 75%
```

### 6. Configuration Options

**Required Settings:**

| Setting | Type | Default | Range | Description |
|---------|------|---------|-------|-------------|
| `transition_time` | float | 4.0 | 0-60 | Default transition duration (seconds) |
| `exclude_entities` | list | [] | - | Light entities to skip |
| `min_step_interval` | float | 1.0 | 0.5-5.0 | Minimum time between brightness steps |
| `max_steps` | int | 60 | 10-120 | Maximum steps per manual transition |
| `rate_limit_buffer` | int | 10 | 0-50 | Remaining rate limit to preserve |

**UI Requirements:**
- Home Assistant config flow integration
- Options flow for runtime changes
- Validation of numeric ranges
- Entity selector for exclusions

### 7. Transition State Management

**Requirement:** Track active transitions to enable cancellation and prevent conflicts.

**Data Structure:**
```python
active_transitions = {
    "light.living_room": {
        "task": asyncio.Task,
        "start_time": datetime,
        "target_brightness": int,
        "context_id": str,
    }
}
```

**Lifecycle:**
1. **Start:** Register transition when initiated
2. **Monitor:** Listen for state changes
3. **Cancel:** Stop task if manual intervention detected
4. **Complete:** Remove from registry when finished
5. **Cleanup:** Remove on component unload

### 8. Error Handling

**Requirements:**

**Non-blocking:** Errors in transition logic must not break `light.turn_on` calls
- Wrap all transition logic in try/except
- Log errors but allow service call to proceed
- Fall back to instant on/off if transition fails

**Light Availability:**
- Check if light is available before starting transition
- If light becomes unavailable mid-transition, continue trying until transition duration ends in case it comes back
- Handle connection errors gracefully

**Edge Cases:**
- Rapid successive calls to same light → cancel previous, start new
- Light already at target brightness → skip transition
- Invalid brightness values → clamp to 0-100

## Non-Functional Requirements

### Performance
- Service call interception overhead: <10ms
- No impact on lights that already specify transitions
- Async/await for all I/O operations
- Cancel transitions immediately (no lingering tasks)

### Compatibility
- Home Assistant 2024.1.0+
- All light integrations that support brightness control
- HACS compatible
- No external dependencies (pure Python)

### Logging
- DEBUG: Every intercepted call
- INFO: Transition start/stop/cancel
- WARNING: Rate limit concerns
- ERROR: Transition failures

## Success Metrics

1. **Reliability:** <1% error rate in transition execution
3. **Performance:** No user-reported slowdowns
4. **Compatibility:** Works with 90%+ of popular light integrations

## Future Enhancements (Out of Scope for v1.0)

- Per-light transition time overrides
- Different transition times for on vs off
- Easing curves (linear, ease-in, ease-out)
- Color temperature transitions
- Integration with scenes
- Dashboard card for transition monitoring

## Technical Architecture

### Components

1. **Service Interceptor** (`interceptor.py`)
   - Hooks into HA service registry
   - Modifies service call data

2. **Transition Manager** (`transition_manager.py`)
   - Manages active transitions
   - Handles step-based transitions
   - Monitors state changes

3. **Rate Limit Handler** (`rate_limit.py`)
   - Detects rate-limited lights
   - Calculates safe step intervals

4. **Config Flow** (`config_flow.py`)
   - UI configuration
   - Options flow

## Testing Strategy

### Unit Tests
- Service interception logic
- Proportional scaling calculations
- Rate limit calculations
- State change detection

### Integration Tests
- Test with mock lights (transition-capable)
- Test with mock lights (non-transition)
- Test with mock Govee lights (rate limited)
- Test cancellation scenarios
- Test rapid successive calls

### Manual Testing
- Real Govee lights
- Real Zigbee lights
- Real WiFi lights (Tuya, etc.)
- Physical switch interactions
- Voice assistant commands

## Release Plan

### Phase 1: Core Implementation
- Service interception
- Native transition support
- Proportional scaling
- Basic config flow

### Phase 2: Advanced Features
- Manual transition stepping
- Rate limit handling
- State change detection
- Transition cancellation

### Phase 3: Polish
- Comprehensive testing
- Documentation
- HACS validation
- Community feedback

### Phase 4: Release
- GitHub release v1.0.0
- HACS submission
- Home Assistant Community forum post
- Reddit announcement

## Documentation Requirements

1. **README.md**
   - Installation instructions
   - Configuration guide
   - Examples
   - Troubleshooting

2. **info.md** (HACS UI)
   - Quick overview
   - Key features
   - Quick start

3. **Code Comments**
   - Why comments (not what)
   - Complex logic explanations
   - Type hints on all functions

## Compliance

- **License:** MIT
- **HACS:** Meets all validation requirements
- **HA Standards:** Follows integration quality scale
- **Privacy:** No data collection, 100% local

