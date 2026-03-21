//---------------------------------------------------------------------------//
// Unpublished work. Copyright 2023 Siemens                                  //
//                                                                           //
// This material contains trade secrets or otherwise confidential            //
// information owned by Siemens Industry Software Inc. or its affiliates     //
// (collectively, "SISW"), or its licensors. Access to and use of this       //
// information is strictly limited as set forth in the Customer's applicable //
// agreements with SISW.                                                     //
//---------------------------------------------------------------------------//

#include "invPend.h"

static unsigned char srcMacAddress[XlEtherPacketSnooper::ETH_ADDR_NUM_BYTES] = {0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc};

static unsigned char srcIpAddress[XlEtherPacketSnooper::IPV4_ADDR_NUM_BYTES] = {192, 168, 1, 1};
static unsigned char controllerIpAddress[XlEtherPacketSnooper::IPV4_ADDR_NUM_BYTES] = {192, 168, 1, 2};

static unsigned InvPendSocketPortNumber0 = 8080;

#define Controller0 0

#define MAX_STRING_SIZE 100000
// Start of user custom code region. Please apply edits only within these regions:  Global Variables & Definitions


// End of user custom code region. Please don't edit beyond this point.

//----------------------------------------------------------------------------
// Method: ethernetRxFrameHandler
// This is a callback method which will be called upon receiving new packets.
// it casts the context to the InvPend object that will handle
// the incoming packet
//----------------------------------------------------------------------------
static void ethernetRxFrameHandler (unsigned char *payload, unsigned numBytes, unsigned short destPortNumber, unsigned short srcPortNumber, void *context)
{
	InvPend *me = reinterpret_cast<InvPend*>(context);
	return me->handleReceivedEtherPacket(payload, numBytes, destPortNumber, srcPortNumber);
}

//----------------------------------------------------------------------------
// Method: InvPend() constructor
//----------------------------------------------------------------------------
InvPend::InvPend (RawcTlmApiThreaded *session , string fmuPath, string tmpPath) 
	: dSession(session)
{
	// Start of user custom code region. Please apply edits only within these regions:  Constructor


	// End of user custom code region. Please don't edit beyond this point.

	ethGateway = new VsiTcpUdpGateway(dSession,
		/*txConduitId =*/   ":txEtherFrameConduit0",
		/*rxConduitId =*/   ":rxEtherFrameConduit0",
		/*myMacAddress=*/   srcMacAddress,
		/*myIpAddress=*/    srcIpAddress);
	clientPortNum = new unsigned short [1]{};
	ethGateway->registerRxCallback(this, ethernetRxFrameHandler);

	vsiFmiMaster = new VsiFmiMaster(fmuPath, tmpPath);
	mySignals = {};
	// Start of user custom code region. Please apply edits only within these regions:  Constructor End


	// End of user custom code region. Please don't edit beyond this point.
}

// ---------------------------------------------------------------------------
// Destructor 
// ---------------------------------------------------------------------------
InvPend::~InvPend() 
{
	delete vsiFmiMaster;
	delete ethGateway;
	delete [] clientPortNum;
	// Start of user custom code region. Please apply edits only within these regions:  Destructor


	// End of user custom code region. Please don't edit beyond this point.
}

//----------------------------------------------------------------------------
// Method:: mainThread()
// The main thread is called every simulation step (RTOS interrupt).
//----------------------------------------------------------------------------
void InvPend::mainThread()
{
	// Start of user custom code region. Please apply edits only within these regions:  Start of main thread


	// End of user custom code region. Please don't edit beyond this point.

	//Read available FMU inputs(s)
	vector<string> fmuInputs = vsiFmiMaster->getInputsNamesList();
	vector<string> fmuOutputs = vsiFmiMaster->getOutputsNamesList();

	//Setting the input FMU variable(s)
	if (std::find(fmuInputs.begin(), fmuInputs.end(), "amesim_interface.force") != fmuInputs.end())
		vsiFmiMaster->setFmuVariable("amesim_interface.force" , (double) mySignals.amesim_interface_1force);


	vsiFmiMaster->advanceSimulationStep(0.001);


	//Getting the output FMU variable(s)
	if (std::find(fmuOutputs.begin(), fmuOutputs.end(), "amesim_interface.x_desired") != fmuOutputs.end())
		mySignals.amesim_interface_1x_desired = (double) vsiFmiMaster->getFmuVariable<fmi2Real>("amesim_interface.x_desired");
	if (std::find(fmuOutputs.begin(), fmuOutputs.end(), "amesim_interface.x_current") != fmuOutputs.end())
		mySignals.amesim_interface_1x_current = (double) vsiFmiMaster->getFmuVariable<fmi2Real>("amesim_interface.x_current");
	if (std::find(fmuOutputs.begin(), fmuOutputs.end(), "amesim_interface.angle") != fmuOutputs.end())
		mySignals.amesim_interface_1angle = (double) vsiFmiMaster->getFmuVariable<fmi2Real>("amesim_interface.angle");
	// Start of user custom code region. Please apply edits only within these regions:  Before sending the packet


	// End of user custom code region. Please don't edit beyond this point.

	//------------------------------------------------------------------------
	//Output can be set by updating the output variables in the mySignals struct here
	//------------------------------------------------------------------------
	sendEthernetPacketToComponentController();

	cout<<"\n+=invPend+=";
	cout<<"\n  VSI time: " << convert.timeInNs() << " ns";

	cout<<"\n  Inputs:";
	cout << "\n\tamesim_interface_1force = " << (mySignals.amesim_interface_1force);

	cout<<"\n  Outputs:";
	cout << "\n\tamesim_interface_1x_desired = " << (mySignals.amesim_interface_1x_desired);
	cout << "\n\tamesim_interface_1x_current = " << (mySignals.amesim_interface_1x_current);
	cout << "\n\tamesim_interface_1angle = " << (mySignals.amesim_interface_1angle);
	cout<<"\n\n";
	// Start of user custom code region. Please apply edits only within these regions:  After sending the packet


	// End of user custom code region. Please don't edit beyond this point.

}

// ---------------------------------------------------------------------------
// Method:: handleReceivedEtherPacket
// This method does the actual handling of the received packets from other 
// clients.
//----------------------------------------------------------------------------
void InvPend::handleReceivedEtherPacket(unsigned char *payload, unsigned numBytes, unsigned short destPortNumber, unsigned short srcPortNumber)
{
	// Start of user custom code region. Please apply edits only within these regions:  Protocol's callback function


	// End of user custom code region. Please don't edit beyond this point.

	uint64_t numBytesToCopy;
	if(srcPortNumber == clientPortNum[Controller0])
	{
		// Received packet from controller

		memcpy((unsigned char*) &mySignals.amesim_interface_1force, payload, sizeof(mySignals.amesim_interface_1force));
		payload += sizeof(mySignals.amesim_interface_1force);
	}
}

//----------------------------------------------------------------------------
// Method: sendEthernetPacketToComponent
// This method sends an Ethernet packet to the specified component
//----------------------------------------------------------------------------
void InvPend::sendEthernetPacketToComponentController(){
	unsigned numBytes = 0;
	unsigned currentIndex = 0;

	numBytes += sizeof(mySignals.amesim_interface_1angle);

	unsigned char *payload = new unsigned char[numBytes];

	memcpy(payload + currentIndex, (unsigned char*) &mySignals.amesim_interface_1angle, sizeof(mySignals.amesim_interface_1angle));
	currentIndex += sizeof(mySignals.amesim_interface_1angle);


	// Send ethernet packet to Controller
	ethGateway->sendEthernetPacket(clientPortNum[Controller0], payload, numBytes);
}
//----------------------------------------------------------------------------
// Method: establishTcpUdpConnection
// This method is used to establish all the TCP/IP connections with
// the connected ports
//----------------------------------------------------------------------------
void InvPend::establishTcpUdpConnection()
{
	unsigned int attempts = 0;
	while(attempts < 3)
	{

		if(clientPortNum[Controller0] == 0)
		{
			clientPortNum[Controller0]= ethGateway->tcpListen(InvPendSocketPortNumber0);
		}
		attempts++;
	}
	if(clientPortNum[Controller0] == 0)
	{
		cerr << "Error: Failed to connect to port: InvPend on TCP port: "<< InvPendSocketPortNumber0 << endl;
		exit(EXIT_FAILURE);
	}
}

void InvPend::initializeFmu()
{
    vsiFmiMaster->initialize();
}

//----------------------------------------------------------------------------
// Method: terminate
// This method is used to terminate all the TCP/IP connections with
// the connected ports
//----------------------------------------------------------------------------
void InvPend::terminate()
{
	ethGateway->terminate();
}

//----------------------------------------------------------------------------
// Method: isTerminationOnGoing
// This method checks if a termination process already started
//----------------------------------------------------------------------------
bool InvPend::isTerminationOnGoing()
{
	return ethGateway->isTerminationOnGoing();
}
//----------------------------------------------------------------------------
// Method: isTerminated
// This method checks whether the TCP/IP ports have been already terminated
//----------------------------------------------------------------------------
bool InvPend::isTerminated()
{
	return ethGateway->isTerminated();
}
