//---------------------------------------------------------------------------//
// Unpublished work. Copyright 2023 Siemens                                  //
//                                                                           //
// This material contains trade secrets or otherwise confidential            //
// information owned by Siemens Industry Software Inc. or its affiliates     //
// (collectively, "SISW"), or its licensors. Access to and use of this       //
// information is strictly limited as set forth in the Customer's applicable //
// agreements with SISW.                                                     //
//---------------------------------------------------------------------------//


#ifndef _controller_h
#define _controller_h
#include "VsiTcpUdpGateway.h"
#include "VsiPortConfigGateway.h"
#include "VsiFmiMaster.h"
#include <cstdio>
#include <algorithm> // For std::find
#include <cstddef>   // For std::size_t
#include <cstring>
#include <cmath>

#pragma pack(push, 1)

struct MySignals {
	double theta;
	double force;
};

#pragma pack(pop)
// Start of user custom code region. Please apply edits only within these regions:  Global Variables & Definitions


// End of user custom code region. Please don't edit beyond this point.

// ---------------------------------------------------------------------------
// Class Controller
// ---------------------------------------------------------------------------
class Controller  
{
	private:
		RawcTlmApiThreaded * dSession;
		VsiFmiMaster * vsiFmiMaster;

		MySignals mySignals;

		unsigned short * clientPortNum;
		// Start of user custom code region. Please apply edits only within these regions:  Private class members


		// End of user custom code region. Please don't edit beyond this point.

	public:
		VsiTcpUdpGateway * ethGateway;
		// Start of user custom code region. Please apply edits only within these regions:  Public class members


		// End of user custom code region. Please don't edit beyond this point.
		Controller(RawcTlmApiThreaded *session , string fmuPath, string tmpPath);
		~Controller();
		void mainThread ();
		void establishTcpUdpConnection();
		void handleReceivedEtherPacket(unsigned char *payload, unsigned numBytes, unsigned short destPortNumber, unsigned short srcPortNumber);
		void terminate();
		bool isTerminationOnGoing();
		bool isTerminated();
		void sendEthernetPacketToComponentInvPend();
		void sendEthernetPacketToComponentPlotter();
		void initializeFmu();

};
#endif