#!/usr/bin/env python3
from __future__ import print_function
import struct
import sys
import argparse
import math
import sys
import os
current_dir = os.getcwd()
sys.path.append(current_dir)
from realTimePlotter import RealTimePlotter
PythonGateways = 'pythonGateways/'
sys.path.append(PythonGateways)

import VsiCommonPythonApi as vsiCommonPythonApi
import VsiTcpUdpPythonGateway as vsiEthernetPythonGateway


class MySignals:
	def __init__(self):
		# Inputs
		self.force = 0



srcMacAddress = [0x12, 0x34, 0x56, 0x78, 0x9a, 0xbe]
controllerMacAddress = [0x12, 0x34, 0x56, 0x78, 0x9a, 0xbd]
srcIpAddress = [192, 168, 1, 3]
controllerIpAddress = [192, 168, 1, 2]

ControllerSocketPortNumber0 = 8081

Plotter0 = 0


# Start of user custom code region. Please apply edits only within these regions:  Global Variables & Definitions

# End of user custom code region. Please don't edit beyond this point.
class Plotter:

	def __init__(self, args):
		self.componentId = 2
		self.localHost = args.server_url
		self.domain = args.domain
		self.portNum = 50103
        self.plotter = RealTimePlotter( update_frequency = 1) 
		self.simulationStep = 0
		self.stopRequested = False
		self.totalSimulationTime = 0
        
		self.receivedNumberOfBytes = 0
		self.receivedPayload = []

		self.numberOfPorts = 1
		self.clientPortNum = [0] * self.numberOfPorts
		self.receivedDestPortNumber = 0
		self.receivedSrcPortNumber = 0
		self.expectedNumberOfBytes = 0
		self.mySignals = MySignals()

		# Start of user custom code region. Please apply edits only within these regions:  Constructor

		# End of user custom code region. Please don't edit beyond this point.



	def mainThread(self):
		dSession = vsiCommonPythonApi.connectToServer(self.localHost, self.domain, self.portNum, self.componentId)
		vsiEthernetPythonGateway.initialize(dSession, self.componentId, bytes(srcMacAddress), bytes(srcIpAddress))
		try:
			vsiCommonPythonApi.waitForReset()

			# Start of user custom code region. Please apply edits only within these regions:  After Reset

			# End of user custom code region. Please don't edit beyond this point.
			self.updateInternalVariables()

			if(vsiCommonPythonApi.isStopRequested()):
				raise Exception("stopRequested")
			self.establishTcpUdpConnection()
			nextExpectedTime = vsiCommonPythonApi.getSimulationTimeInNs()
			while(vsiCommonPythonApi.getSimulationTimeInNs() < self.totalSimulationTime):

				# Start of user custom code region. Please apply edits only within these regions:  Inside the while loop
					9:58 pm
9:58 pm
155
9:54 pm
1
9:54 pm
1
9:28 pm
1
8:41 pm
7:55 pm
5
7:31 pm
126
7:27 pm
16
6:49 pm
2
4:57 pm
4:50 pm
2:59 pm
1
1:35 pm
8:27 am
3:50 am
1
Yesterday
2
Yesterday
Yesterday
Yesterday
3
Yesterday
228
Yesterday
1
Yesterday
Yesterday
Yesterday
Yesterday
1
Yesterday
10
Yesterday
Yesterday
Yesterday
Friday
Friday
Friday
Friday
13
Friday
2
Friday
4
Friday
Friday
1
Friday
1
Thursday
22
Thursday
2
Thursday
Thursday
15
Thursday
5
Thursday
2
Thursday
1
Thursday
2
Thursday
1
Thursday
Wednesday
Wednesday
Wednesday
4
Wednesday
Wednesday
6
Tuesday
Tuesday
Tuesday
Monday
57
Monday
08/03/2026
07/03/2026
04/03/2026
6
04/03/2026
1
04/03/2026
03/03/2026
03/03/2026
02/03/2026
Today
Lw ba3d elfetar 2oly
4:36 pm
Eb3atyly link tyb
4:36 pm
Bet3mly eh
4:36 pm
Ba3ml haga mama talbaha bs khalst
4:36 pm
You
Ba3ml haga mama talbaha bs khalst
Lw 3ayza ba3d elfetar mashy
4:37 pm
Ana ay haga walahi shofy eh el ahsn
4:37 pm
3ayza akhals 3a4an abda2 fe el gp
4:37 pm
Ehna sa3a w han2fl
4:37 pm

0:03

4:38 pm

0:12

5:57 pm
Ha
6:25 pm
Mashy ah
6:47 pm

0:04

7:37 pm
meet.google.com/mdh-ehta-wkb 
Or dial: (US) +1 470-765-8619 
PIN: 425 101 713#
7:59 pm
1 unread message
self.plotter.update_data(vsiCommonPythonApi.getSimulationTimeInNs() * 1e-9, self.mySignals.x_current,self.mySignals.x_desired, self.mySignals.angle, self.mySignals.force)
				# End of user custom code region. Please don't edit beyond this point.

				self.updateInternalVariables()

				if(vsiCommonPythonApi.isStopRequested()):
					raise Exception("stopRequested")

				if(vsiEthernetPythonGateway.isTerminationOnGoing()):
					print("Termination is on going")
					break

				if(vsiEthernetPythonGateway.isTerminated()):
					print("Application terminated")
					break

				receivedData = vsiEthernetPythonGateway.recvEthernetPacket(ControllerSocketPortNumber0)
				if(receivedData[3] != 0):
					self.decapsulateReceivedData(receivedData)

				# Start of user custom code region. Please apply edits only within these regions:  Before sending the packet

				# End of user custom code region. Please don't edit beyond this point.

				# Start of user custom code region. Please apply edits only within these regions:  After sending the packet

				# End of user custom code region. Please don't edit beyond this point.

				print("\n+=plotter+=")
				print("  VSI time:", end = " ")
				print(vsiCommonPythonApi.getSimulationTimeInNs(), end = " ")
				print("ns")
				print("  Inputs:")
				print("\tforce =", end = " ")
				print(self.mySignals.force)
				print("\n\n")

				self.updateInternalVariables()

				if(vsiCommonPythonApi.isStopRequested()):
					raise Exception("stopRequested")
				nextExpectedTime += self.simulationStep

				if(vsiCommonPythonApi.getSimulationTimeInNs() >= nextExpectedTime):
					continue

				if(nextExpectedTime > self.totalSimulationTime):
					remainingTime = self.totalSimulationTime - vsiCommonPythonApi.getSimulationTimeInNs()
					vsiCommonPythonApi.advanceSimulation(remainingTime)
					break

				vsiCommonPythonApi.advanceSimulation(nextExpectedTime - vsiCommonPythonApi.getSimulationTimeInNs())

			if(vsiCommonPythonApi.getSimulationTimeInNs() < self.totalSimulationTime):
				vsiEthernetPythonGateway.terminate()
		except Exception as e:
			if str(e) == "stopRequested":
				print("Terminate signal has been received from one of the VSI clients")
				# Advance time with a step that is equal to "simulationStep + 1" so that all other clients
				# receive the terminate packet before terminating this client
				vsiCommonPythonApi.advanceSimulation(self.simulationStep + 1)
			else:
				print(f"An error occurred: {str(e)}")
		except:
			# Advance time with a step that is equal to "simulationStep + 1" so that all other clients
			# receive the terminate packet before terminating this client
			vsiCommonPythonApi.advanceSimulation(self.simulationStep + 1)



	def establishTcpUdpConnection(self):
		if(self.clientPortNum[Plotter0] == 0):
			self.clientPortNum[Plotter0] = vsiEthernetPythonGateway.tcpConnect(bytes(controllerIpAddress), ControllerSocketPortNumber0)

		if(self.clientPortNum[Plotter0] == 0):
			print("Error: Failed to connect to port: Controller on TCP port: ") 
			print(ControllerSocketPortNumber0)
			exit()



	def decapsulateReceivedData(self, receivedData):
		self.receivedDestPortNumber = receivedData[0]
		self.receivedSrcPortNumber = receivedData[1]
		self.receivedNumberOfBytes = receivedData[3]
		self.receivedPayload = [0] * (self.receivedNumberOfBytes)

		for i in range(self.receivedNumberOfBytes):
			self.receivedPayload[i] = receivedData[2][i]

		if(self.receivedSrcPortNumber == ControllerSocketPortNumber0):
			print("Received packet from controller")
			receivedPayload = bytes(self.receivedPayload)
			self.mySignals.force, receivedPayload = self.unpackBytes('d', receivedPayload)


		# Start of user custom code region. Please apply edits only within these regions:  Protocol's callback function

		# End of user custom code region. Please don't edit beyond this point.



	def packBytes(self, signalType, signal):
		if isinstance(signal, list):
			if signalType == 's':
				packedData = b''
				for str in signal:
					str += '\0'
					str = str.encode('utf-8')
					packedData += struct.pack(f'={len(str)}s', str)
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



	def unpackBytes(self, signalType, packedBytes, signal = ""):
		if isinstance(signal, list):
			if signalType == 's':
				unpackedStrings = [''] * len(signal)
				for i in range(len(signal)):
					nullCharacterIndex = packedBytes.find(b'\0')
					if nullCharacterIndex == -1:
						break
					unpackedString = struct.unpack(f'={nullCharacterIndex}s', packedBytes[:nullCharacterIndex])[0].decode('utf-8')
					unpackedStrings[i] = unpackedString
					packedBytes = packedBytes[nullCharacterIndex + 1:]
				return unpackedStrings, packedBytes
			else:
				unpackedVariable = struct.unpack(f'={len(signal)}{signalType}', packedBytes[:len(signal)*struct.calcsize(f'={signalType}')])
				packedBytes = packedBytes[len(unpackedVariable)*struct.calcsize(f'={signalType}'):]
				return list(unpackedVariable), packedBytes
		elif signalType == 's':
			nullCharacterIndex = packedBytes.find(b'\0')
			unpackedVariable = struct.unpack(f'={nullCharacterIndex}s', packedBytes[:nullCharacterIndex])[0].decode('utf-8')
			packedBytes = packedBytes[nullCharacterIndex + 1:]
			return unpackedVariable, packedBytes
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
			unpackedVariable = struct.unpack(f'={signalType}', packedBytes[0:numBytes])[0]
			packedBytes = packedBytes[numBytes:]
			return unpackedVariable, packedBytes

	def updateInternalVariables(self):
		self.totalSimulationTime = vsiCommonPythonApi.getTotalSimulationTime()
		self.stopRequested = vsiCommonPythonApi.isStopRequested()
		self.simulationStep = vsiCommonPythonApi.getSimulationStep()



def main():
	inputArgs = argparse.ArgumentParser(" ")
	inputArgs.add_argument('--domain', metavar='D', default='AF_UNIX', help='Socket domain for connection with the VSI TLM fabric server')
	inputArgs.add_argument('--server-url', metavar='CO', default='localhost', help='server URL of the VSI TLM Fabric Server')

	# Start of user custom code region. Please apply edits only within these regions:  Main method

	# End of user custom code region. Please don't edit beyond this point.

	args = inputArgs.parse_args()
                      
	plotter = Plotter(args)
	plotter.mainThread()



if __name__ == '__main__':
    main()
