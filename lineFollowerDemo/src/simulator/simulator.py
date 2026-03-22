#!/usr/bin/env python3
from __future__ import print_function
import struct
import sys
import argparse
import math
import random
import os

PythonGateways = 'pythonGateways/'
sys.path.append(PythonGateways)

import VsiCommonPythonApi as vsiCommonPythonApi
import VsiCanPythonGateway as vsiCanPythonGateway


class MySignals:
    def __init__(self):
        # Inputs from controller
        self.v = 0.0
        self.omega = 0.0

        # Outputs to controller / plotter
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.ref_x = 0.0
        self.ref_y = 0.0


# ============================================================================
# User custom code region: Robot simulation, path generation, noise
# ============================================================================
class RobotSimulator:
    def __init__(self):
        # Robot state (random spawn)
        self.x = random.uniform(-0.2, 0.2)
        self.y = random.uniform(-0.1, 0.1)
        self.theta = random.uniform(-0.1, 0.1)

        # Reference path progress (time)
        self.t = 0.0

        # Read experiment parameters from environment
        self.path_type = int(os.environ.get('PATH_TYPE', '0'))   # 0=straight, 1=curved, 2=L-shape
        self.noise_level = float(os.environ.get('NOISE_LEVEL', '0.0'))   # 0.0 = no noise

        # Robot limits
        self.max_v = 0.5
        self.max_w = 2.0

        print(f"Simulator: path_type={self.path_type}, noise_level={self.noise_level}")

    def generate_reference(self, t):
        """Update reference path based on current time."""
        if self.path_type == 0:                     # straight line along x
            self.ref_x = 0.3 * t
            self.ref_y = 0.0
        elif self.path_type == 1:                   # curved (sine wave)
            self.ref_x = 0.3 * t
            self.ref_y = 0.5 * math.sin(0.5 * t)
        elif self.path_type == 2:                   # L‑shape
            if t < 10.0:
                self.ref_x = 0.3 * t
                self.ref_y = 0.0
            else:
                self.ref_x = 3.0
                self.ref_y = 0.3 * (t - 10.0)
        else:
            self.ref_x = 0.3 * t
            self.ref_y = 0.0

    def update_physics(self, dt):
        """Differential drive kinematics with optional noise."""
        # Apply noise to commands if enabled
        v_cmd = self.v
        w_cmd = self.omega
        if self.noise_level > 0:
            v_cmd += self.noise_level * (random.random() - 0.5) * 2 * self.max_v
            w_cmd += self.noise_level * (random.random() - 0.5) * 2 * self.max_w

        # Clamp velocities
        v_cmd = max(-self.max_v, min(v_cmd, self.max_v))
        w_cmd = max(-self.max_w, min(w_cmd, self.max_w))

        # Update pose
        if abs(w_cmd) < 1e-6:
            self.x += v_cmd * dt * math.cos(self.theta)
            self.y += v_cmd * dt * math.sin(self.theta)
        else:
            radius = v_cmd / w_cmd
            self.x += radius * (math.sin(self.theta + w_cmd * dt) - math.sin(self.theta))
            self.y += radius * (math.cos(self.theta) - math.cos(self.theta + w_cmd * dt))
            self.theta += w_cmd * dt

        # Normalise angle
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        # Update reference path based on current time
        self.generate_reference(self.t)

# End of user custom code region.
# ============================================================================


class Simulator:
    def __init__(self, args):
        self.componentId = 0
        self.localHost = args.server_url
        self.domain = args.domain
        self.portNum = 50101

        self.simulationStep = 0
        self.stopRequested = False
        self.totalSimulationTime = 0

        self.mySignals = MySignals()

        # Create robot simulator instance
        self.robot = RobotSimulator()

    def mainThread(self):
        dSession = vsiCommonPythonApi.connectToServer(self.localHost, self.domain, self.portNum, self.componentId)
        vsiCanPythonGateway.initialize(dSession, self.componentId)
        try:
            vsiCommonPythonApi.waitForReset()
            self.updateInternalVariables()

            if vsiCommonPythonApi.isStopRequested():
                raise Exception("stopRequested")

            nextExpectedTime = vsiCommonPythonApi.getSimulationTimeInNs()
            while vsiCommonPythonApi.getSimulationTimeInNs() < self.totalSimulationTime:
                current_time_ns = vsiCommonPythonApi.getSimulationTimeInNs()
                self.robot.t = current_time_ns * 1e-9   # seconds

                # --- Receive commands from controller (IDs 15 and 16) ---
                data = vsiCanPythonGateway.recvVariableFromCanPacket(8, 0, 64, 15)
                if data:
                    self.mySignals.v, _ = self.unpackBytes('d', data, self.mySignals.v)

                data = vsiCanPythonGateway.recvVariableFromCanPacket(8, 0, 64, 16)
                if data:
                    self.mySignals.omega, _ = self.unpackBytes('d', data, self.mySignals.omega)

                # Store commands in robot
                self.robot.v = self.mySignals.v
                self.robot.omega = self.mySignals.omega

                # --- Update robot physics ---
                dt = self.simulationStep * 1e-9
                self.robot.update_physics(dt)

                # --- Update output signals ---
                self.mySignals.x = self.robot.x
                self.mySignals.y = self.robot.y
                self.mySignals.theta = self.robot.theta
                self.mySignals.ref_x = self.robot.ref_x
                self.mySignals.ref_y = self.robot.ref_y

                # --- Send robot state and reference path (IDs 10-14) ---
                vsiCanPythonGateway.setCanId(10)
                vsiCanPythonGateway.setCanPayloadBits(self.packBytes('d', self.mySignals.x), 0, 64)
                vsiCanPythonGateway.setDataLengthInBits(64)
                vsiCanPythonGateway.sendCanPacket()

                vsiCanPythonGateway.setCanId(11)
                vsiCanPythonGateway.setCanPayloadBits(self.packBytes('d', self.mySignals.y), 0, 64)
                vsiCanPythonGateway.sendCanPacket()

                vsiCanPythonGateway.setCanId(12)
                vsiCanPythonGateway.setCanPayloadBits(self.packBytes('d', self.mySignals.theta), 0, 64)
                vsiCanPythonGateway.sendCanPacket()

                vsiCanPythonGateway.setCanId(13)
                vsiCanPythonGateway.setCanPayloadBits(self.packBytes('d', self.mySignals.ref_x), 0, 64)
                vsiCanPythonGateway.sendCanPacket()

                vsiCanPythonGateway.setCanId(14)
                vsiCanPythonGateway.setCanPayloadBits(self.packBytes('d', self.mySignals.ref_y), 0, 64)
                vsiCanPythonGateway.sendCanPacket()

                # --- Print for debugging ---
                print("\n+=simulator+=")
                print("  VSI time:", current_time_ns, "ns")
                print("  Inputs:")
                print("\tv =", self.mySignals.v)
                print("\tomega =", self.mySignals.omega)
                print("  Outputs:")
                print("\tx =", self.mySignals.x)
                print("\ty =", self.mySignals.y)
                print("\ttheta =", self.mySignals.theta)
                print("\tref_x =", self.mySignals.ref_x)
                print("\tref_y =", self.mySignals.ref_y)
                print("\n\n")

                # --- Advance simulation ---
                self.updateInternalVariables()
                if vsiCommonPythonApi.isStopRequested():
                    break

                nextExpectedTime += self.simulationStep
                if vsiCommonPythonApi.getSimulationTimeInNs() >= nextExpectedTime:
                    continue

                if nextExpectedTime > self.totalSimulationTime:
                    remaining = self.totalSimulationTime - vsiCommonPythonApi.getSimulationTimeInNs()
                    vsiCommonPythonApi.advanceSimulation(remaining)
                    break

                vsiCommonPythonApi.advanceSimulation(nextExpectedTime - vsiCommonPythonApi.getSimulationTimeInNs())

        except Exception as e:
            if str(e) == "stopRequested":
                print("Terminate signal received")
            else:
                print(f"An error occurred: {str(e)}")
        finally:
            vsiCommonPythonApi.advanceSimulation(self.simulationStep + 1)

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
    args = parser.parse_args()

    sim = Simulator(args)
    sim.mainThread()


if __name__ == '__main__':
    main()