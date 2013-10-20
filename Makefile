# Use swipl-ld as CC to automatically find include/lib locations
CC=swipl-ld

# Add SWI-Prolog include dirs if not using swipl-ld as CC
SWIPL_INCLUDES=
# SWI-Prolog libraries
SWIPL_LIBS=-lswipl

# Get Python Version
PYTHON_VERSION=`python2 -c "import distutils.sysconfig as sc;print sc.get_config_var('VERSION')"`
# Find location of Python.h
PYTHON_INCLUDES=`python2 -c "import distutils.sysconfig as sc;print '-I'+sc.get_python_inc()"`
# Python libraries
PYTHON_LIBS=-lpython${PYTHON_VERSION}

INCLUDES=${PYTHON_INCLUDES} ${SWIPL_INCLUDES}
LIBS=${PYTHON_LIBS} ${SWIPL_LIBS} -ldl -lm -lncurses

pyswipl.so: build/pyswipl.o
	${CC} -shared -g build/pyswipl.o ${LIBS} -o pyswipl.so

build/pyswipl.o: src/pyswipl.c
	${CC} -g -c src/pyswipl.c ${INCLUDES} -o build/pyswipl.o

clean:
	rm -rf pyswipl.so build/* log/* *~ *.pyc src/*~ ggp/*~ ggp/*.pyc
