//---------------------------------------------------------------------------//
// Unpublished work. Copyright 2023 Siemens                                  //
//                                                                           //
// This material contains trade secrets or otherwise confidential            //
// information owned by Siemens Industry Software Inc. or its affiliates     //
// (collectively, "SISW"), or its licensors. Access to and use of this       //
// information is strictly limited as set forth in the Customer's applicable //
// agreements with SISW.                                                     //
//---------------------------------------------------------------------------//

#include "controller.h"

static unsigned char srcMacAddress[XlEtherPacketSnooper::ETH_ADDR_NUM_BYTES] = {0x12, 0x34, 0x56, 0x78, 0x9a, 0xbd};

static unsigned char srcIpAddress[XlEtherPacketSnooper::IPV4_ADDR_NUM_BYTES] = {192, 168, 1, 2};
static unsigned char invPendIpAddress[XlEtherPacketSnooper::IPV4_ADDR_NUM_BYTES] = {192, 168, 1, 1};
static unsigned char plotterIpAddress[XlEtherPacketSnooper::IPV4_ADDR_NUM_BYTES] = {192, 168, 1, 3};

static unsigned InvPendSocketPortNumber0 = 8080;
static unsigned ControllerSocketPortNumber1 = 8081;

#define Controller0 0
#define Plotter1 1

#define MAX_STRING_SIZE 100000
// Start of user custom code region. Please apply edits only within these regions:  Global Variables & Definitions


// End of user custom code region. Please don't edit beyond this point.

//----------------------------------------------------------------------------
// Method: ethernetRxFrameHandler
// This is a callback method which will be called upon receiving new packets.
// it casts the context to the Controller object that will handle
// the incoming packet
//----------------------------------------------------------------------------
static void ethernetRxFrameHandler (unsigned char *payload, unsigned numBytes, unsigned short destPortNumber, unsigned short srcPortNumber, void *context)
{
	Controller *me = reinterpret_cast<Controller*>(context);
	return me->handleReceivedEtherPacket(payload, numBytes, destPortNumber, srcPortNumber);
}

//----------------------------------------------------------------------------
// Method: Controller() constructor
//----------------------------------------------------------------------------
Controller::Controller (RawcTlmApiThreaded *session , string fmuPath, string tmpPath) 
	: dSession(session)
{
	// Start of user custom code region. Please apply edits only within these regions:  Constructor


	// End of user custom code region. Please don't edit beyond this point.

	ethGateway = new VsiTcpUdpGateway(dSession,
		/*txConduitId =*/   ":txEtherFrameConduit1",
		/*rxConduitId =*/   ":rxEtherFrameConduit1",
		/*myMacAddress=*/   srcMacAddress,
		/*myIpAddress=*/    srcIpAddress);
	clientPortNum = new unsigned short [2]{};
	ethGateway->registerRxCallback(this, ethernetRxFrameHandler);

	vsiFmiMaster = new VsiFmiMaster(fmuPath, tmpPath);
	mySignals = {};
	// Start of user custom code region. Please apply edits only within these regions:  Constructor End


	// End of user custom code region. Please don't edit beyond this point.
}

// ---------------------------------------------------------------------------
// Destructor 
// ---------------------------------------------------------------------------
Controller::~Controller() 
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
void Controller::mainThread()
{
	// Start of user custom code region. Please apply edits only within these regions:  Start of main thread


	// End of user custom code region. Please don't edit beyond this point.

	//Read available FMU inputs(s)
	vector<string> fmuInputs = vsiFmiMaster->getInputsNamesList();
	vector<string> fmuOutputs = vsiFmiMaster->getOutputsNamesList();

	//Setting the input FMU variable(s)
	if (std::find(fmuInputs.begin(), fmuInputs.end(), "theta") != fmuInputs.end())
		vsiFmiMaster->setFmuVariable("theta" , (double) mySignals.theta);


	vsiFmiMaster->advanceSimulationStep(0.01);


	//Getting the output FMU variable(s)
	if (std::find(fmuOutputs.begin(), fmuOutputs.end(), "force") != fmuOutputs.end())
		mySignals.force = (double) vsiFmiMaster->getFmuVariable<fmi2Real>("force");
	// Start of user custom code region. Please apply edits only within these regions:  Before sending the packet


	// End of user custom code region. Please don't edit beyond this point.

	//------------------------------------------------------------------------
	//Output can be set by updating the output variables in the mySignals struct here
	//------------------------------------------------------------------------
	sendEthernetPacketToComponentInvPend();
	sendEthernetPacketToComponentPlotter();

	cout<<"\n+=controller+=";
	cout<<"\n  VSI time: " << convert.timeInNs() << " ns";

	cout<<"\n  Inputs:";
	cout << "\n\ttheta = " << (mySignals.theta);

	cout<<"\n  Outputs:";
	cout << "\n\tforce = " << (mySignals.force);
	cout<<"\n\n";
	// Start of user custom code region. Please apply edits only within these regions:  After sending the packet


	// End of user custom code region. Please don't edit beyond this point.

}

// ---------------------------------------------------------------------------
// Method:: handleReceivedEtherPacket
// This method does the actual handling of the received packets from other 
// clients.
//----------------------------------------------------------------------------
void Controller::handleReceivedEtherPacket(unsigned char *payload, unsigned numBytes, unsigned short destPortNumber, unsigned short srcPortNumber)
{
	// Start of user custom code region. Please apply edits only within these regions:  Protocol's callback function


	// End of user custom code region. Please don't edit beyond this point.

	uint64_t numBytesToCopy;
	if(srcPortNumber == InvPendSocketPortNumber0)
	{
		// Received packet from invPend

		memcpy((unsigned char*) &mySignals.theta, payload, sizeof(mySignals.theta));
		payload += sizeof(mySignals.theta);
	}
}

//----------------------------------------------------------------------------
// Method: sendEthernetPacketToComponent
// This method sends an Ethernet packet to the specified component
//----------------------------------------------------------------------------
void Controller::sendEthernetPacketToComponentInvPend(){
	unsigned numBytes = 0;
	unsigned currentIndex = 0;

	numBytes += sizeof(mySignals.force);

	unsigned char *payload = new unsigned char[numBytes];

	memcpy(payload + currentIndex, (unsigned char*) &mySignals.force, sizeof(mySignals.force));
	currentIndex += sizeof(mySignals.force);


	// Send ethernet packet to InvPend
	ethGateway->sendEthernetPacket(InvPendSocketPortNumber0, payload, numBytes);
}
//----------------------------------------------------------------------------
// Method: sendEthernetPacketToComponent
// This method sends an Ethernet packet to the specified component
//----------------------------------------------------------------------------
void Controller::sendEthernetPacketToComponentPlotter(){
	unsigned numBytes = 0;
	unsigned currentIndex = 0;

	numBytes += sizeof(mySignals.force);

	unsigned char *payload = new unsigned char[numBytes];

	memcpy(payload + currentIndex, (unsigned char*) &mySignals.force, sizeof(mySignals.force));
	currentIndex += sizeof(mySignals.force);


	// Send ethernet packet to Plotter
	ethGateway->sendEthernetPacket(clientPortNum[Plotter1], payload, numBytes);
}
//----------------------------------------------------------------------------
// Method: establishTcpUdpConnection
// This method is used to establish all the TCP/IP connections with
// the connected ports
//----------------------------------------------------------------------------
void Controller::establishTcpUdpConnection()
{
	unsigned int attempts = 0;
	while(attempts < 3)
	{

		if(clientPortNum[Controller0] == 0)
		{
			clientPortNum[Controller0]= ethGateway->tcpConnect(invPendIpAddress, InvPendSocketPortNumber0);
		}
		if(clientPortNum[Plotter1] == 0)
		{
			clientPortNum[Plotter1]= ethGateway->tcpListen(ControllerSocketPortNumber1);
		}
		attempts++;
	}
	if(clientPortNum[Controller0] == 0)
	{
		cerr << "Error: Failed to connect to port: InvPend on TCP port: "<< InvPendSocketPortNumber0 << endl;
		exit(EXIT_FAILURE);
	}

	if(clientPortNum[Plotter1] == 0)
	{
		cerr << "Error: Failed to connect to port: Controller on TCP port: "<< ControllerSocketPortNumber1 << endl;
		exit(EXIT_FAILURE);
	}
}

void Controller::initializeFmu()
{
    vsiFmiMaster->initialize();
}

//----------------------------------------------------------------------------
// Method: terminate
// This method is used to terminate all the TCP/IP connections with
// the connected ports
//----------------------------------------------------------------------------
void Controller::terminate()
{
	ethGateway->terminate();
}

//----------------------------------------------------------------------------
// Method: isTerminationOnGoing
// This method checks if a termination process already started
//----------------------------------------------------------------------------
bool Controller::isTerminationOnGoing()
{
	return ethGateway->isTerminationOnGoing();
}
//----------------------------------------------------------------------------
// Method: isTerminated
// This method checks whether the TCP/IP ports have been already terminated
//----------------------------------------------------------------------------
bool Controller::isTerminated()
{
	return ethGateway->isTerminated();
}
