#include "FMI2/fmi2Functions.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>  

typedef struct {
    // Inputs from robot
    double robot_x;
    double robot_y;
    double robot_theta;
    double ref_x;
    double ref_y;
    double cross_error;
    
    // Outputs to robot
    double cmd_v;
    double cmd_w;
    
    // PID gains
    double kp_lateral;
    double ki_lateral;
    double kd_lateral;
    double kp_heading;
    
    // PID state
    double integral;
    double prev_error;
    double prev_heading_error;
    
    // Limits
    double integral_limit;
    double output_limit;
    double dt;
} FMUInstance;

static FMUInstance* fmu = NULL;

fmi2Component fmi2Instantiate(const char* instanceName, fmi2Type fmuType, const char* fmuGUID, const char* fmuResourceLocation, const fmi2CallbackFunctions* functions, fmi2Boolean visible, fmi2Boolean loggingOn) {
     fmu = (FMUInstance*) calloc(1, sizeof(FMUInstance));
    
    // Initialize robot inputs
    fmu->robot_x = 0.0;
    fmu->robot_y = 0.0;
    fmu->robot_theta = 0.0;
    fmu->ref_x = 0.0;
    fmu->ref_y = 0.0;
    fmu->cross_error = 0.0;
    
    // Initialize outputs
    fmu->cmd_v = 0.3;  // constant linear velocity
    fmu->cmd_w = 0.0;
    
    // PID gains (balanced set)
    fmu->kp_lateral = 2.0;
    fmu->ki_lateral = 0.15;
    fmu->kd_lateral = 0.3;
    fmu->kp_heading = 1.5;
    
    // PID state
    fmu->integral = 0.0;
    fmu->prev_error = 0.0;
    fmu->prev_heading_error = 0.0;
    fmu->integral_limit = 1.0;
    fmu->output_limit = 2.0;
    fmu->dt = 0.01;
    
    return (fmi2Component) fmu;
}

// Start of Model-specific FMI functions

 fmi2Status fmi2SetReal(
    fmi2Component c, const fmi2ValueReference valueRefs[],
    size_t numValueRefs, const fmi2Real values[] )
{
        for (size_t i = 0; i < numValueRefs; ++i) {
        switch (valueRefs[i]) {
            case 0: fmu->robot_x = values[i]; break;
            case 1: fmu->robot_y = values[i]; break;
            case 2: fmu->robot_theta = values[i]; break;
            case 3: fmu->ref_x = values[i]; break;
            case 4: fmu->ref_y = values[i]; break;
            case 5: fmu->cross_error = values[i]; break;
        }
    }
    return fmi2OK; 
}

fmi2Status fmi2GetReal(
        fmi2Component c, const fmi2ValueReference valueRefs[],
        size_t numValueRefs, fmi2Real values[] )
    {
        for (size_t i = 0; i < numValueRefs; ++i) {
        switch (valueRefs[i]) {
            case 6: values[i] = fmu->cmd_v; break;
            case 7: values[i] = fmu->cmd_w; break;
        }
    }
    return fmi2OK;
}

fmi2Status fmi2DoStep(fmi2Component c, fmi2Real currentCommunicationPoint, fmi2Real communicationStepSize, fmi2Boolean noSetFMUStatePriorToCurrentPoint) {
        fmu->dt = communicationStepSize;
    
    // Calculate heading error
    double dx = fmu->ref_x - fmu->robot_x;
    double dy = fmu->ref_y - fmu->robot_y;
    double desired_theta = atan2(dy, dx);
    double heading_error = desired_theta - fmu->robot_theta;
    
    // Normalize heading error to [-pi, pi]
    heading_error = atan2(sin(heading_error), cos(heading_error));
    
    // Use cross-track error from robot simulator
    double error = fmu->cross_error;
    
    // PID for lateral error
    fmu->integral += error * fmu->dt;
    
    // Anti-windup
    if (fmu->integral > fmu->integral_limit)
        fmu->integral = fmu->integral_limit;
    if (fmu->integral < -fmu->integral_limit)
        fmu->integral = -fmu->integral_limit;
    
    // Derivative
    double derivative = (error - fmu->prev_error) / fmu->dt;
    
    // PID output
    double lateral_output = fmu->kp_lateral * error + 
                           fmu->ki_lateral * fmu->integral + 
                           fmu->kd_lateral * derivative;
    
    // Heading correction
    double heading_output = fmu->kp_heading * heading_error;
    
    // Combine for angular velocity
    double raw_w = lateral_output + heading_output;
    
    // Limit output
    if (raw_w > fmu->output_limit) raw_w = fmu->output_limit;
    if (raw_w < -fmu->output_limit) raw_w = -fmu->output_limit;
    
    fmu->cmd_w = raw_w;
    fmu->cmd_v = 0.3;  // constant forward speed
    
    // Save for next step
    fmu->prev_error = error;
    fmu->prev_heading_error = heading_error;
    
    return fmi2OK;

}


// End of Model-specific FMI functions

void errorUnimplementedFunction( const char *functionName,
    int line, const char *file )
{   printf( "FMI2-FATAL: Attempted call to function '%s' [line #%d of '%s'].\n",
        functionName, line, file ); }

fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer value[]) {
errorUnimplementedFunction( "fmi2SetInteger()",
        __LINE__, __FILE__ );
    return fmi2Fatal; }


fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Integer value[]) {
errorUnimplementedFunction( "fmi2GetInteger()",
        __LINE__, __FILE__ );
    return fmi2Fatal; }



/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2EnterInitializationMode( fmi2Component c ) {
    if( c == NULL ) return fmi2Fatal;
    else return fmi2OK;
}

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2ExitInitializationMode( fmi2Component c ) {
    if( c == NULL ) return fmi2Fatal;
    else return fmi2OK;
}

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Boolean value[])
{   errorUnimplementedFunction( "fmi2GetBoolean()", __LINE__, __FILE__ );
    return fmi2Fatal; }

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2GetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2String  value[])
{   errorUnimplementedFunction( "fmi2GetString()", __LINE__, __FILE__ );
    return fmi2Fatal; }

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Boolean value[])
{   errorUnimplementedFunction( "fmi2SetBoolean()", __LINE__, __FILE__ );
    return fmi2Fatal; }

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2SetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2String  value[])
{   errorUnimplementedFunction( "fmi2SetString()", __LINE__, __FILE__ );
    return fmi2Fatal; }

/*---------------------------------------------------------*/
FMI2_Export const char* fmi2GetTypesPlatform() { return fmi2TypesPlatform; }

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2Terminate(fmi2Component c) {
    return fmi2OK;
}

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2Reset(fmi2Component c) {
    return fmi2OK; }

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2SetRealInputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer order[], const fmi2Real value[])
{   errorUnimplementedFunction( "fmi2SetRealInputDerivatives()",
        __LINE__, __FILE__ );
    return fmi2Fatal; }

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2GetRealOutputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer order[], fmi2Real value[])
{   errorUnimplementedFunction( "fmi2GetRealOutputDerivatives()",
        __LINE__, __FILE__ );
    return fmi2Fatal; }

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2CancelStep(fmi2Component c) {
    return fmi2OK; }

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2GetStatus(
    fmi2Component c, const fmi2StatusKind s, fmi2Status*  value ) {
    switch (s) {
        case fmi2DoStepStatus:
            /* Return fmiPending if we are waiting.
               Otherwise the result from fmiDoStep */
            *value = fmi2OK;
            return fmi2OK;
        default: /* Not defined for status for this function */
            *value = fmi2Discard;
            return fmi2OK;
    }
}

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2GetRealStatus(fmi2Component c, const fmi2StatusKind s, fmi2Real*    value)
{   errorUnimplementedFunction( "fmi2GetRealStatus()", __LINE__, __FILE__ );
    return fmi2Fatal; }

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2GetIntegerStatus(fmi2Component c, const fmi2StatusKind s, fmi2Integer* value)
{   errorUnimplementedFunction( "fmi2GetIntegerStatus()", __LINE__, __FILE__ );
    return fmi2Fatal; }

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2GetBooleanStatus(fmi2Component c, const fmi2StatusKind s, fmi2Boolean* value)
{   errorUnimplementedFunction( "fmi2GetBooleanStatus()", __LINE__, __FILE__ );
    return fmi2Fatal; }

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2GetStringStatus(fmi2Component c, const fmi2StatusKind s, fmi2String*  value)
{   errorUnimplementedFunction( "fmi2GetStringStatus()", __LINE__, __FILE__ );
    return fmi2Fatal; }

/*---------------------------------------------------------*/
FMI2_Export const char* fmi2GetVersion() { return "2.0"; }

FMI2_Export void fmi2FreeInstance( fmi2Component c ) {
 
}
/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2GetFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) {
    return fmi2Error;
}

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2SetFMUstate(fmi2Component c, fmi2FMUstate FMUstate) {
    // In a basic model like yours, you might not need FMU state serialization
    return fmi2Error;  // Placeholder for non-implemented state setting
}

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2SetDebugLogging(
    fmi2Component c, fmi2Boolean loggingOn, size_t n, const fmi2String cat[])
{   errorUnimplementedFunction( "fmi2SetDebugLogging()", __LINE__, __FILE__ );
    return fmi2Fatal; }

/*---------------------------------------------------------*/
FMI2_Export fmi2Status fmi2SetupExperiment( fmi2Component c, 
    fmi2Boolean isToleranceDefined, fmi2Real tolerance,
    fmi2Real startTime, fmi2Boolean isStopTimeDefined,
    fmi2Real stopTime)
{
    return fmi2OK;
}
/*---------------------------------------------------------*/