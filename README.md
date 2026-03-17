# CineTrack Pro - Professional Cinematic Camera System for Blender

[![Blender Version](https://img.shields.io/badge/Blender-4.2+-orange.svg)](https://www.blender.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Version](https://img.shields.io/badge/Version-2.1.0-green.svg)](https://github.com/yourusername/cinetrack-pro)

**CineTrack Pro** transforms Blender into a professional cinematography tool with Hollywood-grade camera control.

## ✨ Features

- **Advanced Object Tracking** - 7 tracking modes with motion prediction
- **Operator Behavior Simulation** - Realistic human camera operation
- **Intelligent Framing** - Automatic rule of thirds and composition
- **Shot Management** - Plan and execute entire cinematic sequences
- **Professional Rigs** - Generate dolly, steadicam, car rigs
- **Motion Presets** - 20+ presets for any situation

## 🚀 Quick Installation

1. Download `cinetrack_pro-2.1.0.zip`
2. In Blender: `Edit → Preferences → Get Extensions → Install from Disk`
3. Select the downloaded ZIP file
4. Enable the add-on

## 📖 Documentation

Full documentation available in the [docs](docs/) folder:
- [User Guide](docs/USER_GUIDE.md)
- [Quick Reference](docs/QUICK_REFERENCE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

## 🎯 Quick Start

```python
1. Open 3D Viewport → Sidebar (N) → "Camera Motion" tab
2. Select your camera in "Target Camera"
3. Enable "Tracking ON" and set a target object
4. Watch your camera automatically follow!

![CineTrack Pro Banner](https://via.placeholder.com/1200x300/1a1a1a/ffffff?text=CineTrack+Pro+2.1.0+-+Professional+Cinematic+Camera+System)

[![Blender Version](https://img.shields.io/badge/Blender-4.0+-orange.svg)](https://www.blender.org)
[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)
[![Version](https://img.shields.io/badge/Version-2.1.0-green.svg)](https://github.com/yourusername/cinetrack-pro)
[![Downloads](https://img.shields.io/badge/Downloads-1k%2B-brightgreen.svg)](https://github.com/yourusername/cinetrack-pro/releases)

---

## 🎬 Overview

**CineTrack Pro** is a comprehensive cinematic camera motion system for Blender that transforms your animation workflow. Whether you're a professional animator, filmmaker, or hobbyist, this add-on provides Hollywood-grade camera control with features previously only available in high-end production software.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🎯 **Advanced Object Tracking** | Follow subjects with cinematic precision using 7 tracking modes |
| 👤 **Operator Behavior Simulation** | Realistic human camera operation with breathing, fatigue, and micro-adjustments |
| 🖼️ **Intelligent Framing** | Automatic rule of thirds, headroom control, and composition rules |
| 🔮 **Motion Prediction** | Anticipate subject movement for smoother tracking |
| 📋 **Shot Management System** | Plan, generate, and execute entire cinematic sequences |
| 🎥 **Professional Camera Rigs** | Generate dolly, steadicam, car rigs, and SnorriCam |
| 💫 **Motion Presets** | 20+ presets for handheld, vehicle, impact, and cinematic motion |
| ⚡ **Physics Simulation** | Spring-mass-damper systems for natural movement |
| 🔄 **Event Triggers** | Timed motion events for impacts and effects |
| 🎚️ **Motion Layers** | Combine multiple motion types with blending |
| 📊 **Real-time Preview** | Visualize motion paths and framing guides |

---

## 🚀 Quick Start

### Installation

1. **Download** `cinetrack_pro.py` from the [Releases](https://github.com/yourusername/cinetrack-pro/releases) page
2. **Install in Blender**:
   ```
   Edit → Preferences → Add-ons → Install → Select cinetrack_pro.py
   ```
3. **Enable** the add-on (search for "CineTrack Pro")
4. **Access** in 3D Viewport sidebar: Press `N` → "Camera Motion" tab

### First Steps

#### Basic Camera Shake (30 seconds)

```python
1. Select your camera in "Target Camera" field
2. Check "Shake ON" in main panel
3. Scrub timeline to see the effect
4. Adjust "Intensity" slider for desired strength
```

#### Simple Object Tracking (1 minute)

```python
1. Set "Target Camera" to your camera
2. Expand "Camera Tracking" panel
3. Set "Target Object" to follow
4. Click "Enable Tracking" in main panel
5. Move your target object and watch camera follow
```

#### Create Your First Shot (2 minutes)

```python
1. Set "Target Object" in Shot Generator panel
2. Choose "Quick Shot" type (Close-up, Medium, etc.)
3. Click "Add Quick Shot"
4. Click "Execute Shot" to animate
```

---

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) folder:

- **[User Guide](docs/USER_GUIDE.md)** - Complete feature documentation
- **[Quick Reference Card](docs/QUICK_REFERENCE.md)** - Cheat sheet for common tasks
- **[API Reference](docs/API_REFERENCE.md)** - For developers and scripters
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Solutions to common issues

---

## 🎯 Features in Detail

### 1. Advanced Camera Tracking

| Mode | Description | Use Case |
|------|-------------|----------|
| **Follow** | Camera follows behind subject | Standard tracking shots |
| **Orbit** | Camera circles around subject | Reveals, dramatic shots |
| **Lead** | Camera moves ahead of subject | Racing, anticipation |
| **Trail** | Camera follows behind | Chase scenes |
| **Frame** | Fixed position relative to subject | Interviews |
| **Locked** | Camera attached to subject | SnorriCam, fight scenes |
| **Predictive** | Anticipates subject motion | Fast action, sports |

**Parameters:**
- Distance control (Fixed/Dynamic/Composition)
- Height control (Fixed/Eye Level/Dynamic)
- Angle control with smoothing
- Motion prediction (0-30 frames ahead)

### 2. Operator Behavior Simulation

Simulates a real human camera operator:

| Parameter | Range | Effect |
|-----------|-------|--------|
| Skill Level | 0.0-1.0 | Low = amateur, High = professional |
| Reaction Time | 0.0-1.0s | Delay in responding to movement |
| Breathing | 0.1-2.0 Hz | Subtle rhythmic motion |
| Micro-adjustments | 0.1-5.0 Hz | Constant tiny corrections |
| Handheld Weight | 1-20 kg | Heavier = more inertia |
| Fatigue | 0.0-1.0 | Degrades performance over time |

### 3. Cinematic Framing Rules

- **Rule of Thirds** - Keep subject on intersection points
- **Auto Headroom** - Perfect spacing above subject
- **Lead Room** - Space in direction of movement
- **Horizon Stabilization** - Keep horizon level
- **Auto Focus Pull** - Automatic rack focus

### 4. Shot Management System

**Shot Categories:**
- **Distance-Based**: ECU to Extreme Long Shot
- **Angle-Based**: Eye Level to Dutch Angle
- **Movement-Based**: Pan to Whip Pan
- **Follow Shots**: Tracking to SnorriCam
- **Special Shots**: Two-Shot to Establishing

**Shot Generator:**
- Quick Shot presets
- Action sequences (Walk, Run, Drive, Dialogue, Action)
- Cinematic styles (Hollywood, Documentary, Horror, Action, Romantic)

### 5. Professional Camera Rigs

| Rig Type | Components | Best For |
|----------|------------|----------|
| **Dolly** | Track, Cart, Mount, Camera | Smooth tracking shots |
| **Steadicam** | Vest, Arm, Sled, Gimbal, Camera | Stabilized follow |
| **Car Rig** | Chassis, 3 camera mounts | Vehicle sequences |
| **SnorriCam** | Bracket, Arm, Camera | Body-mounted POV |

### 6. Motion Presets Library

**Handheld:** Static, Walking, Running, Steadicam, Documentary  
**Vehicle:** Car Idle, Car Driving, Helicopter, Boat  
**Impact:** Explosion, Earthquake, Footstep, Collision  
**Cinematic:** Breathing, Cinematic Drift, Horror Shake, Action Cam

---

## 📦 Installation Structure

```
cinetrack_pro.py
├── Blender registration info
├── CinematographyUtils class
├── Property groups
│   ├── ShakeControls
│   ├── PhysicsSettings
│   ├── CameraTraceProperties (NEW)
│   ├── ShotProperties (NEW)
│   └── ...
├── Motion engines
│   ├── MotionEngine (base shake)
│   └── AdvancedMotionEngine (tracking)
├── Operators (50+)
├── UI Panels (15+)
├── Preset data (20+ presets)
└── Registration code
```

---

## 🔧 Requirements

- **Blender**: Version 4.0.0 or higher
- **RAM**: 4GB minimum (8GB+ recommended)
- **Graphics**: OpenGL 3.3+ compatible
- **OS**: Windows 10/11, macOS 10.15+, Linux

---

## 📖 Usage Examples

### Example 1: Documentary Interview Shot

```python
# Settings
Camera: Medium Shot
Tracking: Follow (fixed distance)
Operator: Skill 0.8, Breathing 0.2
Framing: Rule of thirds 0.6, Headroom auto
Motion: Documentary preset
```

### Example 2: Action Chase Sequence

```python
# Shot 1: Establishing
Shot Type: Extreme Long Shot
Duration: 60 frames
Movement: Static

# Shot 2: Following
Shot Type: Tracking
Duration: 120 frames
Follow Mode: Trail

# Shot 3: POV
Shot Type: Handheld
Duration: 90 frames
Operator: Low skill (0.3), Heavy breathing
```

### Example 3: Horror Atmosphere

```python
# Settings
Camera: Close-up
Tracking: Trail (behind subject)
Operator: Skill 0.3, Micro-adjustments ON
Framing: Dutch angle, tight framing
Motion: Horror Shake preset
```

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Report Bugs**: Open an issue with detailed reproduction steps
2. **Suggest Features**: Share your ideas for new features
3. **Submit PRs**: Fix bugs or add features
4. **Share Presets**: Contribute your custom motion presets
5. **Documentation**: Help improve the docs

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/cinetrack-pro.git

# Install in Blender development build
# Copy cinetrack_pro.py to Blender's addons directory
```

### Code Style

- Follow PEP 8 guidelines
- Document all functions with docstrings
- Test with Blender 4.0+
- Keep backwards compatibility in mind

---

## 📋 Changelog

### Version 2.1.0 (Current)
- ✅ Advanced Object Tracking system
- ✅ Operator Behavior Simulation
- ✅ Cinematic Framing Rules
- ✅ Multiple Target Tracking
- ✅ Motion Prediction
- ✅ Shot Management System
- ✅ Camera Rig Generator
- ✅ Fixed auto-rotation on installation
- ✅ Improved tracking accuracy

### Version 2.0.0
- Initial release with shake system
- Motion presets library
- Physics simulation
- Event triggers
- Motion layers

### Planned for 3.0.0
- Camera dolly system with UI control
- Motion capture integration
- AI-powered shot suggestion
- Real-time collaboration
- VR camera rigs
- Stereo 3D support

---

## 🐛 Known Issues

- **Performance**: Very complex scenes may experience slowdown
  - *Workaround*: Reduce history length, disable real-time preview
- **Multiple Targets**: Full implementation pending
  - *Workaround*: Use primary target with blend modes
- **Mac Compatibility**: Tested on Intel, M1/M2 pending verification

---

## 📞 Support

- **Documentation**: See [`docs/`](docs/) folder
- **Issues**: [GitHub Issues](https://github.com/yourusername/cinetrack-pro/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/cinetrack-pro/discussions)
- **Email**: your.email@example.com

---

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

```
CineTrack Pro - Professional Cinematic Camera System for Blender
Copyright (C) 2026 Your Name

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
```

---

## 🙏 Acknowledgements

- Blender Foundation for the amazing software
- Contributors and testers
- Open-source community for inspiration
- Professional cinematographers who provided feedback

---

## 📊 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yourusername/cinetrack-pro&type=Date)](https://star-history.com/#yourusername/cinetrack-pro&Date)

---

## 🔗 Links

- [Documentation](docs/USER_GUIDE.md)
- [Download Latest Release](https://github.com/yourusername/cinetrack-pro/releases)
- [Report Bug](https://github.com/yourusername/cinetrack-pro/issues)
- [Request Feature](https://github.com/yourusername/cinetrack-pro/issues)
- [Blender Market](https://blendermarket.com) (Coming Soon)

---

**Made with ❤️ for the Blender Community**

*CineTrack Pro - Professional Cinematic Camera System*  
*Version 2.1.0 MEGA UPDATE*  
*March 2026*

---

## 🚦 Quick Installation Command

```bash
# Linux/Mac
cp cinetrack_pro.py ~/.config/blender/4.0/scripts/addons/

# Windows (PowerShell)
Copy-Item cinetrack_pro.py "$env:APPDATA\Blender Foundation\Blender\4.0\scripts\addons\"
```

---

## 📸 Screenshots

*(Add screenshots here showing the interface, tracking in action, shot manager, etc.)*

```
[Screenshot 1: Main Interface]
[Screenshot 2: Tracking in Action]
[Screenshot 3: Shot Manager]
[Screenshot 4: Camera Rigs]
```

---

*This README was last updated on March 17, 2026*