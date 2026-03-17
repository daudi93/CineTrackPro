You're right! Here's the complete `QUICK_REFERENCE.md` file:

# 📋 CineTrack Pro - Quick Reference Card

## 🎯 MAIN INTERFACE

```
┌─────────────────────────────────────┐
│  Cinematic Camera Motion MEGA       │
├─────────────────────────────────────┤
│  [Camera: Select Camera...]         │
├─────────────────────────────────────┤
│  [Tracking ON] [Shake ON] [Auto]    │
├─────────────────────────────────────┤
│  ┌─ Motion Presets ───────────────┐ │
│  │ [Handheld ▼] [Apply Preset]    │ │
│  └────────────────────────────────┘ │
├─────────────────────────────────────┤
│  ▼ Camera Tracking (NEW)            │
│  ▼ Operator Behavior (NEW)          │
│  ▼ Framing Rules (NEW)              │
│  ▼ Multiple Targets (NEW)           │
│  ▼ Shake Controls                    │
│  ▼ Physics Simulation                │
│  ▼ Motion Layers                     │
│  ▼ Event Triggers                    │
│  ▼ Preview & Bake                    │
│  ▼ Shot Manager (NEW)                │
│  ▼ Shot Generator (NEW)              │
│  ▼ Camera Rigs (NEW)                 │
└─────────────────────────────────────┘
```

## 🚀 QUICK START WORKFLOWS

### Basic Camera Shake (30 seconds)
```
1. Select Camera → "Target Camera" field
2. Check "Shake ON" 
3. Scrub timeline → see effect
4. Adjust "Intensity" slider
```

### Object Tracking (1 minute)
```
1. Select Camera → "Target Camera"
2. Expand "Camera Tracking" panel
3. Set "Target Object" to follow
4. Click "Enable Tracking" in main panel
5. Move target → camera follows
```

### First Shot (2 minutes)
```
1. Set "Target Object" in Shot Generator
2. Choose "Quick Shot" type
3. Click "Add Quick Shot"
4. Click "Execute Shot"
```

## 🎬 TRACKING MODES

| Mode | Icon | Description | Best Use |
|------|------|-------------|----------|
| **Follow** | 👤 | Camera behind subject | Standard tracking |
| **Orbit** | ⭕ | Circles around subject | Dramatic reveals |
| **Lead** | ⏩ | Moves ahead of subject | Racing, anticipation |
| **Trail** | ⏪ | Follows behind | Chase scenes |
| **Frame** | 🖼️ | Fixed relative position | Interviews |
| **Locked** | 🔒 | Attached to subject | SnorriCam, fight scenes |
| **Predictive** | 🔮 | Anticipates motion | Fast action, sports |

## 👤 OPERATOR SKILL LEVELS

```
0.0 - 0.3 = Amateur     (shaky, unpredictable)
0.3 - 0.7 = Experienced (natural, human-like)
0.7 - 1.0 = Professional (near perfect, smooth)

Quick Settings:
□ Documentary  (0.6) - Natural, believable
□ Hollywood    (0.8) - Smooth, professional
□ Horror       (0.3) - Shaky, tense
□ Action       (0.4) - Energetic, dynamic
```

## 📏 SHOT DISTANCES

```
ECU (Extreme Close-Up)   = 0.5m  █
CU (Close-Up)           = 1.0m  ██
MCU (Medium Close-Up)   = 2.0m  ███
MS (Medium Shot)        = 3.0m  ████
CS (Cowboy Shot)        = 5.0m  ██████
FS (Full Shot)          = 10.0m ██████████
LS (Long Shot)          = 20.0m ████████████████████
ELS (Extreme Long Shot) = 50.0m ██████████████████████████████████████████████████
```

## 🎥 CAMERA ANGLES

```
Eye Level     → 0°      (Neutral)
Low Angle     → -30°    (Powerful, dominant)
High Angle    → +30°    (Vulnerable, small)
Dutch Angle   → 15-45°  (Tension, unease)
Bird's-Eye    → 90°     (Top-down, omniscient)
```

## 💫 MOTION PRESETS QUICK REFERENCE

### Handheld
```
Static      → Subtle, living shot
Walking     → Bouncy, following
Running     → Intense, chaotic
Steadicam   → Smooth glide
Documentary → Natural, believable
```

### Vehicle
```
Car Idle     → Engine vibration
Car Driving  → Road vibration
Helicopter   → Rotor shake
Boat         → Rocking motion
```

### Impact
```
Explosion    → Violent shockwave
Earthquake   → Rolling tremor
Footstep     → Step vibration
Collision    → Sharp impact
```

### Cinematic
```
Breathing    → Subtle organic
Drift        → Slow floating
Horror Shake → Tense, erratic
Action Cam   → Dynamic energy
```

## ⚙️ KEY PARAMETERS

### Shake Controls
```
Location X/Y/Z → Position movement (0.0-5.0)
Rotation X/Y/Z → Angular movement (0-360°)
Frequency      → Speed of oscillation (0.1-20.0)
Intensity      → Global strength multiplier
Smoothness     → Transition smoothness (0.0-1.0)
```

### Physics
```
Mass           → Weight (0.1-100 kg)
Spring         → Return force (0-1000)
Damping        → Energy dissipation (0-100)
Inertia        → Momentum simulation
Follow Through → Motion continuation
```

### Tracking
```
Target Distance → How far from subject (0.5-50m)
Height Offset   → Vertical position (-10 to +10m)
Smoothing       → Movement smoothness (0.0-1.0)
Prediction      → Frames ahead (0-30)
```

## 🎚️ MOTION LAYERS

```
Layer 1: Base Motion (Handheld)    → Blend Mode: Add
Layer 2: Impact (Explosion)        → Blend Mode: Add  
Layer 3: Breathing (Subtle)        → Blend Mode: Multiply

Blend Modes:
□ Add      → Combine motions
□ Multiply → Amplify effects
□ Replace  → Override previous
```

## ⏱️ EVENT TRIGGERS

```
Event at Frame 50:
Duration: 30 frames
Intensity: 1.5
Direction: (1,0,0) [right]
Decay: Smooth

Decay Curves:
Linear      ████████░░░░
Exponential ██████░░░░░░
Smooth      ████░░░░████
Sustained   ████████░░░░
```

## 📊 SHOT GENERATOR

### Quick Shot Types
```
Close-Up    → Emotional, detailed
Medium      → Standard dialogue
Long        → Environmental
POV         → Character perspective
Tracking    → Following action
```

### Action Sequences
```
Walk    → 3 shots (LS, MS, CU)
Run     → 3 shots (ELS, MS, ECU)
Drive   → 4 shots (ELS, LS, OTS, CU)
Dialogue → 4 shots (2-shot, OTSx2, CU)
Action  → 5 shots (ELS, Low, Dutch, POV, CU)
```

### Cinematic Styles
```
Hollywood    → Classic coverage (7 shots)
Documentary  → Observational (5 shots)
Horror       → Tense framing (6 shots)
Action       → Dynamic (7 shots)
Romantic     → Intimate (6 shots)
```

## 🎪 CAMERA RIGS

```
Dolly Rig:
├── Track (curve path)
├── Cart
├── Mount
└── Camera

Steadicam:
├── Vest (hidden)
├── Arm
├── Sled
├── Gimbal
└── Camera

Car Rig:
├── Chassis
├── Hood Cam
├── Side Cam
└── Chase Cam

SnorriCam:
├── Bracket (attached to subject)
├── Arm
└── Camera
```

## ⌨️ KEYBOARD SHORTCUTS

| Shortcut | Function |
|----------|----------|
| `N` | Toggle sidebar (Camera Motion tab) |
| `Space` | Play/Stop animation |
| `Alt + A` | Bake current shot |
| `Shift + T` | Toggle tracking |
| `Shift + S` | Add quick shot |
| `Ctrl + Shift + P` | Apply preset |
| `Ctrl + Shift + R` | Randomize seed |
| `Ctrl + Shift + C` | Create camera rig |

## 🔧 QUICK FIXES

### Problem: Camera moves when add-on idle
```
Fix: Update to v2.1.0 - Handler now only activates when features enabled
```

### Problem: Not following target
```
Checklist:
□ Tracking enabled?
□ Target object selected?
□ Camera selected?
□ In active viewport?
```

### Problem: Motion too jerky
```
Solution: Increase smoothing (0.7-0.9) or enable operator behavior
```

### Problem: Motion too smooth/robotic
```
Solution: Decrease smoothing (0.3-0.5) or add breathing (0.1-0.3)
```

### Problem: Performance slow
```
Quick fixes:
□ Reduce history length to 15
□ Disable motion path preview
□ Bake animation
□ Use lower sampling
```

## 📈 PERFORMANCE TIPS

```
Heavy Scene Optimization:
1. props.camera_trace.history_length = 15
2. props.show_motion_path = False
3. Use baking: bpy.ops.cinematic_camera.bake_animation()
4. Disable operator behavior temporarily
5. Use lower sampling rates (12-18)
```

## 🎨 CREATIVE RECIPES

### Living Interview Shot
```
Camera: Medium Shot
Tracking: Follow (fixed)
Operator: Skill 0.7, Breathing 0.3
Framing: Rule of thirds 0.6
Result: Professional, organic
```

### Intense Action Sequence
```
Shot 1: Extreme Long (establishing)
Shot 2: Tracking (following runner)
Shot 3: Handheld (POV runner)
Shot 4: Low Angle (hero shot)
Shot 5: Whip Pan (transition)
```

### Horror Atmosphere
```
Camera: Close-up
Tracking: Trail (behind)
Operator: Skill 0.3, Heavy breathing
Framing: Dutch angle, tight
Motion: Horror Shake preset
```

### Dream Sequence
```
Camera: Long Shot
Movement: Cinematic Drift
Operator: Skill 0.9, No micro-adjustments
Framing: Rule of thirds 0.3
Duration: Slow, floating motion
```

## 🔍 DEBUG INFO

Enable in Tracking panel:
```
□ Target position history
□ Calculated velocities
□ Prediction data
□ Operator state
□ Frame timing
```

## 📚 COMMAND REFERENCE

### Python Console Commands
```python
# Get add-on properties
props = bpy.context.scene.camera_motion

# Enable tracking
props.camera_trace.enabled = True
props.camera_trace.target_object = bpy.context.active_object

# Apply preset
bpy.ops.cinematic_camera.apply_preset(preset='HANDHELD_WALKING')

# Bake animation
bpy.ops.cinematic_camera.bake_animation()

# Create rig
bpy.ops.cinematic_camera.create_camera_rig(rig_type='DOLLY')
```

## 📞 SUPPORT

```
Documentation: /docs/USER_GUIDE.md
Issues: GitHub Issues
Discussions: GitHub Discussions
Email: your.email@example.com

Please include:
- Blender version
- Add-on version
- Steps to reproduce
- Console output
- Example .blend (if possible)
```

---

**CineTrack Pro v2.1.0** - *Professional Cinematic Camera System*  
Quick Reference Card - Last Updated: March 2026

```
┌─────────────────────────────────────────────────────────┐
│     Print this card and keep it near your workstation!   │
└─────────────────────────────────────────────────────────┘
```