"""Calcula las métricas y genera los gráficos del proyecto.

Uso:
    python graficos.py resultados/pc_2026-10-11
        lee los tiempos_<sistema>.csv de esa carpeta y deja los gráficos en la misma carpeta.
    python graficos.py resultados/pc_2026-10-11 resultados/cluster_2026-10-12
        junta los sistemas de varias carpetas (para compararlos) y deja los gráficos
        en resultados/comparacion. Con --salida <carpeta> se elige otro destino.

Este codigo lee todos los archivos tiempos_<sistema>.csv de las carpetas indicadas (uno por
sistema medido) y genera en la carpeta de salida:

    resumen.csv              mediana del tiempo, speedup y eficiencia
    intuicion.png            grafico para explicar cómo funcionan los dos experimentos
    convergencia.png         demuestra como las estimaciones se acercan al valor real al aumentar N
    error.png                comprueba que el error baja como 1/raíz(N)
    error_procesos.png       comprueba que el error no depende de la cantidad de procesos
    tiempo_<sistema>.png     tiempo en función de la cantidad de procesos
    tiempo_n_<sistema>.png   tiempo en función de N, con la versión serial incluida
    speedup_<sistema>.png    muestra el speedup obtenido en función de la cantidad de procesos
    speedup_<sistema>_n_grande.png   lo mismo, solo con los N a partir de 10^7
    speedup.png              compara el speedup entre todos los sistemas evaluados
    eficiencia.png           grafica final para comparar eficiencia entre todos los sistemas evaluados
"""
import argparse
import glob
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CARPETA = "resultados"   # carpeta de salida; se define en main()
REAL = {"pi": math.pi, "e": math.e}
NOMBRE = {"pi": "π", "e": "e"}

# Desvío estándar teórico de una muestra de cada estimador.
# pi: 4 * Bernoulli(p) con p = pi/4.   e: cantidad de sumandos, varianza 3e - e^2.
P_CIRCULO = math.pi / 4
SIGMA = {"pi": 4 * math.sqrt(P_CIRCULO * (1 - P_CIRCULO)),
         "e": math.sqrt(3 * math.e - math.e ** 2)}

AZUL, NARANJA, GRIS = "#2a78d6", "#eb6834", "#898781"
AZULES = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]

plt.rcParams.update({"axes.grid": True, "axes.axisbelow": True, "grid.color": "#e1e0d9", "axes.spines.top": False,
                     "axes.spines.right": False, "lines.linewidth": 2, "legend.frameon": False})


def cargar_datos(carpetas):
    """Une los CSV de todos los sistemas de las carpetas indicadas en una sola tabla."""
    tablas = []
    archivos = sorted(a for c in carpetas for a in glob.glob(os.path.join(c, "tiempos_*.csv")))
    for archivo in archivos:
        tabla = pd.read_csv(archivo)
        tabla["sistema"] = os.path.basename(archivo)[len("tiempos_"):-len(".csv")]
        tablas.append(tabla)
    if not tablas:
        raise SystemExit("No hay tiempos_*.csv en las carpetas indicadas. Correr antes ./benchmark.sh <sistema>")
    return pd.concat(tablas, ignore_index=True)


#Acá agrupa las repeticiones que hizo el Bash y saca la mediana del tiempo
def calcular_resumen(datos):
    """Mediana del tiempo de cada configuración, speedup y eficiencia."""
    medianas = (datos.groupby(["sistema", "programa", "constante", "N", "P"])["tiempo_s"]
                .median().reset_index().rename(columns={"tiempo_s": "t_mediana"}))

    serial = medianas[medianas["programa"] == "serial"]
    serial = serial[["sistema", "constante", "N", "t_mediana"]].rename(columns={"t_mediana": "t_serial"})

    resumen = medianas[medianas["programa"] == "mpi"].merge(serial, on=["sistema", "constante", "N"])
    resumen["speedup"] = resumen["t_serial"] / resumen["t_mediana"]     # S = T_serial / T_P
    resumen["eficiencia"] = resumen["speedup"] / resumen["P"]           # E = S / P
    return resumen.sort_values(["sistema", "constante", "N", "P"])


def ejecuciones_distintas(datos):
    """Quita las ejecuciones repetidas entre sistemas.

    Con la misma semilla y la misma cantidad de procesos, dos sistemas generan exactamente
    los mismos números y dan la misma estimación. Para el análisis del error esas ejecuciones
    son una sola muestra y se cuentan una única vez.
    """
    return datos.drop_duplicates(["programa", "constante", "N", "P", "semilla", "estimacion"])


def potencia(n):
    return f"$10^{{{round(math.log10(n))}}}$"


def eje_de_procesos(eje, procesos):
    """Marca en el eje horizontal los valores de P medidos.

    Con pocos procesos se usa escala lineal. Si el barrido llega a muchos procesos
    (más de 32) se usa escala logarítmica, porque en escala lineal los puntos
    1, 2, 4 y 8 quedarían amontonados. Devuelve True si usó escala logarítmica.
    """
    logaritmico = max(procesos) > 32
    if logaritmico:
        eje.set_xscale("log", base=2)
    eje.set_xticks(procesos)
    eje.set_xticklabels([str(p) for p in procesos])
    eje.minorticks_off()
    eje.set_xlabel("P (procesos)")
    return logaritmico


def eje_de_speedup_logaritmico(eje, procesos):
    """Speedup en escala log-log: el ideal S = P sigue siendo una recta."""
    eje.set_yscale("log", base=2)
    eje.set_yticks(procesos)
    eje.set_yticklabels([str(p) for p in procesos])
    eje.minorticks_off()


def tonos_de_azul(cantidad):
    """Una escala de azules, de claro a oscuro, con tantos tonos como líneas haya que dibujar."""
    return plt.cm.Blues(np.linspace(0.35, 1, cantidad))




# Muestra visualmente cómo funcionan los dos experimentos: 
# a la izquierda los puntos de Monte Carlo para Pi, y a la derecha el histograma de las sumas para 'e'.
def grafico_intuicion():
    """Los dos experimentos, con pocas muestras para que se vean."""
    rng = np.random.default_rng(1)
    fig, (izq, der) = plt.subplots(1, 2, figsize=(11, 5))

    x, y = rng.random(2000), rng.random(2000)
    dentro = x * x + y * y <= 1
    izq.scatter(x[dentro], y[dentro], s=6, color=AZUL, label=f"Dentro: {dentro.sum()}")
    izq.scatter(x[~dentro], y[~dentro], s=6, color=NARANJA, label=f"Fuera: {(~dentro).sum()}")
    angulo = np.linspace(0, np.pi / 2, 100)
    izq.plot(np.cos(angulo), np.sin(angulo), color="black", linewidth=1.5)
    izq.set_aspect("equal")
    izq.grid(False)
    izq.set_title(f"π ≈ 4 × {dentro.sum()} / 2000 = {4 * dentro.sum() / 2000:.3f}")
    izq.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=2, markerscale=2)

    # Cada fila es un ensayo: la cantidad de sumandos es la posición donde la suma acumulada pasa de 1.
    sumas = rng.random((100000, 15)).cumsum(axis=1)
    cantidad = (sumas > 1).argmax(axis=1) + 1
    valores = np.arange(2, 8)
    der.bar(valores, [(cantidad == v).mean() for v in valores], color=AZUL, label="Observado")
    der.plot(valores, [(v - 1) / math.factorial(v) for v in valores], "o", color="black",
             label="Teórico: (n − 1) / n!")
    der.set_xlabel("Cantidad de números hasta que la suma supera 1")
    der.set_ylabel("Proporción de ensayos")
    der.set_title(f"e ≈ promedio de la cantidad = {cantidad.mean():.3f}")
    der.legend()

    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, "intuicion.png"), dpi=150)
    plt.close(fig)




# Grafica cómo las estimaciones (los puntos) se van acercando y estabilizando 
# en el valor real (línea negra) a medida que aumento la cantidad de muestras (N).
def grafico_convergencia(datos):
    datos = ejecuciones_distintas(datos)
    fig, ejes = plt.subplots(1, 2, figsize=(11, 4.5))
    for eje, constante, color in zip(ejes, ["pi", "e"], [AZUL, NARANJA]):
        d = datos[datos["constante"] == constante]
        eje.scatter(d["N"], d["estimacion"], s=12, color=color, alpha=0.6, label="Estimaciones")
        eje.axhline(REAL[constante], color="black", linewidth=1.2, label="Valor real")
        margen = 4 * SIGMA[constante] / math.sqrt(d["N"].min())
        eje.set_ylim(REAL[constante] - margen, REAL[constante] + margen)
        eje.set_xscale("log")
        eje.set_xlabel("N (cantidad de muestras)")
        eje.set_ylabel(f"Estimación de {NOMBRE[constante]}")
        eje.set_title(f"Convergencia de {NOMBRE[constante]}")
        eje.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, "convergencia.png"), dpi=150)
    plt.close(fig)





# Comprueba matemáticamente que a medida que aumento N, el error de mis mediciones 
# baja clavado a un ritmo de 1/√N, coincidiendo exactamente con la teoría.
def grafico_error(datos):
    """Error medido contra la recta teórica sigma / raíz(N), en escala log-log."""
    datos = ejecuciones_distintas(datos)
    fig, eje = plt.subplots(figsize=(7, 5))
    for constante, color in zip(["pi", "e"], [AZUL, NARANJA]):
        d = datos[datos["constante"] == constante]
        # Raíz del error cuadrático medio de todas las ejecuciones con cada N
        error = d.groupby("N")["error_abs"].apply(lambda e: math.sqrt((e ** 2).mean()))
        pendiente = np.polyfit(np.log10(error.index), np.log10(error.values), 1)[0]
        eje.plot(error.index, SIGMA[constante] / np.sqrt(error.index), "--", color=color,
                 linewidth=1.5, label=f"{NOMBRE[constante]}: teoría σ/√N")
        eje.plot(error.index, error.values, "o", color=color, markersize=8,
                 label=f"{NOMBRE[constante]}: medido (pendiente {pendiente:.2f})")
        print(f"Pendiente del error de {constante}: {pendiente:.3f} (teoría: -0.5)")
    eje.set_xscale("log")
    eje.set_yscale("log")
    eje.set_xlabel("N (cantidad de muestras)")
    eje.set_ylabel("Error absoluto")
    eje.set_title("El error baja como 1/√N")
    eje.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, "error.png"), dpi=150)
    plt.close(fig)






# Grafica el tiempo o el speedup según la cantidad de procesos (P).
# Con N grande el costo fijo de sincronizar y reducir es despreciable frente al cómputo
# y la curva se acerca al speedup ideal. Con N chico ese costo fijo pesa y la curva se aplana.
# n_minimo permite dejar fuera los N chicos, cuyos tiempos (de milisegundos) son poco confiables.
def grafico_por_procesos(resumen, sistema, columna, etiqueta, archivo, n_minimo=0):
    """Tiempo o speedup en función de P: un panel por constante y una línea por cada N."""
    r = resumen[(resumen["sistema"] == sistema) & (resumen["N"] >= n_minimo)]
    procesos = sorted(r["P"].unique())
    fig, ejes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for eje, constante in zip(ejes, ["pi", "e"]):
        if columna == "speedup":
            eje.plot(procesos, procesos, "--", color=GRIS, linewidth=1.5, label="Ideal")
        tamanios = sorted(r["N"].unique())
        for n, color in zip(tamanios, AZULES[-len(tamanios):]):
            linea = r[(r["constante"] == constante) & (r["N"] == n)]
            eje.plot(linea["P"], linea[columna], "o-", color=color, label=f"N = {potencia(n)}")
        logaritmico = eje_de_procesos(eje, procesos)
        if columna == "t_mediana":
            eje.set_yscale("log")
        elif logaritmico:
            eje_de_speedup_logaritmico(eje, procesos)
        eje.set_title(f"{NOMBRE[constante]} — sistema: {sistema}")
    ejes[0].set_ylabel(etiqueta)
    ejes[1].legend(loc="center left", bbox_to_anchor=(1, 0.5))
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, archivo), dpi=150)
    plt.close(fig)





# Grafica el tiempo según la cantidad de muestras (N), con la versión serial como referencia.
# El tiempo de cómputo crece en forma lineal con N (rectas paralelas en log-log). Con N chico
# y muchos procesos las curvas se aplanan: el costo fijo de sincronizar y reducir los resultados
# pasa a ser comparable con el cómputo. El lanzamiento de los procesos no entra en el tiempo medido.
def grafico_tiempo_por_n(resumen, sistema):
    """Tiempo en función de N: un panel por constante, la serial y una línea por cada P."""
    r = resumen[resumen["sistema"] == sistema]
    procesos = sorted(r["P"].unique())
    fig, ejes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for eje, constante in zip(ejes, ["pi", "e"]):
        c = r[r["constante"] == constante]
        serial = c.groupby("N")["t_serial"].first()
        for p, color in zip(procesos, tonos_de_azul(len(procesos))):
            linea = c[c["P"] == p].sort_values("N")
            eje.plot(linea["N"], linea["t_mediana"], "o-", color=color, label=f"MPI, P = {p}")
        eje.plot(serial.index, serial.values, "s--", color=NARANJA, label="Serial")
        eje.set_xscale("log")
        eje.set_yscale("log")
        eje.set_xlabel("N (cantidad de muestras)")
        eje.set_title(f"{NOMBRE[constante]} — sistema: {sistema}")
    ejes[0].set_ylabel("Tiempo mediano (s)")
    ejes[1].legend(loc="center left", bbox_to_anchor=(1, 0.5))
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, f"tiempo_n_{sistema}.png"), dpi=150)
    plt.close(fig)





# Comprueba que paralelizar no empeora la precisión: el error depende de N y no de P.
# Como el error esperado cambia con N, cada error se divide por su valor teórico σ/√N;
# así se pueden juntar las ejecuciones de todos los N y el resultado tiene que dar cerca de 1.
# Si diera bastante más que 1 al aumentar P, los procesos estarían generando números
# aleatorios correlacionados entre sí (semillas mal independizadas).
def grafico_error_por_procesos(datos):
    """Error normalizado (error / (σ/√N)) de la versión serial y de cada P."""
    d = ejecuciones_distintas(datos).copy()
    d["error_norm"] = d["error_abs"] * np.sqrt(d["N"]) / d["constante"].map(SIGMA)
    d["caso"] = np.where(d["programa"] == "serial", "serial", "P = " + d["P"].astype(str))
    casos = ["serial"] + [f"P = {p}" for p in sorted(d[d["programa"] == "mpi"]["P"].unique())]

    fig, eje = plt.subplots(figsize=(8, 5))
    eje.axhline(1, linestyle="--", color=GRIS, linewidth=1.5, label="Teoría: σ/√N")
    for constante, color in zip(["pi", "e"], [AZUL, NARANJA]):
        c = d[d["constante"] == constante]
        # Raíz del error cuadrático medio de todas las ejecuciones de cada caso
        error = c.groupby("caso")["error_norm"].apply(lambda e: math.sqrt((e ** 2).mean())).reindex(casos)
        eje.plot(casos, error.values, "o-", color=color, markersize=8, label=NOMBRE[constante])
        print(f"Error normalizado de {constante}: "
              + ", ".join(f"{caso}: {valor:.2f}" for caso, valor in error.items()))
    eje.set_ylim(0, 2)
    eje.set_ylabel("Error medido / error teórico")
    eje.set_title("El error no depende de la cantidad de procesos")
    eje.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, "error_procesos.png"), dpi=150)
    plt.close(fig)





# Compara el speedup o la eficiencia de los distintos sistemas usando el N más grande.
# Muestra hasta qué cantidad de procesos cada sistema mantiene un speedup cercano al ideal.
def grafico_entre_sistemas(resumen, columna, titulo, etiqueta, archivo):
    """Speedup o eficiencia con el N más grande medido en todos los sistemas, una línea por sistema."""
    sistemas = sorted(resumen["sistema"].unique())
    n = min(resumen[resumen["sistema"] == s]["N"].max() for s in sistemas)
    procesos = sorted(resumen["P"].unique())
    fig, ejes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for eje, constante in zip(ejes, ["pi", "e"]):
        if columna == "speedup":
            eje.plot(procesos, procesos, "--", color=GRIS, linewidth=1.5, label="Ideal")
        else:
            eje.axhline(1, linestyle="--", color=GRIS, linewidth=1.5, label="Ideal")
        for sistema, color in zip(sistemas, [AZUL, NARANJA, "#1baf7a"]):
            linea = resumen[(resumen["sistema"] == sistema) & (resumen["constante"] == constante)
                            & (resumen["N"] == n)]
            eje.plot(linea["P"], linea[columna], "o-", color=color, label=sistema)
        logaritmico = eje_de_procesos(eje, procesos)
        if columna == "eficiencia":
            eje.set_ylim(0, 1.3)
        elif logaritmico:
            eje_de_speedup_logaritmico(eje, procesos)
        eje.set_title(f"{titulo} — {NOMBRE[constante]} con N = {potencia(n)}")
    ejes[0].set_ylabel(etiqueta)
    ejes[1].legend(loc="center left", bbox_to_anchor=(1, 0.5))
    fig.tight_layout()
    fig.savefig(os.path.join(CARPETA, archivo), dpi=150)
    plt.close(fig)





def main():
    global CARPETA
    parser = argparse.ArgumentParser(description="Métricas y gráficos del proyecto")
    parser.add_argument("carpetas", nargs="+", help="carpetas de corridas con los tiempos_<sistema>.csv")
    parser.add_argument("--salida", help="carpeta donde guardar los gráficos "
                        "(por defecto la carpeta de la corrida, o resultados/comparacion si son varias)")
    args = parser.parse_args()
    CARPETA = args.salida or (args.carpetas[0] if len(args.carpetas) == 1 else os.path.join("resultados", "comparacion"))
    os.makedirs(CARPETA, exist_ok=True)

    datos = cargar_datos(args.carpetas)
    resumen = calcular_resumen(datos)
    resumen.to_csv(os.path.join(CARPETA, "resumen.csv"), index=False, float_format="%.4f")
    print(resumen.to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    grafico_intuicion()
    grafico_convergencia(datos)
    grafico_error(datos)
    grafico_error_por_procesos(datos)
    for sistema in sorted(resumen["sistema"].unique()):
        grafico_por_procesos(resumen, sistema, "t_mediana", "Tiempo mediano (s)", f"tiempo_{sistema}.png")
        grafico_tiempo_por_n(resumen, sistema)
        grafico_por_procesos(resumen, sistema, "speedup", "Speedup = T serial / T paralelo",
                             f"speedup_{sistema}.png")
        grafico_por_procesos(resumen, sistema, "speedup", "Speedup = T serial / T paralelo",
                             f"speedup_{sistema}_n_grande.png", n_minimo=10 ** 7)
    grafico_entre_sistemas(resumen, "speedup", "Speedup", "Speedup = T serial / T paralelo", "speedup.png")
    grafico_entre_sistemas(resumen, "eficiencia", "Eficiencia", "Eficiencia = speedup / P", "eficiencia.png")
    print(f"Gráficos guardados en {CARPETA}/")


if __name__ == "__main__":
    main()