"""
Experimento paralelo: strip packing de itens irregulares COM e SEM rotação.

Roda, no mesmo lote e sob as mesmas condições, as duas versões
  - strip_packing_rotacao_interna.py  (versao "com_rotacao")
  - strip_packing_sem_rotacao.py      (versao "sem_rotacao")
sobre as instâncias de data/STRIP (ou outra pasta), com semente fixa por execução.

Cada tarefa = (versão, instância, semente) roda em UM processo. Só o processo principal
escreve no arquivo de resultados (resultados.csv), então as linhas nunca se misturam.
O CSV é escrito a cada tarefa concluída: se a máquina cair, basta rodar de novo com a
mesma --saida e as tarefas já feitas são puladas.

Ao final de cada execução o leiaute é VALIDADO com geometria exata dos polígonos
(sem usar as matrizes NFP): peças fora da faixa e pares sobrepostos.

Exemplos (a partir da raiz do repositório):
  # Rodada A: todas as instâncias, as duas versões, 1 semente, 3 processos
  python src/rodar_experimento_paralelo.py --processos 3 --sementes 42

  # Rodada B: subconjunto com 10 sementes
  python src/rodar_experimento_paralelo.py --processos 3 --sementes 42-51 \
      --instancias blazewicz2,blazewicz3,dagli1,fu,fu8,jakobs1,poly1a,poly1c,rco2,rco3,shapes4,shapes5,shirts2-4,shirts3-6

  # Rodada C (tempo): um processo por vez, para medir tempo sem disputa de núcleos
  python src/rodar_experimento_paralelo.py --processos 1 --sementes 42 --instancias fu5,fu8,rco2,poly1a --saida results/outubro/RodadaC_tempo
"""
import argparse
import contextlib
import csv
import importlib
import io
import json
import os
import platform
import random
import subprocess
import sys
import time
from datetime import datetime
from multiprocessing import Pool

import numpy as np

SRC = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(SRC)
sys.path.insert(0, SRC)

MODULOS = {
    "com_rotacao": "strip_packing_rotacao_interna",
    "sem_rotacao": "strip_packing_sem_rotacao",
}

CAMPOS = [
    "versao", "instancia", "semente", "L", "ocupacao_pct", "itens_empacotados", "itens_total",
    "houve_rotacao", "itens_rotacionados", "por_angulo", "rotacoes_permitidas",
    "tempo_s", "cpu_s", "limite_atingido", "fallbacks",
    "validado", "fora_da_faixa", "pares_sobrepostos", "erro",
]


# ----------------------------------------------------------------------------
# Validação geométrica independente (não usa NFP)
# ----------------------------------------------------------------------------
def _poligono_final(item, angulo, x, y, m):
    """Mesma transformação usada no plot: rotaciona, alinha ao (0,0) e translada para (x, y)."""
    v = [m.rotacionar_ponto(a, b, angulo) for a, b in item.vertices]
    mx = min(a for a, _ in v)
    my = min(b for _, b in v)
    return np.array([(a - mx + x, b - my + y) for a, b in v], dtype=float)


def _pontos_dentro(poly, P):
    """Ponto-dentro-de-polígono (crossing number), vetorizado; funciona para polígonos não convexos."""
    x, y = P[:, 0], P[:, 1]
    dentro = np.zeros(len(P), dtype=bool)
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        cruza = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-300) + x1)
        dentro ^= cruza
    return dentro


def _sobrepoe(A, B, passo=0.25):
    lo = np.maximum(A.min(0), B.min(0))
    hi = np.minimum(A.max(0), B.max(0))
    if (hi <= lo).any():
        return False
    # deslocamento irracional pequeno evita cair exatamente sobre arestas/vértices inteiros
    xs = np.arange(lo[0] + passo / 2 + 0.0123, hi[0], passo)
    ys = np.arange(lo[1] + passo / 2 + 0.0123, hi[1], passo)
    if len(xs) == 0 or len(ys) == 0:
        return False
    P = np.array([(a, b) for a in xs for b in ys])
    return bool((_pontos_dentro(A, P) & _pontos_dentro(B, P)).any())


def validar_leiaute(placed, itens_por_id, largura, comprimento, m):
    polys = []
    for p in placed:
        it = itens_por_id[p["id"]]
        polys.append(_poligono_final(it, it.rotacoes[p["rot"]], p["x"], p["y"], m))
    fora = sum(
        1 for P in polys
        if P[:, 1].min() < -1e-6 or P[:, 1].max() > largura + 1e-6
        or P[:, 0].min() < -1e-6 or P[:, 0].max() > comprimento + 1e-6
    )
    pares = 0
    for i in range(len(polys)):
        for j in range(i + 1, len(polys)):
            if _sobrepoe(polys[i], polys[j]):
                pares += 1
    return fora, pares


# ----------------------------------------------------------------------------
# Tarefa (executada em um processo worker)
# ----------------------------------------------------------------------------
def executar_tarefa(tarefa):
    versao, nome, semente, cfg = tarefa
    linha = {c: "" for c in CAMPOS}
    linha.update(versao=versao, instancia=nome, semente=semente)
    log = io.StringIO()
    try:
        m = importlib.import_module(MODULOS[versao])
        with contextlib.redirect_stdout(log):
            dados = m.read_modular_instance(os.path.join(cfg["dados"], nome))
            if not dados:
                raise RuntimeError("falha na leitura da instância")

            itens = [
                m.Item(p["id"], p["demand"], p["rotations"], p["rfr_matrices"], p["vertices"])
                for p in dados["pieces"]
            ]
            b = dados["bins"][0]
            inst = m.Instance(nome, int(b["H"]), b["matrix"], itens, dados["nfp"])
            pecas = [it for it in itens for _ in range(it.demanda)]
            inst.items = pecas
            area_total = sum(it.area for it in pecas)

            random.seed(semente)
            t0_wall, t0_cpu = time.time(), time.process_time()
            ordem, L, limite = m.recozimento_simulado(
                inst, t0=cfg["t0"], alpha=cfg["alpha"], iter_max=cfg["iter_max"],
                limite_tempo=cfg["limite"])
            log.truncate(0)  # só interessa o que o BL final imprime (contagem de fallback)
            log.seek(0)
            _, placed, _ = m.bottom_left_placement(ordem, inst)
            tempo, cpu = time.time() - t0_wall, time.process_time() - t0_cpu

        fallbacks = log.getvalue().count("REJEITADA")
        itens_por_id = {it.id: it for it in itens}
        q, por_angulo = m.resumo_rotacoes(placed, itens)
        permitidas = sorted({int(r) for it in itens for r in it.rotacoes})
        fora, pares = validar_leiaute(placed, itens_por_id, inst.w, L, m)
        ocupacao = area_total / (inst.w * L) * 100 if L > 0 else 0.0

        if cfg["imagens"]:
            pasta_img = os.path.join(cfg["saida"], "imagens", versao)
            os.makedirs(pasta_img, exist_ok=True)
            with contextlib.redirect_stdout(io.StringIO()):
                m.plot_solution(inst.w, L, placed, itens, 1.0, nome,
                                os.path.join(pasta_img, f"layout_{nome}_s{semente}.png"),
                                ocupacao, len(pecas), q)

        linha.update(
            L=L, ocupacao_pct=f"{ocupacao:.2f}", itens_empacotados=len(placed), itens_total=len(pecas),
            houve_rotacao="Sim" if q > 0 else "Nao", itens_rotacionados=q,
            por_angulo=";".join(f"{a}:{n}" for a, n in por_angulo.items()),
            rotacoes_permitidas=";".join(str(a) for a in permitidas),
            tempo_s=f"{tempo:.2f}", cpu_s=f"{cpu:.2f}",
            limite_atingido="Sim" if limite else "Nao", fallbacks=fallbacks,
            validado="Sim" if (fora == 0 and pares == 0 and fallbacks == 0 and len(placed) == len(pecas)) else "NAO",
            fora_da_faixa=fora, pares_sobrepostos=pares,
        )
    except (Exception, SystemExit) as e:
        linha["erro"] = repr(e)[:200]
        linha["validado"] = "NAO"
    return linha


# ----------------------------------------------------------------------------
# Processo principal
# ----------------------------------------------------------------------------
def parse_sementes(txt):
    if "-" in txt and "," not in txt:
        a, b = txt.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in txt.split(",")]


def instancias_validas(pasta):
    return sorted(
        d for d in os.listdir(pasta)
        if os.path.isdir(os.path.join(pasta, d, "items")) and os.listdir(os.path.join(pasta, d, "items"))
    )


def custo_estimado(nome, pasta_dados):
    """Para ordenar as tarefas das mais longas para as mais curtas (melhor balanceamento)."""
    ref = os.path.join(RAIZ, "results", "agosto", "ExperimentoFinal", "resultados.txt")
    if os.path.isfile(ref):
        with open(ref, encoding="utf-8") as f:
            for linha in f:
                if linha.startswith(nome + ":"):
                    try:
                        return float(linha.split("Tempo=")[1].rstrip("s\n"))
                    except (IndexError, ValueError):
                        pass
    try:
        return float(len(os.listdir(os.path.join(pasta_dados, nome, "nfr"))))
    except OSError:
        return 0.0


def info_ambiente(args, n_tarefas):
    try:
        commit = subprocess.check_output(["git", "-C", RAIZ, "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit = "desconhecido"
    return {
        "inicio": datetime.now().isoformat(timespec="seconds"),
        "commit": commit,
        "python": platform.python_version(),
        "sistema": platform.platform(),
        "processador": platform.processor(),
        "nucleos_logicos": os.cpu_count(),
        "processos_usados": args.processos,
        "parametros_rs": {"t0": args.t0, "alpha": args.alpha, "iter_max": args.iter_max},
        "limite_tempo_s": args.limite,
        "sementes": parse_sementes(args.sementes),
        "versoes": args.versoes.split(","),
        "pasta_dados": args.dados,
        "n_tarefas": n_tarefas,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dados", default=os.path.join(RAIZ, "data", "STRIP"))
    ap.add_argument("--instancias", default="todas", help="lista separada por vírgula, ou 'todas'")
    ap.add_argument("--versoes", default="com_rotacao,sem_rotacao")
    ap.add_argument("--sementes", default="42", help="ex.: 42  |  42,43,44  |  42-51")
    ap.add_argument("--processos", type=int, default=3)
    ap.add_argument("--limite", type=float, default=3600, help="limite de tempo do RS por execução (s)")
    ap.add_argument("--t0", type=float, default=100)
    ap.add_argument("--alpha", type=float, default=0.9)
    ap.add_argument("--iter-max", dest="iter_max", type=int, default=300)
    ap.add_argument("--saida", default=None, help="pasta de saída (reutilize para retomar)")
    ap.add_argument("--sem-imagens", action="store_true")
    args = ap.parse_args()

    validas = instancias_validas(args.dados)
    nomes = validas if args.instancias == "todas" else args.instancias.split(",")
    faltando = [n for n in nomes if n not in validas]
    if faltando:
        sys.exit(f"Instâncias inexistentes/inválidas em {args.dados}: {faltando}")

    saida = args.saida or os.path.join(
        RAIZ, "results", "outubro", f"Experimento_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(saida, exist_ok=True)
    csv_path = os.path.join(saida, "resultados.csv")

    feitas = set()
    if os.path.isfile(csv_path):
        with open(csv_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if not r["erro"]:
                    feitas.add((r["versao"], r["instancia"], int(r["semente"])))
        print(f"Retomando: {len(feitas)} tarefas já concluídas em {csv_path}")

    sementes = parse_sementes(args.sementes)
    ordem_inst = sorted(nomes, key=lambda n: -custo_estimado(n, args.dados))
    cfg = {"dados": args.dados, "t0": args.t0, "alpha": args.alpha, "iter_max": args.iter_max,
           "limite": args.limite, "saida": saida, "imagens": not args.sem_imagens}
    tarefas = []
    for n in ordem_inst:               # as duas versões da mesma instância ficam adjacentes
        for s in sementes:
            for v in args.versoes.split(","):
                if (v, n, s) not in feitas:
                    tarefas.append((v, n, s, cfg))

    info = info_ambiente(args, len(tarefas))
    nome_amb = "ambiente.json"
    if os.path.isfile(os.path.join(saida, nome_amb)):  # retomada: preserva o registro original
        nome_amb = f"ambiente_retomada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(os.path.join(saida, nome_amb), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

    print(f"{len(tarefas)} tarefas | {args.processos} processos | limite {args.limite:.0f}s | saída: {saida}")
    novo = not os.path.isfile(csv_path)
    inicio = time.time()
    with open(csv_path, "a", newline="", encoding="utf-8") as f, Pool(args.processos, maxtasksperchild=1) as pool:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        if novo:
            w.writeheader()
        for k, r in enumerate(pool.imap_unordered(executar_tarefa, tarefas, chunksize=1), 1):
            w.writerow(r)
            f.flush()
            os.fsync(f.fileno())
            marca = "OK " if r["validado"] == "Sim" else "!! "
            print(f"[{k}/{len(tarefas)}] {marca}{r['versao']:11s} {r['instancia']:12s} s={r['semente']} "
                  f"L={r['L']} rot={r['houve_rotacao']} t={r['tempo_s']}s "
                  f"lim={r['limite_atingido']} {r['erro']}", flush=True)
    print(f"Concluído em {(time.time() - inicio) / 3600:.2f} h. Resultados: {csv_path}")


if __name__ == "__main__":
    main()
