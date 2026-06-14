"""Autonomous-driving labeling functions (Snorkel baseline arm).

Mirrors the baseline repo's design (keyword sets + per-LF abstain), adapted to our
binary task on Title+Abstract:  SEED=1 / NOT_SEED=0 / ABSTAIN=-1  (matches eval cats.SEED).

The VOTE PREDICATES are pure python (no snorkel) so LF coverage can be checked
locally on Python 3.14. `build_snorkel_lfs()` wraps them with @labeling_function
for the actual LabelModel run (Colab, Python 3.10/3.11).
"""
from __future__ import annotations

SEED = 1
NOT_SEED = 0
ABSTAIN = -1

# ---- positive signal vocabularies ----
AUTONOMY_CORE = {
    "autonomous vehicle", "autonomous vehicles", "autonomous driving", "self-driving",
    "self driving", "driverless", "automated driving", "automated vehicle",
    "autonomous navigation", "autonomous car", "robotaxi", "self-driving car",
    "autonomously drive", "drive autonomously", "fully autonomous", "ego vehicle",
    "autonomous mobile", "autonomous control of a vehicle",
}
PLANNING = {
    "motion planning", "trajectory planning", "path planning", "trajectory generation",
    "trajectory prediction", "behavior planning", "decision planning", "route planning",
    "driving policy", "path generation",
}
PERCEPTION = {
    "sensor fusion", "lidar", "point cloud", "object detection", "obstacle detection",
    "lane detection", "lane keeping", "traffic sign", "traffic light", "free space",
    "drivable area", "semantic segmentation", "depth estimation", "radar", "camera",
    "bird's eye view", "occupancy grid", "pedestrian detection",
}
LOCALIZATION = {
    "localization", "hd map", "high-definition map", "slam", "odometry", "ego-motion",
    "pose estimation",
}
V2X = {
    "v2x", "v2v", "v2i", "vehicle-to-vehicle", "vehicle to vehicle", "vehicle-to-everything",
    "vehicle to everything", "connected vehicle", "connected vehicles", "cooperative driving",
    "platooning",
}
# context words that confirm the driving setting (used to gate generic perception/planning)
DRIVING_CTX = {
    "vehicle", "driving", "driver", "road", "lane", "traffic", "autonomous", "car",
    "automotive", "highway", "intersection", "steering", "ego",
}

# ---- hard-negative (ADAS / driver-assist where the human keeps control) ----
DRIVER_ASSIST = {
    "driver assistance", "driver-assistance", "advanced driver assistance",
    "lane departure warning", "blind spot warning", "blind-spot", "forward collision warning",
    "collision warning", "parking assist", "park assist", "driver monitoring",
    "drowsiness", "driver alert", "warns the driver", "alert the driver", "assist the driver",
    "adaptive cruise control", "lane keeping assist",
}
ASSIST_CONTROL_CUES = {
    "driver remains", "driver maintains", "human driver", "keeps the driver",
    "the driver in control", "manual control", "driver in control",
}


def _has_any(text: str, terms) -> bool:
    t = text.lower()
    return any(term in t for term in terms)


# ---------------- vote predicates (pure) ----------------
def vote_autonomy_core(text: str) -> int:
    return SEED if _has_any(text, AUTONOMY_CORE) else ABSTAIN


def vote_planning(text: str) -> int:
    if _has_any(text, PLANNING) and _has_any(text, DRIVING_CTX):
        return SEED
    return ABSTAIN


def vote_perception_driving(text: str) -> int:
    if _has_any(text, PERCEPTION) and (_has_any(text, AUTONOMY_CORE) or "autonomous" in text.lower()):
        return SEED
    return ABSTAIN


def vote_localization_driving(text: str) -> int:
    if _has_any(text, LOCALIZATION) and (_has_any(text, AUTONOMY_CORE) or "autonomous" in text.lower()):
        return SEED
    return ABSTAIN


def vote_v2x(text: str) -> int:
    return SEED if _has_any(text, V2X) else ABSTAIN


def vote_driver_assist_hardneg(text: str) -> int:
    """ADAS look-alike: assist signal present but no genuine autonomy core."""
    if _has_any(text, DRIVER_ASSIST) and not _has_any(text, AUTONOMY_CORE):
        return NOT_SEED
    if _has_any(text, ASSIST_CONTROL_CUES) and not _has_any(text, AUTONOMY_CORE):
        return NOT_SEED
    return ABSTAIN


# ---- non-road / non-driving autonomy look-alikes (robots, drones, etc.) ----
NONROAD_ROBOT = {
    "robotic vehicle", "robot vehicle", "mobile robot", "robotic mower", "lawn mower",
    "aerial vehicle", "unmanned aerial", "uav", "drone", "quadcopter", "aircraft",
    "underwater", "submarine", "marine robot", "spacecraft", "satellite", "rover",
    "climbing robot", "warehouse robot", "industrial robot", "robotic arm",
    "vacuum cleaner", "agricultural robot", "delivery robot",
}
ROAD_CUES = {
    "road", "lane", "highway", "intersection", "traffic", "street", "driving",
    "car", "automobile", "automotive", "self-driving",
}


def vote_nonroad_robot(text: str) -> int:
    """Autonomy in a non-road setting (aerial/underwater/industrial robot) -> NOT_SEED.

    Only fires when a non-road robot signal is present AND there is no road-driving cue.
    """
    if _has_any(text, NONROAD_ROBOT) and not _has_any(text, ROAD_CUES):
        return NOT_SEED
    return ABSTAIN


def vote_no_autonomy(text: str) -> int:
    """No autonomy / perception / planning / localization / V2X signal at all."""
    if not (_has_any(text, AUTONOMY_CORE) or _has_any(text, PLANNING)
            or _has_any(text, PERCEPTION) or _has_any(text, LOCALIZATION)
            or _has_any(text, V2X)):
        return NOT_SEED
    return ABSTAIN


# name -> predicate (order = column order in the label matrix)
LF_SPECS: list[tuple[str, callable]] = [
    ("lf_autonomy_core", vote_autonomy_core),
    ("lf_planning", vote_planning),
    ("lf_perception_driving", vote_perception_driving),
    ("lf_localization_driving", vote_localization_driving),
    ("lf_v2x", vote_v2x),
    ("lf_driver_assist_hardneg", vote_driver_assist_hardneg),
    ("lf_nonroad_robot", vote_nonroad_robot),
    ("lf_no_autonomy", vote_no_autonomy),
]


# ---------------- snorkel wrappers (Colab only) ----------------
def build_snorkel_lfs():
    """Wrap the pure predicates as Snorkel LabelingFunctions. Requires snorkel."""
    from snorkel.labeling import LabelingFunction

    def make(fn):
        return lambda x: fn(x.text)

    return [LabelingFunction(name=name, f=make(fn)) for name, fn in LF_SPECS]
