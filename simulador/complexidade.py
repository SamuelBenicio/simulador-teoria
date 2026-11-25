"""Módulo 6 - Complexidade Computacional.

Tabela dos algoritmos implementados (O, Ω, Θ) + benchmark empírico simples
para confirmar o crescimento observado.
"""
from __future__ import annotations

import time
from typing import Callable, List, Tuple

from .automato import AutomatoFinito
from .ap import AutomatoPilha
from .glc import GLC
from .turing import MaquinaTuring

# (algoritmo, melhor caso, caso médio, pior caso, justificativa)
TABELA = [
    ("Validar cadeia em Σ*",
     "Ω(1)", "Θ(n)", "O(n)",
     "Melhor caso: 1º símbolo já é inválido (para cedo). Caso geral: percorre os n símbolos com busca O(1) em conjunto hash."),
    ("Gerar Σ^k / Σ* até k",
     "Ω(|Σ|^k)", "Θ(|Σ|^k)", "O(k·|Σ|^k)",
     "Há |Σ|^k cadeias de tamanho k; montar cada uma custa O(k). Σ* até k soma ≈ |Σ|^(k+1)/(|Σ|-1)."),
    ("Tamanho e concatenação",
     "Ω(1)", "Θ(n+m)", "O(n+m)",
     "Tamanho em Python é O(1); concatenar copia as duas cadeias."),
    ("AFD - executar cadeia",
     "Ω(1)", "Θ(n)", "O(n)",
     "Melhor caso: transição indefinida no 1º símbolo. Senão 1 transição O(1) por símbolo."),
    ("AFN - simulação por conjuntos",
     "Ω(n)", "Θ(n·|Q|)", "O(n·|Q|²)",
     "A cada símbolo, move + λ-fecho sobre até |Q| estados, cada um com até |Q| destinos."),
    ("AFN → AFD (subconjuntos)",
     "Ω(|Q|·|Σ|)", "—", "O(2^|Q|·|Σ|·|Q|)",
     "Podem existir até 2^|Q| subconjuntos; exemplo clássico de explosão exponencial."),
    ("GLC - derivação (BFS esquerda + poda)",
     "Ω(n)", "depende da gramática", "O(|P|^n) (exponencial)",
     "S → aSb|λ gera ~n/2 formas: O(n²) com cópias. Gramáticas ambíguas podem explodir; CYK seria Θ(n³·|G|)."),
    ("AP - simulação (BFS de configurações)",
     "Ω(n)", "Θ(n) configurações", "O(n²) p/ aⁿbⁿ; exponencial em AP não determinístico geral",
     "aⁿbⁿ é determinístico: Θ(n) configurações, mas cada uma copia a pilha (string imutável, O(n)) => O(n²) no pior caso; com lista seria Θ(n). Em AP não determinístico o nº de configurações pode crescer exponencialmente (limitado por limite_pilha)."),
    ("MT - reconhecer w#w",
     "Ω(n)", "Θ(n²)", "O(n²)",
     "Entrada de tamanho n: rejeita após ~1 varredura quando o 1º símbolo de w difere (Ω(n)); aceitar exige conferir cada um dos n/2 símbolos, varrendo ~n células e voltando => Θ(n²)."),
    ("MT - soma unária",
     "Ω(n)", "Θ(n)", "O(n)",
     "Uma passada da esquerda para a direita (n+1 passos) mais volta de 1 célula e apagamento."),
]


def imprimir_tabela() -> str:
    linhas = []
    for alg, mc, cm, pc, just in TABELA:
        linhas.append(f"• {alg}\n    Melhor caso: {mc}    Caso médio: {cm}    Pior caso: {pc}\n    {just}")
    return "\n".join(linhas)


def _medir(func: Callable[[int], object], n: int, repeticoes: int = 3) -> float:
    melhor = float("inf")
    for _ in range(repeticoes):
        t0 = time.perf_counter()
        func(n)
        melhor = min(melhor, time.perf_counter() - t0)
    return melhor


def benchmark(tamanhos: Tuple[int, ...] = (50, 100, 200, 400)) -> str:
    """Mede tempo (em ms) de cada simulador com entradas crescentes e a razão t(2n)/t(n).

    Razão ≈ 2 indica crescimento linear, ≈ 4 quadrático.
    """
    afd = AutomatoFinito(["a"], ["q"], "q", ["q"], [("q", "a", "q")])
    ap = AutomatoPilha.an_bn()
    glc = GLC.de_texto("S -> aSb | λ")
    mt = MaquinaTuring.reconhecedor_w_hash_w()
    testes: List[Tuple[str, Callable[[int], object]]] = [
        ("AFD (a^n)", lambda n: afd.executar("a" * n)),
        ("AP  (a^n b^n)", lambda n: ap.executar("a" * n + "b" * n)),
        ("GLC (a^n b^n)", lambda n: glc.derivar("a" * n + "b" * n)),
        ("MT  (a^n # a^n)", lambda n: mt.executar("a" * n + "#" + "a" * n, registrar_passos=False)),
    ]
    linhas = [f"{'Algoritmo':<18}" + "".join(f"n={n:<10}" for n in tamanhos) + "razão t(2n)/t(n)"]
    for nome, f in testes:
        ts = [_medir(f, n) for n in tamanhos]
        razoes = [ts[i + 1] / ts[i] for i in range(len(ts) - 1) if ts[i] > 0]
        razao_media = sum(razoes) / len(razoes) if razoes else float("nan")
        linhas.append(f"{nome:<18}" + "".join(f"{t * 1000:<12.3f}" for t in ts) + f"{razao_media:.2f}")
    return "\n".join(linhas)
