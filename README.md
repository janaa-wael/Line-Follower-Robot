# Line-Follower-Robot-Project

This project was developed as part of the **Digital Twin course at Siemens Academy**. It implements a differential‑drive line-following robot using the **Innexis Virtual System Interconnect (VSI)** fabric. Three independent Python clients communicate over a CAN‑like bus to simulate the robot, compute PID control, and visualize the trajectory in real time.

The system is designed to study PID tuning, path tracking, and robustness under noise. All experiments (gain sweep, curved path, noise rejection, PD vs PID) are driven by environment variables — no code changes are required.


## 📁 Repository Structure

.
├── vsiBuildCommands # VSI configuration (signals, frames, components)
├── src/ # Source code for the three clients
│ ├── simulator/ # Robot simulator (kinematics, path, noise)
│ │ └── simulator.py
│ ├── controller/ # PID controller (lateral & heading errors)
│ │ └── controller.py
│ └── plotter/ # Real-time visualizer & data logger
│ └── plotter.py
├── README.md # This file
└── ... (generated VSI folders after vsiBuild)

## 🚀 Getting Started

### Prerequisites

- **Innexis VSI** installed and properly licensed (provided by Siemens Academy)
- Python 3.8+ with the following packages:
  - `numpy`, `matplotlib`, `pyqtgraph`, `PyQt6` (or `PySide6`

### 1. Generate the VSI System

First, create the digital twin using `vsiBuild`. This generates the `lineFollowerDemo` folder with all necessary C++ wrappers and the `FabricServer`.

```bash
cd /path/to/your/project/src
vsiBuild -f vsiBuildCommands
cd lineFollowerDemo
```

### 2. Run the Simulation

You need **four terminals** (or tabs). In each, navigate to the `lineFollowerDemo` folder.

| Terminal           | Command                                                      |
| ------------------ | ------------------------------------------------------------ |
| **1 – Server**     | `./FabricServer`                                             |
| **2 – Simulator**  | `export PATH_TYPE=0 NOISE_LEVEL=0.0; python3 src/simulator/simulator.py` |
| **3 – Controller** | `export KP_LATERAL=2.0 KI_LATERAL=0.15 KD_LATERAL=0.3 KP_HEADING=1.5; python3 src/controller/controller.py` |
| **4 – Plotter**    | `python3 src/plotter/plotter.py --save`                      |

The plotter window will open (if X11 is enabled) and the simulation will run for 60 seconds. After completion, CSV, PNG, and JSON files are saved in `results/`.

------

## 🧪 Experiments

All experiments are controlled by **environment variables**. Change them in the respective terminals and restart the simulation.

### E1 – PID Gain Sweep

Set the four gain variables in **Terminal 3** to different values. Example gain sets:

| Set          | KP_LATERAL | KI_LATERAL | KD_LATERAL | KP_HEADING |
| ------------ | ---------- | ---------- | ---------- | ---------- |
| Conservative | 0.5        | 0.05       | 0.1        | 0.4        |
| Moderate     | 1.0        | 0.1        | 0.2        | 0.8        |
| Balanced     | 2.0        | 0.15       | 0.3        | 1.5        |
| Aggressive   | 3.0        | 0.2        | 0.4        | 2.2        |
| High D       | 1.5        | 0.1        | 0.8        | 1.2        |

### E2 – Curved Path

In **Terminal 2**, set `PATH_TYPE=1` (curved sine wave). Use the best gains from E1.

### E3 – Noise Rejection

In **Terminal 2**, set `NOISE_LEVEL` to 0.1, 0.2, 0.3, etc. Keep the best gains.

### E4 – PD vs PID

- **PID**: use a set with `KI_LATERAL > 0`.
- **PD**: set `KI_LATERAL=0` in Terminal 3.

------

## 🔧 Environment Variables Reference

| Variable         | Default    | Description                                             |
| ---------------- | ---------- | ------------------------------------------------------- |
| `PATH_TYPE`      | 0          | Path type: 0 = straight, 1 = curved (sine), 2 = L-shape |
| `NOISE_LEVEL`    | 0.0        | Standard deviation of noise added to measurements (m)   |
| `KP_LATERAL`     | 2.0        | Proportional gain for lateral error                     |
| `KI_LATERAL`     | 0.15       | Integral gain for lateral error                         |
| `KD_LATERAL`     | 0.3        | Derivative gain for lateral error                       |
| `KP_HEADING`     | 1.5        | Proportional gain for heading error                     |
| `PLOTTER_OUTPUT` | experiment | Base name for output files                              |

------

## 📽️ Deliverables

- **Source code** – this repository
- **Report** – PDF with modeling equations, controller design, experiment descriptions, and KPI tables
- **Screencast** – 2–3 minute video showing the simulation (straight path, curved path, noise)
- **Plots & KPIs** – included in `results/` and the report

------

## 👥 Author

- [Jana Wael] – janawael119@gmail.com

*This project was created as part of the **Digital Twin course at Siemens Academy**.

------

*For any questions, please contact the author.*

