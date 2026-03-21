//---------------------------------------------------------------------------//
// Unpublished work. Copyright 2023 Siemens                                  //
//                                                                           //
// This material contains trade secrets or otherwise confidential            //
// information owned by Siemens Industry Software Inc. or its affiliates     //
// (collectively, "SISW"), or its licensors. Access to and use of this       //
// information is strictly limited as set forth in the Customer's applicable //
// agreements with SISW.                                                     //
//---------------------------------------------------------------------------//


#if defined WIN32 || defined _WIN32
#include <WinSock2.h>
#else
#include <arpa/inet.h>
#endif
#include "controller.h"

const char *DEFAULT_SERVER_URL = "localhost";
const unsigned DEFAULT_DOMAIN = AF_UNIX; 
const unsigned DEFAULT_PORT_NUM = 50102;


// Start of user custom code region. Please apply edits only within these regions:  Global Variables & Definitions


// End of user custom code region. Please don't edit beyond this point.

// ---------------------------------------------------------------------------
// Class VsiClient1
// ---------------------------------------------------------------------------
class VsiClient1  
{
	private:
		RawcTlmApiThreaded * dSession;
		// Start of user custom code region. Please apply edits only within these regions:  Private class members


		// End of user custom code region. Please don't edit beyond this point.
		VsiPortConfigGateway* vsiPortConfigGateway;
		uint64_t simulationStep;
		uint64_t totalSimulationTime;
		bool stopRequested;
		uint64_t nextExpectedTime;
		void updateInternalVariables();
	public:
		Controller * controller;
		// Start of user custom code region. Please apply edits only within these regions:  Public class members


		// End of user custom code region. Please don't edit beyond this point.
		void rtosTimerThread ();
		void initialize ();
		void executeSimulationStep ();
		void terminate ();
		VsiClient1(const char *serverUrl, unsigned domain, unsigned portNum , string fmuPath, string tmpPath);
		~VsiClient1();
};

//----------------------------------------------------------------------------
// Method: VsiClient1() constructor
//----------------------------------------------------------------------------
VsiClient1::VsiClient1 (const char *serverUrl, unsigned domain, unsigned portNum , string fmuPath, string tmpPath) 
	
{
	dSession = new RawcTlmApiThreaded (serverUrl, domain, portNum, ":remoteSession1", ":timeServerConduit1", ":resetServerConduit1");
	controller = new Controller (dSession, fmuPath, tmpPath);
	vsiPortConfigGateway = new VsiPortConfigGateway(dSession, ":txConfigPort1", ":rxConfigPort1");
	// Start of user custom code region. Please apply edits only within these regions:  Constructor


	// End of user custom code region. Please don't edit beyond this point.
}

// ---------------------------------------------------------------------------
// Destructor 
// ---------------------------------------------------------------------------
VsiClient1::~VsiClient1() 
{
	delete controller;
	delete vsiPortConfigGateway;
	delete dSession;
	// Start of user custom code region. Please apply edits only within these regions:  Destructor


	// End of user custom code region. Please don't edit beyond this point.
}

// ----------------------------------------------------------------------------
// Method:: rtosTimerThread()
// 
// This method implements the function of a very simple RTOS timer that
// fires at regular intervals and then notifies one or more modules
// that wish to be interrupted on these RTOS alarms.
// In this case the only module wishing to be notified is the ~controller~.
// ----------------------------------------------------------------------------
void VsiClient1::rtosTimerThread() 
{
    initialize();
    while(convert.timeInNs()<totalSimulationTime && !stopRequested) 
    {
        executeSimulationStep();
    }
    terminate();
}

// ---------------------------------------------------------------------------
// Method: updateInternalVariables()
// This method is responsible for reading the configurable arguments from the
// vsiPortConfigGateway
// ---------------------------------------------------------------------------
void VsiClient1::updateInternalVariables()
{
    simulationStep = vsiPortConfigGateway->getSimulationStep();
    totalSimulationTime = vsiPortConfigGateway->getTotalSimulationTime();
    stopRequested = vsiPortConfigGateway->isStopRequested();
}

// ---------------------------------------------------------------------------
// Method: readArgs()
// This method is responsible for reading the arguments passed to the
// main function
// ---------------------------------------------------------------------------
static int readArgs(int argc, char *argv[], unsigned &domain, unsigned &portNum, string &serverUrl , string &fmuPath, string &tmpPath)
{   
    int i, usage = 0;
    char argName[BUFSIZ];
    char argVal[BUFSIZ];
    // Start of user custom code region. Please apply edits only within these regions:  readArgs() instances


	// End of user custom code region. Please don't edit beyond this point.

    
    for(i = 1; i < argc && usage == 0; i++) 
    {    
        int numArgs = sscanf(argv[i], "--%[^=]=%s", argName, argVal);
        if(numArgs != 2) usage = 1;

        string arg = argName;
        
        if(arg == "domain") 
        {
            arg = argVal;
            sscanf(argVal, " %d", &domain);

            if(arg == "AF_INET") 
                domain = AF_INET;
            else if(arg == "AF_UNIX") 
                domain = AF_UNIX;
            else usage = 1;
        } 
        else if(arg == "port-num") 
        {
            sscanf(argVal, " %d", &portNum);
        }
        else if(arg == "server-url") 
        {
            serverUrl = argVal;
        }
        // Start of user custom code region. Please apply edits only within these regions:  readArgs() custom conditions


		// End of user custom code region. Please don't edit beyond this point.

        
		else if(arg == "fmuPath") { fmuPath = argVal; } 
		else if(arg == "tmpPath") { tmpPath = argVal; }

        else 
        {
            usage = 1;
        }
    }

    if(usage) 
    {
        printf("usage: VsiClient1\n");
        printf("    --domain=AF_INET | AF_UNIX    (default: AF_INET)   |\n");
        printf("    --server-url=<server IP addr> (default: localhost) |\n");
        printf("    --port-num=<value>            (default: 50102)\n");
        
    }
    return(usage);
}

//----------------------------------------------------------
// Method: int main()
// The top-level ~main()~ entrypoint  is shown here.
//---------------------------------------------------------
int main (int argc, char *argv[])
{
	VsiClient1 * vsiClient1;

	int ret = 0;
    unsigned domain  = DEFAULT_DOMAIN;
    unsigned portNum = DEFAULT_PORT_NUM;
    string serverUrl = DEFAULT_SERVER_URL;

    string fmuPath;
	string tmpPath;


    if(readArgs(argc, (char **)argv, domain, portNum, serverUrl , fmuPath, tmpPath)) 
        return-1;
    
	try 
	{
		vsiClient1 = new VsiClient1(serverUrl.c_str(), domain, portNum  , fmuPath, tmpPath);
		vsiClient1->rtosTimerThread();
	}
	catch (const std::runtime_error& e)
	{
		cout << e.what() << endl;
		cout << "Fatal Error: Program aborting." << endl;
		ret = -1;
	}
	catch(string message) 
	{
		cout << message << endl;
		cout << "Fatal Error: Program aborting." << endl;
		ret = -1;
	}
	catch(...) 
	{
		cout << "Error: Unclassified exception." << endl;
		cout << "Fatal Error: Program aborting." << endl;
		ret = -1;
	}
	if (vsiClient1) delete vsiClient1;
	return ret;
}

// ----------------------------------------------------------------------------
// Method:: initialize()
// 
// This method implements the initialization functions for this module
// ----------------------------------------------------------------------------
void VsiClient1::initialize() 
{
    try
    {
        dSession->waitForReset();
        // Start of user custom code region. Please apply edits only within these regions:  After waiting for reset


		// End of user custom code region. Please don't edit beyond this point.

        // get the latest variables
        updateInternalVariables();
        if (stopRequested) throw string("stopRequested");
        controller->initializeFmu();
        controller->establishTcpUdpConnection();
        // Wait for the configuration packet to be received
        while(!vsiPortConfigGateway -> isConfigurationDone()) dSession -> yield();
        nextExpectedTime = convert.timeInNs();
        updateInternalVariables();
    }
    catch(string message)
    {
        if (message == "stopRequested") 
        {
            printf("=+= Terminate signal has been received from one of the VSI clients\n");
            dSession->advanceNs(simulationStep + 1);
        } 
    }
    catch(...)
    {
        vsiPortConfigGateway->sendTerminatePacket();
        // Advance time with a step that is equal to "simulationStep + 1" so that all other clients
        // receive the terminate packet before terminating this client
        dSession->advanceNs(simulationStep + 1);
        throw;
    }   
}

// ----------------------------------------------------------------------------
// Method:: executeSimulationStep()
// 
// This method executes the operations needed every simulation step
// ----------------------------------------------------------------------------
void VsiClient1::executeSimulationStep() 
{
    try
    {
        // Start of user custom code region. Please apply edits only within these regions:  Inside the while loop


		// End of user custom code region. Please don't edit beyond this point.

        if (controller->isTerminationOnGoing())
		{
			cerr << "Application: Termination ongoing" << endl;
			stopRequested = true;
			return;
		}

        if (controller->isTerminated())
		{
			cerr << "Application: Terminated" << endl;
			stopRequested = true;
			return;
		}

        updateInternalVariables();
        if (stopRequested) throw string("stopRequested");
        controller->mainThread();
        //update all internal variables
        updateInternalVariables();
        if (stopRequested) throw string("stopRequested");
        nextExpectedTime += simulationStep * 10;
        if (convert.timeInNs() >= nextExpectedTime)
        {
            printf("Warning: Packet exchange time exceeds simulation step, Larger simulation step is needed\n");
        }

        // Remaining time is less than the needed time for performing a step
        if(nextExpectedTime > totalSimulationTime)
        {
            uint64_t remainingTime = totalSimulationTime - convert.timeInNs();
            dSession->advanceNs(remainingTime);
            return;
        }

        if(convert.timeInNs() < nextExpectedTime)
        {
            dSession->advanceNs(nextExpectedTime - convert.timeInNs());
        }
    }
    catch(string message)
    {
        if (message == "stopRequested") 
        {
            printf("=+= Terminate signal has been received from one of the VSI clients\n");
            dSession->advanceNs(simulationStep + 1);
        } 
    }
    catch(...)
    {
        vsiPortConfigGateway->sendTerminatePacket();
        // Advance time with a step that is equal to "simulationStep + 1" so that all other clients
        // receive the terminate packet before terminating this client
        dSession->advanceNs(simulationStep + 1);
        throw;
    }
}

// ----------------------------------------------------------------------------
// Method:: terminate()
// 
// This method implements the termination functions for this module
// ----------------------------------------------------------------------------
void VsiClient1::terminate() 
{
    
	if (convert.timeInNs() < totalSimulationTime) 
	{
		controller->terminate();
	}

}
