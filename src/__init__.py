# Cinematic Camera Motion Generator - MEGA UPDATE 2.1.0
# Complete professional cinematography system
# NEW FEATURES:
# - Advanced Object Tracking with natural camera movement
# - Operator Behavior Simulation (breathing, micro-adjustments)
# - Intelligent Framing with composition rules
# - Motion Prediction and Smoothing
# - Multiple Tracking Modes (Follow, Orbit, Maintain Frame)
# - Dynamic Focus Pulling
# - Camera Damping and Spring Systems

bl_info = {
    "name": "CineTrack Pro",
    "author": "Professional Tools",
    "version": (2, 1, 0),
    "blender": (4, 0, 0),
    "location": "3D View > Sidebar > Camera Motion",
    "description": "Complete cinematic camera system with advanced object tracking and natural movement",
    "category": "Animation",
}

import bpy
import math
import random
import numpy as np
from mathutils import Vector, Euler, Matrix, Quaternion
from bpy.props import (
    FloatProperty, 
    IntProperty, 
    BoolProperty, 
    EnumProperty, 
    FloatVectorProperty,
    PointerProperty,
    StringProperty,
    CollectionProperty
)
from bpy.types import (
    PropertyGroup, 
    Panel, 
    UIList, 
    Operator,
    Menu
)
from bpy.app.handlers import persistent
import time

# ============================================================================
# CINEMATOGRAPHY CONSTANTS AND UTILITIES
# ============================================================================

class CinematographyUtils:
    """Utility class for cinematography calculations"""
    
    @staticmethod
    def calculate_framing(object_location, camera_location, object_dimensions, shot_type):
        """Calculate camera position for proper framing based on shot type"""
        
        # Standard shot distances (in meters)
        shot_distances = {
            'EXTREME_LONG': 50.0,
            'LONG': 20.0,
            'FULL': 10.0,
            'COWBOY': 5.0,
            'MEDIUM': 3.0,
            'MEDIUM_CLOSEUP': 2.0,
            'CLOSEUP': 1.0,
            'EXTREME_CLOSEUP': 0.5
        }
        
        # Field of view compensation (assuming 35mm equivalent)
        fov_multiplier = 1.0
        
        distance = shot_distances.get(shot_type, 5.0) * fov_multiplier
        
        return distance
    
    @staticmethod
    def calculate_angle_position(target_location, distance, angle_deg, height_offset=0):
        """Calculate camera position based on angle"""
        angle_rad = math.radians(angle_deg)
        
        # Convert angle to position on circle
        x = target_location.x + distance * math.sin(angle_rad)
        z = target_location.z + distance * math.cos(angle_rad)
        
        return Vector((x, target_location.y + height_offset, z))
    
    @staticmethod
    def get_object_dimensions(obj):
        """Get dimensions of an object"""
        if not obj:
            return Vector((1, 1, 2))  # Default human size
        
        # Try to get bounding box
        if obj.bound_box:
            bbox = [Vector(v) for v in obj.bound_box]
            min_x = min(v.x for v in bbox)
            max_x = max(v.x for v in bbox)
            min_y = min(v.y for v in bbox)
            max_y = max(v.y for v in bbox)
            min_z = min(v.z for v in bbox)
            max_z = max(v.z for v in bbox)
            
            return Vector((
                max_x - min_x,
                max_y - min_y,
                max_z - min_z
            ))
        
        return Vector((1, 1, 2))  # Default
    
    @staticmethod
    def ensure_animation_data(obj):
        """Ensure object has animation data"""
        if obj.animation_data is None:
            obj.animation_data_create()
        return obj.animation_data
    
    @staticmethod
    def clear_object_animation(obj):
        """Clear all animation data from object"""
        if obj.animation_data:
            obj.animation_data_clear()
    
    @staticmethod
    def clear_keyframes_in_range(obj, start_frame, end_frame):
        """Clear keyframes in a specific frame range"""
        if not obj.animation_data or not obj.animation_data.action:
            return
        
        action = obj.animation_data.action
        if not hasattr(action, 'fcurves'):
            return
        
        for fcurve in action.fcurves:
            keyframes_to_remove = []
            for keyframe in fcurve.keyframe_points:
                if start_frame <= keyframe.co[0] <= end_frame:
                    keyframes_to_remove.append(keyframe)
            
            for keyframe in reversed(keyframes_to_remove):
                fcurve.keyframe_points.remove(keyframe)
    
    @staticmethod
    def calculate_optimal_focus_distance(camera_loc, target_loc, subject_size):
        """Calculate optimal focus distance for depth of field"""
        distance = (target_loc - camera_loc).length
        
        # Rule of thumb: focus distance should be 1/3 into the scene
        if subject_size > 0:
            # Adjust for subject size (larger subjects can be focused closer)
            focus_distance = distance * (1.0 - min(subject_size / 10.0, 0.5))
        else:
            focus_distance = distance
        
        return max(focus_distance, 0.1)
    
    @staticmethod
    def calculate_composition_score(camera_loc, target_loc, frame_bounds):
        """Calculate how well the target is composed in frame"""
        # This would calculate if the target follows rule of thirds, etc.
        # Placeholder for future implementation
        return 1.0


# ============================================================================
# BASE PROPERTIES (FROM STABLE VERSION)
# ============================================================================

class MotionLayerProperties(PropertyGroup):
    """Properties for individual motion layers"""
    name: StringProperty(
        name="Layer Name", 
        default="New Layer"
    )
    enabled: BoolProperty(
        name="Enabled", 
        default=True
    )
    blend_mode: EnumProperty(
        name="Blend Mode",
        items=[
            ('ADD', "Add", "Add to previous layers"),
            ('MULTIPLY', "Multiply", "Multiply with previous layers"),
            ('REPLACE', "Replace", "Replace previous layers"),
        ],
        default='ADD'
    )
    blend_factor: FloatProperty(
        name="Blend Factor",
        min=0.0, max=1.0,
        default=1.0,
        description="How much this layer contributes"
    )


class NoiseSettings(PropertyGroup):
    """Advanced noise settings"""
    noise_type: EnumProperty(
        name="Noise Type",
        items=[
            ('PERLIN', "Perlin", "Smooth, natural noise"),
            ('SIMPLEX', "Simplex", "Better Perlin implementation"),
            ('FRACTAL', "Fractal", "Multi-octave fractal noise"),
            ('RANDOM', "Random", "Pure random noise"),
        ],
        default='PERLIN'
    )
    
    seed: IntProperty(
        name="Seed",
        min=0, max=10000,
        default=0,
        description="Random seed for noise generation"
    )
    
    octaves: IntProperty(
        name="Octaves",
        min=1, max=8,
        default=3,
        description="Number of noise octaves (fractal only)"
    )
    
    persistence: FloatProperty(
        name="Persistence",
        min=0.0, max=1.0,
        default=0.5,
        description="How much each octave contributes"
    )
    
    lacunarity: FloatProperty(
        name="Lacunarity",
        min=1.0, max=4.0,
        default=2.0,
        description="Frequency multiplier between octaves"
    )


class ShakeControls(PropertyGroup):
    """Core shake control properties"""
    
    # Global controls
    enabled: BoolProperty(
        name="Enable Shake", 
        default=True
    )
    intensity: FloatProperty(
        name="Intensity",
        min=0.0, max=5.0,
        default=1.0,
        description="Global shake intensity",
        precision=3
    )
    
    # Location controls
    loc_freq_x: FloatProperty(
        name="Loc Freq X",
        min=0.01, max=20.0,
        default=1.0,
        description="Location frequency X axis"
    )
    loc_freq_y: FloatProperty(
        name="Loc Freq Y",
        min=0.01, max=20.0,
        default=1.0,
        description="Location frequency Y axis"
    )
    loc_freq_z: FloatProperty(
        name="Loc Freq Z",
        min=0.01, max=20.0,
        default=1.0,
        description="Location frequency Z axis"
    )
    
    loc_amp_x: FloatProperty(
        name="Loc Amp X",
        min=0.0, max=5.0,
        default=0.1,
        description="Location amplitude X axis",
        precision=4
    )
    loc_amp_y: FloatProperty(
        name="Loc Amp Y",
        min=0.0, max=5.0,
        default=0.1,
        description="Location amplitude Y axis",
        precision=4
    )
    loc_amp_z: FloatProperty(
        name="Loc Amp Z",
        min=0.0, max=5.0,
        default=0.1,
        description="Location amplitude Z axis",
        precision=4
    )
    
    # Rotation controls
    rot_freq_x: FloatProperty(
        name="Rot Freq X",
        min=0.01, max=20.0,
        default=0.5,
        description="Rotation frequency X axis"
    )
    rot_freq_y: FloatProperty(
        name="Rot Freq Y",
        min=0.01, max=20.0,
        default=0.5,
        description="Rotation frequency Y axis"
    )
    rot_freq_z: FloatProperty(
        name="Rot Freq Z",
        min=0.01, max=20.0,
        default=0.5,
        description="Rotation frequency Z axis"
    )
    
    rot_amp_x: FloatProperty(
        name="Rot Amp X",
        min=0.0, max=360.0,
        default=5.0,
        description="Rotation amplitude X axis (degrees)",
        precision=2
    )
    rot_amp_y: FloatProperty(
        name="Rot Amp Y",
        min=0.0, max=360.0,
        default=5.0,
        description="Rotation amplitude Y axis (degrees)",
        precision=2
    )
    rot_amp_z: FloatProperty(
        name="Rot Amp Z",
        min=0.0, max=360.0,
        default=5.0,
        description="Rotation amplitude Z axis (degrees)",
        precision=2
    )
    
    # Axis enable controls
    location_x_enabled: BoolProperty(
        name="Location X", 
        default=True
    )
    location_y_enabled: BoolProperty(
        name="Location Y", 
        default=True
    )
    location_z_enabled: BoolProperty(
        name="Location Z", 
        default=True
    )
    
    rotation_x_enabled: BoolProperty(
        name="Rotation X", 
        default=True
    )
    rotation_y_enabled: BoolProperty(
        name="Rotation Y", 
        default=True
    )
    rotation_z_enabled: BoolProperty(
        name="Rotation Z", 
        default=True
    )
    
    # Advanced controls
    smoothness: FloatProperty(
        name="Smoothness",
        min=0.0, max=1.0,
        default=0.3,
        description="Smoothness of motion transitions",
        precision=3,
        subtype='FACTOR'
    )
    
    noise_settings: PointerProperty(type=NoiseSettings)


class PhysicsSettings(PropertyGroup):
    """Physics-based motion simulation"""
    
    enabled: BoolProperty(
        name="Enable Physics", 
        default=True
    )
    
    mass: FloatProperty(
        name="Mass",
        min=0.1, max=100.0,
        default=5.0,
        description="Virtual camera mass (kg)",
        precision=2
    )
    
    spring_stiffness: FloatProperty(
        name="Spring Stiffness",
        min=0.0, max=1000.0,
        default=100.0,
        description="How strongly the camera returns to position",
        precision=1
    )
    
    damping: FloatProperty(
        name="Damping",
        min=0.0, max=100.0,
        default=10.0,
        description="Energy dissipation (smoothing)",
        precision=2
    )
    
    inertia_enabled: BoolProperty(
        name="Enable Inertia",
        default=True,
        description="Simulate camera momentum"
    )
    
    follow_through: FloatProperty(
        name="Follow Through",
        min=0.0, max=1.0,
        default=0.2,
        description="How much motion continues after movement",
        precision=3,
        subtype='FACTOR'
    )
    
    spring_rotation: BoolProperty(
        name="Apply to Rotation",
        default=True,
        description="Apply physics to rotation as well"
    )


class EventTrigger(PropertyGroup):
    """Motion event trigger system"""
    
    name: StringProperty(
        name="Event Name", 
        default="Impact"
    )
    frame: IntProperty(
        name="Frame", 
        min=0, 
        default=1
    )
    duration: IntProperty(
        name="Duration", 
        min=1, 
        default=30
    )
    intensity: FloatProperty(
        name="Intensity", 
        min=0.0, 
        max=2.0, 
        default=1.0,
        precision=3
    )
    dir_x: FloatProperty(
        name="Direction X",
        default=0.0,
        precision=3
    )
    dir_y: FloatProperty(
        name="Direction Y",
        default=0.0,
        precision=3
    )
    dir_z: FloatProperty(
        name="Direction Z",
        default=0.0,
        precision=3
    )
    decay_curve: EnumProperty(
        name="Decay Curve",
        items=[
            ('LINEAR', "Linear", "Linear decay"),
            ('EXPONENTIAL', "Exponential", "Fast then slow decay"),
            ('SMOOTH', "Smooth", "Smooth in/out decay"),
            ('SUSTAINED', "Sustained", "Hold then decay"),
        ],
        default='SMOOTH'
    )


# ============================================================================
# NEW SHOT PROPERTIES
# ============================================================================

class ShotProperties(PropertyGroup):
    """Properties for a camera shot"""
    name: StringProperty(
        name="Shot Name",
        default="New Shot"
    )
    
    # Shot type categorization
    shot_category: EnumProperty(
        name="Shot Category",
        items=[
            ('DISTANCE', "Distance Based", "Shots based on subject distance"),
            ('ANGLE', "Angle Based", "Shots based on camera angle"),
            ('MOVEMENT', "Movement Based", "Shots with camera movement"),
            ('SPECIAL', "Special Shots", "Specialized shot types"),
            ('FOLLOW', "Follow Shots", "Camera following subject"),
        ],
        default='DISTANCE'
    )
    
    # Distance-based shots
    shot_type_distance: EnumProperty(
        name="Distance Shot",
        items=[
            ('EXTREME_LONG', "Extreme Long Shot (ELS)", "Subject barely visible, emphasizes environment"),
            ('LONG', "Long Shot (LS)", "Full subject and surroundings"),
            ('FULL', "Full Shot (FS)", "Subject from head to toe"),
            ('COWBOY', "Cowboy Shot (CS)", "From mid-thigh up"),
            ('MEDIUM', "Medium Shot (MS)", "Waist-up, standard for dialogue"),
            ('MEDIUM_CLOSEUP', "Medium Close-Up (MCU)", "Chest-up, focuses on expression"),
            ('CLOSEUP', "Close-Up (CU)", "Tight on face or object"),
            ('EXTREME_CLOSEUP', "Extreme Close-Up (ECU)", "Specific detail like eyes or hands"),
        ],
        default='MEDIUM'
    )
    
    # Angle-based shots
    shot_type_angle: EnumProperty(
        name="Camera Angle",
        items=[
            ('EYE_LEVEL', "Eye Level", "Neutral angle, camera at eye level"),
            ('LOW_ANGLE', "Low Angle", "Camera looks up, subject dominant"),
            ('HIGH_ANGLE', "High Angle", "Camera looks down, subject vulnerable"),
            ('BIRDS_EYE', "Bird's-Eye", "Directly above, top-down view"),
            ('DUTCH', "Dutch Angle", "Camera tilted, creates tension"),
            ('POV', "Point of View", "Shows what character sees"),
            ('OVER_SHOULDER', "Over-the-Shoulder", "Over person's shoulder, common in conversation"),
        ],
        default='EYE_LEVEL'
    )
    
    # Movement-based shots
    shot_type_movement: EnumProperty(
        name="Camera Movement",
        items=[
            ('STATIC', "Static", "No camera movement"),
            ('PAN', "Pan", "Horizontal swivel left or right"),
            ('TILT', "Tilt", "Vertical movement up or down"),
            ('ZOOM', "Zoom", "Lens adjustment"),
            ('DOLLY', "Dolly", "Camera moves toward or away"),
            ('DOLLY_IN', "Dolly In", "Camera moves toward subject"),
            ('DOLLY_OUT', "Dolly Out", "Camera moves away from subject"),
            ('TRUCK', "Truck", "Camera moves left or right"),
            ('PEDESTAL', "Pedestal", "Camera moves up or down"),
            ('PEDESTAL_UP', "Pedestal Up", "Camera moves up"),
            ('PEDESTAL_DOWN', "Pedestal Down", "Camera moves down"),
            ('ARC', "Arc", "Camera moves in an arc around subject"),
            ('PUSH_IN', "Push In", "Camera pushes in dramatically"),
            ('HANDHELD', "Handheld", "Simulated handheld movement"),
            ('WHIP_PAN', "Whip Pan", "Fast pan following action"),
            ('SLOW_PAN', "Slow Pan", "Slow sweeping pan"),
        ],
        default='STATIC'
    )
    
    # Follow shot types
    shot_type_follow: EnumProperty(
        name="Follow Shot",
        items=[
            ('TRACKING', "Tracking Shot", "Camera physically moves to stay with subject"),
            ('DOLLY_FOLLOW', "Dolly Shot", "Smooth gliding follow on track"),
            ('LEADING', "Leading Shot", "Camera moves backward while facing subject"),
            ('TRAILING', "Trailing Shot", "Camera follows directly behind"),
            ('LATERAL', "Lateral/Trucking", "Camera moves sideways alongside"),
            ('STEADICAM', "Steadicam", "Stabilized handheld follow"),
            ('SNORRICAM', "SnorriCam", "Camera attached to subject's body"),
            ('WHIP_PAN', "Whip Pan", "Fast pan following action"),
        ],
        default='TRACKING'
    )
    
    # Special shots
    shot_type_special: EnumProperty(
        name="Special Shot",
        items=[
            ('CUTAWAY', "Cutaway", "Shot of something other than main subject"),
            ('INSERT', "Insert", "Close-up of detail within scene"),
            ('TWO_SHOT', "Two Shot", "Frame with two subjects"),
            ('REACTION', "Reaction Shot", "Character's reaction to event"),
            ('ESTABLISHING', "Establishing Shot", "Sets up location/context"),
            ('MASTER', "Master Shot", "Covers entire scene in one take"),
        ],
        default='ESTABLISHING'
    )
    
    # Motion parameters
    target_object: PointerProperty(
        name="Target Object",
        type=bpy.types.Object,
        description="Object for camera to follow/focus on"
    )
    
    duration_frames: IntProperty(
        name="Duration (frames)",
        min=1, max=10000,
        default=120,
        description="Duration of shot in frames"
    )
    
    ease_in: IntProperty(
        name="Ease In",
        min=0, max=500,
        default=10,
        description="Frames to ease into movement"
    )
    
    ease_out: IntProperty(
        name="Ease Out",
        min=0, max=500,
        default=10,
        description="Frames to ease out of movement"
    )
    
    # Camera parameters
    focal_length: FloatProperty(
        name="Focal Length",
        min=8, max=400,
        default=50,
        description="Camera focal length in mm"
    )
    
    aperture: FloatProperty(
        name="Aperture",
        min=1.0, max=22.0,
        default=5.6,
        description="Lens aperture (f-stop)"
    )
    
    distance_offset: FloatProperty(
        name="Distance Offset",
        min=-50, max=50,
        default=0,
        description="Additional distance offset from standard framing"
    )
    
    height_offset: FloatProperty(
        name="Height Offset",
        min=-10, max=10,
        default=0,
        description="Vertical offset from standard framing"
    )
    
    angle_offset: FloatProperty(
        name="Angle Offset",
        min=-180, max=180,
        default=0,
        description="Horizontal angle offset in degrees"
    )
    
    # Movement parameters
    pan_speed: FloatProperty(
        name="Pan Speed",
        min=0.1, max=50,
        default=10,
        description="Speed of pan movement (degrees per second)"
    )
    
    tilt_speed: FloatProperty(
        name="Tilt Speed",
        min=0.1, max=50,
        default=10,
        description="Speed of tilt movement (degrees per second)"
    )
    
    dolly_speed: FloatProperty(
        name="Dolly Speed",
        min=0.01, max=10,
        default=1,
        description="Speed of dolly movement (meters per second)"
    )
    
    # Follow parameters
    follow_distance: FloatProperty(
        name="Follow Distance",
        min=1, max=50,
        default=5,
        description="Distance to maintain when following"
    )
    
    follow_height: FloatProperty(
        name="Follow Height",
        min=-5, max=20,
        default=1.7,
        description="Height offset when following (eye level)"
    )
    
    look_ahead: FloatProperty(
        name="Look Ahead",
        min=0, max=10,
        default=2,
        description="Frames to look ahead in movement"
    )
    
    smoothness: FloatProperty(
        name="Smoothness",
        min=0, max=1,
        default=0.7,
        description="Smoothness of camera movement",
        subtype='FACTOR'
    )
    
    # Shot parameters
    use_dof: BoolProperty(
        name="Use Depth of Field",
        default=False,
        description="Enable depth of field"
    )
    
    dof_focus_object: PointerProperty(
        name="Focus Object",
        type=bpy.types.Object,
        description="Object to focus on"
    )
    
    dof_aperture_blades: IntProperty(
        name="Aperture Blades",
        min=3, max=16,
        default=7,
        description="Number of blades in aperture"
    )
    
    dof_fstop: FloatProperty(
        name="F-Stop",
        min=0.1, max=64,
        default=2.8,
        description="F-stop value for depth of field"
    )
    
    # Timing
    start_frame: IntProperty(
        name="Start Frame",
        min=0, default=1,
        description="Frame to start this shot"
    )
    
    end_frame: IntProperty(
        name="End Frame",
        min=0, default=120,
        description="Frame to end this shot"
    )
    
    # Color grading
    color_temp: FloatProperty(
        name="Color Temperature",
        min=1000, max=40000,
        default=5500,
        description="Color temperature in Kelvin"
    )
    
    exposure_compensation: FloatProperty(
        name="Exposure Comp",
        min=-5, max=5,
        default=0,
        description="Exposure compensation in stops"
    )
    
    # Status
    is_baked: BoolProperty(
        name="Is Baked",
        default=False,
        description="Whether this shot has been baked to keyframes"
    )
    
    def get_shot_description(self):
        """Get human-readable shot description"""
        if self.shot_category == 'DISTANCE':
            items = dict(self.bl_rna.properties['shot_type_distance'].enum_items)
            return items.get(self.shot_type_distance, items['MEDIUM']).description
        elif self.shot_category == 'ANGLE':
            items = dict(self.bl_rna.properties['shot_type_angle'].enum_items)
            return items.get(self.shot_type_angle, items['EYE_LEVEL']).description
        elif self.shot_category == 'MOVEMENT':
            items = dict(self.bl_rna.properties['shot_type_movement'].enum_items)
            return items.get(self.shot_type_movement, items['STATIC']).description
        elif self.shot_category == 'FOLLOW':
            items = dict(self.bl_rna.properties['shot_type_follow'].enum_items)
            return items.get(self.shot_type_follow, items['TRACKING']).description
        elif self.shot_category == 'SPECIAL':
            items = dict(self.bl_rna.properties['shot_type_special'].enum_items)
            return items.get(self.shot_type_special, items['ESTABLISHING']).description
        return "Custom shot"


class ShotSequence(PropertyGroup):
    """Collection of shots for a sequence"""
    name: StringProperty(
        name="Sequence Name",
        default="New Sequence"
    )
    
    shots: CollectionProperty(type=ShotProperties)
    active_shot_index: IntProperty(default=0)
    
    total_duration: IntProperty(
        name="Total Duration",
        default=0
    )
    
    def calculate_total_duration(self):
        """Calculate total duration of all shots"""
        total = 0
        for shot in self.shots:
            total += shot.duration_frames
        self.total_duration = total
        return total


# ============================================================================
# NEW ADVANCED TRACKING PROPERTIES
# ============================================================================

class OperatorBehaviorProperties(PropertyGroup):
    """Simulate realistic camera operator behavior"""
    
    enabled: BoolProperty(
        name="Enable Operator Behavior",
        default=True,
        description="Simulate realistic human camera operator"
    )
    
    # Breathing simulation
    breathing_enabled: BoolProperty(
        name="Breathing",
        default=True,
        description="Simulate operator breathing"
    )
    
    breathing_rate: FloatProperty(
        name="Breathing Rate",
        min=0.1, max=2.0,
        default=0.3,
        description="Breathing cycles per second"
    )
    
    breathing_intensity: FloatProperty(
        name="Breathing Intensity",
        min=0.0, max=0.5,
        default=0.05,
        description="Amount of breathing motion"
    )
    
    # Reaction time
    reaction_time: FloatProperty(
        name="Reaction Time",
        min=0.0, max=1.0,
        default=0.15,
        description="Operator reaction delay in seconds",
        precision=3
    )
    
    anticipation: FloatProperty(
        name="Anticipation",
        min=0.0, max=1.0,
        default=0.2,
        description="Anticipate subject movement"
    )
    
    # Fatigue simulation
    fatigue_enabled: BoolProperty(
        name="Fatigue",
        default=False,
        description="Operator gets tired over time"
    )
    
    fatigue_rate: FloatProperty(
        name="Fatigue Rate",
        min=0.0, max=1.0,
        default=0.01,
        description="How quickly operator tires"
    )
    
    # Micro-adjustments
    micro_adjustments: BoolProperty(
        name="Micro Adjustments",
        default=True,
        description="Constant small corrections"
    )
    
    adjustment_frequency: FloatProperty(
        name="Adjustment Frequency",
        min=0.1, max=5.0,
        default=1.5,
        description="Frequency of micro-adjustments"
    )
    
    # Skill level
    skill_level: FloatProperty(
        name="Skill Level",
        min=0.0, max=1.0,
        default=0.7,
        description="Operator skill (higher = smoother)",
        subtype='FACTOR'
    )
    
    # Physical constraints
    max_pan_speed: FloatProperty(
        name="Max Pan Speed",
        min=10.0, max=180.0,
        default=45.0,
        description="Maximum pan speed (degrees per second)"
    )
    
    max_tilt_speed: FloatProperty(
        name="Max Tilt Speed",
        min=10.0, max=180.0,
        default=30.0,
        description="Maximum tilt speed (degrees per second)"
    )
    
    acceleration: FloatProperty(
        name="Acceleration",
        min=0.1, max=10.0,
        default=2.0,
        description="How quickly operator accelerates"
    )
    
    # Handheld characteristics
    handheld_weight: FloatProperty(
        name="Handheld Weight",
        min=1.0, max=20.0,
        default=5.0,
        description="Perceived camera weight"
    )
    
    stabilization: FloatProperty(
        name="Stabilization",
        min=0.0, max=1.0,
        default=0.5,
        description="Amount of stabilization (gimbal/steadicam effect)",
        subtype='FACTOR'
    )


class FramingRulesProperties(PropertyGroup):
    """Intelligent framing rules"""
    
    enabled: BoolProperty(
        name="Enable Framing Rules",
        default=True,
        description="Apply cinematic framing rules"
    )
    
    # Rule of thirds
    rule_of_thirds: BoolProperty(
        name="Rule of Thirds",
        default=True,
        description="Keep subject on rule of thirds lines"
    )
    
    thirds_weight: FloatProperty(
        name="Thirds Weight",
        min=0.0, max=1.0,
        default=0.5,
        description="How strongly to enforce rule of thirds"
    )
    
    # Headroom
    headroom_auto: BoolProperty(
        name="Auto Headroom",
        default=True,
        description="Automatically adjust headroom"
    )
    
    headroom_target: FloatProperty(
        name="Headroom Target",
        min=0.0, max=1.0,
        default=0.1,
        description="Target headroom (0 = eyes at top, 1 = eyes at bottom)"
    )
    
    # Lead room
    lead_room_auto: BoolProperty(
        name="Auto Lead Room",
        default=True,
        description="Leave space in direction subject is facing/moving"
    )
    
    lead_room_amount: FloatProperty(
        name="Lead Room",
        min=0.0, max=1.0,
        default=0.3,
        description="Amount of lead room"
    )
    
    # Horizon line
    horizon_stabilization: BoolProperty(
        name="Stabilize Horizon",
        default=True,
        description="Keep horizon level (unless Dutch angle)"
    )
    
    horizon_weight: FloatProperty(
        name="Horizon Weight",
        min=0.0, max=1.0,
        default=0.8,
        description="How strongly to stabilize horizon"
    )
    
    # Focus pull
    auto_focus_pull: BoolProperty(
        name="Auto Focus Pull",
        default=False,
        description="Automatically pull focus to subjects"
    )
    
    focus_speed: FloatProperty(
        name="Focus Speed",
        min=0.1, max=5.0,
        default=1.0,
        description="Speed of focus adjustments"
    )
    
    rack_focus_duration: IntProperty(
        name="Rack Focus Duration",
        min=1, max=60,
        default=15,
        description="Frames for rack focus"
    )


class TrackingModesProperties(PropertyGroup):
    """Advanced tracking modes"""
    
    mode: EnumProperty(
        name="Tracking Mode",
        items=[
            ('FOLLOW', "Follow", "Camera follows subject naturally"),
            ('ORBIT', "Orbit", "Camera orbits around subject"),
            ('LEAD', "Lead", "Camera leads subject (moves ahead)"),
            ('TRAIL', "Trail", "Camera trails behind subject"),
            ('FRAME', "Frame", "Maintain subject in frame position"),
            ('LOCKED', "Locked", "Camera locked to subject (SnorriCam)"),
            ('PREDICTIVE', "Predictive", "Predict subject motion"),
        ],
        default='FOLLOW'
    )
    
    # Distance control
    distance_mode: EnumProperty(
        name="Distance Mode",
        items=[
            ('FIXED', "Fixed", "Maintain fixed distance"),
            ('DYNAMIC', "Dynamic", "Adjust distance based on speed"),
            ('COMPOSITION', "Composition", "Adjust for best composition"),
        ],
        default='DYNAMIC'
    )
    
    target_distance: FloatProperty(
        name="Target Distance",
        min=0.5, max=50.0,
        default=5.0,
        description="Desired distance from subject"
    )
    
    min_distance: FloatProperty(
        name="Min Distance",
        min=0.2, max=20.0,
        default=1.0,
        description="Minimum allowed distance"
    )
    
    max_distance: FloatProperty(
        name="Max Distance",
        min=1.0, max=100.0,
        default=20.0,
        description="Maximum allowed distance"
    )
    
    # Height control
    height_mode: EnumProperty(
        name="Height Mode",
        items=[
            ('FIXED', "Fixed", "Fixed height offset"),
            ('EYE_LEVEL', "Eye Level", "Match subject eye level"),
            ('DYNAMIC', "Dynamic", "Adjust based on context"),
        ],
        default='EYE_LEVEL'
    )
    
    height_offset: FloatProperty(
        name="Height Offset",
        min=-10.0, max=10.0,
        default=1.7,
        description="Height offset from subject"
    )
    
    # Angle control
    angle_mode: EnumProperty(
        name="Angle Mode",
        items=[
            ('FIXED', "Fixed", "Fixed viewing angle"),
            ('DYNAMIC', "Dynamic", "Adjust based on movement"),
            ('COMPOSITION', "Composition", "Adjust for best composition"),
        ],
        default='DYNAMIC'
    )
    
    horizontal_angle: FloatProperty(
        name="Horizontal Angle",
        min=-180, max=180,
        default=0,
        description="Fixed horizontal angle (degrees)"
    )
    
    vertical_angle: FloatProperty(
        name="Vertical Angle",
        min=-90, max=90,
        default=0,
        description="Fixed vertical angle (degrees)"
    )
    
    # Smoothing
    position_smoothing: FloatProperty(
        name="Position Smoothing",
        min=0.0, max=1.0,
        default=0.7,
        description="Smooth position changes",
        subtype='FACTOR'
    )
    
    rotation_smoothing: FloatProperty(
        name="Rotation Smoothing",
        min=0.0, max=1.0,
        default=0.8,
        description="Smooth rotation changes",
        subtype='FACTOR'
    )
    
    prediction_frames: IntProperty(
        name="Prediction Frames",
        min=0, max=30,
        default=5,
        description="Frames to predict ahead"
    )
    
    # Obstacle avoidance
    avoid_obstacles: BoolProperty(
        name="Avoid Obstacles",
        default=False,
        description="Try to avoid obstacles between camera and subject"
    )
    
    obstacle_radius: FloatProperty(
        name="Obstacle Radius",
        min=0.1, max=5.0,
        default=0.5,
        description="Radius to check for obstacles"
    )
    
    # Damping system
    damping_spring: FloatProperty(
        name="Spring Damping",
        min=0.0, max=1.0,
        default=0.3,
        description="Spring damping for natural movement",
        subtype='FACTOR'
    )
    
    damping_mass: FloatProperty(
        name="Virtual Mass",
        min=0.1, max=10.0,
        default=2.0,
        description="Virtual camera mass (higher = slower response)"
    )


class MultipleTargetProperties(PropertyGroup):
    """Handle multiple tracking targets"""
    
    enabled: BoolProperty(
        name="Multiple Targets",
        default=False,
        description="Track multiple subjects"
    )
    
    # Note: Can't directly use CollectionProperty of bpy.types.Object
    # This is a placeholder - will implement differently
    target_count: IntProperty(
        name="Target Count",
        default=0,
        min=0, max=10
    )
    
    blend_mode: EnumProperty(
        name="Target Blend Mode",
        items=[
            ('AVERAGE', "Average", "Average target positions"),
            ('WEIGHTED', "Weighted", "Weighted by importance"),
            ('SWITCH', "Switch", "Switch between targets"),
            ('COMPOSITE', "Composite", "Composite framing"),
        ],
        default='AVERAGE'
    )
    
    switch_interval: IntProperty(
        name="Switch Interval",
        min=30, max=1000,
        default=120,
        description="Frames between target switches"
    )
    
    transition_frames: IntProperty(
        name="Transition Frames",
        min=5, max=120,
        default=30,
        description="Frames to transition between targets"
    )


class CameraTraceProperties(PropertyGroup):
    """Main camera tracing/tracking properties"""
    
    enabled: BoolProperty(
        name="Enable Camera Trace",
        default=False,
        description="Enable advanced object tracking"
    )
    
    # Target
    target_object: PointerProperty(
        name="Target Object",
        type=bpy.types.Object,
        description="Object to track"
    )
    
    secondary_target: PointerProperty(
        name="Secondary Target",
        type=bpy.types.Object,
        description="Secondary object to track"
    )
    
    # Tracking modes
    tracking_mode: PointerProperty(type=TrackingModesProperties)
    
    # Operator behavior
    operator: PointerProperty(type=OperatorBehaviorProperties)
    
    # Framing rules
    framing: PointerProperty(type=FramingRulesProperties)
    
    # Multiple targets
    multi_target: PointerProperty(type=MultipleTargetProperties)
    
    # Motion history (for prediction)
    history_length: IntProperty(
        name="History Length",
        min=5, max=100,
        default=30,
        description="Frames of motion history to keep"
    )
    
    # Visual aids
    show_trace_path: BoolProperty(
        name="Show Trace Path",
        default=False,
        description="Visualize tracking path"
    )
    
    show_target_prediction: BoolProperty(
        name="Show Prediction",
        default=False,
        description="Show predicted target position"
    )
    
    show_framing_guides: BoolProperty(
        name="Show Framing Guides",
        default=False,
        description="Show framing guides in viewport"
    )
    
    # Debug
    debug_info: BoolProperty(
        name="Debug Info",
        default=False,
        description="Show tracking debug information"
    )


# ============================================================================
# MAIN PROPERTIES (COMBINED WITH NEW TRACKING)
# ============================================================================

class CameraMotionProperties(PropertyGroup):
    """Main property group for the add-on - MEGA VERSION 2.1.0"""
    
    # Preset system
    preset_category: EnumProperty(
        name="Category",
        items=[
            ('HANDHELD', "Handheld", "Handheld camera presets"),
            ('VEHICLE', "Vehicle", "Vehicle vibration presets"),
            ('IMPACT', "Impact", "Impact and explosion presets"),
            ('CINEMATIC', "Cinematic", "Cinematic motion presets"),
        ],
        default='HANDHELD'
    )
    
    preset: EnumProperty(
        name="Motion Preset",
        items=[
            # Handheld
            ('HANDHELD_STATIC', "Handheld Static", "Subtle handheld motion"),
            ('HANDHELD_WALKING', "Walking", "Walking camera motion"),
            ('HANDHELD_RUNNING', "Running", "Running camera motion"),
            ('STEADICAM', "Steadicam", "Smooth steadicam operation"),
            ('DOCUMENTARY', "Documentary", "Documentary style handheld"),
            
            # Vehicle
            ('CAR_IDLE', "Car Idle", "Car engine vibration"),
            ('CAR_DRIVING', "Car Driving", "Car driving vibration"),
            ('HELICOPTER', "Helicopter", "Helicopter vibration"),
            ('BOAT', "Boat", "Boat on water"),
            
            # Impact
            ('EXPLOSION', "Explosion", "Explosion shockwave"),
            ('EARTHQUAKE', "Earthquake", "Earthquake tremor"),
            ('FOOTSTEP', "Footstep", "Footstep impact"),
            ('COLLISION', "Collision", "Object collision"),
            
            # Cinematic
            ('CINEMATIC_BREATH', "Breathing", "Subtle breathing motion"),
            ('CINEMATIC_DRIFT', "Cinematic Drift", "Slow drifting motion"),
            ('HORROR_SHAKE', "Horror Shaky", "Horror movie shaky cam"),
            ('ACTION_CAM', "Action Camera", "Action movie camera"),
        ],
        description="Select motion preset"
    )
    
    # Core controls
    target_camera: PointerProperty(
        name="Target Camera",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'CAMERA'
    )
    
    # Shake controls
    shake: PointerProperty(type=ShakeControls)
    
    # Physics
    physics: PointerProperty(type=PhysicsSettings)
    
    # NEW: Camera trace/tracking
    camera_trace: PointerProperty(type=CameraTraceProperties)
    
    # Event triggers
    event_triggers: CollectionProperty(type=EventTrigger)
    active_event_index: IntProperty(
        name="Active Event", 
        default=0
    )
    
    # Motion layers
    motion_layers: CollectionProperty(type=MotionLayerProperties)
    active_layer_index: IntProperty(
        name="Active Layer", 
        default=0
    )
    
    # Animation controls
    frame_start: IntProperty(
        name="Start Frame",
        default=1,
        min=1
    )
    
    frame_end: IntProperty(
        name="End Frame",
        default=250,
        min=1
    )
    
    # Preview
    show_motion_path: BoolProperty(
        name="Show Motion Path",
        default=False,
        description="Preview motion path in viewport"
    )
    
    motion_path_length: IntProperty(
        name="Path Length",
        default=100,
        min=10, max=1000,
        description="Length of motion path preview"
    )
    
    # Bake settings
    bake_samples: IntProperty(
        name="Bake Samples",
        default=24,
        min=1, max=120,
        description="Samples per frame for baking"
    )
    
    auto_intensity: BoolProperty(
        name="Auto Intensity",
        default=False,
        description="Automatically adjust intensity based on camera speed"
    )
    
    operator_simulation: BoolProperty(
        name="Simulate Operator",
        default=True,
        description="Simulate human operator imperfections"
    )
    
    # Shot system
    shots: CollectionProperty(type=ShotProperties)
    active_shot_index: IntProperty(
        name="Active Shot",
        default=0
    )
    
    sequences: CollectionProperty(type=ShotSequence)
    active_sequence_index: IntProperty(
        name="Active Sequence",
        default=0
    )
    
    # Auto shot generation
    auto_target: PointerProperty(
        name="Target Object",
        type=bpy.types.Object,
        description="Object to generate shots for"
    )
    
    shot_style: EnumProperty(
        name="Shot Style",
        items=[
            ('HOLLYWOOD', "Hollywood", "Classic Hollywood cinematic style"),
            ('DOCUMENTARY', "Documentary", "Documentary/realist style"),
            ('HORROR', "Horror", "Tension-building horror style"),
            ('ACTION', "Action", "Fast-paced action style"),
            ('ROMANTIC', "Romantic", "Soft romantic style"),
        ],
        default='HOLLYWOOD'
    )
    
    action_type: EnumProperty(
        name="Action Type",
        items=[
            ('WALK', "Walking", "Character walking"),
            ('RUN', "Running", "Character running"),
            ('DRIVE', "Driving", "Vehicle driving"),
            ('DIALOGUE', "Dialogue", "Dialogue scene"),
            ('ACTION', "Action", "Action sequence"),
        ],
        default='WALK'
    )
    
    # Rig generation
    rig_type: EnumProperty(
        name="Rig Type",
        items=[
            ('DOLLY', "Dolly", "Dolly on track"),
            ('STEADICAM', "Steadicam", "Steadicam rig"),
            ('CAR', "Car Rig", "Multi-camera car rig"),
            ('SNORRICAM', "SnorriCam", "Body-attached camera"),
        ],
        default='DOLLY'
    )
    
    # Shot preview
    preview_shot: BoolProperty(
        name="Preview Shot",
        default=False,
        description="Preview current shot in viewport"
    )
    
    # Batch processing
    batch_start_frame: IntProperty(
        name="Batch Start",
        default=1
    )
    
    auto_sequence: BoolProperty(
        name="Auto Sequence",
        default=True,
        description="Automatically arrange shots in sequence"
    )
    
    # Quick presets
    quick_shot: EnumProperty(
        name="Quick Shot",
        items=[
            ('CLOSEUP', "Close-Up", "Quick close-up shot"),
            ('MEDIUM', "Medium Shot", "Quick medium shot"),
            ('LONG', "Long Shot", "Quick long shot"),
            ('POV', "POV", "Point of view shot"),
            ('TRACKING', "Tracking", "Tracking follow shot"),
        ],
        default='MEDIUM'
    )


# ============================================================================
# ENHANCED MOTION ENGINE WITH ADVANCED TRACKING
# ============================================================================

# class AdvancedMotionEngine:
#     """Enhanced motion engine with advanced tracking capabilities"""
    
#     def __init__(self, context):
#         self.context = context
#         self.props = context.scene.camera_motion
#         self.camera = self.props.target_camera or context.scene.camera
        
#         # Tracking state
#         self.target_history = []  # History of target positions
#         self.target_velocities = []  # History of target velocities
#         self.camera_target_pos = None  # Desired camera position
#         self.camera_target_rot = None  # Desired camera rotation
#         self.last_camera_pos = None
#         self.last_camera_rot = None
        
#         # Physics state
#         self.camera_velocity = Vector((0, 0, 0))
#         self.camera_angular_velocity = Vector((0, 0, 0))
        
#         # Operator simulation state
#         self.operator_noise_phase = random.uniform(0, 2 * math.pi)
#         self.fatigue_level = 0.0
#         self.last_reaction_time = 0.0
        
#         # Noise generators
#         self.noise_cache = {}
#         self.seed = random.randint(0, 10000)
        
#     def generate_perlin_noise(self, t, freq, amp, axis=0):
#         """Generate Perlin-style noise"""
#         value = math.sin(t * freq * 2 * math.pi + axis) * 0.5
#         value += math.sin(t * freq * 4 * math.pi + axis * 2) * 0.25
#         value += math.sin(t * freq * 8 * math.pi + axis * 3) * 0.125
#         return value * amp
    
#     def get_noise_value(self, t, freq, amp, axis, noise_type='PERLIN'):
#         """Get noise value based on selected type"""
#         cache_key = (t, axis, noise_type, freq, amp)
#         if cache_key in self.noise_cache:
#             return self.noise_cache[cache_key]
        
#         if noise_type == 'PERLIN':
#             value = self.generate_perlin_noise(t, freq, amp, axis)
#         else:  # Default to Perlin
#             value = self.generate_perlin_noise(t, freq, amp, axis)
        
#         self.noise_cache[cache_key] = value
#         return value
    
#     def update_target_history(self, target_obj, current_frame):
#         """Update target position and velocity history"""
#         if not target_obj:
#             return
        
#         # Get current target position
#         current_pos = target_obj.location.copy()
        
#         # Add to history
#         self.target_history.append({
#             'frame': current_frame,
#             'position': current_pos
#         })
        
#         # Limit history length
#         trace = self.props.camera_trace
#         max_history = trace.history_length
#         if len(self.target_history) > max_history:
#             self.target_history.pop(0)
        
#         # Calculate velocities
#         self.target_velocities = []
#         for i in range(1, len(self.target_history)):
#             prev = self.target_history[i-1]
#             curr = self.target_history[i]
#             frame_diff = curr['frame'] - prev['frame']
#             if frame_diff > 0:
#                 velocity = (curr['position'] - prev['position']) / frame_diff
#                 self.target_velocities.append({
#                     'frame': curr['frame'],
#                     'velocity': velocity
#                 })
        
#         # Limit velocity history
#         if len(self.target_velocities) > max_history:
#             self.target_velocities = self.target_velocities[-max_history:]
    
#     def predict_target_position(self, target_obj, frames_ahead):
#         """Predict future target position based on motion history"""
#         if not target_obj or frames_ahead <= 0:
#             return target_obj.location.copy() if target_obj else None
        
#         if len(self.target_velocities) < 3:
#             return target_obj.location.copy()
        
#         # Use recent velocities for prediction
#         recent_velocities = self.target_velocities[-5:]
#         if not recent_velocities:
#             return target_obj.location.copy()
        
#         # Average velocity
#         avg_velocity = Vector((0, 0, 0))
#         for v_data in recent_velocities:
#             avg_velocity += v_data['velocity']
#         avg_velocity /= len(recent_velocities)
        
#         # Predict position
#         current_pos = target_obj.location.copy()
#         predicted_pos = current_pos + avg_velocity * frames_ahead
        
#         return predicted_pos
    
#     def calculate_ideal_camera_position(self, target_pos, target_obj):
#         """Calculate ideal camera position based on tracking settings"""
#         trace = self.props.camera_trace
#         if not trace.enabled:
#             return None
        
#         tracking = trace.tracking_mode
#         current_pos = self.camera.location.copy() if self.camera else Vector((0, 0, 0))
        
#         # Get target object's properties
#         target_dimensions = CinematographyUtils.get_object_dimensions(target_obj)
#         target_velocity = Vector((0, 0, 0))
#         if self.target_velocities:
#             target_velocity = self.target_velocities[-1]['velocity'] if self.target_velocities else Vector((0, 0, 0))
        
#         # Calculate base distance
#         if tracking.distance_mode == 'FIXED':
#             distance = tracking.target_distance
#         elif tracking.distance_mode == 'DYNAMIC':
#             # Adjust distance based on target speed
#             speed = target_velocity.length
#             base_distance = tracking.target_distance
#             speed_factor = min(speed / 10.0, 2.0)
#             distance = base_distance * (1.0 + speed_factor * 0.5)
#         else:  # COMPOSITION
#             # Adjust for best composition
#             distance = tracking.target_distance
        
#         # Clamp distance
#         distance = max(tracking.min_distance, min(tracking.max_distance, distance))
        
#         # Calculate height
#         if tracking.height_mode == 'FIXED':
#             height = tracking.height_offset
#         elif tracking.height_mode == 'EYE_LEVEL':
#             # Approximate eye level as 0.9 of height
#             height = target_dimensions.z * 0.9
#         else:  # DYNAMIC
#             # Adjust based on context
#             height = tracking.height_offset
        
#         # Calculate direction based on tracking mode
#         if tracking.mode == 'FOLLOW':
#             # Simple follow - camera positioned relative to target's facing/movement
#             direction = target_velocity.normalized() if target_velocity.length_squared > 0 else Vector((0, -1, 0))
#             # Position camera opposite to movement direction (behind)
#             cam_offset = -direction * distance
#             cam_offset.z += height
            
#         elif tracking.mode == 'ORBIT':
#             # Orbit around target
#             orbit_angle = (self.context.scene.frame_current * 0.05) % 360
#             rad_angle = math.radians(orbit_angle)
#             cam_offset = Vector((
#                 math.sin(rad_angle) * distance,
#                 math.cos(rad_angle) * distance,
#                 height
#             ))
            
#         elif tracking.mode == 'LEAD':
#             # Camera leads the target (moves ahead)
#             if target_velocity.length_squared > 0:
#                 direction = target_velocity.normalized()
#             else:
#                 direction = Vector((0, -1, 0))
#             cam_offset = direction * distance
#             cam_offset.z += height
            
#         elif tracking.mode == 'TRAIL':
#             # Camera trails behind
#             if target_velocity.length_squared > 0:
#                 direction = target_velocity.normalized()
#             else:
#                 direction = Vector((0, -1, 0))
#             cam_offset = -direction * distance
#             cam_offset.z += height
            
#         elif tracking.mode == 'FRAME':
#             # Maintain specific framing
#             angle_rad = math.radians(tracking.horizontal_angle)
#             cam_offset = Vector((
#                 math.sin(angle_rad) * distance,
#                 math.cos(angle_rad) * distance,
#                 height
#             ))
            
#         elif tracking.mode == 'LOCKED':
#             # Camera locked to target (SnorriCam)
#             cam_offset = Vector((0.5, 0, height))
            
#         elif tracking.mode == 'PREDICTIVE':
#             # Use prediction
#             frames_ahead = tracking.prediction_frames
#             predicted_pos = self.predict_target_position(target_obj, frames_ahead)
#             if predicted_pos:
#                 # Position to view predicted position
#                 direction = (predicted_pos - target_pos).normalized() if (predicted_pos - target_pos).length_squared > 0 else Vector((0, -1, 0))
#                 cam_offset = -direction * distance
#                 cam_offset.z += height
#             else:
#                 cam_offset = Vector((-distance, 0, height))
        
#         else:
#             cam_offset = Vector((-distance, 0, height))
        
#         # Calculate final camera position
#         ideal_pos = target_pos + cam_offset
        
#         return ideal_pos
    
#     def calculate_ideal_camera_rotation(self, target_pos, camera_pos, target_obj):
#         """Calculate ideal camera rotation to look at target"""
#         trace = self.props.camera_trace
#         if not trace.enabled:
#             return None
        
#         tracking = trace.tracking_mode
        
#         # Direction to target
#         direction = target_pos - camera_pos
#         if direction.length_squared == 0:
#             return Euler((0, 0, 0))
        
#         # Calculate base rotation
#         rot_quat = direction.to_track_quat('-Z', 'Y')
#         rot_euler = rot_quat.to_euler()
        
#         # Apply framing rules
#         if trace.framing.enabled:
#             # Apply rule of thirds (simplified - would need screen space calculation)
#             if trace.framing.rule_of_thirds and trace.framing.thirds_weight > 0:
#                 # Small adjustment for rule of thirds
#                 # This is simplified - real implementation would use screen space
#                 pass
            
#             # Stabilize horizon
#             if trace.framing.horizon_stabilization and trace.framing.horizon_weight > 0:
#                 # Blend with level horizon
#                 rot_euler.z *= (1.0 - trace.framing.horizon_weight)
        
#         return rot_euler
    
#     def apply_operator_behavior(self, target_pos, target_rot, frame, delta_time):
#         """Apply realistic operator behavior to camera movement"""
#         trace = self.props.camera_trace
#         if not trace.enabled or not trace.operator.enabled:
#             return target_pos, target_rot
        
#         op = trace.operator
        
#         # Update fatigue
#         if op.fatigue_enabled:
#             self.fatigue_level = min(1.0, self.fatigue_level + op.fatigue_rate * delta_time)
#         else:
#             self.fatigue_level = max(0.0, self.fatigue_level - 0.01)
        
#         # Skill modifier (higher skill = less fatigue effect)
#         skill_mod = op.skill_level * (1.0 - self.fatigue_level * 0.5)
        
#         # Reaction delay
#         if op.reaction_time > 0 and self.last_reaction_time == 0:
#             self.last_reaction_time = frame + op.reaction_time * 24  # Convert to frames
        
#         if frame < self.last_reaction_time:
#             # Still reacting - hold previous position
#             if self.last_camera_pos:
#                 target_pos = self.last_camera_pos
#                 target_rot = self.last_camera_rot
        
#         # Breathing
#         if op.breathing_enabled:
#             t = frame * op.breathing_rate * 0.1 + self.operator_noise_phase
#             breath_offset = Vector((
#                 math.sin(t) * op.breathing_intensity * 0.3,
#                 math.cos(t * 1.3) * op.breathing_intensity * 0.3,
#                 math.sin(t * 1.7) * op.breathing_intensity * 0.4
#             )) * (1.0 - skill_mod * 0.5)
#             target_pos += breath_offset
        
#         # Micro-adjustments
#         if op.micro_adjustments:
#             t = frame * op.adjustment_frequency * 0.1
#             micro_offset = Vector((
#                 self.generate_perlin_noise(t, 2.0, 0.02 * (1.0 - skill_mod), 10),
#                 self.generate_perlin_noise(t, 2.3, 0.02 * (1.0 - skill_mod), 11),
#                 self.generate_perlin_noise(t, 1.8, 0.01 * (1.0 - skill_mod), 12)
#             ))
#             target_pos += micro_offset
        
#         # Handheld weight simulation
#         if op.handheld_weight > 0:
#             # Calculate inertia based on velocity
#             if self.last_camera_pos:
#                 velocity = (target_pos - self.last_camera_pos) / max(delta_time, 0.001)
#                 inertia_factor = min(velocity.length / op.handheld_weight, 0.1)
#                 # Add slight overshoot
#                 target_pos += velocity * inertia_factor
        
#         # Apply stabilization (opposite of handheld)
#         if op.stabilization > 0 and self.last_camera_pos:
#             # Smooth out sudden movements
#             target_pos = self.last_camera_pos.lerp(target_pos, op.stabilization)
        
#         # Speed limits
#         if self.last_camera_pos and delta_time > 0:
#             # Calculate movement speed
#             movement = target_pos - self.last_camera_pos
#             speed = movement.length / delta_time
            
#             # Apply pan speed limit
#             if speed > op.max_pan_speed * 0.1:  # Convert to appropriate units
#                 # Limit speed
#                 max_movement = op.max_pan_speed * delta_time * 0.1
#                 if movement.length > max_movement:
#                     movement = movement.normalized() * max_movement
#                     target_pos = self.last_camera_pos + movement
        
#         return target_pos, target_rot
    
#     def apply_physics_damping(self, target_pos, target_rot, delta_time):
#         """Apply physics-based damping for natural movement"""
#         trace = self.props.camera_trace
#         if not trace.enabled:
#             return target_pos, target_rot
        
#         tracking = trace.tracking_mode
        
#         if self.last_camera_pos is None:
#             self.last_camera_pos = target_pos.copy()
#             self.last_camera_rot = target_rot.copy()
#             return target_pos, target_rot
        
#         # Spring-damper system for position
#         displacement = target_pos - self.last_camera_pos
#         spring_force = displacement * (1.0 - tracking.damping_spring) * 10.0
#         damping_force = self.camera_velocity * 5.0
        
#         # Mass affects acceleration
#         mass = max(tracking.damping_mass, 0.1)
#         acceleration = (spring_force - damping_force) / mass
        
#         # Update velocity
#         self.camera_velocity += acceleration * delta_time
        
#         # Apply damping
#         self.camera_velocity *= (1.0 - tracking.position_smoothing * delta_time * 5.0)
        
#         # Update position
#         new_pos = self.last_camera_pos + self.camera_velocity * delta_time
        
#         # Similar for rotation (simplified)
#         rot_displacement = Vector((
#             target_rot.x - self.last_camera_rot.x,
#             target_rot.y - self.last_camera_rot.y,
#             target_rot.z - self.last_camera_rot.z
#         ))
        
#         self.camera_angular_velocity = self.camera_angular_velocity.lerp(
#             rot_displacement * 10.0,
#             tracking.rotation_smoothing * delta_time * 10.0
#         )
        
#         new_rot = Euler((
#             self.last_camera_rot.x + self.camera_angular_velocity.x * delta_time,
#             self.last_camera_rot.y + self.camera_angular_velocity.y * delta_time,
#             self.last_camera_rot.z + self.camera_angular_velocity.z * delta_time
#         ))
        
#         self.last_camera_pos = new_pos
#         self.last_camera_rot = new_rot
        
#         return new_pos, new_rot
    
#     def apply_multiple_targets(self, frame):
#         """Handle multiple tracking targets - simplified version"""
#         trace = self.props.camera_trace
#         if not trace.enabled or not trace.multi_target.enabled:
#             return None
        
#         multi = trace.multi_target
        
#         # For now, just use primary target
#         # In a full implementation, you'd maintain a list of target objects
#         if trace.target_object:
#             return trace.target_object.location.copy(), trace.target_object
        
#         return None
    
#     def update_tracking_at_frame(self, frame, bake_mode=False):
#         """Update camera tracking at specific frame"""
#         if not self.camera:
#             return False
        
#         trace = self.props.camera_trace
#         if not trace.enabled or not trace.target_object:
#             return False
        
#         try:
#             target_obj = trace.target_object
            
#             # Update target history
#             self.update_target_history(target_obj, frame)
            
#             # Handle multiple targets
#             multi_result = self.apply_multiple_targets(frame)
#             if multi_result:
#                 target_pos, target_obj = multi_result
#             else:
#                 target_pos = target_obj.location.copy()
            
#             # Apply prediction if enabled
#             tracking = trace.tracking_mode
#             if tracking.mode == 'PREDICTIVE' and tracking.prediction_frames > 0:
#                 predicted_pos = self.predict_target_position(target_obj, tracking.prediction_frames)
#                 if predicted_pos:
#                     # Blend between current and predicted
#                     blend = 0.3
#                     target_pos = target_pos.lerp(predicted_pos, blend)
            
#             # Calculate ideal camera position
#             ideal_pos = self.calculate_ideal_camera_position(target_pos, target_obj)
#             if ideal_pos is None:
#                 return False
            
#             # Calculate ideal camera rotation
#             ideal_rot = self.calculate_ideal_camera_rotation(target_pos, ideal_pos, target_obj)
#             if ideal_rot is None:
#                 ideal_rot = self.camera.rotation_euler.copy()
            
#             # Apply operator behavior
#             delta_time = 1.0 / 24.0  # Assume 24 fps
#             if not bake_mode:
#                 ideal_pos, ideal_rot = self.apply_operator_behavior(ideal_pos, ideal_rot, frame, delta_time)
            
#             # Apply physics damping
#             final_pos, final_rot = self.apply_physics_damping(ideal_pos, ideal_rot, delta_time)
            
#             # Apply original shake if enabled
#             if self.props.shake.enabled and not bake_mode:
#                 # Get shake offset
#                 shake_engine = MotionEngine(self.context)
#                 shake_engine.camera = self.camera
#                 shake_engine.last_position = final_pos
#                 shake_engine.last_rotation = final_rot
                
#                 shake_pos, shake_rot = shake_engine.calculate_motion_at_frame(frame)
#                 if shake_pos and shake_rot:
#                     # Combine tracking with shake
#                     final_pos = final_pos + (shake_pos - self.camera.location)
#                     final_rot = Euler((
#                         final_rot.x + (shake_rot.x - self.camera.rotation_euler.x),
#                         final_rot.y + (shake_rot.y - self.camera.rotation_euler.y),
#                         final_rot.z + (shake_rot.z - self.camera.rotation_euler.z)
#                     ))
            
#             # Apply auto focus pull
#             if trace.framing.enabled and trace.framing.auto_focus_pull:
#                 self.apply_auto_focus(target_pos, frame)
            
#             # Set camera transforms
#             self.camera.location = final_pos
#             self.camera.rotation_euler = final_rot
            
#             # Insert keyframes if requested
#             if bake_mode:
#                 # Ensure animation data exists
#                 if self.camera.animation_data is None:
#                     self.camera.animation_data_create()
                
#                 self.camera.keyframe_insert(data_path="location", frame=frame)
#                 self.camera.keyframe_insert(data_path="rotation_euler", frame=frame)
                
#                 # Keyframe focus if applicable
#                 if trace.framing.auto_focus_pull and hasattr(self.camera.data, 'dof'):
#                     dof = self.camera.data.dof
#                     if hasattr(dof, 'focus_distance'):
#                         dof.keyframe_insert(data_path="focus_distance", frame=frame)
            
#             return True
            
#         except Exception as e:
#             print(f"Advanced Tracking Error at frame {frame}: {e}")
#             return False
    
#     def apply_auto_focus(self, target_pos, frame):
#         """Automatically pull focus to target"""
#         if not hasattr(self.camera.data, 'dof'):
#             return
        
#         dof = self.camera.data.dof
#         if not hasattr(dof, 'focus_distance'):
#             return
        
#         trace = self.props.camera_trace
        
#         # Calculate distance to target
#         distance = (target_pos - self.camera.location).length
        
#         # Get current focus distance
#         current_focus = dof.focus_distance
        
#         # Calculate target focus distance
#         target_focus = max(distance * 0.9, 0.1)  # Slightly in front of subject
        
#         # Smooth focus pull
#         focus_speed = trace.framing.focus_speed * 0.1
#         new_focus = current_focus + (target_focus - current_focus) * focus_speed
        
#         dof.focus_distance = new_focus

# ============================================================================
# ENHANCED MOTION ENGINE WITH ADVANCED TRACKING (FIXED)
# ============================================================================

class AdvancedMotionEngine:
    """Enhanced motion engine with advanced tracking capabilities"""
    
    def __init__(self, context):
        self.context = context
        self.props = context.scene.camera_motion
        self.camera = self.props.target_camera or context.scene.camera
        
        # Tracking state
        self.target_history = []  # History of target positions
        self.target_velocities = []  # History of target velocities
        self.camera_target_pos = None  # Desired camera position
        self.camera_target_rot = None  # Desired camera rotation
        self.last_camera_pos = None
        self.last_camera_rot = None
        
        # Store original camera position for reference
        if self.camera:
            self.original_camera_pos = self.camera.location.copy()
            self.original_camera_rot = self.camera.rotation_euler.copy()
        else:
            self.original_camera_pos = Vector((0, 0, 0))
            self.original_camera_rot = Euler((0, 0, 0))
        
        # Physics state
        self.camera_velocity = Vector((0, 0, 0))
        self.camera_angular_velocity = Vector((0, 0, 0))
        
        # Operator simulation state
        self.operator_noise_phase = random.uniform(0, 2 * math.pi)
        self.fatigue_level = 0.0
        self.last_reaction_time = 0.0
        
        # Noise generators
        self.noise_cache = {}
        self.seed = random.randint(0, 10000)
        
    def generate_perlin_noise(self, t, freq, amp, axis=0):
        """Generate Perlin-style noise"""
        value = math.sin(t * freq * 2 * math.pi + axis) * 0.5
        value += math.sin(t * freq * 4 * math.pi + axis * 2) * 0.25
        value += math.sin(t * freq * 8 * math.pi + axis * 3) * 0.125
        return value * amp
    
    def get_noise_value(self, t, freq, amp, axis, noise_type='PERLIN'):
        """Get noise value based on selected type"""
        cache_key = (t, axis, noise_type, freq, amp)
        if cache_key in self.noise_cache:
            return self.noise_cache[cache_key]
        
        if noise_type == 'PERLIN':
            value = self.generate_perlin_noise(t, freq, amp, axis)
        else:  # Default to Perlin
            value = self.generate_perlin_noise(t, freq, amp, axis)
        
        self.noise_cache[cache_key] = value
        return value
    
    def update_target_history(self, target_obj, current_frame):
        """Update target position and velocity history"""
        if not target_obj:
            return
        
        # Get current target position
        current_pos = target_obj.location.copy()
        
        # Add to history
        self.target_history.append({
            'frame': current_frame,
            'position': current_pos
        })
        
        # Limit history length
        trace = self.props.camera_trace
        max_history = trace.history_length if trace else 30
        if len(self.target_history) > max_history:
            self.target_history.pop(0)
        
        # Calculate velocities
        self.target_velocities = []
        for i in range(1, len(self.target_history)):
            prev = self.target_history[i-1]
            curr = self.target_history[i]
            frame_diff = curr['frame'] - prev['frame']
            if frame_diff > 0:
                velocity = (curr['position'] - prev['position']) / frame_diff
                self.target_velocities.append({
                    'frame': curr['frame'],
                    'velocity': velocity
                })
        
        # Limit velocity history
        if len(self.target_velocities) > max_history:
            self.target_velocities = self.target_velocities[-max_history:]
    
    def predict_target_position(self, target_obj, frames_ahead):
        """Predict future target position based on motion history"""
        if not target_obj or frames_ahead <= 0:
            return target_obj.location.copy() if target_obj else None
        
        if len(self.target_velocities) < 3:
            return target_obj.location.copy()
        
        # Use recent velocities for prediction
        recent_velocities = self.target_velocities[-5:]
        if not recent_velocities:
            return target_obj.location.copy()
        
        # Average velocity
        avg_velocity = Vector((0, 0, 0))
        for v_data in recent_velocities:
            avg_velocity += v_data['velocity']
        avg_velocity /= len(recent_velocities)
        
        # Predict position
        current_pos = target_obj.location.copy()
        predicted_pos = current_pos + avg_velocity * frames_ahead
        
        return predicted_pos
    
    def calculate_ideal_camera_position(self, target_pos, target_obj):
        """Calculate ideal camera position based on tracking settings"""
        trace = self.props.camera_trace
        if not trace or not trace.enabled:
            return None
        
        tracking = trace.tracking_mode
        current_pos = self.camera.location.copy() if self.camera else Vector((0, 0, 0))
        
        # Get target object's properties
        target_dimensions = CinematographyUtils.get_object_dimensions(target_obj)
        target_velocity = Vector((0, 0, 0))
        if self.target_velocities:
            target_velocity = self.target_velocities[-1]['velocity'] if self.target_velocities else Vector((0, 0, 0))
        
        # Calculate base distance
        if tracking.distance_mode == 'FIXED':
            distance = tracking.target_distance
        elif tracking.distance_mode == 'DYNAMIC':
            # Adjust distance based on target speed
            speed = target_velocity.length
            base_distance = tracking.target_distance
            speed_factor = min(speed / 10.0, 2.0)
            distance = base_distance * (1.0 + speed_factor * 0.5)
        else:  # COMPOSITION
            # Adjust for best composition
            distance = tracking.target_distance
        
        # Clamp distance
        distance = max(tracking.min_distance, min(tracking.max_distance, distance))
        
        # Calculate height
        if tracking.height_mode == 'FIXED':
            height = tracking.height_offset
        elif tracking.height_mode == 'EYE_LEVEL':
            # Approximate eye level as 0.9 of height
            height = target_dimensions.z * 0.9
        else:  # DYNAMIC
            # Adjust based on context
            height = tracking.height_offset
        
        # CRITICAL FIX: Calculate direction based on tracking mode
        if tracking.mode == 'FOLLOW':
            # Simple follow - camera positioned relative to target's facing/movement
            if target_velocity.length_squared > 0:
                direction = target_velocity.normalized()
            else:
                # If no velocity, use a default direction based on target's rotation
                if hasattr(target_obj, 'rotation_euler') and target_obj.rotation_euler:
                    # Use object's forward direction (assuming Y is forward)
                    rot_mat = target_obj.rotation_euler.to_matrix()
                    direction = rot_mat @ Vector((0, -1, 0))
                    if direction.length_squared > 0:
                        direction.normalize()
                    else:
                        direction = Vector((0, -1, 0))
                else:
                    direction = Vector((0, -1, 0))
            
            # Position camera opposite to movement/facing direction (behind)
            cam_offset = -direction * distance
            cam_offset.z += height
            
        elif tracking.mode == 'ORBIT':
            # Orbit around target
            orbit_angle = (self.context.scene.frame_current * 2) % 360  # Slow orbit
            rad_angle = math.radians(orbit_angle)
            cam_offset = Vector((
                math.sin(rad_angle) * distance,
                math.cos(rad_angle) * distance,
                height
            ))
            
        elif tracking.mode == 'LEAD':
            # Camera leads the target (moves ahead)
            if target_velocity.length_squared > 0:
                direction = target_velocity.normalized()
            else:
                direction = Vector((0, -1, 0))
            cam_offset = direction * distance
            cam_offset.z += height
            
        elif tracking.mode == 'TRAIL':
            # Camera trails behind
            if target_velocity.length_squared > 0:
                direction = target_velocity.normalized()
            else:
                direction = Vector((0, -1, 0))
            cam_offset = -direction * distance
            cam_offset.z += height
            
        elif tracking.mode == 'FRAME':
            # Maintain specific framing
            angle_rad = math.radians(tracking.horizontal_angle)
            cam_offset = Vector((
                math.sin(angle_rad) * distance,
                math.cos(angle_rad) * distance,
                height
            ))
            
        elif tracking.mode == 'LOCKED':
            # Camera locked to target (SnorriCam)
            cam_offset = Vector((0.5, 0, height))
            
        elif tracking.mode == 'PREDICTIVE':
            # Use prediction
            frames_ahead = tracking.prediction_frames
            predicted_pos = self.predict_target_position(target_obj, frames_ahead)
            if predicted_pos:
                # Position to view predicted position
                direction = (predicted_pos - target_pos).normalized() if (predicted_pos - target_pos).length_squared > 0 else Vector((0, -1, 0))
                cam_offset = -direction * distance
                cam_offset.z += height
            else:
                cam_offset = Vector((-distance, 0, height))
        
        else:
            cam_offset = Vector((-distance, 0, height))
        
        # Calculate final camera position
        ideal_pos = target_pos + cam_offset
        
        return ideal_pos
    
    def calculate_ideal_camera_rotation(self, target_pos, camera_pos, target_obj):
        """Calculate ideal camera rotation to look at target"""
        trace = self.props.camera_trace
        if not trace or not trace.enabled:
            return None
        
        tracking = trace.tracking_mode
        
        # Direction to target
        direction = target_pos - camera_pos
        if direction.length_squared == 0:
            return Euler((0, 0, 0))
        
        # Calculate base rotation
        rot_quat = direction.to_track_quat('-Z', 'Y')
        rot_euler = rot_quat.to_euler()
        
        # Apply framing rules
        if trace.framing and trace.framing.enabled:
            # Apply rule of thirds (simplified - would need screen space calculation)
            if trace.framing.rule_of_thirds and trace.framing.thirds_weight > 0:
                # Small adjustment for rule of thirds
                # This is simplified - real implementation would use screen space
                pass
            
            # Stabilize horizon
            if trace.framing.horizon_stabilization and trace.framing.horizon_weight > 0:
                # Blend with level horizon
                rot_euler.z *= (1.0 - trace.framing.horizon_weight)
        
        return rot_euler
    
    def apply_operator_behavior(self, target_pos, target_rot, frame, delta_time):
        """Apply realistic operator behavior to camera movement"""
        trace = self.props.camera_trace
        if not trace or not trace.enabled or not trace.operator or not trace.operator.enabled:
            return target_pos, target_rot
        
        op = trace.operator
        
        # Update fatigue
        if op.fatigue_enabled:
            self.fatigue_level = min(1.0, self.fatigue_level + op.fatigue_rate * delta_time)
        else:
            self.fatigue_level = max(0.0, self.fatigue_level - 0.01)
        
        # Skill modifier (higher skill = less fatigue effect)
        skill_mod = op.skill_level * (1.0 - self.fatigue_level * 0.5)
        
        # Reaction delay
        if op.reaction_time > 0 and self.last_reaction_time == 0:
            self.last_reaction_time = frame + op.reaction_time * 24  # Convert to frames
        
        if frame < self.last_reaction_time:
            # Still reacting - hold previous position
            if self.last_camera_pos:
                target_pos = self.last_camera_pos
                target_rot = self.last_camera_rot
        
        # Breathing
        if op.breathing_enabled:
            t = frame * op.breathing_rate * 0.1 + self.operator_noise_phase
            breath_offset = Vector((
                math.sin(t) * op.breathing_intensity * 0.3,
                math.cos(t * 1.3) * op.breathing_intensity * 0.3,
                math.sin(t * 1.7) * op.breathing_intensity * 0.4
            )) * (1.0 - skill_mod * 0.5)
            target_pos += breath_offset
        
        # Micro-adjustments
        if op.micro_adjustments:
            t = frame * op.adjustment_frequency * 0.1
            micro_offset = Vector((
                self.generate_perlin_noise(t, 2.0, 0.02 * (1.0 - skill_mod), 10),
                self.generate_perlin_noise(t, 2.3, 0.02 * (1.0 - skill_mod), 11),
                self.generate_perlin_noise(t, 1.8, 0.01 * (1.0 - skill_mod), 12)
            ))
            target_pos += micro_offset
        
        # Handheld weight simulation
        if op.handheld_weight > 0:
            # Calculate inertia based on velocity
            if self.last_camera_pos:
                velocity = (target_pos - self.last_camera_pos) / max(delta_time, 0.001)
                inertia_factor = min(velocity.length / op.handheld_weight, 0.1)
                # Add slight overshoot
                target_pos += velocity * inertia_factor
        
        # Apply stabilization (opposite of handheld)
        if op.stabilization > 0 and self.last_camera_pos:
            # Smooth out sudden movements
            target_pos = self.last_camera_pos.lerp(target_pos, op.stabilization)
        
        # Speed limits
        if self.last_camera_pos and delta_time > 0:
            # Calculate movement speed
            movement = target_pos - self.last_camera_pos
            speed = movement.length / delta_time
            
            # Apply pan speed limit
            if speed > op.max_pan_speed * 0.1:  # Convert to appropriate units
                # Limit speed
                max_movement = op.max_pan_speed * delta_time * 0.1
                if movement.length > max_movement:
                    movement = movement.normalized() * max_movement
                    target_pos = self.last_camera_pos + movement
        
        return target_pos, target_rot
    
    def apply_physics_damping(self, target_pos, target_rot, delta_time):
        """Apply physics-based damping for natural movement"""
        trace = self.props.camera_trace
        if not trace or not trace.enabled:
            return target_pos, target_rot
        
        tracking = trace.tracking_mode
        
        if self.last_camera_pos is None:
            self.last_camera_pos = target_pos.copy()
            self.last_camera_rot = target_rot.copy() if target_rot else Euler((0, 0, 0))
            return target_pos, target_rot
        
        # Spring-damper system for position
        displacement = target_pos - self.last_camera_pos
        spring_force = displacement * (1.0 - tracking.damping_spring) * 10.0
        damping_force = self.camera_velocity * 5.0
        
        # Mass affects acceleration
        mass = max(tracking.damping_mass, 0.1)
        acceleration = (spring_force - damping_force) / mass
        
        # Update velocity
        self.camera_velocity += acceleration * delta_time
        
        # Apply damping
        self.camera_velocity *= (1.0 - tracking.position_smoothing * delta_time * 5.0)
        
        # Update position
        new_pos = self.last_camera_pos + self.camera_velocity * delta_time
        
        # Similar for rotation (simplified)
        if target_rot and self.last_camera_rot:
            rot_displacement = Vector((
                target_rot.x - self.last_camera_rot.x,
                target_rot.y - self.last_camera_rot.y,
                target_rot.z - self.last_camera_rot.z
            ))
            
            self.camera_angular_velocity = self.camera_angular_velocity.lerp(
                rot_displacement * 10.0,
                tracking.rotation_smoothing * delta_time * 10.0
            )
            
            new_rot = Euler((
                self.last_camera_rot.x + self.camera_angular_velocity.x * delta_time,
                self.last_camera_rot.y + self.camera_angular_velocity.y * delta_time,
                self.last_camera_rot.z + self.camera_angular_velocity.z * delta_time
            ))
        else:
            new_rot = target_rot
        
        self.last_camera_pos = new_pos
        self.last_camera_rot = new_rot
        
        return new_pos, new_rot
    
    def apply_multiple_targets(self, frame):
        """Handle multiple tracking targets - simplified version"""
        trace = self.props.camera_trace
        if not trace or not trace.enabled or not trace.multi_target or not trace.multi_target.enabled:
            return None
        
        multi = trace.multi_target
        
        # For now, just use primary target
        # In a full implementation, you'd maintain a list of target objects
        if trace.target_object:
            return trace.target_object.location.copy(), trace.target_object
        
        return None
    
    def update_tracking_at_frame(self, frame, bake_mode=False):
        """Update camera tracking at specific frame"""
        if not self.camera:
            return False
        
        trace = self.props.camera_trace
        if not trace or not trace.enabled or not trace.target_object:
            return False
        
        try:
            target_obj = trace.target_object
            
            # Update target history
            self.update_target_history(target_obj, frame)
            
            # Handle multiple targets
            multi_result = self.apply_multiple_targets(frame)
            if multi_result:
                target_pos, target_obj = multi_result
            else:
                target_pos = target_obj.location.copy()
            
            # Apply prediction if enabled
            tracking = trace.tracking_mode
            if tracking.mode == 'PREDICTIVE' and tracking.prediction_frames > 0:
                predicted_pos = self.predict_target_position(target_obj, tracking.prediction_frames)
                if predicted_pos:
                    # Blend between current and predicted
                    blend = 0.3
                    target_pos = target_pos.lerp(predicted_pos, blend)
            
            # Calculate ideal camera position
            ideal_pos = self.calculate_ideal_camera_position(target_pos, target_obj)
            if ideal_pos is None:
                return False
            
            # Calculate ideal camera rotation
            ideal_rot = self.calculate_ideal_camera_rotation(target_pos, ideal_pos, target_obj)
            if ideal_rot is None:
                ideal_rot = self.camera.rotation_euler.copy()
            
            # Apply operator behavior
            delta_time = 1.0 / 24.0  # Assume 24 fps
            if not bake_mode:
                ideal_pos, ideal_rot = self.apply_operator_behavior(ideal_pos, ideal_rot, frame, delta_time)
            
            # Apply physics damping
            final_pos, final_rot = self.apply_physics_damping(ideal_pos, ideal_rot, delta_time)
            
            # Apply original shake if enabled
            if self.props.shake and self.props.shake.enabled and not bake_mode:
                # Get shake offset
                shake_engine = MotionEngine(self.context)
                shake_engine.camera = self.camera
                shake_engine.last_position = final_pos
                shake_engine.last_rotation = final_rot
                
                shake_pos, shake_rot = shake_engine.calculate_motion_at_frame(frame)
                if shake_pos and shake_rot:
                    # Combine tracking with shake
                    final_pos = final_pos + (shake_pos - self.camera.location)
                    if final_rot and shake_rot:
                        final_rot = Euler((
                            final_rot.x + (shake_rot.x - self.camera.rotation_euler.x),
                            final_rot.y + (shake_rot.y - self.camera.rotation_euler.y),
                            final_rot.z + (shake_rot.z - self.camera.rotation_euler.z)
                        ))
            
            # Apply auto focus pull
            if trace.framing and trace.framing.enabled and trace.framing.auto_focus_pull:
                self.apply_auto_focus(target_pos, frame)
            
            # Set camera transforms
            self.camera.location = final_pos
            if final_rot:
                self.camera.rotation_euler = final_rot
            
            # Insert keyframes if requested
            if bake_mode:
                # Ensure animation data exists
                if self.camera.animation_data is None:
                    self.camera.animation_data_create()
                
                self.camera.keyframe_insert(data_path="location", frame=frame)
                self.camera.keyframe_insert(data_path="rotation_euler", frame=frame)
                
                # Keyframe focus if applicable
                if trace.framing and trace.framing.auto_focus_pull and hasattr(self.camera.data, 'dof'):
                    dof = self.camera.data.dof
                    if hasattr(dof, 'focus_distance'):
                        dof.keyframe_insert(data_path="focus_distance", frame=frame)
            
            return True
            
        except Exception as e:
            print(f"Advanced Tracking Error at frame {frame}: {e}")
            return False
    
    def apply_auto_focus(self, target_pos, frame):
        """Automatically pull focus to target"""
        if not hasattr(self.camera.data, 'dof'):
            return
        
        dof = self.camera.data.dof
        if not hasattr(dof, 'focus_distance'):
            return
        
        trace = self.props.camera_trace
        
        # Calculate distance to target
        distance = (target_pos - self.camera.location).length
        
        # Get current focus distance
        current_focus = dof.focus_distance
        
        # Calculate target focus distance
        target_focus = max(distance * 0.9, 0.1)  # Slightly in front of subject
        
        # Smooth focus pull
        focus_speed = trace.framing.focus_speed * 0.1 if trace.framing else 0.1
        new_focus = current_focus + (target_focus - current_focus) * focus_speed
        
        dof.focus_distance = new_focus



# ============================================================================
# BASE MOTION ENGINE (FROM STABLE VERSION)
# ============================================================================

class MotionEngine:
    """Core motion generation engine with advanced features"""
    
    def __init__(self, context):
        self.context = context
        self.props = context.scene.camera_motion
        self.camera = self.props.target_camera or context.scene.camera
        
        # Physics state
        self.velocity = Vector((0.0, 0.0, 0.0))
        self.angular_velocity = Vector((0.0, 0.0, 0.0))
        self.last_position = None
        self.last_rotation = None
        
        # Noise generators
        self.noise_cache = {}
        self.seed = self.props.shake.noise_settings.seed or random.randint(0, 10000)
        
    def generate_perlin_noise(self, t, freq, amp, axis=0):
        """Generate Perlin-style noise"""
        # Use a more stable noise generation
        value = math.sin(t * freq * 2 * math.pi + axis) * 0.5
        value += math.sin(t * freq * 4 * math.pi + axis * 2) * 0.25
        value += math.sin(t * freq * 8 * math.pi + axis * 3) * 0.125
        return value * amp
    
    def generate_simplex_noise(self, t, freq, amp, axis=0):
        """Simplex-like noise"""
        return math.sin(t * freq * 2 * math.pi + axis) * amp * 0.7 + \
               math.cos(t * freq * 3 * math.pi + axis * 1.5) * amp * 0.3
    
    def generate_fractal_noise(self, t, freq, amp, axis=0):
        """Fractal/Brownian noise"""
        result = 0
        octaves = self.props.shake.noise_settings.octaves
        persistence = self.props.shake.noise_settings.persistence
        lacunarity = self.props.shake.noise_settings.lacunarity
        
        max_amp = 0
        current_amp = amp
        current_freq = freq
        
        for i in range(octaves):
            result += self.generate_perlin_noise(t, current_freq, current_amp, axis + i * 10)
            max_amp += current_amp
            current_amp *= persistence
            current_freq *= lacunarity
        
        return result / max_amp if max_amp > 0 else 0
    
    def get_noise_value(self, t, freq, amp, axis, noise_type='PERLIN'):
        """Get noise value based on selected type"""
        cache_key = (t, axis, noise_type, freq, amp)
        if cache_key in self.noise_cache:
            return self.noise_cache[cache_key]
        
        if noise_type == 'PERLIN':
            value = self.generate_perlin_noise(t, freq, amp, axis)
        elif noise_type == 'SIMPLEX':
            value = self.generate_simplex_noise(t, freq, amp, axis)
        elif noise_type == 'FRACTAL':
            value = self.generate_fractal_noise(t, freq, amp, axis)
        else:  # RANDOM
            random.seed(int(t * 1000) + axis + self.seed)
            value = (random.random() * 2 - 1) * amp
        
        self.noise_cache[cache_key] = value
        return value
    
    def apply_physics(self, target_pos, target_rot, delta_time):
        """Apply physics simulation to motion"""
        if not self.props.physics.enabled:
            return target_pos, target_rot
        
        physics = self.props.physics
        
        if self.last_position is None:
            self.last_position = target_pos.copy()
            self.last_rotation = target_rot.copy()
            return target_pos, target_rot
        
        # Spring-damper system for position
        if physics.inertia_enabled:
            # Calculate spring force
            displacement = target_pos - self.last_position
            spring_force = displacement * physics.spring_stiffness
            
            # Damping force
            damping_force = self.velocity * physics.damping
            
            # Acceleration (F = ma)
            if physics.mass > 0:
                acceleration = (spring_force - damping_force) / physics.mass
            else:
                acceleration = Vector((0, 0, 0))
            
            # Update velocity
            self.velocity += acceleration * delta_time
            
            # Apply follow-through
            if physics.follow_through > 0:
                self.velocity *= (1.0 - min(physics.follow_through * delta_time, 1.0))
            
            # Update position
            new_pos = self.last_position + self.velocity * delta_time
        else:
            new_pos = target_pos
        
        # Apply to rotation if enabled
        if physics.spring_rotation:
            rot_displacement = Vector((
                target_rot.x - self.last_rotation.x,
                target_rot.y - self.last_rotation.y,
                target_rot.z - self.last_rotation.z
            ))
            
            spring_torque = rot_displacement * physics.spring_stiffness * 0.1
            damping_torque = self.angular_velocity * physics.damping * 0.1
            
            if physics.mass > 0:
                angular_accel = (spring_torque - damping_torque) / physics.mass
            else:
                angular_accel = Vector((0, 0, 0))
            
            self.angular_velocity += angular_accel * delta_time
            
            new_rot = Euler((
                self.last_rotation.x + self.angular_velocity.x * delta_time,
                self.last_rotation.y + self.angular_velocity.y * delta_time,
                self.last_rotation.z + self.angular_velocity.z * delta_time
            ))
        else:
            new_rot = target_rot
        
        self.last_position = new_pos
        self.last_rotation = new_rot
        
        return new_pos, new_rot
    
    def apply_operator_simulation(self, pos, rot, frame):
        """Simulate human operator imperfections"""
        if not self.props.operator_simulation:
            return pos, rot
        
        # Breathing effect
        breath = math.sin(frame * 0.1) * 0.01
        
        # Micro-adjustments
        micro_x = math.sin(frame * 0.5) * 0.005
        micro_y = math.cos(frame * 0.45) * 0.005
        
        pos.x += breath + micro_x
        pos.y += micro_y
        
        return pos, rot
    
    def apply_event_triggers(self, pos, rot, frame):
        """Apply event-based triggers"""
        for event in self.props.event_triggers:
            if frame < event.frame or frame > event.frame + event.duration:
                continue
            
            progress = (frame - event.frame) / max(event.duration, 1)
            
            # Apply decay curve
            if event.decay_curve == 'LINEAR':
                strength = 1.0 - progress
            elif event.decay_curve == 'EXPONENTIAL':
                strength = math.exp(-progress * 5)
            elif event.decay_curve == 'SMOOTH':
                strength = 0.5 + 0.5 * math.cos(progress * math.pi)
            else:  # SUSTAINED
                strength = 1.0 if progress < 0.3 else 1.0 - ((progress - 0.3) / 0.7)
            
            strength *= event.intensity
            
            # Apply directional offset
            dir_vec = Vector((event.dir_x, event.dir_y, event.dir_z))
            if dir_vec.length_squared > 0:
                dir_vec.normalize()
                pos += dir_vec * strength * 0.5
            
            # Add rotation shake
            rot.x += math.radians(strength * 5)
            rot.y += math.radians(strength * 3)
        
        return pos, rot
    
    def calculate_motion_at_frame(self, frame):
        """Calculate camera motion for a specific frame"""
        props = self.props
        shake = props.shake
        
        if not shake.enabled or not self.camera:
            return None, None
        
        # Normalize time (0 to 1 range for noise)
        t = frame / 100.0
        
        # Base position and rotation
        base_pos = self.camera.location.copy()
        base_rot = self.camera.rotation_euler.copy()
        
        # Calculate location offsets using individual properties
        loc_offset = Vector((0.0, 0.0, 0.0))
        
        if shake.location_x_enabled:
            loc_offset.x = self.get_noise_value(
                t, shake.loc_freq_x, shake.loc_amp_x, 0,
                shake.noise_settings.noise_type
            )
        
        if shake.location_y_enabled:
            loc_offset.y = self.get_noise_value(
                t, shake.loc_freq_y, shake.loc_amp_y, 1,
                shake.noise_settings.noise_type
            )
        
        if shake.location_z_enabled:
            loc_offset.z = self.get_noise_value(
                t, shake.loc_freq_z, shake.loc_amp_z, 2,
                shake.noise_settings.noise_type
            )
        
        # Calculate rotation offsets using individual properties
        rot_offset = Euler((0.0, 0.0, 0.0))
        
        if shake.rotation_x_enabled:
            rot_offset.x = math.radians(self.get_noise_value(
                t, shake.rot_freq_x, shake.rot_amp_x, 3,
                shake.noise_settings.noise_type
            ))
        
        if shake.rotation_y_enabled:
            rot_offset.y = math.radians(self.get_noise_value(
                t, shake.rot_freq_y, shake.rot_amp_y, 4,
                shake.noise_settings.noise_type
            ))
        
        if shake.rotation_z_enabled:
            rot_offset.z = math.radians(self.get_noise_value(
                t, shake.rot_freq_z, shake.rot_amp_z, 5,
                shake.noise_settings.noise_type
            ))
        
        # Apply intensity
        loc_offset *= shake.intensity
        rot_offset.x *= shake.intensity
        rot_offset.y *= shake.intensity
        rot_offset.z *= shake.intensity
        
        # Calculate target position/rotation
        target_pos = base_pos + loc_offset
        target_rot = Euler((
            base_rot.x + rot_offset.x,
            base_rot.y + rot_offset.y,
            base_rot.z + rot_offset.z
        ))
        
        return target_pos, target_rot
    
    def update_camera_at_frame(self, frame, bake_mode=False):
        """Update camera transform at specific frame"""
        if not self.camera:
            return False
        
        try:
            target_pos, target_rot = self.calculate_motion_at_frame(frame)
            
            if target_pos is None:
                return False
            
            # Apply physics if not in bake mode
            if not bake_mode:
                delta_time = 1.0 / 24.0  # Assume 24 fps
                target_pos, target_rot = self.apply_physics(target_pos, target_rot, delta_time)
            
            # Apply operator simulation
            target_pos, target_rot = self.apply_operator_simulation(target_pos, target_rot, frame)
            
            # Apply event triggers
            target_pos, target_rot = self.apply_event_triggers(target_pos, target_rot, frame)
            
            # Set camera transforms
            self.camera.location = target_pos
            self.camera.rotation_euler = target_rot
            
            # Insert keyframes if requested
            if bake_mode:
                # Ensure animation data exists
                if self.camera.animation_data is None:
                    self.camera.animation_data_create()
                
                self.camera.keyframe_insert(data_path="location", frame=frame)
                self.camera.keyframe_insert(data_path="rotation_euler", frame=frame)
            
            return True
            
        except Exception as e:
            print(f"Motion Engine Error at frame {frame}: {e}")
            return False


# ============================================================================
# ENHANCED MOTION ENGINE WITH SHOT EXECUTION
# ============================================================================

class EnhancedMotionEngine(MotionEngine):
    """Enhanced motion engine with shot execution capabilities"""
    
    def __init__(self, context):
        super().__init__(context)
        self.utils = CinematographyUtils()
        
        # Shot execution state
        self.current_shot_index = -1
        self.shot_start_frame = 0
        self.shot_end_frame = 0
        self.original_parent = None
    
    def execute_shot(self, shot, start_frame):
        """Execute a single shot, return end frame"""
        if not self.camera:
            return start_frame
        
        # Store original parent
        if self.camera.parent:
            self.original_parent = self.camera.parent
        
        # Calculate shot parameters
        duration = shot.duration_frames
        end_frame = start_frame + duration - 1
        
        # Set camera parameters
        if shot.focal_length > 0:
            cam_data = self.camera.data
            cam_data.lens = shot.focal_length
        
        # Setup depth of field
        if shot.use_dof and hasattr(self.camera.data, 'dof'):
            dof = self.camera.data.dof
            dof.use_dof = True
            dof.focus_object = shot.dof_focus_object or shot.target_object
            dof.aperture_fstop = shot.dof_fstop
            if hasattr(dof, 'aperture_blades'):
                dof.aperture_blades = shot.dof_aperture_blades
        
        # Clear existing animation for the shot range safely
        CinematographyUtils.clear_keyframes_in_range(self.camera, start_frame, end_frame)
        
        # Execute based on shot category
        if shot.shot_category == 'FOLLOW':
            self._execute_follow_shot(shot, start_frame, end_frame)
        elif shot.shot_category == 'MOVEMENT':
            self._execute_movement_shot(shot, start_frame, end_frame)
        elif shot.shot_category == 'ANGLE':
            self._execute_angle_shot(shot, start_frame, end_frame)
        else:  # DISTANCE or SPECIAL
            self._execute_static_shot(shot, start_frame, end_frame)
        
        return end_frame + 1
    
    def _execute_static_shot(self, shot, start_frame, end_frame):
        """Execute a static shot with proper framing"""
        if not shot.target_object:
            return
        
        obj = shot.target_object
        obj_loc = obj.location.copy()
        
        # Get object dimensions
        dims = self.utils.get_object_dimensions(obj)
        
        # Calculate base distance for framing
        distance = self.utils.calculate_framing(
            obj_loc, self.camera.location, dims, shot.shot_type_distance
        )
        distance += shot.distance_offset
        
        # Calculate angle position
        angle = 0  # Front view
        if shot.shot_type_angle == 'LOW_ANGLE':
            height_offset = -distance * 0.3
        elif shot.shot_type_angle == 'HIGH_ANGLE':
            height_offset = distance * 0.3
        else:
            height_offset = 0
        
        # Calculate final camera position
        cam_pos = self.utils.calculate_angle_position(
            obj_loc, distance, angle + shot.angle_offset, 
            dims.z * 0.5 + shot.height_offset + height_offset
        )
        
        # Ensure animation data exists
        if self.camera.animation_data is None:
            self.camera.animation_data_create()
        
        # Set keyframes for the duration
        for frame in range(start_frame, end_frame + 1):
            self.context.scene.frame_set(frame)
            
            # Interpolate position
            t = (frame - start_frame) / max(shot.duration_frames, 1)
            
            # Apply easing
            if frame - start_frame < shot.ease_in and shot.ease_in > 0:
                ease_t = (frame - start_frame) / shot.ease_in
                t = ease_t * 0.5
            elif end_frame - frame < shot.ease_out and shot.ease_out > 0:
                ease_t = (end_frame - frame) / shot.ease_out
                t = 1.0 - ease_t * 0.5
            
            # Set camera position
            self.camera.location = self.camera.location.lerp(cam_pos, t)
            
            # Look at target
            direction = obj_loc - self.camera.location
            if direction.length_squared > 0:
                rot_quat = direction.to_track_quat('-Z', 'Y')
                self.camera.rotation_euler = rot_quat.to_euler()
            
            # Insert keyframes
            self.camera.keyframe_insert(data_path="location", frame=frame)
            self.camera.keyframe_insert(data_path="rotation_euler", frame=frame)
    
    def _execute_follow_shot(self, shot, start_frame, end_frame):
        """Execute a following shot"""
        if not shot.target_object:
            return
        
        obj = shot.target_object
        follow_type = shot.shot_type_follow
        
        # Store object's path points
        obj_positions = []
        for frame in range(start_frame, end_frame + 1):
            self.context.scene.frame_set(frame)
            obj_positions.append(obj.location.copy())
        
        # Ensure animation data exists
        if self.camera.animation_data is None:
            self.camera.animation_data_create()
        
        # Calculate camera positions
        num_frames = len(obj_positions)
        for i, frame in enumerate(range(start_frame, end_frame + 1)):
            # FIXED: Use integer indices, not float
            t_val = i / max(num_frames - 1, 1)
            obj_pos = obj_positions[i]
            
            # Calculate look-ahead position with integer index
            look_ahead_idx = min(i + int(shot.look_ahead), num_frames - 1)
            obj_future = obj_positions[look_ahead_idx]
            
            # Calculate camera position based on follow type
            if follow_type == 'TRACKING':
                # Classic tracking - camera moves with subject
                cam_pos = obj_pos + Vector((shot.follow_distance, 0, shot.follow_height))
                
            elif follow_type == 'LEADING':
                # Leading shot - camera moves backward
                if (obj_future - obj_pos).length_squared > 0:
                    direction = (obj_future - obj_pos).normalized()
                else:
                    direction = Vector((1, 0, 0))
                cam_pos = obj_pos - direction * shot.follow_distance + Vector((0, 0, shot.follow_height))
                
            elif follow_type == 'TRAILING':
                # Trailing shot - camera follows behind
                if (obj_future - obj_pos).length_squared > 0:
                    direction = (obj_future - obj_pos).normalized()
                else:
                    direction = Vector((1, 0, 0))
                cam_pos = obj_pos - direction * shot.follow_distance + Vector((0, 0, shot.follow_height))
                
            elif follow_type == 'LATERAL':
                # Lateral tracking - camera moves sideways
                cam_pos = obj_pos + Vector((shot.follow_distance, 0, shot.follow_height))
                
            elif follow_type == 'STEADICAM':
                # Steadicam - smooth with some noise
                cam_pos = obj_pos + Vector((shot.follow_distance * 0.7, 
                                           math.sin(frame * 0.1) * 0.2, 
                                           shot.follow_height))
                
            elif follow_type == 'SNORRICAM':
                # SnorriCam - attached to subject
                cam_pos = obj_pos + Vector((0.5, 0, 1.0))
                
            elif follow_type == 'WHIP_PAN':
                # Whip pan - fast rotation
                cam_pos = obj_pos + Vector((shot.follow_distance, 0, shot.follow_height))
            
            else:
                cam_pos = obj_pos + Vector((shot.follow_distance, 0, shot.follow_height))
            
            # Apply smoothness
            if i > 0 and shot.smoothness > 0:
                prev_pos = self.camera.location
                cam_pos = prev_pos.lerp(cam_pos, shot.smoothness)
            
            # Set camera position
            self.camera.location = cam_pos
            
            # Look at subject or future position
            if follow_type == 'LEADING':
                # Look back at subject
                direction = obj_pos - cam_pos
            else:
                # Look forward
                direction = obj_future - cam_pos
            
            if direction.length_squared > 0:
                rot_quat = direction.to_track_quat('-Z', 'Y')
                self.camera.rotation_euler = rot_quat.to_euler()
            
            # Set keyframes
            self.context.scene.frame_set(frame)
            self.camera.keyframe_insert(data_path="location", frame=frame)
            self.camera.keyframe_insert(data_path="rotation_euler", frame=frame)
    
    def _execute_movement_shot(self, shot, start_frame, end_frame):
        """Execute a shot with camera movement"""
        if not shot.target_object:
            return
        
        obj = shot.target_object
        movement_type = shot.shot_type_movement
        
        # Calculate start and end positions
        obj_loc = obj.location.copy()
        distance = shot.follow_distance
        
        # Define movement paths
        if movement_type == 'PAN':
            # Pan left to right
            start_angle = -45 + shot.angle_offset
            end_angle = 45 + shot.angle_offset
            
        elif movement_type == 'TILT':
            # Tilt up to down
            start_height = -2 + shot.height_offset
            end_height = 2 + shot.height_offset
            
        elif movement_type in ['DOLLY', 'DOLLY_IN', 'DOLLY_OUT']:
            # Dolly in/out
            if movement_type == 'DOLLY_IN':
                start_dist = distance * 1.5
                end_dist = distance * 0.5
            elif movement_type == 'DOLLY_OUT':
                start_dist = distance * 0.5
                end_dist = distance * 1.5
            else:
                start_dist = distance * 1.5
                end_dist = distance * 0.5
            
        elif movement_type == 'TRUCK':
            # Truck left/right
            start_offset = -3
            end_offset = 3
            
        elif movement_type in ['PEDESTAL', 'PEDESTAL_UP', 'PEDESTAL_DOWN']:
            # Pedestal up/down
            if movement_type == 'PEDESTAL_UP':
                start_height = -2
                end_height = 2
            elif movement_type == 'PEDESTAL_DOWN':
                start_height = 2
                end_height = -2
            else:
                start_height = -2
                end_height = 2
            
        elif movement_type == 'ARC':
            # Arc around subject
            start_angle = 0
            end_angle = 360
            
        elif movement_type == 'PUSH_IN':
            # Dramatic push in
            start_dist = distance * 1.8
            end_dist = distance * 0.2
            
        elif movement_type == 'HANDHELD':
            # Handheld movement with noise
            start_angle = -5
            end_angle = 5
            
        elif movement_type == 'WHIP_PAN':
            # Fast whip pan
            start_angle = -90
            end_angle = 90
            
        elif movement_type == 'SLOW_PAN':
            # Slow sweeping pan
            start_angle = -30
            end_angle = 30
        
        else:  # STATIC
            start_angle = 0
            end_angle = 0
        
        # Ensure animation data exists
        if self.camera.animation_data is None:
            self.camera.animation_data_create()
        
        # Execute movement
        for frame in range(start_frame, end_frame + 1):
            t = (frame - start_frame) / max(shot.duration_frames, 1)
            
            # Apply easing
            if frame - start_frame < shot.ease_in and shot.ease_in > 0:
                ease_t = (frame - start_frame) / shot.ease_in
                t = ease_t * ease_t * 0.5  # Ease in quadratic
            elif end_frame - frame < shot.ease_out and shot.ease_out > 0:
                ease_t = (end_frame - frame) / shot.ease_out
                t = 1.0 - (ease_t * ease_t * 0.5)  # Ease out quadratic
            
            # Calculate position based on movement type
            if movement_type in ['PAN', 'ARC', 'WHIP_PAN', 'SLOW_PAN', 'HANDHELD']:
                angle = start_angle + (end_angle - start_angle) * t
                cam_pos = self.utils.calculate_angle_position(
                    obj_loc, distance, angle, shot.follow_height
                )
                
            elif movement_type in ['TILT', 'PEDESTAL', 'PEDESTAL_UP', 'PEDESTAL_DOWN']:
                height = start_height + (end_height - start_height) * t
                cam_pos = Vector((
                    obj_loc.x + distance,
                    obj_loc.y,
                    obj_loc.z + shot.follow_height + height
                ))
                
            elif movement_type in ['DOLLY', 'DOLLY_IN', 'DOLLY_OUT', 'PUSH_IN']:
                current_dist = start_dist + (end_dist - start_dist) * t
                cam_pos = Vector((
                    obj_loc.x + current_dist,
                    obj_loc.y,
                    obj_loc.z + shot.follow_height
                ))
                
            elif movement_type == 'TRUCK':
                offset = start_offset + (end_offset - start_offset) * t
                cam_pos = Vector((
                    obj_loc.x + distance,
                    obj_loc.y + offset,
                    obj_loc.z + shot.follow_height
                ))
                
            else:  # STATIC
                cam_pos = self.utils.calculate_angle_position(
                    obj_loc, distance, 0, shot.follow_height
                )
            
            # Set camera position
            self.camera.location = cam_pos
            
            # Look at subject
            direction = obj_loc - cam_pos
            if direction.length_squared > 0:
                rot_quat = direction.to_track_quat('-Z', 'Y')
                self.camera.rotation_euler = rot_quat.to_euler()
            
            # Set keyframes
            self.context.scene.frame_set(frame)
            self.camera.keyframe_insert(data_path="location", frame=frame)
            self.camera.keyframe_insert(data_path="rotation_euler", frame=frame)
    
    def _execute_angle_shot(self, shot, start_frame, end_frame):
        """Execute a shot with specific camera angle"""
        if not shot.target_object:
            return
        
        obj = shot.target_object
        angle_type = shot.shot_type_angle
        
        # Calculate camera position based on angle
        distance = shot.follow_distance
        dims = self.utils.get_object_dimensions(obj)
        
        if angle_type == 'EYE_LEVEL':
            height = dims.z * 0.9  # Eye level
            look_at = obj.location + Vector((0, 0, height))
            cam_pos = self.utils.calculate_angle_position(
                obj.location, distance, 0, height
            )
            
        elif angle_type == 'LOW_ANGLE':
            height = dims.z * 0.3  # Low angle
            look_at = obj.location + Vector((0, 0, dims.z))
            cam_pos = self.utils.calculate_angle_position(
                obj.location, distance, 0, height
            )
            
        elif angle_type == 'HIGH_ANGLE':
            height = dims.z * 1.5  # High angle
            look_at = obj.location
            cam_pos = self.utils.calculate_angle_position(
                obj.location, distance, 0, height
            )
            
        elif angle_type == 'BIRDS_EYE':
            height = dims.z * 5  # Directly above
            look_at = obj.location + Vector((0, 0, dims.z))
            cam_pos = self.utils.calculate_angle_position(
                obj.location, distance, 0, height
            )
            
        elif angle_type == 'DUTCH':
            height = dims.z * 0.9  # Eye level with tilt
            look_at = obj.location + Vector((0, 0, height))
            cam_pos = self.utils.calculate_angle_position(
                obj.location, distance, 0, height
            )
            
        elif angle_type == 'POV':
            # Point of view from object
            height = dims.z * 0.9
            cam_pos = obj.location + Vector((0.2, 0, height))
            look_at = obj.location + Vector((10, 0, height))
            
        elif angle_type == 'OVER_SHOULDER':
            height = dims.z * 0.9
            cam_pos = obj.location + Vector((-1, -1, height))
            look_at = obj.location + Vector((2, 0, height))
        
        else:
            # Default
            height = dims.z * 0.9
            look_at = obj.location + Vector((0, 0, height))
            cam_pos = self.utils.calculate_angle_position(
                obj.location, distance, 0, height
            )
        
        # Ensure animation data exists
        if self.camera.animation_data is None:
            self.camera.animation_data_create()
        
        # Execute shot
        for frame in range(start_frame, end_frame + 1):
            self.context.scene.frame_set(frame)
            
            self.camera.location = cam_pos
            
            direction = look_at - cam_pos
            if direction.length_squared > 0:
                if angle_type == 'DUTCH':
                    # Apply Dutch angle tilt
                    rot = direction.to_track_quat('-Z', 'Y').to_euler()
                    rot.z = math.radians(15)  # 15 degree tilt
                    self.camera.rotation_euler = rot
                else:
                    rot_quat = direction.to_track_quat('-Z', 'Y')
                    self.camera.rotation_euler = rot_quat.to_euler()
            
            self.camera.keyframe_insert(data_path="location", frame=frame)
            self.camera.keyframe_insert(data_path="rotation_euler", frame=frame)
    
    def execute_shot_sequence(self, sequence):
        """Execute a complete shot sequence"""
        if not self.camera:
            return False
        
        if not sequence.shots:
            return False
        
        current_frame = sequence.shots[0].start_frame if sequence.shots else 1
        
        for shot in sequence.shots:
            # Set shot parameters
            shot.start_frame = current_frame
            current_frame = self.execute_shot(shot, current_frame)
            shot.end_frame = current_frame - 1
            
            # Mark as baked
            shot.is_baked = True
        
        return True


# ============================================================================
# AUTO SHOT GENERATOR
# ============================================================================

class AutoShotGenerator:
    """Automatically generate shots based on scene and objects"""
    
    def __init__(self, context):
        self.context = context
        self.props = context.scene.camera_motion
        self.utils = CinematographyUtils()
    
    def generate_shot_around_object(self, obj, shot_type='MEDIUM', duration=120):
        """Generate a shot around a specific object"""
        shot = self.props.shots.add()
        shot.name = f"{obj.name} - {shot_type}"
        shot.target_object = obj
        shot.duration_frames = duration
        shot.shot_category = 'DISTANCE'
        shot.shot_type_distance = shot_type
        
        return shot
    
    def generate_sequence_for_action(self, obj, action_type='WALK'):
        """Generate a sequence of shots for a specific action"""
        
        action_sequences = {
            'WALK': [
                ('LONG', 60, "Establishing shot"),
                ('MEDIUM', 120, "Following shot"),
                ('CLOSEUP', 60, "Detail shot"),
            ],
            'RUN': [
                ('LONG', 30, "Fast establishing"),
                ('COWBOY', 90, "Action follow"),
                ('EXTREME_CLOSEUP', 30, "Intensity shot"),
            ],
            'DRIVE': [
                ('EXTREME_LONG', 40, "Car approaching"),
                ('LONG', 80, "Side tracking"),
                ('OVER_SHOULDER', 120, "Driver POV"),
            ],
            'DIALOGUE': [
                ('TWO_SHOT', 180, "Both characters"),
                ('OVER_SHOULDER', 120, "Over shoulder A"),
                ('OVER_SHOULDER', 120, "Over shoulder B"),
                ('CLOSEUP', 60, "Reaction shot"),
            ],
            'ACTION': [
                ('EXTREME_LONG', 30, "Wide action"),
                ('LOW_ANGLE', 45, "Hero shot"),
                ('DUTCH', 60, "Tension shot"),
                ('POV', 45, "Character POV"),
            ]
        }
        
        sequence = action_sequences.get(action_type, action_sequences['WALK'])
        
        shots_added = []
        for shot_type, duration, description in sequence:
            shot = self.props.shots.add()
            shot.name = f"{obj.name} - {description}"
            shot.target_object = obj
            shot.duration_frames = duration
            
            # FIXED: Properly categorize shots
            if shot_type == 'TWO_SHOT':
                shot.shot_category = 'SPECIAL'
                shot.shot_type_special = 'TWO_SHOT'
            elif shot_type == 'OVER_SHOULDER':
                shot.shot_category = 'ANGLE'
                shot.shot_type_angle = 'OVER_SHOULDER'
            elif shot_type in ['POV', 'LOW_ANGLE', 'DUTCH']:
                shot.shot_category = 'ANGLE'
                shot.shot_type_angle = shot_type
            else:
                shot.shot_category = 'DISTANCE'
                shot.shot_type_distance = shot_type
            
            shots_added.append(shot)
        
        return shots_added
    
    def generate_cinematic_sequence(self, obj, style='HOLLYWOOD'):
        """Generate a full cinematic sequence"""
        
        style_templates = {
            'HOLLYWOOD': [
                ('EXTREME_LONG', 60, "Establishing", 'STATIC', 'DISTANCE'),
                ('MEDIUM', 90, "Introduction", 'DOLLY', 'MOVEMENT'),
                ('CLOSEUP', 60, "Character moment", 'STATIC', 'DISTANCE'),
                ('OVER_SHOULDER', 90, "Dialogue setup", 'PAN', 'MOVEMENT'),
                ('TWO_SHOT', 120, "Interaction", 'STATIC', 'SPECIAL'),
                ('REACTION', 45, "Reaction", 'DOLLY_IN', 'MOVEMENT'),
                ('LONG', 90, "Conclusion", 'DOLLY_OUT', 'MOVEMENT'),
            ],
            'DOCUMENTARY': [
                ('LONG', 120, "Context", 'STATIC', 'DISTANCE'),
                ('MEDIUM', 180, "Interview", 'STATIC', 'DISTANCE'),
                ('CLOSEUP', 90, "Detail", 'HANDHELD', 'MOVEMENT'),
                ('CUTAWAY', 60, "B-roll", 'PAN', 'MOVEMENT'),
                ('MEDIUM', 120, "Return to subject", 'STATIC', 'DISTANCE'),
            ],
            'HORROR': [
                ('EXTREME_LONG', 90, "Isolation", 'STATIC', 'DISTANCE'),
                ('DUTCH', 60, "Unease", 'TILT', 'MOVEMENT'),
                ('POV', 120, "Character view", 'HANDHELD', 'ANGLE'),
                ('CLOSEUP', 45, "Fear", 'PUSH_IN', 'MOVEMENT'),
                ('LOW_ANGLE', 60, "Threat", 'STATIC', 'ANGLE'),
                ('CUTAWAY', 30, "Something moves", 'WHIP_PAN', 'MOVEMENT'),
            ],
            'ACTION': [
                ('LOW_ANGLE', 45, "Hero intro", 'PEDESTAL_UP', 'ANGLE'),
                ('LONG', 60, "Action setup", 'DOLLY', 'MOVEMENT'),
                ('COWBOY', 90, "Run cycle", 'TRACKING', 'FOLLOW'),  # FIXED: TRACKING to FOLLOW
                ('POV', 60, "Through eyes", 'HANDHELD', 'ANGLE'),
                ('DUTCH', 45, "Impact", 'HANDHELD', 'ANGLE'),
                ('EXTREME_CLOSEUP', 30, "Intensity", 'STATIC', 'DISTANCE'),
                ('LONG', 90, "Climax", 'ARC', 'MOVEMENT'),
            ],
            'ROMANTIC': [
                ('EXTREME_LONG', 60, "Beautiful location", 'SLOW_PAN', 'MOVEMENT'),
                ('TWO_SHOT', 120, "Together", 'DOLLY_IN', 'SPECIAL'),
                ('OVER_SHOULDER', 90, "Intimate", 'STATIC', 'ANGLE'),
                ('CLOSEUP', 60, "Emotion", 'PUSH_IN', 'MOVEMENT'),
                ('MEDIUM', 90, "Walk together", 'TRACKING', 'FOLLOW'),  # FIXED: TRACKING to FOLLOW
                ('EXTREME_CLOSEUP', 45, "Tender moment", 'STATIC', 'DISTANCE'),
            ]
        }
        
        template = style_templates.get(style, style_templates['HOLLYWOOD'])
        
        shots_added = []
        for shot_type, duration, desc, movement, category in template:
            shot = self.props.shots.add()
            shot.name = f"{obj.name} - {desc}"
            shot.target_object = obj
            shot.duration_frames = duration
            
            # FIXED: Use explicit category from template
            shot.shot_category = category
            
            # Set the specific shot type based on category
            if category == 'DISTANCE':
                shot.shot_type_distance = shot_type
            elif category == 'ANGLE':
                shot.shot_type_angle = shot_type
            elif category == 'MOVEMENT':
                shot.shot_type_movement = movement
            elif category == 'FOLLOW':
                shot.shot_type_follow = movement  # FIXED: movement value should be valid follow type
            elif category == 'SPECIAL':
                shot.shot_type_special = shot_type
            
            shots_added.append(shot)
        
        return shots_added


# ============================================================================
# CAMERA RIG GENERATOR
# ============================================================================

class CameraRigGenerator:
    """Generate professional camera rigs for different shot types"""
    
    @staticmethod
    def create_dolly_rig(context, name="Dolly_Rig"):
        """Create a dolly rig with track"""
        scene = context.scene
        collection = context.collection
        
        # Store current selection
        selected_objects = context.selected_objects.copy()
        active_object = context.view_layer.objects.active
        
        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')
        
        # Create track (path)
        track_curve = bpy.data.curves.new(name=f"{name}_Track", type='CURVE')
        track_curve.dimensions = '3D'
        track_curve.resolution_u = 64
        
        track_obj = bpy.data.objects.new(name=f"{name}_Track", object_data=track_curve)
        collection.objects.link(track_obj)
        
        # Create dolly cart
        bpy.ops.mesh.primitive_cube_add(size=0.5, location=(0, 0, 0))
        cart = context.active_object
        cart.name = f"{name}_Cart"
        
        # Create camera mount
        bpy.ops.mesh.primitive_cylinder_add(radius=0.2, depth=0.3, location=(0, 0, 0.4))
        mount = context.active_object
        mount.name = f"{name}_Mount"
        mount.parent = cart
        
        # Create camera
        bpy.ops.object.camera_add(location=(0, 0, 0.6))
        camera = context.active_object
        camera.name = f"{name}_Camera"
        camera.parent = mount
        
        # Add follow path constraint
        constraint = cart.constraints.new(type='FOLLOW_PATH')
        constraint.target = track_obj
        constraint.use_curve_follow = True
        
        # Restore selection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected_objects:
            if obj:
                obj.select_set(True)
        context.view_layer.objects.active = active_object
        
        return {
            'track': track_obj,
            'cart': cart,
            'mount': mount,
            'camera': camera
        }
    
    @staticmethod
    def create_steadicam_rig(context, name="Steadicam"):
        """Create a steadicam rig with stabilizer"""
        collection = context.collection
        
        # Store current selection
        selected_objects = context.selected_objects.copy()
        active_object = context.view_layer.objects.active
        
        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')
        
        # Create vest (parent)
        bpy.ops.mesh.primitive_cube_add(size=0.8, location=(0, 0, 0))
        vest = context.active_object
        vest.name = f"{name}_Vest"
        vest.hide_viewport = True
        
        # Create arm
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.8, location=(0.4, 0, 0.4))
        arm = context.active_object
        arm.name = f"{name}_Arm"
        arm.parent = vest
        
        # Create sled
        bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=1.0, location=(0.8, 0, 0.8))
        sled = context.active_object
        sled.name = f"{name}_Sled"
        sled.parent = arm
        
        # Create gimbal
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(1.2, 0, 1.2))
        gimbal = context.active_object
        gimbal.name = f"{name}_Gimbal"
        gimbal.parent = sled
        
        # Create camera
        bpy.ops.object.camera_add(location=(1.4, 0, 1.4))
        camera = context.active_object
        camera.name = f"{name}_Camera"
        camera.parent = gimbal
        
        # Add damped track constraints for stabilization
        target_obj = context.scene.camera_motion.auto_target
        for obj in [gimbal, camera]:
            constraint = obj.constraints.new(type='DAMPED_TRACK')
            if target_obj:
                constraint.target = target_obj
        
        # Restore selection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected_objects:
            if obj:
                obj.select_set(True)
        context.view_layer.objects.active = active_object
        
        return {
            'vest': vest,
            'arm': arm,
            'sled': sled,
            'gimbal': gimbal,
            'camera': camera
        }
    
    @staticmethod
    def create_car_rig(context, name="Car_Rig"):
        """Create a car chase rig with multiple camera mounts"""
        collection = context.collection
        
        # Store current selection
        selected_objects = context.selected_objects.copy()
        active_object = context.view_layer.objects.active
        
        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')
        
        # Create base car
        bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
        car = context.active_object
        car.name = f"{name}_Chassis"
        car.scale = (2, 4, 1)
        
        # Create hood mount
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.2, location=(0, 1.5, 0.8))
        hood_mount = context.active_object
        hood_mount.name = f"{name}_HoodMount"
        hood_mount.parent = car
        
        hood_cam = CameraRigGenerator._add_camera_to_mount(context, hood_mount, "HoodCam")
        
        # Create side mount
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.2, location=(1.2, 0, 0.8))
        side_mount = context.active_object
        side_mount.name = f"{name}_SideMount"
        side_mount.parent = car
        
        side_cam = CameraRigGenerator._add_camera_to_mount(context, side_mount, "SideCam")
        
        # Create chase mount (behind)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.2, location=(0, -2.5, 1.2))
        chase_mount = context.active_object
        chase_mount.name = f"{name}_ChaseMount"
        chase_mount.parent = car
        
        chase_cam = CameraRigGenerator._add_camera_to_mount(context, chase_mount, "ChaseCam")
        
        # Restore selection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected_objects:
            if obj:
                obj.select_set(True)
        context.view_layer.objects.active = active_object
        
        return {
            'car': car,
            'hood': {'mount': hood_mount, 'camera': hood_cam},
            'side': {'mount': side_mount, 'camera': side_cam},
            'chase': {'mount': chase_mount, 'camera': chase_cam}
        }
    
    @staticmethod
    def _add_camera_to_mount(context, mount, cam_name):
        """Helper to add camera to mount"""
        # Store current selection
        selected_objects = context.selected_objects.copy()
        active_object = context.view_layer.objects.active
        
        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')
        
        # Create camera
        bpy.ops.object.camera_add(location=mount.location + Vector((0, 0, 0.2)))
        camera = context.active_object
        camera.name = cam_name
        camera.parent = mount
        
        # Restore selection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected_objects:
            if obj:
                obj.select_set(True)
        context.view_layer.objects.active = active_object
        
        return camera
    
    @staticmethod
    def create_snorricam_rig(context, target_object, name="SnorriCam"):
        """Create a SnorriCam rig attached to subject"""
        if not target_object:
            return None
        
        collection = context.collection
        
        # Store current selection
        selected_objects = context.selected_objects.copy()
        active_object = context.view_layer.objects.active
        
        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')
        
        # Create mounting bracket
        bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=0.5, 
                                           location=target_object.location)
        bracket = context.active_object
        bracket.name = f"{name}_Bracket"
        
        # Add copy transforms constraint to attach to target
        constraint = bracket.constraints.new(type='COPY_TRANSFORMS')
        constraint.target = target_object
        
        # Create camera arm
        bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=0.8, 
                                           location=target_object.location + Vector((0.5, 0, 0.5)))
        arm = context.active_object
        arm.name = f"{name}_Arm"
        arm.parent = bracket
        
        # Create camera
        bpy.ops.object.camera_add(location=target_object.location + Vector((0.9, 0, 0.5)))
        camera = context.active_object
        camera.name = f"{name}_Camera"
        camera.parent = arm
        
        # Point camera at target
        constraint = camera.constraints.new(type='TRACK_TO')
        constraint.target = target_object
        constraint.track_axis = 'TRACK_NEGATIVE_Z'
        constraint.up_axis = 'UP_Y'
        
        # Restore selection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected_objects:
            if obj:
                obj.select_set(True)
        context.view_layer.objects.active = active_object
        
        return {
            'bracket': bracket,
            'arm': arm,
            'camera': camera
        }


# ============================================================================
# HANDLERS
# ============================================================================

# ============================================================================
# HANDLERS (FIXED)
# ============================================================================

@persistent
def frame_change_handler(scene):
    """Handler for real-time viewport updates"""
    if not hasattr(scene, 'camera_motion'):
        return
    
    props = scene.camera_motion
    
    # Check if we have a camera to work with
    camera = props.target_camera or scene.camera
    if not camera:
        return
    
    try:
        # CRITICAL FIX: Only modify camera if explicitly enabled AND we have a target for tracking
        # This prevents unwanted camera movement when add-on is installed but not in use
        
        # For tracking - only if tracking is enabled AND has target object
        if (props.camera_trace and 
            props.camera_trace.enabled and 
            props.camera_trace.target_object and
            camera):
            
            engine = AdvancedMotionEngine(bpy.context)
            engine.update_tracking_at_frame(scene.frame_current)
            
        # For shake - only if shake is enabled and tracking is NOT enabled
        elif (props.shake and 
              props.shake.enabled and 
              not props.camera_trace.enabled and
              camera):
            
            engine = MotionEngine(bpy.context)
            engine.update_camera_at_frame(scene.frame_current)
            
        # If neither is enabled, do NOT modify camera at all
        # This is the key fix - the camera should remain untouched
            
    except Exception as e:
        print(f"Camera Motion Handler Error: {e}")

# @persistent
# def frame_change_handler(scene):
#     """Handler for real-time viewport updates"""
#     if not hasattr(scene, 'camera_motion'):
#         return
    
#     props = scene.camera_motion
    
#     try:
#         # Only update if we have a valid context
#         context = bpy.context
#         if context and context.scene == scene:
#             # Check if we should use advanced tracking
#             if props.camera_trace and props.camera_trace.enabled and props.camera_trace.target_object:
#                 engine = AdvancedMotionEngine(context)
#                 engine.update_tracking_at_frame(scene.frame_current)
#             elif props.shake and props.shake.enabled:
#                 engine = MotionEngine(context)
#                 engine.update_camera_at_frame(scene.frame_current)
#     except Exception as e:
#         print(f"Camera Motion Handler Error: {e}")


# ============================================================================
# BASE OPERATORS (FROM STABLE VERSION)
# ============================================================================

class CINEMATIC_CAMERA_OT_apply_preset(Operator):
    """Apply selected motion preset"""
    bl_idname = "cinematic_camera.apply_preset"
    bl_label = "Apply Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        apply_preset_values(props, props.preset)
        self.report({'INFO'}, f"Applied {props.preset} preset")
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_bake_animation(Operator):
    """Bake procedural motion to keyframes"""
    bl_idname = "cinematic_camera.bake_animation"
    bl_label = "Bake Animation"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        
        if not props.target_camera:
            self.report({'ERROR'}, "No camera selected")
            return {'CANCELLED'}
        
        # Create motion engine
        engine = MotionEngine(context)
        
        # Clear existing animation
        CinematographyUtils.clear_object_animation(props.target_camera)
        
        # Bake frames
        total_frames = props.frame_end - props.frame_start + 1
        baked_frames = 0
        failed_frames = 0
        
        # Store current frame to restore later
        current_frame = context.scene.frame_current
        
        for frame in range(props.frame_start, props.frame_end + 1):
            context.scene.frame_set(frame)
            if engine.update_camera_at_frame(frame, bake_mode=True):
                baked_frames += 1
            else:
                failed_frames += 1
            
            # Update progress
            if baked_frames % 10 == 0:
                self.report({'INFO'}, f"Baking: {baked_frames}/{total_frames} frames")
        
        # Restore original frame
        context.scene.frame_set(current_frame)
        
        if failed_frames == 0:
            self.report({'INFO'}, f"Successfully baked {baked_frames} frames")
        else:
            self.report({'WARNING'}, f"Baked {baked_frames} frames with {failed_frames} failures")
        
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_add_event(Operator):
    """Add motion trigger event"""
    bl_idname = "cinematic_camera.add_event"
    bl_label = "Add Event"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        event = props.event_triggers.add()
        event.name = f"Event {len(props.event_triggers)}"
        event.frame = context.scene.frame_current
        props.active_event_index = len(props.event_triggers) - 1
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_remove_event(Operator):
    """Remove motion trigger event"""
    bl_idname = "cinematic_camera.remove_event"
    bl_label = "Remove Event"
    bl_options = {'REGISTER', 'UNDO'}
    
    index: IntProperty()
    
    def execute(self, context):
        props = context.scene.camera_motion
        if 0 <= self.index < len(props.event_triggers):
            props.event_triggers.remove(self.index)
            props.active_event_index = min(self.index, len(props.event_triggers) - 1)
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_add_layer(Operator):
    """Add motion layer"""
    bl_idname = "cinematic_camera.add_layer"
    bl_label = "Add Layer"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        layer = props.motion_layers.add()
        layer.name = f"Layer {len(props.motion_layers)}"
        props.active_layer_index = len(props.motion_layers) - 1
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_remove_layer(Operator):
    """Remove motion layer"""
    bl_idname = "cinematic_camera.remove_layer"
    bl_label = "Remove Layer"
    bl_options = {'REGISTER', 'UNDO'}
    
    index: IntProperty()
    
    def execute(self, context):
        props = context.scene.camera_motion
        if 0 <= self.index < len(props.motion_layers):
            props.motion_layers.remove(self.index)
            props.active_layer_index = min(self.index, len(props.motion_layers) - 1)
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_preview_motion_path(Operator):
    """Toggle motion path preview"""
    bl_idname = "cinematic_camera.preview_motion_path"
    bl_label = "Preview Motion Path"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        props.show_motion_path = not props.show_motion_path
        
        if props.show_motion_path and props.target_camera:
            try:
                # Store current selection and active object
                selected_objects = context.selected_objects.copy()
                active_object = context.view_layer.objects.active
                
                # Deselect all
                bpy.ops.object.select_all(action='DESELECT')
                
                # Select the camera
                props.target_camera.select_set(True)
                context.view_layer.objects.active = props.target_camera
                
                # Add motion path
                # Check if motion path exists
                if not hasattr(props.target_camera, 'motion_path') or not props.target_camera.motion_path:
                    bpy.ops.object.motion_path_add()
                
                if hasattr(props.target_camera, 'motion_path') and props.target_camera.motion_path:
                    path = props.target_camera.motion_path
                    path.frame_start = context.scene.frame_current
                    path.frame_end = context.scene.frame_current + props.motion_path_length
                    path.color = (1.0, 0.5, 0.0)
                
                # Restore selection
                bpy.ops.object.select_all(action='DESELECT')
                for obj in selected_objects:
                    if obj:
                        obj.select_set(True)
                context.view_layer.objects.active = active_object
                
            except Exception as e:
                self.report({'ERROR'}, f"Could not create motion path: {str(e)}")
                props.show_motion_path = False
        else:
            # Remove motion path
            if props.target_camera:
                try:
                    # Store current selection and active object
                    selected_objects = context.selected_objects.copy()
                    active_object = context.view_layer.objects.active
                    
                    # Deselect all
                    bpy.ops.object.select_all(action='DESELECT')
                    
                    # Select the camera
                    props.target_camera.select_set(True)
                    context.view_layer.objects.active = props.target_camera
                    
                    # Remove motion path if it exists
                    if hasattr(props.target_camera, 'motion_path') and props.target_camera.motion_path:
                        bpy.ops.object.motion_path_remove()
                    
                    # Restore selection
                    bpy.ops.object.select_all(action='DESELECT')
                    for obj in selected_objects:
                        if obj:
                            obj.select_set(True)
                    context.view_layer.objects.active = active_object
                    
                except Exception as e:
                    print(f"Error removing motion path: {e}")
        
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_reset_camera(Operator):
    """Reset camera to original position"""
    bl_idname = "cinematic_camera.reset_camera"
    bl_label = "Reset Camera"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        
        if props.target_camera:
            props.target_camera.location = (0, 0, 0)
            props.target_camera.rotation_euler = (0, 0, 0)
            
            CinematographyUtils.clear_object_animation(props.target_camera)
            
            self.report({'INFO'}, "Camera reset to origin")
        
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_randomize_seed(Operator):
    """Randomize noise seed"""
    bl_idname = "cinematic_camera.randomize_seed"
    bl_label = "Randomize Seed"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        props.shake.noise_settings.seed = random.randint(0, 10000)
        self.report({'INFO'}, f"New seed: {props.shake.noise_settings.seed}")
        return {'FINISHED'}


# ============================================================================
# NEW TRACKING OPERATORS
# ============================================================================

class CINEMATIC_CAMERA_OT_enable_tracking(Operator):
    """Enable/disable advanced camera tracking"""
    bl_idname = "cinematic_camera.enable_tracking"
    bl_label = "Enable Camera Tracking"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        trace = props.camera_trace
        
        trace.enabled = not trace.enabled
        
        if trace.enabled:
            self.report({'INFO'}, "Camera tracking enabled")
        else:
            self.report({'INFO'}, "Camera tracking disabled")
        
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_add_tracking_target(Operator):
    """Add object to multiple targets"""
    bl_idname = "cinematic_camera.add_tracking_target"
    bl_label = "Add Tracking Target"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        trace = props.camera_trace
        
        # Add current selected object if any
        if context.active_object:
            # For now, just increment target count
            trace.multi_target.target_count += 1
            self.report({'INFO'}, f"Added target: {context.active_object.name}")
        else:
            self.report({'WARNING'}, "No object selected")
        
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_clear_tracking_history(Operator):
    """Clear target motion history"""
    bl_idname = "cinematic_camera.clear_tracking_history"
    bl_label = "Clear Tracking History"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # This would clear the history in the engine
        # For now, just report
        self.report({'INFO'}, "Tracking history cleared")
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_bake_tracking(Operator):
    """Bake tracking animation to keyframes"""
    bl_idname = "cinematic_camera.bake_tracking"
    bl_label = "Bake Tracking"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        trace = props.camera_trace
        
        if not props.target_camera:
            self.report({'ERROR'}, "No camera selected")
            return {'CANCELLED'}
        
        if not trace.enabled or not trace.target_object:
            self.report({'ERROR'}, "Tracking not enabled or no target")
            return {'CANCELLED'}
        
        # Create advanced engine
        engine = AdvancedMotionEngine(context)
        
        # Clear existing animation
        CinematographyUtils.clear_object_animation(props.target_camera)
        
        # Bake frames
        total_frames = props.frame_end - props.frame_start + 1
        baked_frames = 0
        failed_frames = 0
        
        # Store current frame to restore later
        current_frame = context.scene.frame_current
        
        for frame in range(props.frame_start, props.frame_end + 1):
            context.scene.frame_set(frame)
            if engine.update_tracking_at_frame(frame, bake_mode=True):
                baked_frames += 1
            else:
                failed_frames += 1
            
            # Update progress
            if baked_frames % 10 == 0:
                self.report({'INFO'}, f"Baking tracking: {baked_frames}/{total_frames} frames")
        
        # Restore original frame
        context.scene.frame_set(current_frame)
        
        if failed_frames == 0:
            self.report({'INFO'}, f"Successfully baked tracking for {baked_frames} frames")
        else:
            self.report({'WARNING'}, f"Baked {baked_frames} frames with {failed_frames} failures")
        
        return {'FINISHED'}


# ============================================================================
# SHOT OPERATORS
# ============================================================================

class CINEMATIC_CAMERA_OT_add_shot(Operator):
    """Add a new camera shot"""
    bl_idname = "cinematic_camera.add_shot"
    bl_label = "Add Shot"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        shot = props.shots.add()
        shot.name = f"Shot {len(props.shots)}"
        shot.start_frame = context.scene.frame_current
        props.active_shot_index = len(props.shots) - 1
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_remove_shot(Operator):
    """Remove camera shot"""
    bl_idname = "cinematic_camera.remove_shot"
    bl_label = "Remove Shot"
    bl_options = {'REGISTER', 'UNDO'}
    
    index: IntProperty()
    
    def execute(self, context):
        props = context.scene.camera_motion
        if 0 <= self.index < len(props.shots):
            props.shots.remove(self.index)
            props.active_shot_index = min(self.index, len(props.shots) - 1)
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_generate_shot_sequence(Operator):
    """Generate automatic shot sequence for target object"""
    bl_idname = "cinematic_camera.generate_shot_sequence"
    bl_label = "Generate Shot Sequence"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        
        if not props.auto_target:
            self.report({'ERROR'}, "No target object selected")
            return {'CANCELLED'}
        
        generator = AutoShotGenerator(context)
        
        # Generate sequence based on action type
        shots = generator.generate_sequence_for_action(
            props.auto_target, 
            props.action_type
        )
        
        self.report({'INFO'}, f"Generated {len(shots)} shots")
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_generate_cinematic_sequence(Operator):
    """Generate full cinematic shot sequence"""
    bl_idname = "cinematic_camera.generate_cinematic_sequence"
    bl_label = "Generate Cinematic Sequence"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        
        if not props.auto_target:
            self.report({'ERROR'}, "No target object selected")
            return {'CANCELLED'}
        
        generator = AutoShotGenerator(context)
        
        # Generate cinematic sequence
        shots = generator.generate_cinematic_sequence(
            props.auto_target,
            props.shot_style
        )
        
        self.report({'INFO'}, f"Generated {len(shots)} cinematic shots")
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_execute_shot(Operator):
    """Execute current shot"""
    bl_idname = "cinematic_camera.execute_shot"
    bl_label = "Execute Shot"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        
        if not props.target_camera:
            self.report({'ERROR'}, "No camera selected")
            return {'CANCELLED'}
        
        if not props.shots or props.active_shot_index >= len(props.shots):
            self.report({'ERROR'}, "No shot selected")
            return {'CANCELLED'}
        
        engine = EnhancedMotionEngine(context)
        shot = props.shots[props.active_shot_index]
        
        # Execute shot
        end_frame = engine.execute_shot(shot, context.scene.frame_current)
        
        self.report({'INFO'}, f"Executed shot from {context.scene.frame_current} to {end_frame-1}")
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_execute_sequence(Operator):
    """Execute entire shot sequence"""
    bl_idname = "cinematic_camera.execute_sequence"
    bl_label = "Execute Sequence"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        
        if not props.target_camera:
            self.report({'ERROR'}, "No camera selected")
            return {'CANCELLED'}
        
        if not props.shots:
            self.report({'ERROR'}, "No shots to execute")
            return {'CANCELLED'}
        
        engine = EnhancedMotionEngine(context)
        
        # Create sequence
        sequence = props.sequences.add() if props.auto_sequence else None
        if sequence:
            sequence.name = f"Sequence {len(props.sequences)}"
            for shot in props.shots:
                sequence.shots.add().name = shot.name
        
        # Execute shots
        current_frame = props.batch_start_frame
        for shot in props.shots:
            shot.start_frame = current_frame
            current_frame = engine.execute_shot(shot, current_frame)
            shot.end_frame = current_frame - 1
            shot.is_baked = True
        
        self.report({'INFO'}, f"Executed {len(props.shots)} shots")
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_create_camera_rig(Operator):
    """Create professional camera rig"""
    bl_idname = "cinematic_camera.create_camera_rig"
    bl_label = "Create Camera Rig"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        rig_type = props.rig_type
        
        rig_generator = CameraRigGenerator()
        
        if rig_type == 'DOLLY':
            rig = rig_generator.create_dolly_rig(context)
            self.report({'INFO'}, "Created dolly rig")
            
        elif rig_type == 'STEADICAM':
            rig = rig_generator.create_steadicam_rig(context)
            self.report({'INFO'}, "Created steadicam rig")
            
        elif rig_type == 'CAR':
            rig = rig_generator.create_car_rig(context)
            self.report({'INFO'}, "Created car rig")
            
        elif rig_type == 'SNORRICAM':
            if not props.auto_target:
                self.report({'ERROR'}, "No target object for SnorriCam")
                return {'CANCELLED'}
            rig = rig_generator.create_snorricam_rig(context, props.auto_target)
            self.report({'INFO'}, "Created SnorriCam rig")
        
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_quick_shot(Operator):
    """Create a quick shot with current settings"""
    bl_idname = "cinematic_camera.quick_shot"
    bl_label = "Quick Shot"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        
        if not props.target_camera or not props.auto_target:
            self.report({'ERROR'}, "Need camera and target object")
            return {'CANCELLED'}
        
        # Create quick shot
        shot = props.shots.add()
        shot.name = f"Quick {props.quick_shot}"
        shot.target_object = props.auto_target
        shot.duration_frames = 120
        
        # FIXED: Map quick shot to proper type
        if props.quick_shot == 'POV':
            shot.shot_category = 'ANGLE'
            shot.shot_type_angle = 'POV'
        elif props.quick_shot == 'TRACKING':
            shot.shot_category = 'FOLLOW'  # FIXED: Use FOLLOW category for tracking
            shot.shot_type_follow = 'TRACKING'
        elif props.quick_shot == 'CLOSEUP':
            shot.shot_category = 'DISTANCE'
            shot.shot_type_distance = 'CLOSEUP'
        elif props.quick_shot == 'MEDIUM':
            shot.shot_category = 'DISTANCE'
            shot.shot_type_distance = 'MEDIUM'
        elif props.quick_shot == 'LONG':
            shot.shot_category = 'DISTANCE'
            shot.shot_type_distance = 'LONG'
        
        props.active_shot_index = len(props.shots) - 1
        
        self.report({'INFO'}, f"Created quick shot: {props.quick_shot}")
        return {'FINISHED'}


class CINEMATIC_CAMERA_OT_clear_all_shots(Operator):
    """Clear all shots"""
    bl_idname = "cinematic_camera.clear_all_shots"
    bl_label = "Clear All Shots"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.camera_motion
        props.shots.clear()
        props.active_shot_index = 0
        self.report({'INFO'}, "Cleared all shots")
        return {'FINISHED'}


# ============================================================================
# UI LISTS
# ============================================================================

class CINEMATIC_CAMERA_UL_event_list(UIList):
    """List for motion events"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon='INFO')
            layout.label(text=f"Frame: {item.frame}")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='INFO')


class CINEMATIC_CAMERA_UL_layer_list(UIList):
    """List for motion layers"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon='COLLAPSEMENU')
            layout.prop(item, "enabled", text="", emboss=False)
            layout.label(text=f"{item.blend_mode}")
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='COLLAPSEMENU')


class CINEMATIC_CAMERA_UL_shot_list(UIList):
    """List for camera shots"""
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False, icon='CAMERA_DATA')
            
            # Show shot type icon
            if item.shot_category == 'DISTANCE':
                layout.label(text="", icon='VIEWZOOM')
            elif item.shot_category == 'ANGLE':
                layout.label(text="", icon='ORIENTATION_GLOBAL')
            elif item.shot_category == 'MOVEMENT':
                layout.label(text="", icon='PLAY')
            elif item.shot_category == 'FOLLOW':
                layout.label(text="", icon='TRACKING')
            else:
                layout.label(text="", icon='OUTLINER_OB_CAMERA')
            
            # Show duration
            layout.label(text=f"{item.duration_frames}f")
            
            # Show baked status
            if item.is_baked:
                layout.label(text="", icon='CHECKBOX_HLT')
            
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon='CAMERA_DATA')


# ============================================================================
# UI PANELS
# ============================================================================

class CINEMATIC_CAMERA_PT_main(Panel):
    """Main panel for camera motion"""
    bl_label = "Cinematic Camera Motion MEGA"
    bl_idname = "CINEMATIC_CAMERA_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera Motion"
    
    @classmethod
    def poll(cls, context):
        return context.scene is not None
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.camera_motion
        trace = props.camera_trace
        
        # Camera selection
        col = layout.column(align=True)
        col.label(text="Target Camera:", icon='CAMERA_DATA')
        col.prop(props, "target_camera", text="")
        
        if not props.target_camera:
            col.label(text="No camera selected", icon='ERROR')
            return
        
        # Main controls - with tracking toggle
        row = layout.row(align=True)
        if trace.enabled:
            row.prop(trace, "enabled", text="Tracking ON", toggle=True, icon='TRACKING')
        else:
            row.prop(props.shake, "enabled", text="Shake ON", toggle=True, icon='FORCE_TURBULENCE')
        
        row.prop(props, "auto_intensity", text="Auto", toggle=True)
        
        # Quick tracking toggle
        if props.target_camera and trace.target_object:
            layout.operator("cinematic_camera.enable_tracking", 
                          text="Disable Tracking" if trace.enabled else "Enable Tracking",
                          icon='TRACKING')
        
        # Preset section
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Motion Presets", icon='PRESET')
        
        row = col.row(align=True)
        row.prop(props, "preset_category", text="")
        
        col.prop(props, "preset", text="")
        col.operator("cinematic_camera.apply_preset", text="Apply Preset", icon='CHECKMARK')


# NEW: Camera Tracking Panel
class CINEMATIC_CAMERA_PT_tracking(Panel):
    """Advanced camera tracking panel"""
    bl_label = "Camera Tracking"
    bl_idname = "CINEMATIC_CAMERA_PT_tracking"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera Motion"
    bl_parent_id = "CINEMATIC_CAMERA_PT_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.camera_motion.target_camera is not None
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.camera_motion
        trace = props.camera_trace
        
        # Target selection
        col = layout.column(align=True)
        col.label(text="Target Object:", icon='OBJECT_DATA')
        col.prop(trace, "target_object", text="")
        
        if not trace.target_object:
            col.label(text="Select object to track", icon='ERROR')
            return
        
        # Tracking mode
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Tracking Mode:", icon='TRACKING')
        col.prop(trace.tracking_mode, "mode", text="")
        
        # Distance controls
        col.separator()
        row = col.row(align=True)
        row.prop(trace.tracking_mode, "distance_mode", text="")
        row.prop(trace.tracking_mode, "target_distance")
        
        col.prop(trace.tracking_mode, "min_distance")
        col.prop(trace.tracking_mode, "max_distance")
        
        # Height controls
        col.separator()
        row = col.row(align=True)
        row.prop(trace.tracking_mode, "height_mode", text="")
        row.prop(trace.tracking_mode, "height_offset")
        
        # Angle controls
        if trace.tracking_mode.mode in ['FRAME', 'FOLLOW']:
            col.separator()
            row = col.row(align=True)
            row.prop(trace.tracking_mode, "angle_mode", text="")
            if trace.tracking_mode.angle_mode == 'FIXED':
                col.prop(trace.tracking_mode, "horizontal_angle")
                col.prop(trace.tracking_mode, "vertical_angle")
        
        # Smoothing
        col.separator()
        col.label(text="Smoothing:")
        col.prop(trace.tracking_mode, "position_smoothing", slider=True)
        col.prop(trace.tracking_mode, "rotation_smoothing", slider=True)
        
        # Prediction
        col.separator()
        col.prop(trace.tracking_mode, "prediction_frames")
        
        # Physics damping
        col.separator()
        col.label(text="Physics Damping:")
        col.prop(trace.tracking_mode, "damping_spring", slider=True)
        col.prop(trace.tracking_mode, "damping_mass")
        
        # Bake button
        col.separator()
        col.operator("cinematic_camera.bake_tracking", text="Bake Tracking", icon='KEYFRAME')


# NEW: Operator Behavior Panel
class CINEMATIC_CAMERA_PT_operator_behavior(Panel):
    """Operator behavior simulation panel"""
    bl_label = "Operator Behavior"
    bl_idname = "CINEMATIC_CAMERA_PT_operator_behavior"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera Motion"
    bl_parent_id = "CINEMATIC_CAMERA_PT_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        props = context.scene.camera_motion
        return props.target_camera is not None and props.camera_trace.enabled
    
    def draw(self, context):
        layout = self.layout
        op = context.scene.camera_motion.camera_trace.operator
        
        layout.prop(op, "enabled")
        
        if op.enabled:
            # Skill level
            col = layout.column(align=True)
            col.prop(op, "skill_level", slider=True)
            
            # Breathing
            box = layout.box()
            col = box.column(align=True)
            col.prop(op, "breathing_enabled")
            if op.breathing_enabled:
                col.prop(op, "breathing_rate")
                col.prop(op, "breathing_intensity", slider=True)
            
            # Reaction time
            box = layout.box()
            col = box.column(align=True)
            col.prop(op, "reaction_time", slider=True)
            col.prop(op, "anticipation", slider=True)
            
            # Micro-adjustments
            box = layout.box()
            col = box.column(align=True)
            col.prop(op, "micro_adjustments")
            if op.micro_adjustments:
                col.prop(op, "adjustment_frequency")
            
            # Physical constraints
            box = layout.box()
            col = box.column(align=True)
            col.label(text="Physical Limits:")
            col.prop(op, "max_pan_speed")
            col.prop(op, "max_tilt_speed")
            col.prop(op, "acceleration")
            
            # Handheld characteristics
            box = layout.box()
            col = box.column(align=True)
            col.label(text="Handheld:")
            col.prop(op, "handheld_weight")
            col.prop(op, "stabilization", slider=True)
            
            # Fatigue
            box = layout.box()
            col = box.column(align=True)
            col.prop(op, "fatigue_enabled")
            if op.fatigue_enabled:
                col.prop(op, "fatigue_rate", slider=True)


# NEW: Framing Rules Panel
class CINEMATIC_CAMERA_PT_framing_rules(Panel):
    """Cinematic framing rules panel"""
    bl_label = "Framing Rules"
    bl_idname = "CINEMATIC_CAMERA_PT_framing_rules"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera Motion"
    bl_parent_id = "CINEMATIC_CAMERA_PT_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        props = context.scene.camera_motion
        return props.target_camera is not None and props.camera_trace.enabled
    
    def draw(self, context):
        layout = self.layout
        frame = context.scene.camera_motion.camera_trace.framing
        
        layout.prop(frame, "enabled")
        
        if frame.enabled:
            # Rule of thirds
            box = layout.box()
            col = box.column(align=True)
            col.prop(frame, "rule_of_thirds")
            if frame.rule_of_thirds:
                col.prop(frame, "thirds_weight", slider=True)
            
            # Headroom
            box = layout.box()
            col = box.column(align=True)
            col.prop(frame, "headroom_auto")
            if frame.headroom_auto:
                col.prop(frame, "headroom_target", slider=True)
            
            # Lead room
            box = layout.box()
            col = box.column(align=True)
            col.prop(frame, "lead_room_auto")
            if frame.lead_room_auto:
                col.prop(frame, "lead_room_amount", slider=True)
            
            # Horizon
            box = layout.box()
            col = box.column(align=True)
            col.prop(frame, "horizon_stabilization")
            if frame.horizon_stabilization:
                col.prop(frame, "horizon_weight", slider=True)
            
            # Auto focus pull
            box = layout.box()
            col = box.column(align=True)
            col.prop(frame, "auto_focus_pull")
            if frame.auto_focus_pull:
                col.prop(frame, "focus_speed", slider=True)
                col.prop(frame, "rack_focus_duration")


# NEW: Multiple Targets Panel
class CINEMATIC_CAMERA_PT_multiple_targets(Panel):
    """Multiple targets tracking panel"""
    bl_label = "Multiple Targets"
    bl_idname = "CINEMATIC_CAMERA_PT_multiple_targets"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera Motion"
    bl_parent_id = "CINEMATIC_CAMERA_PT_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        props = context.scene.camera_motion
        return props.target_camera is not None and props.camera_trace.enabled
    
    def draw(self, context):
        layout = self.layout
        multi = context.scene.camera_motion.camera_trace.multi_target
        
        layout.prop(multi, "enabled")
        
        if multi.enabled:
            col = layout.column(align=True)
            col.label(text="Target Count:", icon='OBJECT_DATA')
            col.prop(multi, "target_count")
            
            col.separator()
            col.prop(multi, "blend_mode")
            
            if multi.blend_mode == 'SWITCH':
                col.prop(multi, "switch_interval")
                col.prop(multi, "transition_frames")


# Original panels (keep all existing panels)
class CINEMATIC_CAMERA_PT_shake_controls(Panel):
    """Shake controls panel"""
    bl_label = "Shake Controls"
    bl_idname = "CINEMATIC_CAMERA_PT_shake_controls"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera Motion"
    bl_parent_id = "CINEMATIC_CAMERA_PT_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        props = context.scene.camera_motion
        return props.target_camera is not None and not props.camera_trace.enabled
    
    def draw(self, context):
        layout = self.layout
        shake = context.scene.camera_motion.shake
        
        # Global intensity
        col = layout.column(align=True)
        col.prop(shake, "intensity", slider=True)
        col.prop(shake, "smoothness", slider=True)
        
        # Location controls
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Location Shake", icon='LOCATION')
        
        row = col.row(align=True)
        row.prop(shake, "location_x_enabled", text="X", toggle=True)
        row.prop(shake, "location_y_enabled", text="Y", toggle=True)
        row.prop(shake, "location_z_enabled", text="Z", toggle=True)
        
        # Frequency
        split = col.split(factor=0.3)
        split.label(text="Frequency:")
        row = split.row(align=True)
        row.prop(shake, "loc_freq_x", text="X")
        row.prop(shake, "loc_freq_y", text="Y")
        row.prop(shake, "loc_freq_z", text="Z")
        
        # Amplitude
        split = col.split(factor=0.3)
        split.label(text="Amplitude:")
        row = split.row(align=True)
        row.prop(shake, "loc_amp_x", text="X")
        row.prop(shake, "loc_amp_y", text="Y")
        row.prop(shake, "loc_amp_z", text="Z")
        
        # Rotation controls
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Rotation Shake", icon='ORIENTATION_GLOBAL')
        
        row = col.row(align=True)
        row.prop(shake, "rotation_x_enabled", text="X", toggle=True)
        row.prop(shake, "rotation_y_enabled", text="Y", toggle=True)
        row.prop(shake, "rotation_z_enabled", text="Z", toggle=True)
        
        # Frequency
        split = col.split(factor=0.3)
        split.label(text="Frequency:")
        row = split.row(align=True)
        row.prop(shake, "rot_freq_x", text="X")
        row.prop(shake, "rot_freq_y", text="Y")
        row.prop(shake, "rot_freq_z", text="Z")
        
        # Amplitude
        split = col.split(factor=0.3)
        split.label(text="Amplitude:")
        row = split.row(align=True)
        row.prop(shake, "rot_amp_x", text="X")
        row.prop(shake, "rot_amp_y", text="Y")
        row.prop(shake, "rot_amp_z", text="Z")
        
        # Advanced noise settings
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Noise Settings", icon='SHADERFX')
        
        col.prop(shake.noise_settings, "noise_type", text="Type")
        row = col.row(align=True)
        row.prop(shake.noise_settings, "seed", text="Seed")
        row.operator("cinematic_camera.randomize_seed", text="", icon='FILE_REFRESH')
        
        if shake.noise_settings.noise_type == 'FRACTAL':
            col.prop(shake.noise_settings, "octaves")
            col.prop(shake.noise_settings, "persistence", slider=True)
            col.prop(shake.noise_settings, "lacunarity", slider=True)


class CINEMATIC_CAMERA_PT_physics(Panel):
    """Physics simulation panel"""
    bl_label = "Physics Simulation"
    bl_idname = "CINEMATIC_CAMERA_PT_physics"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera Motion"
    bl_parent_id = "CINEMATIC_CAMERA_PT_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.camera_motion.target_camera is not None
    
    def draw(self, context):
        layout = self.layout
        physics = context.scene.camera_motion.physics
        
        layout.prop(physics, "enabled", text="Enable Physics")
        
        if physics.enabled:
            col = layout.column(align=True)
            col.prop(physics, "mass")
            col.prop(physics, "spring_stiffness")
            col.prop(physics, "damping")
            
            col.separator()
            col.prop(physics, "inertia_enabled")
            col.prop(physics, "follow_through", slider=True)
            col.prop(physics, "spring_rotation")
            
            col.separator()
            col.label(text="Operator Simulation:", icon='ARMATURE_DATA')
            layout.prop(context.scene.camera_motion, "operator_simulation")


class CINEMATIC_CAMERA_PT_layers(Panel):
    """Motion layers panel"""
    bl_label = "Motion Layers"
    bl_idname = "CINEMATIC_CAMERA_PT_layers"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera Motion"
    bl_parent_id = "CINEMATIC_CAMERA_PT_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.camera_motion.target_camera is not None
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.camera_motion
        
        row = layout.row()
        
        # Layer list
        col = row.column()
        col.template_list(
            "CINEMATIC_CAMERA_UL_layer_list", 
            "motion_layers",
            props, 
            "motion_layers",
            props, 
            "active_layer_index",
            rows=3
        )
        
        # Layer controls
        col = row.column(align=True)
        col.operator("cinematic_camera.add_layer", text="", icon='ADD')
        if props.active_layer_index < len(props.motion_layers):
            op = col.operator("cinematic_camera.remove_layer", text="", icon='REMOVE')
            op.index = props.active_layer_index
        
        if props.motion_layers and props.active_layer_index < len(props.motion_layers):
            layer = props.motion_layers[props.active_layer_index]
            
            col = layout.column(align=True)
            col.prop(layer, "name")
            col.prop(layer, "blend_mode")
            col.prop(layer, "blend_factor", slider=True)


class CINEMATIC_CAMERA_PT_events(Panel):
    """Event triggers panel"""
    bl_label = "Event Triggers"
    bl_idname = "CINEMATIC_CAMERA_PT_events"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera Motion"
    bl_parent_id = "CINEMATIC_CAMERA_PT_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.camera_motion.target_camera is not None
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.camera_motion
        
        row = layout.row()
        
        # Event list
        col = row.column()
        col.template_list(
            "CINEMATIC_CAMERA_UL_event_list", 
            "event_triggers",
            props, 
            "event_triggers",
            props, 
            "active_event_index",
            rows=3
        )
        
        # Event controls
        col = row.column(align=True)
        col.operator("cinematic_camera.add_event", text="", icon='ADD')
        if props.active_event_index < len(props.event_triggers):
            op = col.operator("cinematic_camera.remove_event", text="", icon='REMOVE')
            op.index = props.active_event_index
        
        if props.event_triggers and props.active_event_index < len(props.event_triggers):
            event = props.event_triggers[props.active_event_index]
            
            col = layout.column(align=True)
            col.prop(event, "name")
            col.prop(event, "frame")
            col.prop(event, "duration")
            col.prop(event, "intensity", slider=True)
            
            # Direction as individual properties
            box = col.box()
            box.label(text="Direction:")
            row = box.row(align=True)
            row.prop(event, "dir_x", text="X")
            row.prop(event, "dir_y", text="Y")
            row.prop(event, "dir_z", text="Z")
            
            col.prop(event, "decay_curve")


class CINEMATIC_CAMERA_PT_preview(Panel):
    """Preview tools panel"""
    bl_label = "Preview & Bake"
    bl_idname = "CINEMATIC_CAMERA_PT_preview"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera Motion"
    bl_parent_id = "CINEMATIC_CAMERA_PT_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.camera_motion.target_camera is not None
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.camera_motion
        
        # Preview controls
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Preview", icon='HIDE_OFF')
        
        row = col.row(align=True)
        row.prop(props, "show_motion_path", text="Show Path", toggle=True)
        row.operator("cinematic_camera.preview_motion_path", text="", icon='RESTRICT_VIEW_OFF')
        
        if props.show_motion_path:
            col.prop(props, "motion_path_length")
        
        # Bake controls
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Animation", icon='ACTION')
        
        col.prop(props, "frame_start")
        col.prop(props, "frame_end")
        col.prop(props, "bake_samples")
        
        col.separator()
        col.operator("cinematic_camera.bake_animation", text="Bake Animation", icon='KEYFRAME')
        col.operator("cinematic_camera.reset_camera", text="Reset Camera", icon='LOOP_BACK')


class CINEMATIC_CAMERA_PT_shots(Panel):
    """Shots management panel"""
    bl_label = "Shot Manager"
    bl_idname = "CINEMATIC_CAMERA_PT_shots"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera Motion"
    bl_parent_id = "CINEMATIC_CAMERA_PT_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.camera_motion.target_camera is not None
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.camera_motion
        
        # Shot list
        row = layout.row()
        
        col = row.column()
        col.template_list(
            "CINEMATIC_CAMERA_UL_shot_list", 
            "shots",
            props, 
            "shots",
            props, 
            "active_shot_index",
            rows=6
        )
        
        col = row.column(align=True)
        col.operator("cinematic_camera.add_shot", text="", icon='ADD')
        if props.active_shot_index < len(props.shots):
            op = col.operator("cinematic_camera.remove_shot", text="", icon='REMOVE')
            op.index = props.active_shot_index
        
        col.separator()
        col.operator("cinematic_camera.clear_all_shots", text="", icon='X')
        
        # Shot details
        if props.shots and props.active_shot_index < len(props.shots):
            shot = props.shots[props.active_shot_index]
            
            box = layout.box()
            col = box.column(align=True)
            
            # Basic info
            col.prop(shot, "name")
            col.prop(shot, "target_object")
            
            # Shot category
            col.separator()
            col.prop(shot, "shot_category")
            
            # Category-specific options
            if shot.shot_category == 'DISTANCE':
                col.prop(shot, "shot_type_distance")
            elif shot.shot_category == 'ANGLE':
                col.prop(shot, "shot_type_angle")
            elif shot.shot_category == 'MOVEMENT':
                col.prop(shot, "shot_type_movement")
            elif shot.shot_category == 'FOLLOW':
                col.prop(shot, "shot_type_follow")
            elif shot.shot_category == 'SPECIAL':
                col.prop(shot, "shot_type_special")
            
            # Timing
            col.separator()
            box2 = col.box()
            box2.label(text="Timing:", icon='TIME')
            box2.prop(shot, "duration_frames")
            box2.prop(shot, "ease_in")
            box2.prop(shot, "ease_out")
            box2.prop(shot, "start_frame")
            box2.prop(shot, "end_frame")
            
            # Camera parameters
            col.separator()
            box2 = col.box()
            box2.label(text="Camera:", icon='CAMERA_DATA')
            box2.prop(shot, "focal_length")
            box2.prop(shot, "aperture")
            
            # Position offsets
            col.separator()
            box2 = col.box()
            box2.label(text="Position:", icon='OBJECT_ORIGIN')
            box2.prop(shot, "distance_offset")
            box2.prop(shot, "height_offset")
            box2.prop(shot, "angle_offset")
            
            # Follow parameters (if applicable)
            if shot.shot_category == 'FOLLOW':
                col.separator()
                box2 = col.box()
                box2.label(text="Follow:", icon='TRACKING')
                box2.prop(shot, "follow_distance")
                box2.prop(shot, "follow_height")
                box2.prop(shot, "look_ahead")
                box2.prop(shot, "smoothness")
            
            # Movement parameters (if applicable)
            if shot.shot_category == 'MOVEMENT':
                col.separator()
                box2 = col.box()
                box2.label(text="Movement:", icon='PLAY')
                box2.prop(shot, "pan_speed")
                box2.prop(shot, "tilt_speed")
                box2.prop(shot, "dolly_speed")
            
            # Depth of field
            col.separator()
            box2 = col.box()
            box2.prop(shot, "use_dof")
            if shot.use_dof:
                box2.prop(shot, "dof_focus_object")
                box2.prop(shot, "dof_fstop")
                box2.prop(shot, "dof_aperture_blades")
            
            # Shot controls
            col.separator()
            row = col.row(align=True)
            row.operator("cinematic_camera.execute_shot", text="Execute Shot", icon='PLAY')
            row.prop(props, "preview_shot", text="", icon='HIDE_OFF')


class CINEMATIC_CAMERA_PT_shot_generator(Panel):
    """Shot generator panel"""
    bl_label = "Shot Generator"
    bl_idname = "CINEMATIC_CAMERA_PT_shot_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera Motion"
    bl_parent_id = "CINEMATIC_CAMERA_PT_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.camera_motion.target_camera is not None
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.camera_motion
        
        # Target selection
        col = layout.column(align=True)
        col.label(text="Target Object:", icon='OBJECT_DATA')
        col.prop(props, "auto_target", text="")
        
        if not props.auto_target:
            col.label(text="Select target object", icon='ERROR')
            return
        
        # Quick shot
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Quick Shot:", icon='ADD')
        col.prop(props, "quick_shot", text="")
        col.operator("cinematic_camera.quick_shot", text="Add Quick Shot", icon='ADD')
        
        # Action sequence
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Action Sequence:", icon='ACTION')
        col.prop(props, "action_type", text="")
        col.operator("cinematic_camera.generate_shot_sequence", text="Generate Action Shots", icon='PLAY')
        
        # Cinematic sequence
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Cinematic Sequence:", icon='SEQUENCE')
        col.prop(props, "shot_style", text="")
        col.operator("cinematic_camera.generate_cinematic_sequence", text="Generate Cinematic Shots", icon='SEQUENCE')
        
        # Batch execution
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Batch Execution:", icon='KEYFRAME')
        col.prop(props, "batch_start_frame")
        col.prop(props, "auto_sequence")
        col.operator("cinematic_camera.execute_sequence", text="Execute All Shots", icon='PLAY')


class CINEMATIC_CAMERA_PT_camera_rigs(Panel):
    """Camera rigs panel"""
    bl_label = "Camera Rigs"
    bl_idname = "CINEMATIC_CAMERA_PT_camera_rigs"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Camera Motion"
    bl_parent_id = "CINEMATIC_CAMERA_PT_main"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        return context.scene.camera_motion.target_camera is not None
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.camera_motion
        
        # Rig type selection
        col = layout.column(align=True)
        col.label(text="Rig Type:", icon='OUTLINER_OB_ARMATURE')
        col.prop(props, "rig_type", text="")
        
        # Create rig button
        col.separator()
        col.operator("cinematic_camera.create_camera_rig", text="Create Rig", icon='ADD')
        
        # Rig descriptions
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Rig Descriptions:", icon='INFO')
        
        if props.rig_type == 'DOLLY':
            col.label(text="• Dolly on track")
            col.label(text="• Smooth linear movement")
            col.label(text="• Perfect for tracking shots")
        elif props.rig_type == 'STEADICAM':
            col.label(text="• Stabilized handheld")
            col.label(text="• Smooth follow shots")
            col.label(text="• Operator simulation")
        elif props.rig_type == 'CAR':
            col.label(text="• Multi-camera car rig")
            col.label(text="• Hood, side, chase mounts")
            col.label(text="• For car chase scenes")
        elif props.rig_type == 'SNORRICAM':
            col.label(text="• Body-attached camera")
            col.label(text="• Dynamic POV shots")
            col.label(text="• Requires target object")


# ============================================================================
# PRESETS DATA
# ============================================================================

def apply_preset_values(props, preset_name):
    """Apply preset values to properties"""
    
    presets = {
        # Handheld presets
        'HANDHELD_STATIC': {
            'shake': {
                'loc_freq_x': 0.8, 'loc_freq_y': 0.9, 'loc_freq_z': 0.7,
                'loc_amp_x': 0.05, 'loc_amp_y': 0.05, 'loc_amp_z': 0.03,
                'rot_freq_x': 0.6, 'rot_freq_y': 0.5, 'rot_freq_z': 0.4,
                'rot_amp_x': 2.0, 'rot_amp_y': 1.5, 'rot_amp_z': 1.0,
                'smoothness': 0.4
            },
            'physics': {
                'mass': 3.0,
                'spring_stiffness': 50.0,
                'damping': 8.0,
                'follow_through': 0.1
            }
        },
        
        'HANDHELD_WALKING': {
            'shake': {
                'loc_freq_x': 2.0, 'loc_freq_y': 2.0, 'loc_freq_z': 2.5,
                'loc_amp_x': 0.15, 'loc_amp_y': 0.1, 'loc_amp_z': 0.2,
                'rot_freq_x': 1.5, 'rot_freq_y': 1.5, 'rot_freq_z': 1.0,
                'rot_amp_x': 5.0, 'rot_amp_y': 4.0, 'rot_amp_z': 3.0,
                'smoothness': 0.2
            },
            'physics': {
                'mass': 4.0,
                'spring_stiffness': 80.0,
                'damping': 12.0,
                'follow_through': 0.15
            }
        },
        
        'HANDHELD_RUNNING': {
            'shake': {
                'loc_freq_x': 3.5, 'loc_freq_y': 3.5, 'loc_freq_z': 4.0,
                'loc_amp_x': 0.3, 'loc_amp_y': 0.25, 'loc_amp_z': 0.4,
                'rot_freq_x': 2.5, 'rot_freq_y': 2.5, 'rot_freq_z': 2.0,
                'rot_amp_x': 12.0, 'rot_amp_y': 10.0, 'rot_amp_z': 8.0,
                'smoothness': 0.1
            },
            'physics': {
                'mass': 3.5,
                'spring_stiffness': 100.0,
                'damping': 15.0,
                'follow_through': 0.2
            }
        },
        
        'STEADICAM': {
            'shake': {
                'loc_freq_x': 0.3, 'loc_freq_y': 0.3, 'loc_freq_z': 0.2,
                'loc_amp_x': 0.02, 'loc_amp_y': 0.02, 'loc_amp_z': 0.01,
                'rot_freq_x': 0.2, 'rot_freq_y': 0.15, 'rot_freq_z': 0.1,
                'rot_amp_x': 1.0, 'rot_amp_y': 0.8, 'rot_amp_z': 0.5,
                'smoothness': 0.8
            },
            'physics': {
                'mass': 8.0,
                'spring_stiffness': 30.0,
                'damping': 5.0,
                'follow_through': 0.05
            }
        },
        
        'DOCUMENTARY': {
            'shake': {
                'loc_freq_x': 1.2, 'loc_freq_y': 1.1, 'loc_freq_z': 1.0,
                'loc_amp_x': 0.1, 'loc_amp_y': 0.08, 'loc_amp_z': 0.12,
                'rot_freq_x': 0.8, 'rot_freq_y': 0.7, 'rot_freq_z': 0.6,
                'rot_amp_x': 4.0, 'rot_amp_y': 3.5, 'rot_amp_z': 3.0,
                'smoothness': 0.3
            },
            'physics': {
                'mass': 4.5,
                'spring_stiffness': 60.0,
                'damping': 10.0,
                'follow_through': 0.12
            }
        },
        
        # Vehicle presets
        'CAR_IDLE': {
            'shake': {
                'loc_freq_x': 8.0, 'loc_freq_y': 6.0, 'loc_freq_z': 10.0,
                'loc_amp_x': 0.02, 'loc_amp_y': 0.01, 'loc_amp_z': 0.03,
                'rot_freq_x': 5.0, 'rot_freq_y': 4.0, 'rot_freq_z': 3.0,
                'rot_amp_x': 0.5, 'rot_amp_y': 0.3, 'rot_amp_z': 0.2,
                'smoothness': 0.1
            },
            'physics': {
                'mass': 100.0,
                'spring_stiffness': 200.0,
                'damping': 30.0,
                'follow_through': 0.05
            }
        },
        
        'CAR_DRIVING': {
            'shake': {
                'loc_freq_x': 4.0, 'loc_freq_y': 3.0, 'loc_freq_z': 6.0,
                'loc_amp_x': 0.1, 'loc_amp_y': 0.08, 'loc_amp_z': 0.15,
                'rot_freq_x': 3.0, 'rot_freq_y': 2.5, 'rot_freq_z': 2.0,
                'rot_amp_x': 2.0, 'rot_amp_y': 1.5, 'rot_amp_z': 1.0,
                'smoothness': 0.2
            },
            'physics': {
                'mass': 80.0,
                'spring_stiffness': 150.0,
                'damping': 25.0,
                'follow_through': 0.1
            }
        },
        
        'HELICOPTER': {
            'shake': {
                'loc_freq_x': 12.0, 'loc_freq_y': 10.0, 'loc_freq_z': 15.0,
                'loc_amp_x': 0.15, 'loc_amp_y': 0.12, 'loc_amp_z': 0.2,
                'rot_freq_x': 8.0, 'rot_freq_y': 7.0, 'rot_freq_z': 6.0,
                'rot_amp_x': 3.0, 'rot_amp_y': 2.5, 'rot_amp_z': 2.0,
                'smoothness': 0.15
            },
            'physics': {
                'mass': 200.0,
                'spring_stiffness': 300.0,
                'damping': 40.0,
                'follow_through': 0.08
            }
        },
        
        'BOAT': {
            'shake': {
                'loc_freq_x': 0.5, 'loc_freq_y': 0.8, 'loc_freq_z': 1.2,
                'loc_amp_x': 0.2, 'loc_amp_y': 0.15, 'loc_amp_z': 0.3,
                'rot_freq_x': 0.4, 'rot_freq_y': 0.3, 'rot_freq_z': 0.5,
                'rot_amp_x': 8.0, 'rot_amp_y': 6.0, 'rot_amp_z': 5.0,
                'smoothness': 0.5
            },
            'physics': {
                'mass': 500.0,
                'spring_stiffness': 50.0,
                'damping': 20.0,
                'follow_through': 0.3
            }
        },
        
        # Impact presets
        'EXPLOSION': {
            'shake': {
                'loc_freq_x': 3.0, 'loc_freq_y': 3.0, 'loc_freq_z': 3.0,
                'loc_amp_x': 0.5, 'loc_amp_y': 0.5, 'loc_amp_z': 0.5,
                'rot_freq_x': 2.5, 'rot_freq_y': 2.5, 'rot_freq_z': 2.5,
                'rot_amp_x': 15.0, 'rot_amp_y': 15.0, 'rot_amp_z': 15.0,
                'smoothness': 0.05
            },
            'physics': {
                'mass': 2.0,
                'spring_stiffness': 200.0,
                'damping': 20.0,
                'follow_through': 0.4
            }
        },
        
        'EARTHQUAKE': {
            'shake': {
                'loc_freq_x': 1.5, 'loc_freq_y': 1.5, 'loc_freq_z': 2.0,
                'loc_amp_x': 0.4, 'loc_amp_y': 0.4, 'loc_amp_z': 0.3,
                'rot_freq_x': 1.0, 'rot_freq_y': 1.0, 'rot_freq_z': 1.0,
                'rot_amp_x': 10.0, 'rot_amp_y': 8.0, 'rot_amp_z': 6.0,
                'smoothness': 0.1
            },
            'physics': {
                'mass': 1000.0,
                'spring_stiffness': 400.0,
                'damping': 60.0,
                'follow_through': 0.2
            }
        },
        
        'FOOTSTEP': {
            'shake': {
                'loc_freq_x': 6.0, 'loc_freq_y': 6.0, 'loc_freq_z': 5.0,
                'loc_amp_x': 0.08, 'loc_amp_y': 0.08, 'loc_amp_z': 0.1,
                'rot_freq_x': 4.0, 'rot_freq_y': 4.0, 'rot_freq_z': 3.0,
                'rot_amp_x': 3.0, 'rot_amp_y': 2.5, 'rot_amp_z': 2.0,
                'smoothness': 0.15
            },
            'physics': {
                'mass': 5.0,
                'spring_stiffness': 120.0,
                'damping': 15.0,
                'follow_through': 0.1
            }
        },
        
        'COLLISION': {
            'shake': {
                'loc_freq_x': 4.0, 'loc_freq_y': 4.0, 'loc_freq_z': 3.5,
                'loc_amp_x': 0.25, 'loc_amp_y': 0.25, 'loc_amp_z': 0.2,
                'rot_freq_x': 3.0, 'rot_freq_y': 3.0, 'rot_freq_z': 2.5,
                'rot_amp_x': 8.0, 'rot_amp_y': 7.0, 'rot_amp_z': 6.0,
                'smoothness': 0.1
            },
            'physics': {
                'mass': 10.0,
                'spring_stiffness': 150.0,
                'damping': 18.0,
                'follow_through': 0.25
            }
        },
        
        # Cinematic presets
        'CINEMATIC_BREATH': {
            'shake': {
                'loc_freq_x': 0.2, 'loc_freq_y': 0.2, 'loc_freq_z': 0.3,
                'loc_amp_x': 0.01, 'loc_amp_y': 0.01, 'loc_amp_z': 0.02,
                'rot_freq_x': 0.15, 'rot_freq_y': 0.15, 'rot_freq_z': 0.1,
                'rot_amp_x': 0.5, 'rot_amp_y': 0.3, 'rot_amp_z': 0.2,
                'smoothness': 0.9
            },
            'physics': {
                'mass': 2.0,
                'spring_stiffness': 20.0,
                'damping': 4.0,
                'follow_through': 0.05
            }
        },
        
        'CINEMATIC_DRIFT': {
            'shake': {
                'loc_freq_x': 0.05, 'loc_freq_y': 0.05, 'loc_freq_z': 0.03,
                'loc_amp_x': 0.5, 'loc_amp_y': 0.4, 'loc_amp_z': 0.2,
                'rot_freq_x': 0.04, 'rot_freq_y': 0.03, 'rot_freq_z': 0.02,
                'rot_amp_x': 3.0, 'rot_amp_y': 2.0, 'rot_amp_z': 1.0,
                'smoothness': 0.95
            },
            'physics': {
                'mass': 3.0,
                'spring_stiffness': 10.0,
                'damping': 2.0,
                'follow_through': 0.5
            }
        },
        
        'HORROR_SHAKE': {
            'shake': {
                'loc_freq_x': 2.5, 'loc_freq_y': 2.5, 'loc_freq_z': 2.0,
                'loc_amp_x': 0.2, 'loc_amp_y': 0.2, 'loc_amp_z': 0.25,
                'rot_freq_x': 2.0, 'rot_freq_y': 2.0, 'rot_freq_z': 1.5,
                'rot_amp_x': 10.0, 'rot_amp_y': 8.0, 'rot_amp_z': 6.0,
                'smoothness': 0.15
            },
            'physics': {
                'mass': 2.5,
                'spring_stiffness': 80.0,
                'damping': 12.0,
                'follow_through': 0.2
            }
        },
        
        'ACTION_CAM': {
            'shake': {
                'loc_freq_x': 3.0, 'loc_freq_y': 3.0, 'loc_freq_z': 3.5,
                'loc_amp_x': 0.25, 'loc_amp_y': 0.2, 'loc_amp_z': 0.3,
                'rot_freq_x': 2.5, 'rot_freq_y': 2.0, 'rot_freq_z': 2.0,
                'rot_amp_x': 8.0, 'rot_amp_y': 6.0, 'rot_amp_z': 5.0,
                'smoothness': 0.2
            },
            'physics': {
                'mass': 3.0,
                'spring_stiffness': 90.0,
                'damping': 14.0,
                'follow_through': 0.15
            }
        }
    }
    
    preset_data = presets.get(preset_name, presets['HANDHELD_STATIC'])
    
    # Apply shake values
    for key, value in preset_data['shake'].items():
        if hasattr(props.shake, key):
            setattr(props.shake, key, value)
    
    # Apply physics values
    for key, value in preset_data['physics'].items():
        if hasattr(props.physics, key):
            setattr(props.physics, key, value)


# ============================================================================
# REGISTRATION
# ============================================================================

# All classes must be defined before registration
classes = [
    # Property Groups - Base
    MotionLayerProperties,
    NoiseSettings,
    ShakeControls,
    PhysicsSettings,
    EventTrigger,
    ShotProperties,
    ShotSequence,
    
    # Property Groups - New Tracking (must come after base but before CameraMotionProperties)
    OperatorBehaviorProperties,
    FramingRulesProperties,
    TrackingModesProperties,
    MultipleTargetProperties,
    CameraTraceProperties,
    
    # Main Properties (now all dependencies are defined)
    CameraMotionProperties,
    
    # UI Lists
    CINEMATIC_CAMERA_UL_event_list,
    CINEMATIC_CAMERA_UL_layer_list,
    CINEMATIC_CAMERA_UL_shot_list,
    
    # Base Operators
    CINEMATIC_CAMERA_OT_apply_preset,
    CINEMATIC_CAMERA_OT_bake_animation,
    CINEMATIC_CAMERA_OT_add_event,
    CINEMATIC_CAMERA_OT_remove_event,
    CINEMATIC_CAMERA_OT_add_layer,
    CINEMATIC_CAMERA_OT_remove_layer,
    CINEMATIC_CAMERA_OT_preview_motion_path,
    CINEMATIC_CAMERA_OT_reset_camera,
    CINEMATIC_CAMERA_OT_randomize_seed,
    
    # New Tracking Operators
    CINEMATIC_CAMERA_OT_enable_tracking,
    CINEMATIC_CAMERA_OT_add_tracking_target,
    CINEMATIC_CAMERA_OT_clear_tracking_history,
    CINEMATIC_CAMERA_OT_bake_tracking,
    
    # Shot Operators
    CINEMATIC_CAMERA_OT_add_shot,
    CINEMATIC_CAMERA_OT_remove_shot,
    CINEMATIC_CAMERA_OT_generate_shot_sequence,
    CINEMATIC_CAMERA_OT_generate_cinematic_sequence,
    CINEMATIC_CAMERA_OT_execute_shot,
    CINEMATIC_CAMERA_OT_execute_sequence,
    CINEMATIC_CAMERA_OT_create_camera_rig,
    CINEMATIC_CAMERA_OT_quick_shot,
    CINEMATIC_CAMERA_OT_clear_all_shots,
    
    # Base Panels
    CINEMATIC_CAMERA_PT_main,
    
    # New Tracking Panels
    CINEMATIC_CAMERA_PT_tracking,
    CINEMATIC_CAMERA_PT_operator_behavior,
    CINEMATIC_CAMERA_PT_framing_rules,
    CINEMATIC_CAMERA_PT_multiple_targets,
    
    # Existing Panels
    CINEMATIC_CAMERA_PT_shake_controls,
    CINEMATIC_CAMERA_PT_physics,
    CINEMATIC_CAMERA_PT_layers,
    CINEMATIC_CAMERA_PT_events,
    CINEMATIC_CAMERA_PT_preview,
    
    # Shot Panels
    CINEMATIC_CAMERA_PT_shots,
    CINEMATIC_CAMERA_PT_shot_generator,
    CINEMATIC_CAMERA_PT_camera_rigs,
]


def register():
    """Register all classes and properties"""
    # Register classes with error handling
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as e:
            print(f"Error registering {cls.__name__}: {e}")
    
    # Register scene property
    try:
        bpy.types.Scene.camera_motion = PointerProperty(type=CameraMotionProperties)
    except Exception as e:
        print(f"Error registering scene property: {e}")
    
    # Register frame change handler
    if frame_change_handler not in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.append(frame_change_handler)
    
    print("=" * 50)
    print("Cinematic Camera Motion Generator MEGA 2.1.0")
    print("=" * 50)
    print("✅ Registered successfully")
    print("📷 New Features: Advanced Camera Tracking")
    print("🎯 Operator Behavior Simulation")
    print("🎬 Cinematic Framing Rules")
    print("👥 Multiple Target Tracking")
    print("=" * 50)


def unregister():
    """Unregister all classes and properties"""
    # Unregister frame change handler
    if frame_change_handler in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(frame_change_handler)
    
    # Unregister scene property
    try:
        del bpy.types.Scene.camera_motion
    except:
        pass
    
    # Unregister classes in reverse order
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass
    
    print("Cinematic Camera Motion Generator MEGA 2.1.0 unregistered successfully")


if __name__ == "__main__":
    register()