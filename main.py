import argparse
import hashlib
import time
import multiprocessing
from multiprocessing import Event, Process, Queue


# ===== CONFIGURAÇÃO FIXA =====
DIGITOS = 9
WORKERS_LIST = [12, 8, 4, 2, 1]
# =============================


def brute_force_serial(hash_alvo: str):
    hash_bytes = bytes.fromhex(hash_alvo)
    inicio = time.perf_counter()
    total = 10 ** DIGITOS

    for tentativa in range(total):
        senha = f"{tentativa:09d}".encode("ascii")
        if hashlib.md5(senha).digest() == hash_bytes:
            tempo_total = time.perf_counter() - inicio
            return senha.decode("ascii"), tempo_total

    tempo_total = time.perf_counter() - inicio
    return None, tempo_total


def worker(hash_bytes, inicio_faixa, fim_faixa, encontrado, resultado_queue):
    for tentativa in range(inicio_faixa, fim_faixa):

        if tentativa % 4096 == 0 and encontrado.is_set():
            return

        senha = f"{tentativa:09d}".encode("ascii")
        if hashlib.md5(senha).digest() == hash_bytes:
            encontrado.set()
            resultado_queue.put(senha.decode("ascii"))
            return


def brute_force_parallel(hash_alvo: str, workers: int):
    hash_bytes = bytes.fromhex(hash_alvo)
    total = 10 ** DIGITOS

    inicio = time.perf_counter()
    resultado_queue = Queue()
    encontrado = Event()

    base = total // workers
    resto = total % workers

    blocos = []
    inicio_bloco = 0

    for i in range(workers):
        tamanho = base + (1 if i < resto else 0)
        fim_bloco = inicio_bloco + tamanho
        blocos.append((inicio_bloco, fim_bloco))
        inicio_bloco = fim_bloco

    processos = [
        Process(
            target=worker,
            args=(hash_bytes, inicio_faixa, fim_faixa, encontrado, resultado_queue),
        )
        for inicio_faixa, fim_faixa in blocos
    ]

    for p in processos:
        p.start()

    for p in processos:
        p.join()

    tempo_total = time.perf_counter() - inicio
    senha = resultado_queue.get() if not resultado_queue.empty() else None

    return senha, tempo_total


def main():
    parser = argparse.ArgumentParser(
        description="Brute force MD5 para senha numérica de 9 dígitos."
    )
    parser.add_argument(
        "--hash",
        required=True,
        dest="hash_alvo",
        help="Hash MD5 alvo (32 hex).",
    )

    args = parser.parse_args()

    print(f"\nHash alvo: {args.hash_alvo}")
    print("Dígitos fixos: 9\n")

    tempos = {}

    for workers in WORKERS_LIST:
        print(f"Executando com {workers} processos...")

        senha, tempo = brute_force_parallel(args.hash_alvo, workers)
        tempos[workers] = tempo

        if senha:
            print(f"Senha encontrada: {senha}")

        print(f"Tempo: {tempo:.6f} segundos\n")

    print("===== RESUMO FINAL =====")
    for workers in WORKERS_LIST:
        print(f"{workers} processos -> {tempos[workers]:.6f} segundos")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
