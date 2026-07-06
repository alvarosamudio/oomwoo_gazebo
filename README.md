# oomwoo_gazebo

URDF model, Gazebo simulation, and navigation stack for the [oomwoo](https://github.com/makerspet/oomwoo) open-source robot vacuum.

This is the self-hosted version of the `urdf-gazebo-sim` contribution by [@alvarosamudio](https://github.com/alvarosamudio). Built against the [OOMWOO ROS2 Software Interfaces](https://github.com/makerspet/oomwoo/blob/main/docs/SOFTWARE_INTERFACES.md) contract.

## Credits

This repo incorporates work from several contributors:

- **@xbattlax** — [PR #17](https://github.com/makerspet/oomwoo/pull/17) fix for `bump_recovery.py` (subscribing to `Contacts` + `msg.contacts` with robust `"ground_plane" in name.split("::")` ground-plane detection). Also author of [`oomwoo_recovery_safety`](oomwoo_recovery_safety/), a full recovery state machine with ladder escalation, safety pauses, JSON status, and Nav2 integration hooks. See [recovery-safety RFC](https://github.com/makerspet/oomwoo/tree/main/contributions/recovery-safety/xbattlax) for details.

`bump_recovery.py` is now deprecated in favor of `oomwoo_recovery_safety` for production use.

## Packages

```
oomwoo_gazebo/              # URDF, config, worlds, launch files, bump_recovery
oomwoo_recovery_safety/     # Recovery state machine by xbattlax
```

### oomwoo_gazebo structure

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
│   ├── navigation.yaml    # Nav2 stack parameters (controller, planner, costmaps, collision_monitor, docking)
│   ├── slam_toolbox.yaml  # SLAM Toolbox configuration
│   ├── map.yaml           # Nav2 placeholder map metadata
│   └── map.pgm            # Nav2 placeholder map image
├── worlds/                 # Gazebo simulation worlds
│   ├── empty.sdf
│   ├── living_room.sdf
│   ├── kitchen.sdf
│   ├── multi_room.sdf
│   └── narrow_passage.sdf
├── launch/                 # Launch files
│   ├── sim.launch.py              # Full simulation (Gazebo + bridge + robot + RViz)
│   ├── bumper_test.launch.py      # Bumper contact testing in empty world
│   ├── bump_recovery.launch.py    # Auto-recovery node (deprecated, use oomwoo_recovery_safety)
│   ├── teleop.launch.py           # Keyboard teleop
│   ├── slam.launch.py             # SLAM Toolbox
│   └── nav2.launch.py             # Nav2 navigation stack
├── rviz/
│   └── oomwoo.rviz        # RViz preset with robot, laser, map, plans, TF
├── oomwoo_gazebo/
│   ├── __init__.py
│   └── bump_recovery.py   # Bump-triggered backup + rotate (deprecated)
├── CMakeLists.txt
└── package.xml
```

## Quick Start

```bash
# Source your ROS2 + Gazebo workspace
source /opt/ros/jazzy/setup.bash

# Build
colcon build --packages-select oomwoo_gazebo

# Launch simulation (default: living_room.sdf)
ros2 launch oomwoo_gazebo sim.launch.py

# Use a different world:
ros2 launch oomwoo_gazebo sim.launch.py world:=/path/to/kitchen.sdf

# In another terminal, drive around
ros2 launch oomwoo_gazebo teleop.launch.py
```

> **Note:** The LiDAR uses `type="lidar"` (CpuLidar) — physics-based raycasting
> that requires **no GPU**. It uses the `gz-sim-cpu-lidar-system` plugin with
> DART physics + Bullet collision detector. This requires building the Gazebo
> libraries from source with CpuLidar support (PRs merged May 2026).
> See [Build Requirements](#build-requirements) below.

## Bumper

The front bumper is split into left and right segments, each with its own Gazebo contact sensor:

| Sensor          | Topic           | Collision             |
|-----------------|-----------------|-----------------------|
| Left bumper     | `/bumper_left`  | `bumper_left_collision` |
| Right bumper    | `/bumper_right` | `bumper_right_collision` |

### Recovery (recommended): oomwoo_recovery_safety

The [oomwoo_recovery_safety](oomwoo_recovery_safety/) package (by [@xbattlax](https://github.com/xbattlax)) provides a full recovery state machine:
- Bounded recovery ladders (backup → rotate → wiggle → clear_costmap → pause)
- Immediate safe stop for e-stop, cliff, wheel-drop, pickup
- JSON status on `/oomwoo/status` for integration with Home Assistant
- Nav2 behavior-server hooks via `/oomwoo/recovery/behavior_result`
- Unit tests for guaranteed termination and safety responses

```bash
# Build both packages
colcon build --packages-select oomwoo_gazebo oomwoo_recovery_safety
source install/setup.bash

# Launch recovery safety node
ros2 launch oomwoo_recovery_safety recovery_safety.launch.py
```

### Fallback: bump_recovery.py

A lightweight one-shot recovery node — backs up while rotating away from the collision, stops after 1.5 s.

**Deprecated.** For basic bumper testing:

```bash
ros2 launch oomwoo_gazebo bumper_test.launch.py
# In another terminal:
ros2 topic echo /bumper_left
ros2 topic echo /bumper_right
ros2 run oomwoo_gazebo bump_recovery.py
```

## SLAM

```bash
ros2 launch oomwoo_gazebo slam.launch.py
```

## Navigation

Provide a pre-built map or launch SLAM first to generate one, then:

```bash
ros2 launch oomwoo_gazebo nav2.launch.py map:=/path/to/your/map.yaml
```

The Nav2 bringup includes: controller, planner, smoother, behavior server, BT navigator,
velocity smoother, collision monitor, docking server, waypoint follower, and route server.

## Worlds

| World             | Description                    |
|-------------------|--------------------------------|
| `empty.sdf`       | Bare ground plane              |
| `living_room.sdf` | Sofa, table, walls             |
| `kitchen.sdf`     | Cabinets, island, appliances   |
| `multi_room.sdf`  | Connected rooms with doorways  |
| `narrow_passage.sdf` | Corridor with bottleneck    |

## Build Requirements

The CpuLidar sensor requires Gazebo libraries built from source with the latest
CpuLidar support:

```bash
# Clone Gazebo sources
mkdir -p /gz_ws/src && cd /gz_ws
vcs import src < collection-harmonic.yaml

# Apply CpuLidar patches (already in main branch since May 2026)
# gz-sensors: PR #593 — CpuLidarSensor
# gz-sim:     PR #3343 — CpuLidar system plugin
# gz-physics: PR #880 — Raycast support

# Build
colcon build --merge-install --packages-up-to gz-sim
source install/setup.bash
```

If you cannot build from source, use the **software rendering workaround** instead:
```bash
export MESA_GL_VERSION_OVERRIDE=3.3
export LIBGL_ALWAYS_SOFTWARE=1
gz sim -s -r --headless-rendering <world.sdf>
```

## Fixes Applied

| Issue | Fix |
|-------|-----|
| `param_bridge` executable not found | Renamed to `parameter_bridge` in both launch files |
| `/world/<name>/create` service missing | Added `gz-sim-user-commands-system` plugin to all SDF worlds |
| Robot couldn't be spawned without `-world` flag | Added `-world living_room` argument to `create` call |
| `collision_monitor` crashed on startup | Added `collision_monitor` section with proper polygon config |
| `docking_server` needed charging dock plugins | Added `docking_server` section with `SimpleChargingDock` |
| SDF `box size="..."` attribute syntax deprecated | Changed to nested `<box><size>...</size></box>` in all worlds |
| `fuel.gazebosim.org` remote model references | Replaced with self-contained light + ground_plane models |
| GPU LiDAR requires hardware GPU | Switched to `type="lidar"` (CpuLidar) with physics raycasting |
| Bumper bridge `Contact` → `Contacts` type mismatch | Fixed ROS msg type in `gz_bridge.yaml` and `bump_recovery.py` (by [@xbattlax](https://github.com/xbattlax), PR #17) |
| `bump_recovery.py` used `msg.collisions` on `Contact` (singular) | Switched to `Contacts` subscription and `msg.contacts` field; ground-plane detection uses robust `"ground_plane" in name.split("::")` pattern (by [@xbattlax](https://github.com/xbattlax)) |
| SDF 1.8 gravity deprecation warning | Moved `gravity` to `<world>` level in all SDFs |

## Dependencies

- ROS2 Jazzy
- Gazebo Harmonic (gz-sim9, with CpuLidar support from main branch)
- DART physics with Bullet collision detector
- `nav2_bringup`, `slam_toolbox`, `ros_gz_sim`, `ros_gz_bridge`, `teleop_twist_keyboard`
- `oomwoo_recovery_safety` — optional, recommended for production recovery

## License

Apache-2.0
