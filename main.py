#!/usr/bin/env python3
"""Simulador de Linguagens Formais e Modelos Computacionais (interface de console).

Uso:
    python main.py                      # menu interativo
    python main.py demo                 # executa todos os exemplos do enunciado
    python main.py linguagem --alfabeto ab --cadeia abba
    python main.py af   --arquivo exemplos/afd_ab.json --cadeia ab
    python main.py glc  --arquivo exemplos/glc_anbn.txt --cadeia aaabbb
    python main.py ap   --cadeia aaabbb [--arquivo exemplos/ap_anbn.json]
    python main.py mt   --maquina w#w --cadeia ab#ab
    python main.py mt   --maquina soma --cadeia 000100
    python main.py complexidade [--benchmark]
"""
from __future__ import annotations

import argparse
import os
import sys

from simulador import LAMBDA
from simulador.ap import AutomatoPilha
from simulador.automato import AutomatoFinito
from simulador.complexidade import benchmark, imprimir_tabela
from simulador.glc import GLC, arvore_ascii
from simulador.linguagens import (Alfabeto, Linguagem, analisar_cadeia, concatenar, tamanho)
from simulador.turing import MaquinaTuring

AQUI = os.path.dirname(os.path.abspath(__file__))
EX = lambda nome: os.path.join(AQUI, "exemplos", nome)


def titulo(texto: str) -> None:
    print("\n" + "=" * 62)
    print(texto)
    print("=" * 62)


# ------------------------------------------------------------------ módulos
def mod_linguagem(alfabeto: str, cadeia: str, outra: str | None = None, k: int = 3) -> None:
    sigma = Alfabeto(alfabeto.replace(",", "").replace(" ", ""))
    print(sigma)
    print(analisar_cadeia(sigma, cadeia))
    print("Σ* (até tamanho %d): {%s}" % (k, ", ".join(c or LAMBDA for c in sigma.sigma_estrela(k))))
    print("Σ+ (até tamanho %d): {%s}" % (k, ", ".join(sigma.sigma_mais(k))))
    if outra is not None:
        print(f"Concatenação: {cadeia} · {outra} = {concatenar(cadeia, outra)}")
        print(f"|{cadeia}·{outra}| = {tamanho(concatenar(cadeia, outra))}")


def mod_af(arquivo: str, cadeia: str) -> None:
    af = AutomatoFinito.de_json(arquivo)
    print(af.descricao())
    print(f"Entrada: {cadeia or LAMBDA}")
    print(af.executar(cadeia).formatar())


def mod_glc(arquivo: str, cadeia: str) -> None:
    g = GLC.de_arquivo(arquivo)
    print(g.descricao())
    print(f"Entrada: {cadeia or LAMBDA}")
    r = g.derivar(cadeia)
    print(r.formatar())
    if r.aceita:
        print("\nÁrvore de derivação:")
        print(arvore_ascii(r.arvore))
    print(f"\n(formas sentenciais exploradas: {r.estados_explorados})")


def mod_ap(cadeia: str, arquivo: str | None = None) -> None:
    ap = AutomatoPilha.de_json(arquivo) if arquivo else AutomatoPilha.an_bn()
    print("AP para L = { aⁿbⁿ | n ≥ 1 }" if not arquivo else f"AP carregado de {arquivo}")
    print(f"Entrada: {cadeia or LAMBDA}")
    print(ap.executar(cadeia).formatar())


def mod_mt(maquina: str, cadeia: str, silencioso: bool = False) -> None:
    if maquina in ("w#w", "a"):
        mt = MaquinaTuring.reconhecedor_w_hash_w()
        print("Máquina de Turing - Opção A: L = { w#w | w ∈ {a,b}* }")
    elif maquina in ("soma", "b"):
        mt = MaquinaTuring.somador_unario()
        print("Máquina de Turing - Opção B: soma unária (n zeros, 1, m zeros)")
    else:
        mt = MaquinaTuring.de_json(maquina)
        print(f"Máquina de Turing carregada de {maquina}")
    print(f"Entrada: {cadeia}")
    r = mt.executar(cadeia)
    print(r.formatar(mostrar_passos=not silencioso))
    if maquina in ("soma", "b") and r.aceita:
        n, m = cadeia.split("1")[0].count("0"), cadeia.split("1")[-1].count("0")
        print(f"Resultado: {r.fita_final}  ({n} + {m} = {len(r.fita_final)} em unário)")


def mod_complexidade(com_benchmark: bool) -> None:
    print(imprimir_tabela())
    if com_benchmark:
        print("\nBenchmark empírico (tempo em ms):")
        print(benchmark())


# ------------------------------------------------------------------ demo
def demo() -> None:
    titulo("MÓDULO 1 - LINGUAGENS FORMAIS  (Σ = {a,b}, entrada: abba)")
    mod_linguagem("ab", "abba", "ba", k=2)
    L = Linguagem(Alfabeto("ab"), predicado=lambda w: w == "a" * (len(w) // 2) + "b" * (len(w) // 2) and len(w) % 2 == 0,
                  nome="L = {aⁿbⁿ}")
    print(f"{L.nome}: cadeias até tamanho 6 -> {L.enumerar(6)}")

    titulo("MÓDULO 2 - AUTÔMATO FINITO  (AFD carregado de JSON, entrada: ab)")
    mod_af(EX("afd_ab.json"), "ab")
    titulo("MÓDULO 2 - AFN (termina com 'ab'), entrada: abbab")
    mod_af(EX("afn_termina_ab.json"), "abbab")
    titulo("MÓDULO 2 - AFN com transições λ, entrada: aaa")
    mod_af(EX("afn_lambda.json"), "aaa")

    titulo("MÓDULO 3 - GLC  S -> aSb | λ   (entrada: aaabbb)")
    mod_glc(EX("glc_anbn.txt"), "aaabbb")

    titulo("MÓDULO 4 - AUTÔMATO COM PILHA  (entrada: aaabbb)")
    mod_ap("aaabbb")

    titulo("MÓDULO 5A - MÁQUINA DE TURING  w#w  (entrada: ab#ab)")
    mod_mt("w#w", "ab#ab")
    titulo("MÓDULO 5B - MÁQUINA DE TURING  soma unária  (000100 = 3 + 2)")
    mod_mt("soma", "000100")

    titulo("MÓDULO 6 - COMPLEXIDADE COMPUTACIONAL")
    mod_complexidade(com_benchmark=True)


# ------------------------------------------------------------------ menu
def ler(msg: str, padrao: str = "") -> str:
    try:
        v = input(msg).strip()
    except EOFError:
        sys.exit(0)
    return v or padrao


def menu() -> None:
    while True:
        print("\n===== SIMULADOR DE TEORIA DA COMPUTAÇÃO =====")
        print("1) Linguagens formais     4) Autômato com pilha")
        print("2) Autômato finito (JSON) 5) Máquina de Turing")
        print("3) Gramática livre de contexto   6) Complexidade")
        print("7) Demonstração completa  0) Sair")
        op = ler("Escolha: ")
        try:
            if op == "1":
                mod_linguagem(ler("Alfabeto (ex.: ab): "), ler("Cadeia: "), ler("Cadeia p/ concatenar (opcional): ") or None)
            elif op == "2":
                arq = ler("Arquivo JSON [exemplos/afd_ab.json]: ", EX("afd_ab.json"))
                mod_af(arq, ler("Cadeia: "))
            elif op == "3":
                arq = ler("Arquivo da gramática [exemplos/glc_anbn.txt]: ", EX("glc_anbn.txt"))
                mod_glc(arq, ler("Cadeia: "))
            elif op == "4":
                arq = ler("Arquivo JSON [Enter p/ padrão aⁿbⁿ]: ") or None
                mod_ap(ler("Cadeia (aⁿbⁿ): "), arq)
            elif op == "5":
                m = ler("Máquina (w#w / soma): ", "w#w")
                mod_mt(m, ler("Entrada: "))
            elif op == "6":
                mod_complexidade(ler("Rodar benchmark? (s/N): ").lower() == "s")
            elif op == "7":
                demo()
            elif op == "0":
                return
            else:
                print("Opção inválida.")
        except (ValueError, OSError, KeyError) as e:
            print(f"Erro: {e}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Simulador de Linguagens Formais e Modelos Computacionais")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("demo", help="executa todos os exemplos")
    s = sub.add_parser("linguagem"); s.add_argument("--alfabeto", required=True); s.add_argument("--cadeia", default="")
    s.add_argument("--concatenar"); s.add_argument("-k", type=int, default=3)
    s = sub.add_parser("af"); s.add_argument("--arquivo", default=EX("afd_ab.json")); s.add_argument("--cadeia", default="")
    s = sub.add_parser("glc"); s.add_argument("--arquivo", default=EX("glc_anbn.txt")); s.add_argument("--cadeia", default="")
    s = sub.add_parser("ap"); s.add_argument("--arquivo"); s.add_argument("--cadeia", default="")
    s = sub.add_parser("mt"); s.add_argument("--maquina", default="w#w"); s.add_argument("--cadeia", default="")
    s.add_argument("--resumo", action="store_true", help="não imprime cada passo")
    s = sub.add_parser("complexidade"); s.add_argument("--benchmark", action="store_true")
    a = p.parse_args(argv)

    try:
        if a.cmd is None:
            menu()
        elif a.cmd == "demo":
            demo()
        elif a.cmd == "linguagem":
            mod_linguagem(a.alfabeto, a.cadeia, a.concatenar, a.k)
        elif a.cmd == "af":
            mod_af(a.arquivo, a.cadeia)
        elif a.cmd == "glc":
            mod_glc(a.arquivo, a.cadeia)
        elif a.cmd == "ap":
            mod_ap(a.cadeia, a.arquivo)
        elif a.cmd == "mt":
            mod_mt(a.maquina, a.cadeia, a.resumo)
        elif a.cmd == "complexidade":
            mod_complexidade(a.benchmark)
    except (ValueError, OSError, KeyError) as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
