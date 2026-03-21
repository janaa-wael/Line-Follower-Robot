CC ?= gcc
OPT=-O3
CDEFINES += \
    -DXML_STATIC -DFMI_XML_QUERY -DZLIB_STATIC -DFMILIB_BUILDING_LIBRARY

CFLAGS += \
    $(OPT) -fPIC $(CDEFINES)

INCL += \
    -I. \
    -I$(FMI_LIB_HOME)/$(FMI_LIB_VERSION)/include

COBJS=$(CSRCS:%.c=%.o)
CDEPS=$(CSRCS:%.c=%.d)
OBJS=$(SRCS:%.cxx=%.o)
DEPS=$(SRCS:%.cxx=%.d)
TOBJS=$(TSRCS:%.c=%.o)
TDEPS=$(TSRCS:%.c=%.d)

%.d: %.c
	rm -f $@
	$(CC) -M $(CFLAGS) $(INCL) -c $< | sed -e 's+^.*\.o: \(.*\).cxx+\1.o: \1.cxx+' > $@

%.o: %.c
	$(CC) $(CFLAGS) $(INCL) -c $< -o $@

%.d: %.cxx
	rm -f $@
	$(CXX) -M $(CFLAGS) $(INCL) -c $< | sed -e 's+^.*\.o: \(.*\).cxx+\1.o: \1.cxx+' > $@

%.o: %.cxx
	$(CXX) $(CFLAGS) $(INCL) -c $< -o $@
