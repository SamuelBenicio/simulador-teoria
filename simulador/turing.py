"""Módulo 5 - Máquina de Turing determinística de fita única.

Transição: δ(estado, símbolo) = (novo_estado, símbolo_escrito, movimento) com movimento em {L, R, S}.
Branco = '_'.  Aceita ao entrar em um estado final; rejeita se não há transição definida.

Máquinas prontas:
  - Opção A: reconhece L = { w#w | w ∈ {a,b}* }  (marca símbolos com X/Y e confere um a um)
  - Opção B: soma de dois números em unário, "000100" (3+2) -> "00000"

Formato JSON:
{
  "estados": [...], "alfabeto": [...], "alfabeto_fita": [...], "branco": "_",
  "inicial": "q0", "finais": ["qf"],
  "transicoes": [ {"de":"q0","le":"a","para":"q1","escreve":"X","move":"R"}, ... ]
}
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple

BRANCO = "_"


@dataclass
class ResultadoMT:
    aceita: bool
    passos: List[str] = field(default_factory=list)
    fita_final: str = ""
    num_passos: int = 0
    motivo: str = ""

    def formatar(self, mostrar_passos: bool = True) -> str:
        linhas = list(self.passos) if mostrar_passos else []
        linhas.append(f"Fita final: {self.fita_final or BRANCO}")
        linhas.append(f"Passos executados: {self.num_passos}")
        linhas.append("ACEITA" if self.aceita else f"REJEITA ({self.motivo})")
        return "\n".join(linhas)


class MaquinaTuring:
    def __init__(self, estados: Iterable[str], alfabeto: Iterable[str], inicial: str,
                 finais: Iterable[str], transicoes: Iterable[Tuple[str, str, str, str, str]],
                 branco: str = BRANCO):
        self.estados = set(estados)
        self.alfabeto = set(alfabeto)
        self.inicial = inicial
        self.finais = set(finais)
        self.branco = branco
        self.delta: Dict[Tuple[str, str], Tuple[str, str, str]] = {}
        for de, le, para, escreve, move in transicoes:
            if move not in ("L", "R", "S"):
                raise ValueError(f"Movimento inválido {move!r}: use L, R ou S.")
            if (de, le) in self.delta:
                raise ValueError(f"Máquina não determinística: duas transições para ({de}, {le}).")
            self.delta[(de, le)] = (para, escreve, move)
        if inicial not in self.estados:
            raise ValueError("Estado inicial fora de Q.")
        if not self.finais <= self.estados:
            raise ValueError("Estados finais fora de Q.")

    # ---------------------------------------------------------------- construção
    @classmethod
    def de_dict(cls, d: dict) -> "MaquinaTuring":
        trans = [(t["de"], t["le"], t["para"], t["escreve"], t["move"]) for t in d["transicoes"]]
        return cls(d["estados"], d["alfabeto"], d["inicial"], d["finais"], trans, d.get("branco", BRANCO))

    @classmethod
    def de_json(cls, caminho: str) -> "MaquinaTuring":
        with open(caminho, encoding="utf-8") as f:
            return cls.de_dict(json.load(f))

    @classmethod
    def reconhecedor_w_hash_w(cls, simbolos: Iterable[str] = ("a", "b")) -> "MaquinaTuring":
        """Opção A: L = { w#w }.

        Estratégia: marcar o 1º símbolo livre à esquerda de '#' com X, procurar o 1º
        símbolo livre à direita de '#' e conferir se é igual (marcando com Y).
        Repete até que não restem símbolos à esquerda; então verifica que à direita
        só restam Y's.
        """
        S = sorted(set(simbolos))
        T: List[Tuple[str, str, str, str, str]] = []
        # q0: acha o primeiro símbolo da esquerda ainda não marcado
        T.append(("q0", "X", "q0", "X", "R"))
        T.append(("q0", "#", "qv", "#", "R"))          # esquerda esgotada -> verificar direita
        for s in S:
            T.append(("q0", s, f"c_{s}", "X", "R"))    # carrega o símbolo s
            # c_s: vai até '#'
            for t in S + ["X"]:
                T.append((f"c_{s}", t, f"c_{s}", t, "R"))
            T.append((f"c_{s}", "#", f"d_{s}", "#", "R"))
            # d_s: pula Y's e confere o primeiro símbolo livre
            T.append((f"d_{s}", "Y", f"d_{s}", "Y", "R"))
            T.append((f"d_{s}", s, "qr", "Y", "L"))
            # (qualquer outro símbolo ou branco: sem transição => rejeita)
        # qr: volta ao início da fita
        for t in S + ["X", "Y", "#"]:
            T.append(("qr", t, "qr", t, "L"))
        T.append(("qr", BRANCO, "q0", BRANCO, "R"))
        # qv: só pode haver Y's até o branco
        T.append(("qv", "Y", "qv", "Y", "R"))
        T.append(("qv", BRANCO, "qf", BRANCO, "S"))
        estados = {de for de, *_ in T} | {p for _, _, p, _, _ in T}
        return cls(estados, S + ["#"], "q0", ["qf"], T)

    @classmethod
    def somador_unario(cls) -> "MaquinaTuring":
        """Opção B: n zeros, um '1' e m zeros  ->  n+m zeros.

        Ex.: 000100 (3+2) -> 00000.
        Estratégia: troca o '1' por '0' (junta os dois blocos) e apaga o último '0'.
        """
        T = [
            ("q0", "0", "q0", "0", "R"),       # anda sobre o 1º número
            ("q0", "1", "q1", "0", "R"),       # separador vira 0
            ("q1", "0", "q1", "0", "R"),       # anda sobre o 2º número
            ("q1", BRANCO, "q2", BRANCO, "L"), # fim da entrada, volta 1 posição
            ("q2", "0", "qf", BRANCO, "S"),    # apaga o 0 a mais
        ]
        return cls({"q0", "q1", "q2", "qf"}, ["0", "1"], "q0", ["qf"], T)

    # ---------------------------------------------------------------- execução
    def executar(self, entrada: str, limite_passos: int = 5_000_000,
                 registrar_passos: bool = True) -> ResultadoMT:
        """registrar_passos=False evita o custo O(|fita|) por passo (usado no benchmark)."""
        fita: Dict[int, str] = {i: c for i, c in enumerate(entrada)}
        cabeca, estado, n = 0, self.inicial, 0
        passos = [self._instantanea(fita, cabeca, estado, 0)] if registrar_passos else []
        while True:
            if estado in self.finais:
                return ResultadoMT(True, passos, self._conteudo(fita), n)
            simbolo = fita.get(cabeca, self.branco)
            regra = self.delta.get((estado, simbolo))
            if regra is None:
                return ResultadoMT(False, passos, self._conteudo(fita), n,
                                   f"sem transição para δ({estado}, {simbolo})")
            if n >= limite_passos:
                return ResultadoMT(False, passos, self._conteudo(fita), n, "limite de passos excedido")
            estado, escreve, move = regra
            fita[cabeca] = escreve
            cabeca += {"L": -1, "R": 1, "S": 0}[move]
            n += 1
            if registrar_passos:
                passos.append(self._instantanea(fita, cabeca, estado, n))

    def _conteudo(self, fita: Dict[int, str]) -> str:
        if not fita:
            return ""
        lo, hi = min(fita), max(fita)
        return "".join(fita.get(i, self.branco) for i in range(lo, hi + 1)).strip(self.branco)

    def _instantanea(self, fita: Dict[int, str], cabeca: int, estado: str, n: int) -> str:
        lo = min(min(fita, default=0), cabeca)
        hi = max(max(fita, default=0), cabeca)
        celulas = [fita.get(i, self.branco) for i in range(lo, hi + 1)]
        texto = "".join(celulas)
        prefixo = f"{n:>3}. [{estado}]  "
        seta = " " * (cabeca - lo) + "^"
        return f"{prefixo}{texto}\n{' ' * len(prefixo)}{seta}"

    def aceita(self, entrada: str) -> bool:
        return self.executar(entrada).aceita


def soma_unaria(entrada: str) -> str:
    """Executa o somador unário e devolve a fita resultante (ex.: '000100' -> '00000')."""
    r = MaquinaTuring.somador_unario().executar(entrada)
    return r.fita_final if r.aceita else ""
