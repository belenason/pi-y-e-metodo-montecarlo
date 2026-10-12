# Estimación de π y e mediante el Método de Monte Carlo

**Implementación secuencial en C y paralela con Open MPI**

**Asignatura:** Computación Científica / Métodos Numéricos II  
**Institución:** Facultad de Ciencias Exactas y Tecnología (FACET) – Universidad Nacional de Tucumán (UNT)  
**Repositorio:** [pi-y-e-metodo-montecarlo](https://github.com/belenason/pi-y-e-metodo-montecarlo) ||
**Informe:** [Proyecto HPC Computación Científica - Informe ](https://docs.google.com/document/d/1fGytDr1ASnMOOjRSOQSA6F3Cjop2hToPlUJomgpMeCc/edit?usp=sharing)

## Integrantes

- Ason, Belén
- Cano Arce, Valentina
- Caballero, Leonardo

---

## Descripción

El proyecto estima las constantes π y e con el método de Monte Carlo y mide el rendimiento de una versión secuencial y otra paralela con MPI (modelo SPMD, reparto estático de las muestras, `MPI_Bcast` y `MPI_Reduce`).

- **π:** se sortean puntos en el cuadrado unitario y se cuenta la fracción que cae dentro del cuarto de círculo.
- **e:** se cuenta cuántos números uniformes en [0, 1) hay que sumar para superar 1; el promedio de esa cantidad tiende a e.

Cada proceso MPI usa la semilla `semilla + rank` con `srand48`/`drand48`. El tiempo se mide solo sobre el cómputo y la reducción (después de una barrera), sin incluir el lanzamiento de los procesos.

La metodología, los resultados y su análisis están en el informe.

## Estructura

```text
.
├── montecarlo.h                          # Lectura de argumentos y formato de salida
├── montecarlo_pi.h / montecarlo_e.h      # Núcleo de cada estimación
├── montecarlo_pi_serial.c / montecarlo_e_serial.c   # Versiones secuenciales
├── montecarlo_pi_mpi.c / montecarlo_e_mpi.c         # Versiones paralelas (MPI)
├── Makefile                              # Compilación
├── benchmark.sh                          # Automatiza las mediciones
├── graficos.py                           # Métricas y gráficos a partir de las mediciones
└── resultados/                           # Una carpeta por corrida y las comparaciones
```

## Requisitos

- Linux (o WSL en Windows). El script usa Bash, `lscpu` y `nproc`.
- `gcc` y Open MPI (`mpicc`, `mpirun`).
- Para los gráficos: Python 3 con `pandas`, `numpy` y `matplotlib`.

```bash
sudo apt update
sudo apt install build-essential openmpi-bin libopenmpi-dev \
    python3-pandas python3-numpy python3-matplotlib
```

## Compilación y ejecución

```bash
make          # compila los cuatro programas (gcc/mpicc -O2)
make clean    # borra los ejecutables
```

Todos los programas se invocan como `<N> [semilla]` (semilla por defecto: 12345) e imprimen una línea CSV: `constante,N,P,semilla,estimacion,error_abs,tiempo_s`.

```bash
./montecarlo_pi_serial 100000000 12345
mpirun -np 4 ./montecarlo_pi_mpi 100000000 12345
```

Si se piden más procesos que núcleos disponibles, agregar `--oversubscribe` a `mpirun`.

## Benchmarking

Ejecutar siempre **desde la raíz del repositorio**:

```bash
bash benchmark.sh <sistema>
```

`<sistema>` es una etiqueta para identificar la máquina (por ejemplo `pc` o `cluster`); por defecto es `pc`. El script compila con `make`, y para π y e, cada N y cada P ejecuta la versión serial y la MPI, repitiendo todo `REPETICIONES` veces con semillas distintas.

Configuración por defecto, modificable con variables de entorno:

| Variable | Por defecto | Descripción |
|---|---|---|
| `TAMANIOS` | `100000 1000000 10000000 100000000 1000000000` | Valores de N |
| `PROCESOS` | `1 2 4 8` | Valores de P |
| `REPETICIONES` | `5` | Repeticiones por configuración |
| `OPCIONES_MPI` | `--oversubscribe` | Opciones extra para `mpirun` |
| `CORRIDA` | `<sistema>_<fecha>` | Nombre de la carpeta en `resultados/` |

Ejemplos:

```bash
# Prueba rápida para verificar que todo funciona
TAMANIOS="100000 1000000" PROCESOS="1 2" REPETICIONES=2 CORRIDA=prueba bash benchmark.sh prueba

# Corrida en el clúster (contenedor con 48 núcleos asignados)
PROCESOS="1 2 4 8 12 16 24 32 48" OPCIONES_MPI="--bind-to none --oversubscribe" bash benchmark.sh cluster
```

Cada corrida deja en `resultados/<corrida>/` el archivo `tiempos_<sistema>.csv` (una fila por ejecución) y `sistema_<sistema>.txt` (salida de `lscpu`, `nproc` y límite de CPU del contenedor). Si la carpeta ya existe, el script se detiene para no pisar resultados anteriores.

### Gráficos y métricas

```bash
python3 graficos.py resultados/pc_2026-10-11                  # una corrida
python3 graficos.py resultados/pc_2026-10-11 resultados/cluster_2026-10-11   # comparación
```

Calcula la mediana de las repeticiones, el speedup (`T_serial / T_P`) y la eficiencia (`speedup / P`), y guarda `resumen.csv` y los gráficos en la carpeta de la corrida (o en `resultados/comparacion` si se indican varias; se cambia con `--salida`).

### Qué controlar antes de medir

1. **Núcleos reales:** el máximo de `PROCESOS` no debería superar los núcleos físicos disponibles (`nproc`; en un contenedor, el límite de `cpu.max`). Con `--oversubscribe` por encima de ese valor los tiempos dejan de ser interpretables.
2. **Máquina sin otra carga:** cerrar otras aplicaciones; en notebook, conectarla a la corriente y evitar el modo ahorro de energía. Idealmente no tocar la máquina durante la corrida.
3. **Duración:** con los valores por defecto el N = 10⁹ domina el tiempo total. Conviene hacer primero la prueba rápida y estimar la duración antes de la corrida completa (o correrla con `nohup`/`tmux` si es remota).
4. **Contenedores:** `--bind-to none` evita errores de Open MPI al fijar procesos a núcleos que el contenedor no asigna.
5. **Semillas:** el script usa `REP*100000 + P*1000` (más el rank en MPI), lo que evita repetir semillas dentro de una corrida mientras P < 100. Si se usan más procesos, revisar esa fórmula.
6. **Corridas repetidas en distintos sistemas:** con la misma semilla y P, dos sistemas dan la misma estimación; `graficos.py` ya lo contempla al analizar el error.
7. **Nombre de la corrida:** al correr en otra fecha o máquina usar un `CORRIDA` explícito si se quiere conservar la anterior; `graficos.py` toma el nombre del sistema del archivo `tiempos_<sistema>.csv`, así que cada sistema comparado debe usar una etiqueta distinta.
