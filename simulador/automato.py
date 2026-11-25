"""Módulo 2 - Autômatos Finitos (AFD e AFN, com transições λ).

Formato JSON aceito:
{
  "tipo": "AFD" | "AFN",              (opcional; é inferido se omitido)
  "alfabeto": ["a", "b"],
  "estados": ["q0", "q1", "q2"],
  "inicial": "q0",
  "finais": ["q2"],
  "transicoes": [ {"de": "q0", "le": "a", "para": "q1"}, ... ]   # "le": "λ" = movimento vazio
}
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

from . import LAMBDA, eh_vazio


@dataclass
class ResultadoAF:
    aceita: bool
    passos: List[str] = field(default_factory=list)     # descrição de cada passo
    caminho: List[str] = field(default_factory=list)    # sequência de estados (um caminho aceitador ou o único)
    motivo: str = ""

    def formatar(self) -> str:
        linhas = list(self.passos)
        if self.caminho:
            linhas.append(" -> ".join(self.caminho))
        linhas.append("ACEITA" if self.aceita else f"REJEITA ({self.motivo})")
        return "\n".join(linhas)


class AutomatoFinito:
    def __init__(self, alfabeto: Iterable[str], estados: Iterable[str], inicial: str,
                 finais: Iterable[str], transicoes: Iterable[Tuple[str, str, str]]):
        self.alfabeto = set(alfabeto)
        self.estados = set(estados)
        self.inicial = inicial
        self.finais = set(finais)
        # delta[(estado, simbolo)] -> conjunto de destinos ; símbolo vazio = LAMBDA
        self.delta: Dict[Tuple[str, str], Set[str]] = {}
        for de, le, para in transicoes:
            le = LAMBDA if eh_vazio(le) else le
            self.delta.setdefault((de, le), set()).add(para)
        self._validar()

    # ---------------------------------------------------------------- validação
    def _validar(self) -> None:
        if self.inicial not in self.estados:
            raise ValueError(f"Estado inicial {self.inicial!r} não está em Q.")
        if not self.finais <= self.estados:
            raise ValueError("Há estados finais que não pertencem a Q.")
        for (de, le), destinos in self.delta.items():
            if de not in self.estados or not destinos <= self.estados:
                raise ValueError(f"Transição com estado desconhecido: {de!r} -{le}-> {destinos}")
            if le != LAMBDA and le not in self.alfabeto:
                raise ValueError(f"Símbolo {le!r} de transição não está no alfabeto.")

    @property
    def eh_deterministico(self) -> bool:
        """AFD: sem λ-transições e no máximo 1 destino por (estado, símbolo)."""
        for (de, le), destinos in self.delta.items():
            if le == LAMBDA or len(destinos) > 1:
                return False
        return True

    @property
    def eh_completo(self) -> bool:
        return all((q, a) in self.delta for q in self.estados for a in self.alfabeto)

    @property
    def tipo(self) -> str:
        return "AFD" if self.eh_deterministico else "AFN"

    # ---------------------------------------------------------------- carga JSON
    @classmethod
    def de_dict(cls, d: dict) -> "AutomatoFinito":
        trans = [(t["de"], t["le"], t["para"]) for t in d["transicoes"]]
        return cls(d["alfabeto"], d["estados"], d["inicial"], d["finais"], trans)

    @classmethod
    def de_json(cls, caminho: str) -> "AutomatoFinito":
        with open(caminho, encoding="utf-8") as f:
            return cls.de_dict(json.load(f))

    def descricao(self) -> str:
        n_trans = sum(len(v) for v in self.delta.values())
        return (f"{self.tipo}: Σ={{{', '.join(sorted(self.alfabeto))}}}  Q={{{', '.join(sorted(self.estados))}}}  "
                f"q0={self.inicial}  F={{{', '.join(sorted(self.finais))}}}  |δ|={n_trans}")

    # ---------------------------------------------------------------- λ-fecho
    def fecho_lambda(self, conjunto: Iterable[str]) -> FrozenSet[str]:
        """Todos os estados alcançáveis por zero ou mais λ-transições. O(|Q| + |δ|)."""
        pilha = list(conjunto)
        visto = set(pilha)
        while pilha:
            q = pilha.pop()
            for p in self.delta.get((q, LAMBDA), ()):
                if p not in visto:
                    visto.add(p)
                    pilha.append(p)
        return frozenset(visto)

    def mover(self, conjunto: Iterable[str], simbolo: str) -> Set[str]:
        res: Set[str] = set()
        for q in conjunto:
            res |= self.delta.get((q, simbolo), set())
        return res

    # ---------------------------------------------------------------- execução
    def executar(self, cadeia: str) -> ResultadoAF:
        """Executa a cadeia mostrando passo a passo.

        AFD  : O(n) - um estado por passo.
        AFN  : simulação por conjuntos de estados, O(n · |Q|²) no pior caso.
        """
        w = "" if cadeia == LAMBDA else cadeia
        invalidos = sorted({c for c in w if c not in self.alfabeto})
        if invalidos:
            return ResultadoAF(False, [], [], f"símbolos fora do alfabeto: {', '.join(invalidos)}")
        if self.eh_deterministico:
            return self._executar_afd(w)
        return self._executar_afn(w)

    def _executar_afd(self, w: str) -> ResultadoAF:
        atual = self.inicial
        caminho = [atual]
        passos = [f"Início em {atual}"]
        for i, c in enumerate(w, 1):
            destinos = self.delta.get((atual, c))
            if not destinos:
                passos.append(f"{i}. δ({atual}, {c}) indefinida")
                return ResultadoAF(False, passos, caminho, f"sem transição de {atual} com '{c}'")
            prox = next(iter(destinos))
            passos.append(f"{i}. δ({atual}, {c}) = {prox}")
            atual = prox
            caminho.append(atual)
        ok = atual in self.finais
        return ResultadoAF(ok, passos, caminho, "" if ok else f"{atual} não é estado final")

    def _executar_afn(self, w: str) -> ResultadoAF:
        atual = self.fecho_lambda({self.inicial})
        passos = [f"Início: λ-fecho({{{self.inicial}}}) = {_fmt(atual)}"]
        historico = [atual]
        for i, c in enumerate(w, 1):
            movido = self.mover(atual, c)
            atual = self.fecho_lambda(movido)
            passos.append(f"{i}. lê '{c}': conjunto = {_fmt(atual)}")
            historico.append(atual)
            if not atual:
                return ResultadoAF(False, passos, [], f"conjunto de estados vazio após '{c}'")
        ok = bool(atual & self.finais)
        caminho = self._caminho_aceitador(w) if ok else []
        motivo = "" if ok else "nenhum estado final no conjunto final"
        return ResultadoAF(ok, passos, caminho, motivo)

    def _caminho_aceitador(self, w: str) -> List[str]:
        """Reconstrói UM caminho aceitador (busca em profundidade com memo)."""
        falhos: Set[Tuple[str, int]] = set()

        def dfs(q: str, i: int, visitados_lambda: FrozenSet[str]) -> Optional[List[str]]:
            if (q, i) in falhos and not visitados_lambda:
                return None
            if i == len(w) and q in self.finais:
                return [q]
            # transições λ (sem ciclo λ)
            for p in sorted(self.delta.get((q, LAMBDA), ())):
                if p in visitados_lambda or p == q:
                    continue
                r = dfs(p, i, visitados_lambda | {q})
                if r:
                    return [q] + r
            if i < len(w):
                for p in sorted(self.delta.get((q, w[i]), ())):
                    r = dfs(p, i + 1, frozenset())
                    if r:
                        return [q] + r
            falhos.add((q, i))
            return None

        return dfs(self.inicial, 0, frozenset()) or []

    def aceita(self, cadeia: str) -> bool:
        return self.executar(cadeia).aceita

    # ---------------------------------------------------------------- AFN -> AFD
    def para_afd(self) -> "AutomatoFinito":
        """Construção de subconjuntos. Pior caso O(2^|Q| · |Σ|) estados/transições."""
        inicio = self.fecho_lambda({self.inicial})
        nome = lambda s: "{" + ",".join(sorted(s)) + "}" if s else "∅"
        fila = [inicio]
        vistos = {inicio}
        trans = []
        while fila:
            s = fila.pop(0)
            for a in sorted(self.alfabeto):
                t = self.fecho_lambda(self.mover(s, a))
                trans.append((nome(s), a, nome(t)))
                if t not in vistos:
                    vistos.add(t)
                    fila.append(t)
        estados = {nome(s) for s in vistos}
        finais = {nome(s) for s in vistos if s & self.finais}
        return AutomatoFinito(self.alfabeto, estados, nome(inicio), finais, trans)


def _fmt(conjunto: Iterable[str]) -> str:
    return "{" + ", ".join(sorted(conjunto)) + "}" if conjunto else "∅"
