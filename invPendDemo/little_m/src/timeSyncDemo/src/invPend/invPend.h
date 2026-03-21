//---------------------------------------------------------------------------//
// Unpublished work. Copyright 2023 Siemens                                  //
//                                                                           //
// This material contains trade secrets or otherwise confidential            //
// information owned by Siemens Industry Software Inc. or its affiliates     //
// (collectively, "SISW"), or its licensors. Access to and use of this       //
// information is strictly limited as set forth in the Customer's applicable //
// agreements with SISW.                                                     //
//---------------------------------------------------------------------------//


#ifndef _invPend_h
#define _invPend_h
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
	double amesim_interface_1x_desired;
	double amesim_interface_1x_current;
	double amesim_interface_1angle;
	double amesim_interface_1force;
};

#pragma pack(pop)
// Start of user custom code region. Please apply edits only within these regions:  Global Variables & Definitions


// End of user custom code region. Please don't edit beyond this point.

// ---------------------------------------------------------------------------
// Class InvPend
// ---------------------------------------------------------------------------
class InvPend  
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
		InvPend(RawcTlmApiThreaded *session , string fmuPath, string tmpPath);
		~InvPend();
		void mainThread ();
		void establishTcpUdpConnection();
		void handleReceivedEtherPacket(unsigned char *payload, unsigned numBytes, unsigned short destPortNumber, unsigned short srcPortNumber);
		void terminate();
		bool isTerminationOnGoing();
		bool isTerminated();
		void sendEthernetPacketToComponentController();
		void initializeFmu();

};
#endif