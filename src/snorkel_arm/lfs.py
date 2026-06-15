"""Autonomous-driving labeling functions (Snorkel baseline arm).

Labeling goal (the SAME query the MAS arm reasons over — both arms target this boundary):
    "Does the VEHICLE itself make driving decisions and automate driving (SEED), or does a
     HUMAN driver stay in control and the invention merely assists / warns, or is it unrelated
     (NOT_SEED)? The SAME sensing/CV/control technology is SEED when it automates driving and
     NOT_SEED when it only assists a human driver."

Snorkel cannot take a natural-language query — it can only express this via keyword/heuristic
labeling functions. These LFs are a good-faith keyword approximation of the automate-vs-assist
boundary. Their inherent limitation (e.g. "autonomous driving driver-assistance system" trips
both positive and negative keywords and cannot be resolved by keywords alone) is exactly the
gap the MAS reasoning arm is meant to close.

Binary task on Title+Abstract:  SEED=1 / NOT_SEED=0 / ABSTAIN=-1  (matches eval cats.SEED).
Vote predicates are pure python (testable on 3.14); build_snorkel_lfs() wraps them for Colab.
"""
from __future__ import annotations

SEED = 1
NOT_SEED = 0
ABSTAIN = -1

# ---- AUTOMATE: the vehicle drives itself (strong self-driving signal) ----
SELF_DRIVING_STRONG = {
    "autonomous vehicle", "autonomous vehicles", "self-driving", "self driving", "driverless",
    "automated driving", "autonomous driving", "fully autonomous", "fully automated",
    "without driver intervention", "without a driver", "without human intervention",
    "no human intervention", "drives itself", "drive itself", "autonomous navigation",
    "autonomously navigat", "robotaxi", "sae level 4", "sae level 5", "level 4 autonomous",
    "level 5 autonomous", "autonomous control of the vehicle", "self-driving car",
}
# weaker autonomy vocabulary (positive only with a driving context)
AUTONOMY_VOCAB = {
    "autonomous", "automated vehicle", "ego vehicle", "self-driving", "automated guided vehicle",
    "unmanned ground vehicle",
}
# driving-task tech that is positive ONLY in an autonomy/driving context
DRIVING_TASK = {
    "motion planning", "trajectory planning", "path planning", "trajectory generation",
    "behavior planning", "driving policy", "sensor fusion", "lidar", "point cloud",
    "object detection", "obstacle detection", "lane detection", "occupancy grid",
    "free space", "drivable area", "localization", "hd map", "slam", "ego-motion",
    "v2x", "v2v", "vehicle-to-vehicle", "vehicle-to-everything",
}
DRIVING_CTX = {
    "vehicle", "driving", "driver", "road", "lane", "traffic", "car", "automotive",
    "highway", "intersection", "steering", "ego", "autonomous",
}

# ---- ASSIST: a human driver stays in control (the boundary -> NOT_SEED) ----
ASSIST_TERMS = {
    "driver assistance", "driver-assistance", "advanced driver assistance", "adas",
    "lane departure warning", "blind spot", "forward collision warning", "collision warning",
    "parking assist", "park assist", "lane keeping assist", "lane-keeping assist",
    "adaptive cruise control", "driver monitoring", "drowsiness", "assists the driver",
    "assist the driver", "warns the driver", "warn the driver", "alerts the driver",
    "alert the driver", "notify the driver", "informs the driver", "driver alert",
}
HUMAN_CONTROL = {
    "driver remains in control", "driver maintains control", "the driver in control",
    "driver in control", "human driver", "manual control", "operated by a driver",
    "driver operates", "driver supervises", "driver monitors the", "requires the driver",
    "requires a driver", "under driver supervision", "semi-autonomous", "semi autonomous",
    "supervised by the driver", "driver to take over", "driver intervention is required",
}

# ---- out-of-scope (non-road autonomy / other domains) ----
NONROAD_ROBOT = {
    "robotic vehicle", "robot vehicle", "mobile robot", "robotic mower", "lawn mower",
    "aerial vehicle", "unmanned aerial", "uav", "drone", "quadcopter", "aircraft",
    "underwater", "submarine", "marine robot", "spacecraft", "satellite", "rover",
    "climbing robot", "warehouse robot", "industrial robot", "robotic arm",
    "vacuum cleaner", "agricultural robot", "delivery robot",
}
ROAD_CUES = {"road", "lane", "highway", "intersection", "traffic", "street", "driving",
             "car", "automobile", "automotive", "self-driving"}


def _has(text: str, terms) -> bool:
    t = text.lower()
    return any(term in t for term in terms)


# ---------------- vote predicates (pure) ----------------
def vote_self_driving(text: str) -> int:
    """Vehicle clearly drives itself -> SEED."""
    return SEED if _has(text, SELF_DRIVING_STRONG) else ABSTAIN


def vote_autonomy_context(text: str) -> int:
    """Autonomy vocabulary in a driving context -> SEED."""
    if _has(text, AUTONOMY_VOCAB) and _has(text, DRIVING_CTX):
        return SEED
    return ABSTAIN


def vote_driving_task(text: str) -> int:
    """Perception/planning/control for driving, in autonomy context, not assist-only -> SEED."""
    if _has(text, DRIVING_TASK) and (_has(text, AUTONOMY_VOCAB) or "autonomous" in text.lower()):
        if not (_has(text, ASSIST_TERMS) and not _has(text, SELF_DRIVING_STRONG)):
            return SEED
    return ABSTAIN


def vote_assist_human_control(text: str) -> int:
    """THE boundary LF: driver-assistance / human-in-control -> NOT_SEED, UNLESS the text
    clearly states the vehicle fully drives itself. Keyword approximation of automate-vs-assist."""
    if _has(text, SELF_DRIVING_STRONG):
        return ABSTAIN
    if _has(text, ASSIST_TERMS) or _has(text, HUMAN_CONTROL):
        return NOT_SEED
    return ABSTAIN


def vote_nonroad_robot(text: str) -> int:
    """Autonomy in a non-road setting (aerial/underwater/industrial) -> NOT_SEED."""
    if _has(text, NONROAD_ROBOT) and not _has(text, ROAD_CUES):
        return NOT_SEED
    return ABSTAIN


def vote_no_domain_signal(text: str) -> int:
    """No autonomous-driving signal at all -> NOT_SEED (also catches out-of-domain rows)."""
    if not (_has(text, SELF_DRIVING_STRONG) or _has(text, AUTONOMY_VOCAB)
            or _has(text, DRIVING_TASK) or _has(text, ASSIST_TERMS)):
        return NOT_SEED
    return ABSTAIN


LF_SPECS: list[tuple[str, callable]] = [
    ("lf_self_driving", vote_self_driving),
    ("lf_autonomy_context", vote_autonomy_context),
    ("lf_driving_task", vote_driving_task),
    ("lf_assist_human_control", vote_assist_human_control),
    ("lf_nonroad_robot", vote_nonroad_robot),
    ("lf_no_domain_signal", vote_no_domain_signal),
]


# ---------------- snorkel wrappers (Colab only) ----------------
def build_snorkel_lfs():
    from snorkel.labeling import LabelingFunction

    def make(fn):
        return lambda x: fn(x.text)

    return [LabelingFunction(name=name, f=make(fn)) for name, fn in LF_SPECS]
