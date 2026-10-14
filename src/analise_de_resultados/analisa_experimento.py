"""
Análise do experimento paralelo (com rotação x sem rotação).

Uso (da raiz do repositório):
  python src/analise_de_resultados/analisa_experimento.py results/outubro/<pasta do experimento>

Lê resultados.csv e imprime/salva (analise.md na mesma pasta):
  1. Auditoria: execuções com erro, não validadas, que atingiram o limite de tempo
  2. Tabela por instância: L médio (e desvio, se houver várias sementes) das duas versões
  3. Vitórias / empates / derrotas e teste de Wilcoxon pareado (L médio por instância)
  4. Uso de rotação: em quantas instâncias houve rotação e proporção de itens rotacionados
  5. Tempo médio por versão (ATENÇÃO: tempos medidos em paralelo; ver docs/protocolo-experimental.md)
Não depende de pandas. scipy é opcional (sem ele, usa teste do sinal exato).
"""
import csv
import math
import os
import statistics as st
import sys
from collections import defaultdict


def carregar(pasta):
    with open(os.path.join(pasta, "resultados.csv"), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def media_dp(xs):
    return (st.mean(xs), st.stdev(xs) if len(xs) > 1 else 0.0)


def teste_sinal(a, b):
    """Teste do sinal exato bilateral (fallback sem scipy). Retorna p-valor."""
    d = [x - y for x, y in zip(a, b) if x != y]
    n = len(d)
    if n == 0:
        return 1.0
    k = min(sum(1 for x in d if x > 0), sum(1 for x in d if x < 0))
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n * 2
    return min(1.0, p)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    pasta = sys.argv[1]
    linhas = carregar(pasta)
    out = []
    P = out.append

    ok = [r for r in linhas if not r["erro"]]
    P(f"# Análise do experimento: {os.path.basename(os.path.normpath(pasta))}\n")
    P("## 1. Auditoria\n")
    P(f"- Execuções registradas: {len(linhas)} | com erro: {len(linhas) - len(ok)}")
    nv = [r for r in ok if r["validado"] != "Sim"]
    P(f"- Execuções NÃO validadas (sobreposição/fora da faixa/fallback): {len(nv)}")
    for r in nv[:20]:
        P(f"    - {r['versao']} {r['instancia']} s={r['semente']}: fora={r['fora_da_faixa']} "
          f"pares={r['pares_sobrepostos']} fallbacks={r['fallbacks']} "
          f"empacotados={r['itens_empacotados']}/{r['itens_total']}")
    lim = [r for r in ok if r["limite_atingido"] == "Sim"]
    P(f"- Execuções que atingiram o limite de tempo: {len(lim)}")
    inst_lim = sorted({r["instancia"] for r in lim})
    P(f"- Instâncias com pelo menos uma execução cortada: {', '.join(inst_lim) or 'nenhuma'}\n")

    L = defaultdict(lambda: defaultdict(list))
    T = defaultdict(lambda: defaultdict(list))
    ROT = defaultdict(lambda: defaultdict(list))
    for r in ok:
        L[r["instancia"]][r["versao"]].append(float(r["L"]))
        T[r["instancia"]][r["versao"]].append(float(r["tempo_s"]))
        ROT[r["instancia"]][r["versao"]].append(
            (r["houve_rotacao"] == "Sim", int(r["itens_rotacionados"]), int(r["itens_total"])))

    insts = sorted(i for i in L if "com_rotacao" in L[i] and "sem_rotacao" in L[i])
    P("## 2. L por instância (média ± desvio entre sementes)\n")
    P(f"{'instância':14s} {'n':>3s} {'sem rotação':>16s} {'com rotação':>16s} {'diferença':>10s} {'rot.':>6s} {'cortada':>8s}")
    medias = {}
    for i in insts:
        ms, ds = media_dp(L[i]["sem_rotacao"])
        mc, dc = media_dp(L[i]["com_rotacao"])
        medias[i] = (ms, mc)
        rot = sum(x[1] for x in ROT[i]["com_rotacao"]) / max(1, sum(x[2] for x in ROT[i]["com_rotacao"]))
        corte = "sim" if i in inst_lim else ""
        P(f"{i:14s} {len(L[i]['com_rotacao']):3d} {ms:9.2f}±{ds:5.2f} {mc:9.2f}±{dc:5.2f} {mc - ms:+10.2f} {rot*100:5.0f}% {corte:>8s}")

    def resumo(nomes, titulo):
        a = [medias[i][0] for i in nomes]  # sem rotação
        b = [medias[i][1] for i in nomes]  # com rotação
        v = sum(1 for x, y in zip(a, b) if y < x)
        e = sum(1 for x, y in zip(a, b) if y == x)
        d = sum(1 for x, y in zip(a, b) if y > x)
        P(f"\n{titulo} ({len(nomes)} instâncias): com rotação melhor em {v}, empate em {e}, pior em {d}")
        if len(nomes) >= 5 and v + d > 0:
            try:
                from scipy.stats import wilcoxon
                p = wilcoxon(a, b, zero_method="wilcox").pvalue
                nome = "Wilcoxon pareado"
            except Exception:
                p = teste_sinal(a, b)
                nome = "teste do sinal exato"
            P(f"  {nome}: p = {p:.4f}   (L médio sem rotação = {st.mean(a):.2f}, com rotação = {st.mean(b):.2f})")

    P("\n## 3. Comparação (menor L é melhor)")
    resumo(insts, "Todas as instâncias")
    sem_corte = [i for i in insts if i not in inst_lim]
    if len(sem_corte) != len(insts):
        resumo(sem_corte, "Somente instâncias que terminaram o resfriamento (sem corte por tempo)")

    P("\n## 4. Uso de rotação (versão com rotação)\n")
    com_rot = [i for i in insts if any(x[0] for x in ROT[i]["com_rotacao"])]
    P(f"- Instâncias em que houve rotação em alguma execução: {len(com_rot)}/{len(insts)}")
    perm = {r["instancia"]: r["rotacoes_permitidas"] for r in ok if r["versao"] == "com_rotacao"}
    sem_perm = [i for i in insts if perm.get(i, "0") == "0"]
    P(f"- Instâncias que só permitem 0 grau (rotação impossível): {len(sem_perm)}: {', '.join(sem_perm) or '-'}")

    P("\n## 5. Tempo médio por execução (s) — medido em paralelo\n")
    for v in ("sem_rotacao", "com_rotacao"):
        xs = [x for i in insts for x in T[i][v]]
        P(f"- {v}: média {st.mean(xs):.1f} s | soma {sum(xs)/3600:.2f} h de relógio por processo")

    txt = "\n".join(out)
    print(txt)
    with open(os.path.join(pasta, "analise.md"), "w", encoding="utf-8") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()
