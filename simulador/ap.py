"""Módulo 4 - Autômato com Pilha (AP).

Transição:  δ(estado, entrada, topo) -> (novo_estado, empilha)
  - entrada = λ : não consome símbolo
  - topo    = λ : não lê/desempilha a pilha
  - empilha = λ : só desempilha ; senão o 1º caractere fica no topo
Aceitação por estado final com a entrada totalmente consumida.

Simulação não determinística por busca em largura sobre configurações
(estado, posição, pilha). Limites de pilha e de configurações garantem terminação.

Formato JSON:
{
  "estados": [...], "alfabeto": [...], "alfabeto_pilha": [...],
  "inicial": "q0", "simbolo_inicial_pilha": "Z", "finais": ["qf"],
  "transicoes": [ {"de":"q0","le":"a","topo":"Z","para":"q0","empilha":"AZ"}, ... ]
}
"""
from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from . import LAMBDA, eh_vazio

Config = Tuple[str, int, str]  # (estado, posição, pilha com topo no índice 0)


@dataclass
class PassoAP:
    leitura: str
    estado: str
    pilha: str
    acao: str = ""


@dataclass
class ResultadoAP:
    aceita: bool
    passos: List[PassoAP] = field(default_factory=list)
    configuracoes: int = 0
    motivo: str = ""

    def formatar(self) -> str:
        cab = f"{'Leitura':<10}{'Estado':<10}{'Pilha (topo à esq.)':<26}Ação"
        linhas = [cab, "-" * len(cab)]
        for p in self.passos:
            linhas.append(f"{p.leitura:<10}{p.estado:<10}{p.pilha:<26}{p.acao}")
        linhas.append("ACEITA" if self.aceita else f"REJEITA ({self.motivo})")
        return "\n".join(linhas)


class AutomatoPilha:
    def __init__(self, estados, alfabeto, alfabeto_pilha, inicial, simbolo_inicial, finais, transicoes):
        self.estados = set(estados)
        self.alfabeto = set(alfabeto)
        self.alfabeto_pilha = set(alfabeto_pilha)
        self.inicial = inicial
        self.simbolo_inicial = simbolo_inicial
        self.finais = set(finais)
        # (estado, entrada|λ, topo|λ) -> lista de (novo_estado, empilha)
        self.delta: Dict[Tuple[str, str, str], List[Tuple[str, str]]] = {}
        for de, le, topo, para, empilha in transicoes:
            le = LAMBDA if eh_vazio(le) else le
            topo = LAMBDA if eh_vazio(topo) else topo
            empilha = "" if eh_vazio(empilha) else empilha
            self.delta.setdefault((de, le, topo), []).append((para, empilha))
        self._validar()

    def _validar(self) -> None:
        if self.inicial not in self.estados:
            raise ValueError("Estado inicial fora de Q.")
        if not self.finais <= self.estados:
            raise ValueError("Estados finais fora de Q.")
        if self.simbolo_inicial not in self.alfabeto_pilha:
            raise ValueError("Símbolo inicial da pilha fora de Γ.")
        for (de, le, topo), destinos in self.delta.items():
            if de not in self.estados:
                raise ValueError(f"Estado {de!r} fora de Q.")
            if le != LAMBDA and le not in self.alfabeto:
                raise ValueError(f"Símbolo {le!r} fora de Σ.")
            if topo != LAMBDA and topo not in self.alfabeto_pilha:
                raise ValueError(f"Símbolo de pilha {topo!r} fora de Γ.")
            for para, empilha in destinos:
                if para not in self.estados:
                    raise ValueError(f"Estado {para!r} fora de Q.")
                for s in empilha:
                    if s not in self.alfabeto_pilha:
                        raise ValueError(f"Símbolo de pilha {s!r} fora de Γ.")

    @classmethod
    def de_dict(cls, d: dict) -> "AutomatoPilha":
        trans = [(t["de"], t["le"], t["topo"], t["para"], t["empilha"]) for t in d["transicoes"]]
        return cls(d["estados"], d["alfabeto"], d["alfabeto_pilha"], d["inicial"],
                   d["simbolo_inicial_pilha"], d["finais"], trans)

    @classmethod
    def de_json(cls, caminho: str) -> "AutomatoPilha":
        with open(caminho, encoding="utf-8") as f:
            return cls.de_dict(json.load(f))

    @classmethod
    def an_bn(cls) -> "AutomatoPilha":
        """AP para L = { aⁿbⁿ | n ≥ 1 }, determinístico.

        q0 --a,Z/AZ--> q0   empilha A sobre Z (1º a)
        q0 --a,A/AA--> q0   empilha A
        q0 --b,A/λ --> q1   desempilha A (1º b)
        q1 --b,A/λ --> q1   desempilha A
        q1 --λ,Z/Z --> qf   pilha só com Z => aceita
        """
        trans = [
            ("q0", "a", "Z", "q0", "AZ"),
            ("q0", "a", "A", "q0", "AA"),
            ("q0", "b", "A", "q1", "λ"),
            ("q1", "b", "A", "q1", "λ"),
            ("q1", "λ", "Z", "qf", "Z"),
        ]
        return cls(["q0", "q1", "qf"], ["a", "b"], ["A", "Z"], "q0", "Z", ["qf"], trans)

    # --------------------------------------------------------------- execução
    def executar(self, cadeia: str, limite_config: int = 100_000, limite_pilha: int = 1000) -> ResultadoAP:
        w = "" if cadeia == LAMBDA else cadeia
        invalidos = sorted({c for c in w if c not in self.alfabeto})
        if invalidos:
            return ResultadoAP(False, motivo=f"símbolos fora do alfabeto: {', '.join(invalidos)}")

        inicio: Config = (self.inicial, 0, self.simbolo_inicial)
        pai: Dict[Config, Tuple[Optional[Config], str]] = {inicio: (None, "início")}
        fila = deque([inicio])
        n = 0
        while fila:
            cfg = fila.popleft()
            n += 1
            if n > limite_config:
                return ResultadoAP(False, configuracoes=n, motivo="limite de configurações excedido")
            estado, pos, pilha = cfg
            if pos == len(w) and estado in self.finais:
                return ResultadoAP(True, self._passos(cfg, pai, w), n)
            for prox, acao in self._sucessores(cfg, w):
                if len(prox[2]) > limite_pilha or prox in pai:
                    continue
                pai[prox] = (cfg, acao)
                fila.append(prox)
        return ResultadoAP(False, configuracoes=n, motivo="nenhuma computação aceita a cadeia")

    def _sucessores(self, cfg: Config, w: str):
        estado, pos, pilha = cfg
        topo = pilha[0] if pilha else None
        entradas = [LAMBDA] + ([w[pos]] if pos < len(w) else [])
        for le in entradas:
            tops = [LAMBDA] + ([topo] if topo is not None else [])
            for tp in tops:
                for para, empilha in self.delta.get((estado, le, tp), []):
                    nova_pilha = pilha[1:] if tp != LAMBDA else pilha
                    nova_pilha = empilha + nova_pilha
                    nova_pos = pos + (0 if le == LAMBDA else 1)
                    acao = f"δ({estado},{le},{tp}) = ({para},{empilha or LAMBDA})"
                    if tp != LAMBDA and not empilha:
                        acao += f"  [desempilha {tp}]"
                    elif tp == LAMBDA and empilha:
                        acao += f"  [empilha {empilha}]"
                    elif tp != LAMBDA and empilha.endswith(tp) and len(empilha) > len(tp):
                        acao += f"  [empilha {empilha[:-len(tp)]}]"
                    elif tp != LAMBDA and empilha != tp:
                        acao += f"  [troca {tp} por {empilha}]"
                    yield (para, nova_pos, nova_pilha), acao

    def _passos(self, final: Config, pai, w: str) -> List[PassoAP]:
        seq = []
        atual: Optional[Config] = final
        while atual is not None:
            anterior, acao = pai[atual]
            seq.append((atual, acao))
            atual = anterior
        seq.reverse()
        passos = []
        for (estado, pos, pilha), acao in seq:
            lido = w[:pos] if pos else LAMBDA
            passos.append(PassoAP(lido, estado, pilha or LAMBDA, acao))
        return passos

    def aceita(self, cadeia: str) -> bool:
        return self.executar(cadeia).aceita
