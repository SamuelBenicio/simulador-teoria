"""Módulo 1 - Linguagens Formais.

Alfabeto (Σ), cadeias, Σ*, Σ+, tamanho, concatenação e linguagens.
"""
from __future__ import annotations

from itertools import product
from typing import Callable, Iterable, Iterator, Optional, Set

from . import LAMBDA


class Alfabeto:
    """Conjunto finito, não vazio, de símbolos (cada símbolo é 1 caractere)."""

    def __init__(self, simbolos: Iterable[str]):
        conjunto = set(simbolos)
        if not conjunto:
            raise ValueError("O alfabeto não pode ser vazio.")
        for s in conjunto:
            if len(s) != 1:
                raise ValueError(f"Símbolo inválido {s!r}: use apenas 1 caractere.")
        self.simbolos = frozenset(conjunto)

    def __contains__(self, simbolo: str) -> bool:
        return simbolo in self.simbolos

    def __repr__(self) -> str:
        return "Σ = {" + ", ".join(sorted(self.simbolos)) + "}"

    # ---- validação ----------------------------------------------------
    def valida(self, cadeia: str) -> bool:
        """Cadeia pertence a Σ*? Complexidade: O(n), n = |cadeia|."""
        return all(c in self.simbolos for c in cadeia)

    def simbolos_invalidos(self, cadeia: str) -> list[str]:
        return sorted({c for c in cadeia if c not in self.simbolos})

    # ---- Σ* e Σ+ (geração por comprimento) ----------------------------
    def cadeias_de_tamanho(self, n: int) -> Iterator[str]:
        """Todas as cadeias de comprimento n: |Σ|^n cadeias."""
        if n < 0:
            raise ValueError("n deve ser >= 0")
        ordenados = sorted(self.simbolos)
        for tupla in product(ordenados, repeat=n):
            yield "".join(tupla)

    def sigma_estrela(self, max_tamanho: int) -> Iterator[str]:
        """Σ* limitado a |w| <= max_tamanho (Σ* é infinito), em ordem canônica."""
        for n in range(0, max_tamanho + 1):
            yield from self.cadeias_de_tamanho(n)

    def sigma_mais(self, max_tamanho: int) -> Iterator[str]:
        """Σ+ = Σ* - {λ}, limitado a |w| <= max_tamanho."""
        for n in range(1, max_tamanho + 1):
            yield from self.cadeias_de_tamanho(n)


def tamanho(cadeia: str) -> int:
    """|w|. A cadeia vazia (λ) tem tamanho 0."""
    return 0 if cadeia == LAMBDA else len(cadeia)


def concatenar(u: str, v: str) -> str:
    """u·v. λ é o elemento neutro da concatenação."""
    u = "" if u == LAMBDA else u
    v = "" if v == LAMBDA else v
    r = u + v
    return r if r else LAMBDA


def potencia(w: str, n: int) -> str:
    """w^n (w concatenada n vezes)."""
    if n < 0:
        raise ValueError("n deve ser >= 0")
    base = "" if w == LAMBDA else w
    return concatenar("", base * n) if n > 0 else LAMBDA


def inversa(w: str) -> str:
    """w^R (reverso)."""
    return w[::-1] if w and w != LAMBDA else LAMBDA


class Linguagem:
    """Linguagem L ⊆ Σ*, definida por enumeração finita ou por predicado.

    Exemplos:
        Linguagem(sigma, cadeias={"a", "ab"})
        Linguagem(sigma, predicado=lambda w: w == "a"*(len(w)//2) + "b"*(len(w)//2), nome="aⁿbⁿ")
    """

    def __init__(
        self,
        alfabeto: Alfabeto,
        cadeias: Optional[Set[str]] = None,
        predicado: Optional[Callable[[str], bool]] = None,
        nome: str = "L",
    ):
        if cadeias is None and predicado is None:
            raise ValueError("Informe 'cadeias' (finita) ou 'predicado'.")
        self.alfabeto = alfabeto
        self.nome = nome
        self.cadeias = None if cadeias is None else {("" if c == LAMBDA else c) for c in cadeias}
        self.predicado = predicado
        if self.cadeias is not None:
            for c in self.cadeias:
                if not alfabeto.valida(c):
                    raise ValueError(f"Cadeia {c!r} não pertence a Σ*.")

    def pertence(self, cadeia: str) -> bool:
        w = "" if cadeia == LAMBDA else cadeia
        if not self.alfabeto.valida(w):
            return False
        if self.cadeias is not None:
            return w in self.cadeias
        return bool(self.predicado(w))

    def enumerar(self, max_tamanho: int) -> list[str]:
        """Cadeias de L com |w| <= max_tamanho, em ordem canônica."""
        if self.cadeias is not None:
            achadas = [c for c in self.cadeias if len(c) <= max_tamanho]
            return sorted((c if c else LAMBDA for c in achadas), key=lambda x: (tamanho(x), x))
        return [(w if w else LAMBDA) for w in self.alfabeto.sigma_estrela(max_tamanho) if self.predicado(w)]

    # ---- operações sobre linguagens ----------------------------------
    def concatenacao(self, outra: "Linguagem", max_tamanho: int) -> list[str]:
        """L1·L2 = { uv | u ∈ L1, v ∈ L2 }, truncada em max_tamanho."""
        res = set()
        for u in self.enumerar(max_tamanho):
            for v in outra.enumerar(max_tamanho):
                w = concatenar(u, v)
                if tamanho(w) <= max_tamanho:
                    res.add(w)
        return sorted(res, key=lambda x: (tamanho(x), x))

    def uniao(self, outra: "Linguagem", max_tamanho: int) -> list[str]:
        return sorted(set(self.enumerar(max_tamanho)) | set(outra.enumerar(max_tamanho)),
                      key=lambda x: (tamanho(x), x))

    def __repr__(self) -> str:
        return f"{self.nome} ⊆ Σ*"


def analisar_cadeia(alfabeto: Alfabeto, cadeia: str) -> str:
    """Saída no formato do enunciado (validação + tamanho)."""
    if alfabeto.valida(cadeia):
        return f"Cadeia válida para Σ\nTamanho = {tamanho(cadeia)}"
    inv = ", ".join(alfabeto.simbolos_invalidos(cadeia))
    return f"Cadeia INVÁLIDA para Σ (símbolos fora do alfabeto: {inv})"
