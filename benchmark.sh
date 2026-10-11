#!/bin/bash
#  Script que ejecuta todas las pruebas de rendimiento(serial y paralelo) y guarda los resultados en resultados/tiempos_<sistema>.csv
#
# Uso:
#   ./benchmark.sh pc
#   ./benchmark.sh servidor
#
# Se puede cambiar qué se prueba con variables de entorno, por ejemplo:
#   TAMANIOS="100000 1000000" REPETICIONES=3 ./benchmark.sh prueba
#
# En el servidor (contenedor con 24 núcleos asignados):
#   PROCESOS="1 2 4 8 12 16 24" OPCIONES_MPI="--bind-to none --oversubscribe" ./benchmark.sh cluster_boogie
# --bind-to none: dentro de un contenedor Open MPI no siempre puede fijar cada
# proceso a un núcleo; con esta opción deja que el sistema operativo los ubique.



#  Configuracion por defecto. Define qué sistema es, tamaños de N, procesos (P) y repeticiones.
# Estas variables toman estos valores base, pero se pueden sobreescribir desde la terminal.
SISTEMA=${1:-pc}
TAMANIOS=${TAMANIOS:-"100000 1000000 10000000 100000000 1000000000"}
PROCESOS=${PROCESOS:-"1 2 4 8"}
REPETICIONES=${REPETICIONES:-5}
# --oversubscribe permite lanzar más procesos que núcleos físicos (por ejemplo 8 en una PC de 4 núcleos)
OPCIONES_MPI=${OPCIONES_MPI:-"--oversubscribe"}

make || exit 1

mkdir -p resultados
SALIDA=resultados/tiempos_$SISTEMA.csv

# Se guarda la descripción del sistema para el informe(CPU, nucleos reales y limites). En un contenedor,
# lscpu muestra la máquina completa; lo realmente asignado se ve con nproc
# y con el límite de CPU del contenedor.
#Nos sirve para saber de donde corrio la prueba para armar el informe
lscpu > resultados/sistema_$SISTEMA.txt
echo "CPUs disponibles (nproc): $(nproc)" >> resultados/sistema_$SISTEMA.txt
if [ -f /sys/fs/cgroup/cpu.max ]; then
    echo "Limite de CPU del contenedor (cpu.max): $(cat /sys/fs/cgroup/cpu.max)" >> resultados/sistema_$SISTEMA.txt
fi




#Cabecera en el archivo csv vacio
echo "programa,constante,N,P,semilla,estimacion,error_abs,tiempo_s" > $SALIDA


#itera por cada constante (pi, e) y por cada tamaño de muestra (N).
for CONSTANTE in pi e; do
    SERIAL=./montecarlo_${CONSTANTE}_serial
    PARALELO=./montecarlo_${CONSTANTE}_mpi
    for N in $TAMANIOS; do
        echo "$CONSTANTE con N = $N"

        #  Bucle principal que corre varias repeticiones del mismo experimento para sacar un promedio después.
        for REP in $(seq 1 $REPETICIONES); do
            # Cada ejecución usa una semilla distinta. En la versión MPI cada
            # proceso le suma su número de proceso, por eso se dejan "huecos"
            # entre semillas: así ninguna ejecución repite la semilla de otra
            # (vale mientras P sea menor que 100 y cada proceso sume menos de 1000)
            SEMILLA=$((REP * 100000))

            #Ejecuta la versión serial (1 solo proceso) y manda el resultado al CSV
            echo "serial,$($SERIAL $N $SEMILLA)" >> $SALIDA

            # este bucle paralelo ejecuta el programa MPI escalando la cantidad de procesos (P)
            for P in $PROCESOS; do
                SEMILLA=$((REP * 100000 + P * 1000)) # Ajusta la semilla para que no choque con la de la corrida serial ni entre los procesos
               
                echo "mpi,$(mpirun $OPCIONES_MPI -np $P $PARALELO $N $SEMILLA)" >> $SALIDA
            done
        done
    done
done

echo "Listo. Resultados en $SALIDA"