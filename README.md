
# Estimación de π y e mediante el Método de Monte Carlo

**Implementación secuencial en C y paralela con Open MPI**

**Asignatura:** Computación Científica / Métodos Numéricos II  
**Institución:** Facultad de Ciencias Exactas y Tecnología (FACET) – Universidad Nacional de Tucumán (UNT)  
**Repositorio:** [pi-y-e-metodo-montecarlo](https://github.com/belenason/pi-y-e-metodo-montecarlo)

---

## Integrantes

- **Ason, Belén.**
- **Cano Arce, Valentina.**
- **Caballero, Leonardo.**

---

## Descripción del proyecto

Este proyecto implementa y evalúa la estimación de las constantes matemáticas π y e mediante el **método de Monte Carlo**, una técnica numérica basada en el uso de muestras aleatorias para obtener aproximaciones de problemas matemáticos.

El objetivo es estudiar tanto la precisión de las estimaciones como el rendimiento computacional de las implementaciones secuenciales y paralelas, aplicando conceptos de **Computación de Alto Rendimiento (HPC)**.

El desarrollo comprende las siguientes etapas:

1. **Implementación secuencial en C11:** desarrollo de las versiones secuenciales para π y e, utilizadas como línea base para comparar el rendimiento. La medición del tiempo de ejecución se realiza mediante `clock_gettime(CLOCK_MONOTONIC)`.

2. **Implementación paralela con Open MPI:** distribución del trabajo entre procesos mediante el modelo SPMD (*Single Program, Multiple Data*). Se utilizan operaciones colectivas como `MPI_Bcast` y `MPI_Reduce`, distribución estática de las muestras y semillas diferenciadas por proceso mediante `srand48(semilla + rank)`.

3. **Automatización de pruebas:** ejecución de experimentos con diferentes cantidades de muestras (\(N = 10^5\) a \(10^9\)) y procesos (\(P = 1, 2, 4, 8, 16\)). Se utiliza un script Bash para automatizar las ejecuciones y calcular la mediana de cinco repeticiones consecutivas, reduciendo la influencia de variaciones ocasionales en los tiempos de ejecución.

4. **Análisis y visualización de resultados:** procesamiento de los datos mediante Python y generación de gráficos para analizar la aceleración (*speedup*), la eficiencia paralela y la convergencia del error en función de la cantidad de muestras. Los resultados permiten estudiar el comportamiento del programa paralelo y relacionarlo con la ley de Amdahl.

---

## Estructura del repositorio

```text
.
├── montecarlo.h              # Cabecera principal
├── montecarlo_pi.h           # Definiciones para la estimación de π
├── montecarlo_e.h            # Definiciones para la estimación de e
├── montecarlo_pi_serial.c    # Implementación secuencial de π
├── montecarlo_e_serial.c     # Implementación secuencial de e
├── montecarlo_pi_mpi.c       # Implementación paralela de π con MPI
├── montecarlo_e_mpi.c        # Implementación paralela de e con MPI
├── Makefile                  # Compilación automatizada
├── benchmark.sh              # Automatización de pruebas y mediciones
├── graficos.py               # Procesamiento y generación de gráficos
└── README.md                 # Documentación del proyecto
```

---

## Requisitos

Para compilar y ejecutar el proyecto se necesita:

- **GCC:** compilador de C con soporte para C11.
- **Open MPI o MPICH:** biblioteca de paso de mensajes, con herramientas como `mpicc` y `mpirun`.
- **Sistema operativo:** Linux o Unix. También puede utilizarse un clúster de cómputo compatible.
- **Python 3:** para el análisis de resultados y la generación de gráficos.
- **Bibliotecas de Python:** `pandas`, `numpy` y `matplotlib`.

### Instalación en Ubuntu/Debian

```bash
sudo apt update
sudo apt install build-essential openmpi-bin libopenmpi-dev \
    python3-pandas python3-numpy python3-matplotlib
```

---

## Compilación y ejecución

### 1. Compilar el proyecto

Desde el directorio raíz del repositorio, ejecutar:

```bash
make
```

El `Makefile` permite compilar los programas utilizando las opciones de optimización configuradas, entre ellas `-O3`.

Para eliminar los ejecutables generados:

```bash
make clean
```

### 2. Ejecutar las versiones secuenciales

Las implementaciones secuenciales reciben como argumentos la cantidad de muestras y la semilla del generador pseudoaleatorio.

**Formato:**

```bash
./binario <N_muestras> <semilla>
```

**Ejemplos:**

```bash
./montecarlo_pi_serial 100000000 12345
./montecarlo_e_serial 100000000 12345
```

### 3. Ejecutar las versiones paralelas con MPI

Para ejecutar una implementación paralela, se especifica la cantidad de procesos mediante `mpirun`.

**Formato:**

```bash
mpirun -n <num_procesos> ./binario <N_muestras> <semilla>
```

**Ejemplos:**

```bash
mpirun -n 4 ./montecarlo_pi_mpi 100000000 12345
mpirun -n 4 ./montecarlo_e_mpi 100000000 12345
```

Si se necesita ejecutar más procesos que los espacios de ejecución disponibles localmente, se puede utilizar `--oversubscribe`:

```bash
mpirun -n 8 --oversubscribe ./montecarlo_pi_mpi 100000000 12345
```

> **Nota:** la opción `--oversubscribe` permite ejecutar más procesos de los espacios de ejecución disponibles, pero no garantiza una mejora del rendimiento.

### 4. Ejecutar el benchmarking

El script `benchmark.sh` automatiza las pruebas con diferentes cantidades de muestras y procesos, realiza las repeticiones configuradas y obtiene las medianas de los tiempos medidos.

```bash
chmod +x benchmark.sh
./benchmark.sh
```

Una vez generados los resultados, ejecutar el script de Python para producir los gráficos:

```bash
python3 graficos.py
```

Los rangos de muestras, las cantidades de procesos y los archivos de salida dependen de la configuración implementada en los scripts.

---


## Métricas de rendimiento

### Aceleración (*Speedup*)

Mide cuánto más rápida es la ejecución paralela respecto de la secuencial.

$$
S_P = \frac{T_1}{T_P}
$$

Donde:

- $T_1$: tiempo de ejecución de referencia secuencial.
- $T_P$: tiempo de ejecución utilizando $P$ procesos.

### Eficiencia paralela

Indica qué tan eficazmente se aprovechan los procesos disponibles.

$$
E_P = \frac{S_P}{P} \times 100\%
$$

Una eficiencia cercana al 100 % representa un aprovechamiento ideal de los procesos según esta métrica.

### Error relativo porcentual

Permite medir la diferencia entre la estimación obtenida y el valor de referencia de la constante.

$$
E_{\mathrm{rel}} =
\left|
\frac{\text{Estimación} - \text{Valor real}}
{\text{Valor real}}
\right| \times 100\%
$$

Cuanto menor sea el error relativo, más cercana será la estimación al valor de referencia.

### Convergencia del error

En los métodos de Monte Carlo, el error estadístico típico disminuye aproximadamente según:

$$
E(N) = \mathcal{O}\left(\frac{1}{\sqrt{N}}\right)
$$

Esto significa que, para reducir el error típico aproximadamente a la mitad, se necesita multiplicar por cuatro la cantidad de muestras, suponiendo condiciones estadísticas comparables.

### Ley de Amdahl

La ley de Amdahl permite analizar los límites teóricos de la aceleración de un programa paralelo cuando una parte de su ejecución permanece secuencial.

$$
S(P) = \frac{1}{(1-f) + \frac{f}{P}}
$$

Donde:

- $S(P)$: aceleración teórica con $P$ procesos.
- $f$: fracción del programa que puede paralelizarse.
- $1-f$: fracción secuencial del programa.
- $P$: cantidad de procesos utilizados.

## Optimizaciones avanzadas y trabajo futuro

Como posibles líneas de mejora, se plantean las siguientes optimizaciones:

1. **Generador pseudoaleatorio:** sustituir `drand48` por un generador como `xoshiro256**`, utilizando mecanismos de salto (*jump*) para obtener subsecuencias diferenciadas entre procesos. La independencia estadística debe verificarse; las semillas o los saltos, por sí solos, no garantizan una ausencia absoluta de solapamientos.

2. **Bit-packing y aritmética entera:** explorar la generación de coordenadas a partir de números aleatorios de 64 bits y el uso de operaciones enteras para reducir el costo de generación y evaluación de muestras.

3. **Vectorización SIMD (AVX-512):** evaluar el procesamiento simultáneo de múltiples muestras mediante instrucciones vectoriales, aprovechando las capacidades del procesador y las características de la implementación.

4. **Paralelismo híbrido y aceleración por GPU:** extender la solución mediante una combinación de MPI, OpenMP y CUDA, con el objetivo de aprovechar tanto el paralelismo entre procesos como los recursos multinúcleo y las GPU. Para la generación aleatoria en GPU, puede evaluarse el uso de `cuRAND`.

Estas mejoras permitirían estudiar nuevas estrategias de optimización y comparar su impacto en los tiempos de ejecución, la escalabilidad y la eficiencia.

---

## Tecnologías utilizadas

- **C11:** implementación de los algoritmos secuenciales y paralelos.
- **Open MPI:** comunicación y distribución del trabajo entre procesos.
- **GCC:** compilación y optimización del código.
- **Bash:** automatización de experimentos.
- **Python:** procesamiento de datos y visualización de resultados.
- **NumPy, pandas y Matplotlib:** análisis numérico, organización de datos y generación de gráficos.
- **Git y GitHub:** control de versiones y gestión del repositorio.

---

