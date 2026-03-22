#!/usr/bin/env python3
"""
Plotter Client – receives data from CAN, displays trajectory, error, heading,
and saves CSV/PNG/JSON results.
"""
from __future__ import print_function
import struct
import sys
import argparse
import math
import os
import time
import json
from collections import deque

import numpy as np
import matplotlib.pyplot as plt

try:
    from PyQt6 import QtWidgets, QtCore
except ModuleNotFoundError:
    from PySide6 import QtWidgets, QtCore

import pyqtgraph as pg

# Add pythonGateways path
script_dir = os.path.dirname(os.path.abspath(__file__))
python_gateways = os.path.join(script_dir, '..', '..', 'pythonGateways')
sys.path.insert(0, python_gateways)

import VsiCommonPythonApi as vsiCommonPythonApi
import VsiCanPythonGateway as vsiCanPythonGateway

# Create results directories
os.makedirs("results/json", exist_ok=True)
os.makedirs("results/Plots", exist_ok=True)

pg.setConfigOption('background', (20, 20, 20))
pg.setConfigOption('foreground', 'w')


class MySignals:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.ref_x = 0.0
        self.ref_y = 0.0
        self.error = 0.0
        self.v = 0.0
        self.omega = 0.0


class Plotter:
    def __init__(self, args):
        self.componentId = 2
        self.localHost = args.server_url
        self.domain = args.domain
        self.portNum = 50103

        self.simulationStep = 0
        self.stopRequested = False
        self.totalSimulationTime = 0

        self.mySignals = MySignals()

        # Data storage
        self.time_data = []
        self.x_data = []
        self.y_data = []
        self.theta_data = []
        self.ref_x_data = []
        self.ref_y_data = []
        self.error_data = []
        self.v_data = []
        self.omega_data = []

        # Output file base name from environment
        self.output_base = os.environ.get('PLOTTER_OUTPUT', 'experiment')
        self.save_flag = args.save

        # GUI setup
        self._app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        self.win = pg.GraphicsLayoutWidget(title="Line‑Following Robot – Real‑Time Dashboard")
        self.win.resize(1400, 900)

        # ---------- Plot 1: Trajectory (X vs Y) ----------
        self.traj_plot = self.win.addPlot(title="Robot Trajectory")
        self.traj_plot.setLabel('bottom', 'X Position', units='m')
        self.traj_plot.setLabel('left', 'Y Position', units='m')
        self.traj_plot.setAspectLocked(True)
        self.traj_plot.addLegend()
        self.traj_plot.showGrid(x=True, y=True, alpha=0.5)
        self.traj_plot.getAxis('bottom').enableAutoSIPrefix(False)
        self.traj_plot.getAxis('left').enableAutoSIPrefix(False)

        self.ref_path = self.traj_plot.plot(pen=pg.mkPen('r', width=2, style=QtCore.Qt.PenStyle.DashLine), name="Reference Path")
        self.rob_path = self.traj_plot.plot(pen=pg.mkPen('g', width=2), name="Actual Path")
        self.robot_now = self.traj_plot.plot(pen=None, symbol='o', symbolBrush='y', symbolSize=15, name="Current Robot")

        # ---------- Plot 2: Cross‑Track Error ----------
        self.win.nextColumn()
        self.error_plot = self.win.addPlot(title="Cross‑Track Error")
        self.error_plot.setLabel('bottom', 'Time', units='s')
        self.error_plot.setLabel('left', 'Error', units='m')
        self.error_plot.addLegend()
        self.error_plot.showGrid(x=True, y=True, alpha=0.5)
        self.error_curve = self.error_plot.plot(pen=pg.mkPen('c', width=2), name="Error")
        self.error_plot.addLine(y=0.02, pen=pg.mkPen('g', width=1, style=QtCore.Qt.PenStyle.DotLine))
        self.error_plot.addLine(y=-0.02, pen=pg.mkPen('g', width=1, style=QtCore.Qt.PenStyle.DotLine))

        # ---------- Plot 3: Heading ----------
        self.win.nextRow()
        self.heading_plot = self.win.addPlot(title="Robot Heading")
        self.heading_plot.setLabel('bottom', 'Time', units='s')
        self.heading_plot.setLabel('left', 'Heading', units='rad')
        self.heading_plot.showGrid(x=True, y=True, alpha=0.5)
        self.heading_curve = self.heading_plot.plot(pen=pg.mkPen('m', width=2))

        self.win.show()
        self._app.processEvents()

    def mainThread(self):
        dSession = vsiCommonPythonApi.connectToServer(self.localHost, self.domain, self.portNum, self.componentId)
        vsiCanPythonGateway.initialize(dSession, self.componentId)

        try:
            vsiCommonPythonApi.waitForReset()
            self.updateInternalVariables()

            while vsiCommonPythonApi.getSimulationTimeInNs() < self.totalSimulationTime:
                current_time_ns = vsiCommonPythonApi.getSimulationTimeInNs()
                current_time_s = current_time_ns * 1e-9

                # --- Receive CAN frames ---
                # x (ID 10)
                data = vsiCanPythonGateway.recvVariableFromCanPacket(8, 0, 64, 10)
                if data:
                    self.mySignals.x, _ = self.unpackBytes('d', data, self.mySignals.x)

                # y (ID 11)
                data = vsiCanPythonGateway.recvVariableFromCanPacket(8, 0, 64, 11)
                if data:
                    self.mySignals.y, _ = self.unpackBytes('d', data, self.mySignals.y)

                # theta (ID 12)
                data = vsiCanPythonGateway.recvVariableFromCanPacket(8, 0, 64, 12)
                if data:
                    self.mySignals.theta, _ = self.unpackBytes('d', data, self.mySignals.theta)

                # ref_x (ID 13)
                data = vsiCanPythonGateway.recvVariableFromCanPacket(8, 0, 64, 13)
                if data:
                    self.mySignals.ref_x, _ = self.unpackBytes('d', data, self.mySignals.ref_x)

                # ref_y (ID 14)
                data = vsiCanPythonGateway.recvVariableFromCanPacket(8, 0, 64, 14)
                if data:
                    self.mySignals.ref_y, _ = self.unpackBytes('d', data, self.mySignals.ref_y)

                # error (ID 15)
                data = vsiCanPythonGateway.recvVariableFromCanPacket(8, 0, 64, 15)
                if data:
                    self.mySignals.error, _ = self.unpackBytes('d', data, self.mySignals.error)

                # v (ID 16) – optional, for debugging
                data = vsiCanPythonGateway.recvVariableFromCanPacket(8, 0, 64, 16)
                if data:
                    self.mySignals.v, _ = self.unpackBytes('d', data, self.mySignals.v)

                # --- Store data (avoid initial zeros) ---
                if self.mySignals.x != 0 or self.mySignals.y != 0:
                    self.time_data.append(current_time_s)
                    self.x_data.append(self.mySignals.x)
                    self.y_data.append(self.mySignals.y)
                    self.theta_data.append(self.mySignals.theta)
                    self.ref_x_data.append(self.mySignals.ref_x)
                    self.ref_y_data.append(self.mySignals.ref_y)
                    self.error_data.append(self.mySignals.error)
                    self.v_data.append(self.mySignals.v)
                    self.omega_data.append(self.mySignals.omega)  # if omega is sent

                # --- Update plots every 10 new points ---
                if len(self.x_data) % 10 == 0 and len(self.x_data) > 0:
                    # Trajectory
                    self.ref_path.setData(self.ref_x_data, self.ref_y_data)
                    self.rob_path.setData(self.x_data, self.y_data)
                    self.robot_now.setData([self.mySignals.x], [self.mySignals.y])

                    # Error
                    self.error_curve.setData(self.time_data, self.error_data)

                    # Heading
                    self.heading_curve.setData(self.time_data, self.theta_data)

                    self._app.processEvents()

                # --- Print debug (optional) ---
                print("\n+=plotter+=")
                print("  VSI time:", current_time_ns, "ns")
                print("  Inputs:")
                print("\tx =", self.mySignals.x)
                print("\ty =", self.mySignals.y)
                print("\ttheta =", self.mySignals.theta)
                print("\tref_x =", self.mySignals.ref_x)
                print("\tref_y =", self.mySignals.ref_y)
                print("\terror =", self.mySignals.error)
                print("\n\n")

                # --- Advance simulation ---
                self.updateInternalVariables()
                if vsiCommonPythonApi.isStopRequested():
                    break

                next_time = current_time_ns + self.simulationStep
                if next_time > self.totalSimulationTime:
                    vsiCommonPythonApi.advanceSimulation(self.totalSimulationTime - current_time_ns)
                    break
                vsiCommonPythonApi.advanceSimulation(self.simulationStep)

        except Exception as e:
            if str(e) == "stopRequested":
                print("Terminate signal received")
            else:
                print(f"An error occurred: {str(e)}")
        finally:
            # Save data if requested
            if self.save_flag:
                self.save_results()
            self.win.close()
            vsiCommonPythonApi.advanceSimulation(self.simulationStep + 1)

    def save_results(self):
        """Save CSV, PNG plots, and JSON KPIs."""
        if not self.time_data:
            print("No data collected – nothing to save.")
            return

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        base = f"{self.output_base}_{timestamp}"

        # --- CSV ---
        csv_file = f"results/{base}.csv"
        with open(csv_file, 'w') as f:
            f.write("Time,X,Y,Theta,Ref_X,Ref_Y,Error,V,Omega\n")
            for i in range(len(self.time_data)):
                f.write(f"{self.time_data[i]},{self.x_data[i]},{self.y_data[i]},{self.theta_data[i]},"
                        f"{self.ref_x_data[i]},{self.ref_y_data[i]},{self.error_data[i]},"
                        f"{self.v_data[i]},{self.omega_data[i]}\n")
        print(f"CSV saved to {csv_file}")

        # --- PNG plots ---
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        axes[0,0].plot(self.x_data, self.y_data, 'b-', label='Robot')
        axes[0,0].plot(self.ref_x_data, self.ref_y_data, 'r--', label='Reference')
        axes[0,0].set_xlabel('X (m)'); axes[0,0].set_ylabel('Y (m)')
        axes[0,0].set_title('Trajectory'); axes[0,0].legend(); axes[0,0].grid(True)
        axes[0,0].axis('equal')

        axes[0,1].plot(self.time_data, self.error_data, 'r-')
        axes[0,1].axhline(0.02, color='g', linestyle='--')
        axes[0,1].axhline(-0.02, color='g', linestyle='--')
        axes[0,1].set_xlabel('Time (s)'); axes[0,1].set_ylabel('Error (m)')
        axes[0,1].set_title('Cross‑Track Error'); axes[0,1].grid(True)

        axes[1,0].plot(self.time_data, self.theta_data, 'b-')
        axes[1,0].set_xlabel('Time (s)'); axes[1,0].set_ylabel('Theta (rad)')
        axes[1,0].set_title('Heading'); axes[1,0].grid(True)

        axes[1,1].axis('off')
        max_error = np.max(np.abs(self.error_data)) if self.error_data else 0
        steady_error = np.mean(np.abs(self.error_data[-100:])) if len(self.error_data) > 100 else 0
        settling_time = self.compute_settling_time()
        axes[1,1].text(0.1, 0.5, f"Max Overshoot: {max_error:.4f} m\n"
                                 f"Steady-State Error: {steady_error:.4f} m\n"
                                 f"Settling Time: {settling_time:.2f} s", fontsize=12)
        axes[1,1].set_title('KPIs')

        plt.tight_layout()
        png_file = f"results/Plots/{base}.png"
        plt.savefig(png_file, dpi=150)
        plt.close()
        print(f"PNG saved to {png_file}")

        # --- JSON KPIs ---
        kpi = {
            "timestamp": timestamp,
            "max_overshoot": round(max_error, 4),
            "steady_state_error": round(steady_error, 4),
            "settling_time": round(settling_time, 4),
            "samples": len(self.time_data)
        }
        json_file = f"results/json/{base}.json"
        with open(json_file, 'w') as f:
            json.dump(kpi, f, indent=4)
        print(f"JSON saved to {json_file}")

    def compute_settling_time(self, tolerance=0.02):
        """Find time when error stays within tolerance for 100 consecutive samples."""
        if len(self.error_data) < 100:
            return 0.0
        for i in range(len(self.error_data)-100):
            if np.max(np.abs(self.error_data[i:i+100])) < tolerance:
                return self.time_data[i+100] if i+100 < len(self.time_data) else self.time_data[-1]
        return 0.0

    # ------------------------------------------------------------------
    # Utility methods (unchanged from generated code)
    # ------------------------------------------------------------------
    def packBytes(self, signalType, signal):
        if isinstance(signal, list):
            if signalType == 's':
                packedData = b''
                for s in signal:
                    s += '\0'
                    s = s.encode('utf-8')
                    packedData += struct.pack(f'={len(s)}s', s)
                return packedData
            else:
                return struct.pack(f'={len(signal)}{signalType}', *signal)
        else:
            if signalType == 's':
                signal += '\0'
                signal = signal.encode('utf-8')
                return struct.pack(f'={len(signal)}s', signal)
            else:
                return struct.pack(f'={signalType}', signal)

    def unpackBytes(self, signalType, packedBytes, signal=""):
        if isinstance(signal, list):
            if signalType == 's':
                unpackedStrings = [''] * len(signal)
                for i in range(len(signal)):
                    nullCharIndex = packedBytes.find(b'\0')
                    if nullCharIndex == -1:
                        break
                    unpackedString = struct.unpack(f'={nullCharIndex}s', packedBytes[:nullCharIndex])[0].decode('utf-8')
                    unpackedStrings[i] = unpackedString
                    packedBytes = packedBytes[nullCharIndex + 1:]
                return unpackedStrings, packedBytes
            else:
                unpacked = struct.unpack(f'={len(signal)}{signalType}', packedBytes[:len(signal)*struct.calcsize(f'={signalType}')])
                packedBytes = packedBytes[len(unpacked)*struct.calcsize(f'={signalType}'):]
                return list(unpacked), packedBytes
        elif signalType == 's':
            nullCharIndex = packedBytes.find(b'\0')
            unpacked = struct.unpack(f'={nullCharIndex}s', packedBytes[:nullCharIndex])[0].decode('utf-8')
            packedBytes = packedBytes[nullCharIndex + 1:]
            return unpacked, packedBytes
        else:
            numBytes = 0
            if signalType in ['?', 'b', 'B']:
                numBytes = 1
            elif signalType in ['h', 'H']:
                numBytes = 2
            elif signalType in ['f', 'i', 'I', 'L', 'l']:
                numBytes = 4
            elif signalType in ['q', 'Q', 'd']:
                numBytes = 8
            else:
                raise Exception('received an invalid signal type in unpackBytes()')
            unpacked = struct.unpack(f'={signalType}', packedBytes[:numBytes])[0]
            packedBytes = packedBytes[numBytes:]
            return unpacked, packedBytes

    def updateInternalVariables(self):
        self.totalSimulationTime = vsiCommonPythonApi.getTotalSimulationTime()
        self.stopRequested = vsiCommonPythonApi.isStopRequested()
        self.simulationStep = vsiCommonPythonApi.getSimulationStep()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--domain', default='AF_UNIX')
    parser.add_argument('--server-url', default='localhost')
    parser.add_argument('--save', action='store_true', help='Save CSV/PNG/JSON after simulation')
    args = parser.parse_args()

    plotter = Plotter(args)
    plotter.mainThread()


if __name__ == '__main__':
    main()