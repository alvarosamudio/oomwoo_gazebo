# oomwoo_gazebo

[![ROS2](https://img.shields.io/badge/ROS2-Jazzy-blue)](https://docs.ros.org/en/jazzy/)
[![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-orange)](https://gazebosim.org)
[![License](https://img.shields.io/badge/License-Apache--2.0-green)](LICENSE)

URDF model, Gazebo simulation worlds, and Nav2/SLAM configuration for the [OOMWOO](https://github.com/makerspet/oomwoo) open-source robot vacuum.

This is the self-hosted version of the `urdf-gazebo-sim` contribution by [@alvarosamudio](https://github.com/alvarosamudio), built against the [ROS2 Software Interfaces](https://github.com/makerspet/oomwoo/blob/main/docs/SOFTWARE_INTERFACES.md) contract.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Packages](#packages)
- [Features](#features)
  - [Simulation Worlds](#simulation-worlds)
  - [Bumper & Recovery](#bumper--recovery)
  - [SLAM](#slam)
  - [Navigation](#navigation)
- [Robot Specs](#robot-specs)
- [Build Requirements](#build-requirements)
- [Fixes Applied](#fixes-applied)
- [Dependencies](#dependencies)
- [Credits](#credits)
- [License](#license)

---

## Quick Start

```bash
source /opt/ros/jazzy/setup.bash

# Build
colcon build --packages-select oomwoo_gazebo
source install/setup.bash

# Launch simulation (default: living_room.sdf)
ros2 launch oomwoo_gazebo sim.launch.py

# In another terminal, drive around
ros2 launch oomwoo_gazebo teleop.launch.py
```

Use a different world:

```bash
ros2 launch oomwoo_gazebo sim.launch.py world:=/path/to/kitchen.sdf
```

---

## Packages

This repo contains two ROS2 packages:

| Package | Type | Description |
|---|---|---|
| `oomwoo_gazebo` | `ament_cmake` | URDF, config, worlds, launch files, legacy bump_recovery |
| `oomwoo_recovery_safety` | `ament_python` | Recovery state machine (by [@xbattlax](https://github.com/xbattlax)) |

### oomwoo_gazebo layout

```
oomwoo_gazebo/
├── urdf/                   # Robot description (xacro)
│   ├── robot.urdf.xacro   # Main URDF — includes all macros
│   ├── params.xacro       # Dimensions, masses, physical properties
│   ├── inertial.xacro     # Inertia macros (cylinder, sphere, box)
│   ├── materials.xacro    # Visual colors + Gazebo surface friction
│   └── plugins.xacro      # Gazebo plugins (diff-drive, lidar, bumpers)
├── config/                 # ROS2 + Gazebo configuration
│   ├── gz_bridge.yaml     # Topic bridges between ROS2 and Gazebo
│   ├── navigation.yaml    # Nav2 stack parameters
│   ├── slam_toolbox.yaml  # SLAM Toolbox configuration
│   ├── map.yaml           # Nav2 placeholder map metadata
│   └── map.pgm            # Nav2 placeholder map image
├── worlds/                 # Gazebo simulation worlds
│   ├── empty.sdf          # Bare ground plane
│   ├── living_room.sdf    # Sofa, table, walls
│   ├── kitchen.sdf        # Cabinets, island, appliances
│   ├── multi_room.sdf     # Connected rooms with doorways
│   └── narrow_passage.sdf # Corridor with bottleneck
├── launch/                 # Launch files
│   ├── sim.launch.py      # Full simulation (Gazebo + bridge + robot + RViz)
│   ├── bumper_test.launch.py
│   ├── bump_recovery.launch.py  # Deprecated — use oomwoo_recovery_safety
│   ├── teleop.launch.py
│   ├── slam.launch.py
│   └── nav2.launch.py
├── rviz/
│   └── oomwoo.rviz        # RViz preset with robot, laser, map, plans, TF
├── oomwoo_gazebo/
│   ├── __init__.py
│   └── bump_recovery.py   # Deprecated — use oomwoo_recovery_safety
├── CMakeLists.txt
└── package.xml
```

---

## Features

### Simulation Worlds

| World | Description |
|---|---|
| `empty.sdf` | Bare ground plane — ideal for bumper testing |
| `living_room.sdf` | Sofa, table, plant, obstacle box, walls |
| `kitchen.sdf` | Central island, dining table, chairs |
| `multi_room.sdf` | Two connected rooms with dividing wall |
| `narrow_passage.sdf` | Corridor with bottleneck obstacle |

All worlds use DART physics with Bullet collision detection, the Gazebo Sensors
system plugin for `gpu_lidar`, and contact plugins. The GPU LiDAR can run with
Mesa software rendering in headless Docker environments.

### Bumper & Recovery

The front bumper is split into left and right segments, each publishing contact events via Gazebo contact sensors:

| Sensor | Topic | Collision |
|---|---|---|
| Left bumper | `/bumper_left` | `bumper_left_collision` |
| Right bumper | `/bumper_right` | `bumper_right_collision` |

#### Recommended: oomwoo_recovery_safety

The [oomwoo_recovery_safety](oomwoo_recovery_safety/) package by [@xbattlax](https://github.com/xbattlax) provides a production-ready recovery state machine:

- Bounded recovery ladders: back up → rotate away → wiggle free → clear costmap → pause
- Immediate safe stop for e-stop, cliff, wheel-drop, and pickup events
- JSON status on `/oomwoo/status` (structured for Home Assistant integration)
- Nav2 behavior-server hooks via `/oomwoo/recovery/behavior_result`
- Unit-tested for guaranteed termination and safety responses

```bash
colcon build --packages-select oomwoo_gazebo oomwoo_recovery_safety
source install/setup.bash
ros2 launch oomwoo_recovery_safety recovery_safety.launch.py
```

#### Legacy: bump_recovery.py

A lightweight one-shot recovery node — backs up while rotating away from the collision, stops after 1.5 s. **Deprecated** in favor of `oomwoo_recovery_safety`.

```bash
ros2 launch oomwoo_gazebo bumper_test.launch.py
ros2 run oomwoo_gazebo bump_recovery.py
```

### SLAM

```bash
ros2 launch oomwoo_gazebo slam.launch.py
```

Launches `async_slam_toolbox_node` with `use_sim_time` and configured slam_toolbox parameters.

### Navigation

```bash
ros2 launch oomwoo_gazebo nav2.launch.py map:=/path/to/your/map.yaml
```

The Nav2 bringup includes:

| Component | Description |
|---|---|
| Planner server | Navfn global planner |
| Controller server | DWB local planner with custom critic weights |
| Behavior server | Spin, backup, drive_on_heading, wait |
| BT navigator | Behavior tree with replanning and recovery |
| Collision monitor | Polygon stop zone + scan observation |
| Docking server | SimpleChargingDock plugin |
| Velocity smoother | Acceleration-limited commands |
| Waypoint follower | Sequential goal execution |
| Route server | Multi-segment route planning |

---

## Robot Specs

| Parameter | Value | Description |
|---|---|---|
| base_diameter | 0.33 m | Chassis diameter |
| wheel_diameter | 0.065 m | Drive wheels diameter |
| wheel_base | 0.28 m | Distance between drive wheels |
| lidar_z_offset | 0.075 m | LiDAR height offset |
| bumper_width | 0.12 m | Each bumper pad width |
| bumper_height | 0.025 m | Bumper pad height |

---

## Build Requirements

The supported Docker path uses Gazebo Harmonic's binary packages and the
standard `gz-sim-sensors-system` plugin. The robot URDF uses
`type="gpu_lidar"`; no custom Gazebo build is required.

### Docker (recommended)

The project image contains ROS 2 Jazzy, Gazebo Harmonic, RViz, `colcon`, and
the ROS-Gazebo bridge:

```bash
docker pull makerspet/oomwoo:jazzy-dev
docker run --rm -it \
  -v "$PWD":/workspace/src/oomwoo_gazebo \
  makerspet/oomwoo:jazzy-dev bash
```

Inside the container:

```bash
source /opt/ros/jazzy/setup.bash
cd /workspace
colcon build --symlink-install
source install/setup.bash
```

### Headless / software rendering

For CI, SSH, or hosts without a usable GPU, set Mesa software rendering and
use Gazebo's server-only mode:

```bash
export MESA_GL_VERSION_OVERRIDE=3.3
export LIBGL_ALWAYS_SOFTWARE=1
gz sim -s -r --headless-rendering \
  install/oomwoo_gazebo/share/oomwoo_gazebo/worlds/living_room.sdf
```

The `gz-sim-sensors-system` world plugin must remain enabled for GPU LiDAR;
removing it makes `/scan` exist without publishing samples.

---

## Fixes Applied

| Issue | Fix |
|---|---|
| `param_bridge` executable not found | Renamed to `parameter_bridge` in launch files |
| `/world/<name>/create` service missing | Added `gz-sim-user-commands-system` plugin to all SDF worlds |
| Robot couldn't spawn without `-world` flag | Added `-world living_room` argument to `create` call |
| `collision_monitor` crashed on startup | Added `collision_monitor` with proper polygon config |
| `docking_server` needed charging dock plugins | Added `SimpleChargingDock` configuration |
| SDF `box size="..."` attribute syntax deprecated | Changed to nested `<box><size>...</size></box>` in all worlds |
| `fuel.gazebosim.org` remote model references | Replaced with self-contained light + ground_plane models |
| CpuLidar unavailable in the Jazzy Harmonic image | Switched worlds to `gz-sim-sensors-system` and `type="gpu_lidar"`; headless runs use Mesa software rendering |
| Bumper bridge `Contact` → `Contacts` type mismatch | Fixed ROS msg type in `gz_bridge.yaml` and `bump_recovery.py` (by [@xbattlax](https://github.com/xbattlax), [PR #17](https://github.com/makerspet/oomwoo/pull/17)) |
| `bump_recovery.py` used `msg.collisions` on `Contact` (singular) | Switched to `Contacts` subscription and `msg.contacts` field; ground-plane detection uses robust `"ground_plane" in name.split("::")` pattern (by [@xbattlax](https://github.com/xbattlax)) |
| SDF 1.8 gravity deprecation warning | Moved `gravity` from `<physics>` to `<world>` level in all SDFs |

---

## Dependencies

- **ROS2** Jazzy (also compatible with Humble)
- **Gazebo** Harmonic (gz-sim8, with `gz-sim-sensors-system`)
- **Physics** DART with Bullet collision detector
- **Packages:** `nav2_bringup`, `slam_toolbox`, `ros_gz_sim`, `ros_gz_bridge`, `teleop_twist_keyboard`
- **Optional:** `oomwoo_recovery_safety` — recommended for production recovery

---

## Credits

- [@alvarosamudio](https://github.com/alvarosamudio) — URDF model, Gazebo worlds, launch files, configuration, original bump_recovery node
- [@xbattlax](https://github.com/xbattlax) — [PR #17](https://github.com/makerspet/oomwoo/pull/17) bug fix for bump_recovery (`Contacts` + `msg.contacts` + `"ground_plane" in name.split("::")`); author of [`oomwoo_recovery_safety`](oomwoo_recovery_safety/), a full recovery state machine with ladder escalation, safety pauses, JSON status, and Nav2 integration hooks. See the [recovery-safety RFC](https://github.com/makerspet/oomwoo/tree/main/contributions/recovery-safety/xbattlax) for details.
- [makerspet](https://github.com/makerspet) — OOMWOO project maintainer; [ROS2 Software Interfaces](https://github.com/makerspet/oomwoo/blob/main/docs/SOFTWARE_INTERFACES.md) contract

---

## License

Apache-2.0
