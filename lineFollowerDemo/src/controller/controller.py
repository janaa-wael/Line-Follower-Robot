#!/usr/bin/env python3
from __future__ import print_function
import struct
import sys
import argparse
import math
import os

PythonGateways = 'pythonGateways/'
sys.path.append(PythonGateways)

import VsiCommonPythonApi as vsiCommonPythonApi
import VsiCanPythonGateway as vsiCanPythonGateway


class MySignals:
    def __init__(self):
        # Inputs
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.ref_x = 0.0
        self.ref_y = 0.0

        # Outputs
        self.v = 0.3           # constant forward speed
        self.omega = 0.0


# ============================================================================
# PID Controller with environment-variable gains
# ============================================================================
class PIDController:
    def __init__(self):
        # Read gains from environment
        self.Kp_lateral = float(os.environ.get('KP_LATERAL', 2.0))
        self.Ki_lateral = float(os.environ.get('KI_LATERAL', 0.15))
        self.Kd_lateral = float(os.environ.get('KD_LATERAL', 0.3))
        self.Kp_heading = float(os.environ.get('KP_HEADING', 1.5))

        print(f"PID Gains: Kp_lat={self.Kp_lateral}, Ki_lat={self.Ki_lateral}, "
              f"Kd_lat={self.Kd_lateral}, Kp_head={self.Kp_heading}")

        self.integral = 0.0
        self.prev_error = 0.0
        self.integral_limit = 1.0
        self.output_limit = 2.0

    def compute(self, error, heading_error, dt):
        self.integral += error * dt
        if self.integral > self.integral_limit:
            self.integral = self.integral_limit
        elif self.integral < -self.integral_limit:
            self.integral = -self.integral_limit

        derivative = (error - self.prev_error) / dt if dt > 0 else 0.0
        lateral = (self.Kp_lateral * error +
                   self.Ki_lateral * self.integral +
                   self.Kd_lateral * derivative)
        heading_corr = self.Kp_heading * heading_error
        omega = lateral + heading_corr
        if omega > self.output_limit:
            omega = self.output_limit
        elif omega < -self.output_limit:
            omega = -self.output_limit

        self.prev_error = error
        return omega


pid = PIDController()


class Controller:
    def __init__(self, args):
        self.componentId = 1
        self.localHost = args.server_url
        self.domain = args.domain
        self.portNum = 50102

        self.simulationStep = 0
        self.stopRequested = False
        self.totalSimulationTime = 0

        self.mySignals = MySignals()

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

                # --- Receive frames (IDs 10,11,12,13,14) ---
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

                # --- PID computation (using environment gains) ---
                dt = self.simulationStep * 1e-9

                # Lateral error = y - ref_y (simple approach)
                error = self.mySignals.y - self.mySignals.ref_y

                # Desired heading (angle to reference point)
                dx = self.mySignals.ref_x - self.mySignals.x
                dy = self.mySignals.ref_y - self.mySignals.y
                desired_theta = math.atan2(dy, dx)

                # Heading error (wrap to [-pi, pi])
                heading_error = desired_theta - self.mySignals.theta
                heading_error = math.atan2(math.sin(heading_error), math.cos(heading_error))

                # Compute omega
                self.mySignals.omega = pid.compute(error, heading_error, dt)

                # Constant forward speed
                self.mySignals.v = 0.3

                # --- Send commands (IDs 15 and 16) ---
                vsiCanPythonGateway.setCanId(15)
                vsiCanPythonGateway.setCanPayloadBits(self.packBytes('d', self.mySignals.v), 0, 64)
                vsiCanPythonGateway.setDataLengthInBits(64)
                vsiCanPythonGateway.sendCanPacket()

                vsiCanPythonGateway.setCanId(16)
                vsiCanPythonGateway.setCanPayloadBits(self.packBytes('d', self.mySignals.omega), 0, 64)
                vsiCanPythonGateway.sendCanPacket()

                # --- Print for debugging ---
                print("\n+=controller+=")
                print("  VSI time:", vsiCommonPythonApi.getSimulationTimeInNs(), "ns")
                print("  Inputs:")
                print("\tx =", self.mySignals.x)
                print("\ty =", self.mySignals.y)
                print("\ttheta =", self.mySignals.theta)
                print("\tref_x =", self.mySignals.ref_x)
                print("\tref_y =", self.mySignals.ref_y)
                print("  Outputs:")
                print("\tv =", self.mySignals.v)
                print("\tomega =", self.mySignals.omega)
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
    # Utility methods (unchanged)
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

    ctrl = Controller(args)
    ctrl.mainThread()


if __name__ == '__main__':
    main()