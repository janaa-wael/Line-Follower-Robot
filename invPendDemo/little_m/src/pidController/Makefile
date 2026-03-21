all: build

INV_PEND_PID_FMU= invPend_pid.fmu
LIB_FMU_SO = invPend_V1.so

CSRCS = \
    invPendPid.c \

CDEFINES = -Dfmu2_dll_cs_EXPORTS

CC = gcc
# Enable this for aarch64 build
#CC = aarch64-linux-gcc
PLATFORM=linux64

# Enable this for MinGW
# CC = x86_64-w64-mingw32-gcc
# PLATFORM=win64
# LIB_FMU_SO = TorqueToRpmFMU_V1.dll
# CDEFINES += -DWIN32 -D_WIN32


include common.mk

#-----------------------------------------------------------------------------
build: $(INV_PEND_PID_FMU) install

install: $(INSTALLED_INV_PEND_PID_FMU)

$(INV_PEND_PID_FMU): $(LIB_FMU_SO)
	mkdir -p binaries/$(PLATFORM)
	cp -p $(LIB_FMU_SO) binaries/$(PLATFORM)/$(LIB_FMU_SO)
	compress_test_fmu_zip $@ \
		modelDescription.xml \
		binaries/$(PLATFORM)/$(LIB_FMU_SO) 
	rm -rf binaries modelDescription.xml

$(INSTALLED_INV_PEND_PID_FMU): $(INV_PEND_PID_FMU)
	cp -p $^ $@

$(LIB_FMU_SO): $(COBJS)
	$(CC) -shared -o $@ $^ $(LDFLAGS)

#-----------------------------------------------------------------------------
clean:
	rm -f $(INSTALLED_INV_PEND_PID_FMU) $(LIB_FMU_SO) $(COBJS) $(CDEPS)

include $(CDEPS)
