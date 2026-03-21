"""
real_time_plotter_pg.py
-----------------------

GPU-accelerated real-time dashboard for an inverted-pendulum simulation,
implemented with PyQtGraph.  Public API matches the original Matplotlib
class:

    rtp = RealTimePlotter(buffer_size=1000, update_frequency=5)
    ...
    rtp.update_data(t, x_cur, x_des, angle_deg, force)
    ...
    rtp.close()
"""

from __future__ import annotations
import sys
from collections import deque
from typing import Deque

import numpy as np

# ----------------------------------------------------------------------
#  Qt binding: try PyQt6 first, fall back to PySide6
# ----------------------------------------------------------------------
try:
    from PyQt6 import QtWidgets, QtCore
except ModuleNotFoundError:
    from PySide6 import QtWidgets, QtCore          # type: ignore

import pyqtgraph as pg

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')  

class RealTimePlotter:
    """
    Real-time inverted-pendulum visualiser using PyQtGraph.

    Parameters
    ----------
    buffer_size : int
        Maximum number of samples kept in the sliding window.
    update_frequency : int
        Redraw the dashboard every N calls to `update_data`.
    """

    # ----------------------------- init --------------------------------
    def __init__(self, buffer_size: int = 1000, update_frequency: int = 5):
        self.buffer_size: int      = buffer_size
        self.update_frequency: int = update_frequency
        self._update_counter: int  = 0

        # --- fixed-size FIFO buffers -----------------------------------
        # NEW BUFFERS for line follower:
        self.t_buf:     Deque[float] = deque(maxlen=buffer_size)
        self.x_buf:     Deque[float] = deque(maxlen=buffer_size)      # robot x position
        self.y_buf:     Deque[float] = deque(maxlen=buffer_size)      # robot y position
        self.theta_buf: Deque[float] = deque(maxlen=buffer_size)      # robot heading
        self.ref_x_buf: Deque[float] = deque(maxlen=buffer_size)      # reference x
        self.ref_y_buf: Deque[float] = deque(maxlen=buffer_size)      # reference y
        self.error_buf: Deque[float] = deque(maxlen=buffer_size)      # cross-track error

        # --- Qt application --------------------------------------------
        self._app = (QtWidgets.QApplication.instance()
                     or QtWidgets.QApplication(sys.argv))
        pg.setConfigOptions(antialias=True)        # nicer lines

        # --- build 2 × 2 dashboard layout ------------------------------
        self.win = pg.GraphicsLayoutWidget(title="Real-Time Inverted Pendulum")
        self.win.resize(1200, 800)

        # 1) TRAJECTORY PLOT (X vs Y) 
        self.traj_plot = self.win.addPlot(title="Robot Trajectory")
        self.traj_plot.setLabel('bottom', 'X Position', units='m')
        self.traj_plot.setLabel('left', 'Y Position', units='m')
        self.traj_plot.setAspectLocked(True)
        self.traj_plot.showGrid(x=True, y=True, alpha=0.3)
        self.traj_plot.addLegend()

        # Path reference line
        self.path_line = self.traj_plot.plot(
            pen=pg.mkPen('g', width=2, style=QtCore.Qt.PenStyle.DashLine),
            name="Reference Path"
        )

        # Actual trajectory
        self.traj_line = self.traj_plot.plot(pen=pg.mkPen('b', width=2), name="Robot Path")

        # Robot position marker
        self.robot_marker = self.traj_plot.plot(
            pen=None, symbol='o', symbolBrush='r', symbolSize=10,
            name="Current Position"
        )

        # 2) ERROR PLOT (cross-track error)
        self.win.nextColumn()
        self.error_plot = self.win.addPlot(title="Cross-Track Error")
        self.error_plot.setLabel('bottom', 'Time', units='s')
        self.error_plot.setLabel('left', 'Error', units='m')
        self.error_plot.showGrid(x=True, y=True, alpha=0.3)
        self.error_plot.addLegend()
        self.error_curve = self.error_plot.plot(pen=pg.mkPen('r', width=2), name="Error")

        # Add 2% settling band (for KPI visualization)
        self.error_plot.addLine(y=0.02, pen=pg.mkPen('g', width=1, style=QtCore.Qt.PenStyle.DotLine))
        self.error_plot.addLine(y=-0.02, pen=pg.mkPen('g', width=1, style=QtCore.Qt.PenStyle.DotLine))

        # 3) HEADING PLOT
        self.win.nextRow()
        self.heading_plot = self.win.addPlot(title="Robot Heading")
        self.heading_plot.setLabel('bottom', 'Time', units='s')
        self.heading_plot.setLabel('left', 'Heading', units='rad')
        self.heading_plot.showGrid(x=True, y=True, alpha=0.3)
        self.heading_curve = self.heading_plot.plot(pen=pg.mkPen('b', width=2))

        # 4) KPI DISPLAY (replaces force plot)
        self.kpi_plot = self.win.addPlot(title="Key Performance Indicators")
        self.kpi_plot.hideAxis('bottom')
        self.kpi_plot.hideAxis('left')
        self.kpi_text = pg.TextItem("", anchor=(0,0))
        self.kpi_plot.addItem(self.kpi_text)

        # show non-blocking so the simulation keeps running
        self.win.show()
        self._app.processEvents()

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------
    def update_data(self,
                t: float,
                x: float,
                y: float,
                theta: float,
                ref_x: float,
                ref_y: float,
                error: float) -> None:
            """Push new data to the visualizer."""
            self.t_buf.append(t)
            self.x_buf.append(x)
            self.y_buf.append(y)
            self.theta_buf.append(theta)
            self.ref_x_buf.append(ref_x)
            self.ref_y_buf.append(ref_y)
            self.error_buf.append(error)
            
            # KPI tracking
            self._update_kpis()
            
            self._update_counter += 1
            if self._update_counter >= self.update_frequency:
                self._update_counter = 0
                self._redraw()

    def close(self) -> None:
        """Cleanly close the dashboard window."""
        self.win.close()

    # ------------------------------------------------------------------
    #  Internal helpers
    # ------------------------------------------------------------------
    def _deque_to_ndarray(self, dq: Deque[float]) -> np.ndarray:
        """Convert deque → NumPy array (fast enough for ~1 k points)."""
        # np.fromiter avoids the intermediate list
        return np.fromiter(dq, dtype=float, count=len(dq))

    def _redraw(self) -> None:
    """Update all plots with current data"""
    if len(self.t_buf) < 2:
        return
        
    # Convert to arrays
    t_arr = self._deque_to_ndarray(self.t_buf)
    x_arr = self._deque_to_ndarray(self.x_buf)
    y_arr = self._deque_to_ndarray(self.y_buf)
    theta_arr = self._deque_to_ndarray(self.theta_buf)
    ref_x_arr = self._deque_to_ndarray(self.ref_x_buf)
    ref_y_arr = self._deque_to_ndarray(self.ref_y_buf)
    error_arr = self._deque_to_ndarray(self.error_buf)
    
    # Update trajectory plot
    self.traj_line.setData(x_arr, y_arr)
    self.robot_marker.setData([x_arr[-1]], [y_arr[-1]])
    
    # Update reference path (show recent part)
    if len(ref_x_arr) > 100:
        self.path_line.setData(ref_x_arr[-100:], ref_y_arr[-100:])
    else:
        self.path_line.setData(ref_x_arr, ref_y_arr)
    
    # Update error plot
    self.error_curve.setData(t_arr, error_arr)
    
    # Update heading plot
    self.heading_curve.setData(t_arr, theta_arr)
    
    # Auto-range axes
    self.error_plot.autoRange()
    self.heading_plot.autoRange()
    
    # Auto-range trajectory with padding
    if len(x_arr) > 1:
        x_min, x_max = min(x_arr), max(x_arr)
        y_min, y_max = min(y_arr), max(y_arr)
        padding = 0.5
        self.traj_plot.setXRange(x_min - padding, x_max + padding)
        self.traj_plot.setYRange(y_min - padding, y_max + padding)
    
    self._app.processEvents()

def _update_kpis(self):
    """Calculate and update KPI display"""
    if len(self.error_buf) < 10:
        return
    
    # Max overshoot
    error_array = np.array(self.error_buf)
    max_error = np.max(np.abs(error_array))
    
    # Steady-state error (average of last 100 samples)
    if len(self.error_buf) > 100:
        steady_state = np.mean(np.abs(error_array[-100:]))
    else:
        steady_state = 0.0
    
    # Check for settling (error < 2cm for last 100 samples)
    settled = False
    settling_time = None
    if len(self.error_buf) > 100:
        recent = error_array[-100:]
        if np.max(np.abs(recent)) < 0.02:
            settled = True
            settling_time = self.t_buf[-1] if self.t_buf else 0
    
    # Update text display
    kpi_text = f"""KEY PERFORMANCE INDICATORS
{'='*30}

Current Values:
Time: {self.t_buf[-1]:.2f} s
Position: ({self.x_buf[-1]:.3f}, {self.y_buf[-1]:.3f}) m
Error: {self.error_buf[-1]:.4f} m

KPIs:
Max Overshoot: {max_error:.4f} m
Settling Time: {settling_time:.2f} s
Steady-State Error: {steady_state:.4f} m

Status: {'SETTLED' if settled else 'TRACKING'}"""
    
    self.kpi_text.setText(kpi_text)

def save_results(self, filename: str = None) -> None:
    """Save KPI results for your report"""
    import json
    import csv
    from datetime import datetime
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kpi_results_{timestamp}.json"
    
    # Calculate final KPIs
    error_array = np.array(self.error_buf)
    
    results = {
        'max_overshoot': float(np.max(np.abs(error_array))) if len(error_array) > 0 else 0,
        'steady_state_error': float(np.mean(np.abs(error_array[-100:]))) if len(error_array) > 100 else 0,
        'final_error': float(error_array[-1]) if len(error_array) > 0 else None,
        'samples': len(self.t_buf)
    }
    
    # Add settling time if found
    if len(error_array) > 100:
        for i in range(len(error_array) - 100):
            if np.max(np.abs(error_array[i:i+100])) < 0.02:
                results['settling_time'] = float(self.t_buf[i+100]) if i+100 < len(self.t_buf) else None
                break
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✅ Results saved to {filename}")
    
    # Also save raw data
    csv_filename = filename.replace('.json', '.csv')
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time', 'X', 'Y', 'Theta', 'Ref_X', 'Ref_Y', 'Error'])
        for i in range(len(self.t_buf)):
            writer.writerow([
                self.t_buf[i], self.x_buf[i], self.y_buf[i], 
                self.theta_buf[i], self.ref_x_buf[i], 
                self.ref_y_buf[i], self.error_buf[i]
            ])
    print(f"✅ Raw data saved to {csv_filename}")

# ----------------------------------------------------------------------
#  Example usage
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import math
    import time
    import random
    
    plotter = RealTimePlotter(buffer_size=2000, update_frequency=2)
    
    t = 0.0
    dt = 0.01
    
    try:
        while t < 30:
            # Simulate straight line path
            ref_x = 0.3 * t
            ref_y = 0.0
            
            # Simulate robot with error
            x = ref_x + 0.05 * math.sin(2 * t)
            y = 0.05 * math.sin(1.5 * t) + 0.01 * random.gauss(0, 1)
            theta = math.atan2(0.075 * math.cos(1.5 * t), 0.3)
            error = y - ref_y
            
            plotter.update_data(t, x, y, theta, ref_x, ref_y, error)
            
            t += dt
            time.sleep(dt)
            
    finally:
        plotter.save_results()
        plotter.close()