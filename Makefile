# Compila las versiones serial y MPI para pi y e
#   make         compila los programas que se creen
#   make clean   borra los ejecutables

CFLAGS = -O2 -Wall -Wextra

all: montecarlo_pi_serial montecarlo_e

montecarlo_pi_serial: montecarlo_pi_serial.c montecarlo.h montecarlo_pi.h
	gcc $(CFLAGS) montecarlo_pi_serial.c -o montecarlo_pi_serial -lm

montecarlo_e_serial: montecarlo_e_serial.c montecarlo.h montecarlo_e.h
	gcc $(CFLAGS) montecarlo_e_serial.c -o montecarlo_e_serial -lm

clean:
	rm -f montecarlo_pi_serial montecarlo_e_serial

.PHONY: all clean
