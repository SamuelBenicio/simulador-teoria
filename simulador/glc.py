"""Módulo 3 - Gramática Livre de Contexto (GLC).

Reconhecimento por busca em largura (BFS) sobre formas sentenciais, sempre
expandindo a variável mais à esquerda (derivação mais à esquerda).

Poda (garante terminação, inclusive com recursão à esquerda e produções λ):
  1. prefixo de terminais da forma sentencial deve casar com o prefixo de w;
  2. comprimento mínimo da forma (terminais + variáveis não anuláveis) <= |w|.

Formato de texto das produções (uma por linha, alternativas separadas por '|'):
    S -> aSb | λ
Variáveis são os símbolos à esquerda das setas; todo o resto são terminais.
Símbolos são de 1 caractere (sem espaços), ou separados por espaço se houver tokens longos.
"""
from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from . import LAMBDA, eh_vazio

Producao = Tuple[str, Tuple[str, ...]]  # (variável, corpo) ; corpo vazio = λ


@dataclass
class No:
    simbolo: str
    filhos: List["No"] = field(default_factory=list)


@dataclass
class ResultadoGLC:
    aceita: bool
    derivacao: List[Tuple[str, Optional[Producao]]] = field(default_factory=list)
    arvore: Optional[No] = None
    estados_explorados: int = 0
    motivo: str = ""

    def formatar(self) -> str:
        if not self.aceita:
            return f"REJEITA ({self.motivo})"
        linhas = []
        for i, (forma, prod) in enumerate(self.derivacao):
            if prod is None:
                linhas.append(f"{forma}")
            else:
                corpo = "".join(prod[1]) or LAMBDA
                linhas.append(f"=> {forma}    [{prod[0]} -> {corpo}]")
        linhas.append("ACEITA")
        return "\n".join(linhas)


class GLC:
    def __init__(self, variaveis, terminais, producoes: List[Producao], inicial: str):
        self.variaveis = set(variaveis)
        self.terminais = set(terminais)
        self.producoes = [(v, tuple(c)) for v, c in producoes]
        self.inicial = inicial
        self._validar()
        self.por_variavel: Dict[str, List[Tuple[str, ...]]] = {}
        for v, c in self.producoes:
            self.por_variavel.setdefault(v, []).append(c)
        self.anulaveis = self._calcular_anulaveis()

    # ----------------------------------------------------------------- validação
    def _validar(self) -> None:
        if self.inicial not in self.variaveis:
            raise ValueError("Símbolo inicial deve ser uma variável.")
        if self.variaveis & self.terminais:
            raise ValueError("Variáveis e terminais devem ser disjuntos.")
        for v, c in self.producoes:
            if v not in self.variaveis:
                raise ValueError(f"Lado esquerdo {v!r} não é variável (GLC exige 1 variável).")
            for s in c:
                if s not in self.variaveis and s not in self.terminais:
                    raise ValueError(f"Símbolo {s!r} na produção {v} -> {''.join(c)} não declarado.")

    # ----------------------------------------------------------------- construção
    @classmethod
    def de_texto(cls, texto: str, inicial: Optional[str] = None) -> "GLC":
        """Lê produções no formato 'S -> aSb | λ'. O inicial é o 1º lado esquerdo (ou o informado)."""
        prods: List[Producao] = []
        variaveis: List[str] = []
        for linha in texto.splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            norm = linha.replace("→", "->")
            if "->" not in norm:
                raise ValueError(f"Produção inválida (esperado 'A -> ...'): {linha!r}")
            esq, _, dir_ = norm.partition("->")
            esq = esq.strip()
            if not esq:
                raise ValueError(f"Lado esquerdo vazio na produção: {linha!r}")
            if esq not in variaveis:
                variaveis.append(esq)
            for alt in dir_.split("|"):
                alt = alt.strip()
                if eh_vazio(alt):
                    corpo: Tuple[str, ...] = ()
                else:
                    corpo = tuple(alt.split()) if " " in alt else tuple(alt)
                prods.append((esq, corpo))
        if not variaveis:
            raise ValueError("Nenhuma produção encontrada na gramática.")
        vs = set(variaveis)
        ts = {s for _, c in prods for s in c if s not in vs}
        return cls(vs, ts, prods, inicial or variaveis[0])

    @classmethod
    def de_dict(cls, d: dict) -> "GLC":
        prods = []
        for p in d["producoes"]:
            corpo = () if eh_vazio(p["para"]) else (tuple(p["para"].split()) if " " in p["para"] else tuple(p["para"]))
            prods.append((p["de"], corpo))
        return cls(d["variaveis"], d["terminais"], prods, d["inicial"])

    @classmethod
    def de_arquivo(cls, caminho: str) -> "GLC":
        with open(caminho, encoding="utf-8") as f:
            conteudo = f.read()
        if caminho.endswith(".json"):
            return cls.de_dict(json.loads(conteudo))
        return cls.de_texto(conteudo)

    def descricao(self) -> str:
        linhas = [f"V = {{{', '.join(sorted(self.variaveis))}}}   T = {{{', '.join(sorted(self.terminais))}}}   S = {self.inicial}", "P:"]
        for v in sorted(self.por_variavel, key=lambda x: (x != self.inicial, x)):
            alts = " | ".join("".join(c) or LAMBDA for c in self.por_variavel[v])
            linhas.append(f"  {v} -> {alts}")
        return "\n".join(linhas)

    # ----------------------------------------------------------------- análise auxiliar
    def _calcular_anulaveis(self) -> Set[str]:
        """Variáveis que derivam λ (ponto fixo). O(|P| · |V|)."""
        anul: Set[str] = set()
        mudou = True
        while mudou:
            mudou = False
            for v, c in self.producoes:
                if v not in anul and all(s in anul for s in c):
                    anul.add(v)
                    mudou = True
        return anul

    def _tamanho_minimo(self, forma: Tuple[str, ...]) -> int:
        return sum(1 for s in forma if s in self.terminais or s not in self.anulaveis)

    # ----------------------------------------------------------------- reconhecimento
    def derivar(self, cadeia: str, limite: int = 200_000) -> ResultadoGLC:
        """Procura uma derivação mais à esquerda de `cadeia` a partir de S.

        Pior caso exponencial em |w| para gramáticas ambíguas (ver relatório);
        para gramáticas LL(1)-like como S -> aSb | λ é O(n²) por causa das cópias das formas.
        """
        w = tuple("" if cadeia == LAMBDA else cadeia)
        if any(c not in self.terminais for c in w):
            return ResultadoGLC(False, motivo="a cadeia contém símbolos que não são terminais da gramática")

        inicio = (self.inicial,)
        pai: Dict[Tuple[str, ...], Tuple[Optional[Tuple[str, ...]], Optional[Producao]]] = {inicio: (None, None)}
        fila = deque([inicio])
        explorados = 0
        while fila:
            forma = fila.popleft()
            explorados += 1
            if explorados > limite:
                return ResultadoGLC(False, estados_explorados=explorados,
                                    motivo=f"limite de {limite} formas sentenciais excedido")
            # índice da variável mais à esquerda
            idx = next((i for i, s in enumerate(forma) if s in self.variaveis), None)
            if idx is None:
                if forma == w:
                    return self._montar(forma, pai, explorados)
                continue
            for corpo in self.por_variavel.get(forma[idx], []):
                nova = forma[:idx] + corpo + forma[idx + 1:]
                if nova in pai:
                    continue
                if self._podar(nova, w):
                    continue
                pai[nova] = (forma, (forma[idx], corpo))
                fila.append(nova)
        return ResultadoGLC(False, estados_explorados=explorados, motivo="nenhuma derivação encontrada")

    def _podar(self, forma: Tuple[str, ...], w: Tuple[str, ...]) -> bool:
        # (1) prefixo de terminais precisa casar com w
        i = 0
        while i < len(forma) and forma[i] in self.terminais:
            if i >= len(w) or forma[i] != w[i]:
                return True
            i += 1
        # (2) tamanho mínimo
        return self._tamanho_minimo(forma) > len(w)

    def _montar(self, final, pai, explorados) -> ResultadoGLC:
        cadeia_derivacao: List[Tuple[Tuple[str, ...], Optional[Producao]]] = []
        atual = final
        while atual is not None:
            anterior, prod = pai[atual]
            cadeia_derivacao.append((atual, prod))
            atual = anterior
        cadeia_derivacao.reverse()
        deriv = [("".join(f) or LAMBDA, p) for f, p in cadeia_derivacao]
        prods = [p for _, p in cadeia_derivacao if p is not None]
        return ResultadoGLC(True, deriv, self._construir_arvore(prods), explorados)

    def _construir_arvore(self, prods: List[Producao]) -> No:
        """Constrói a árvore a partir da sequência de produções da derivação mais à esquerda."""
        it = iter(prods)

        def expandir(simbolo: str) -> No:
            no = No(simbolo)
            if simbolo in self.variaveis:
                _, corpo = next(it)
                if not corpo:
                    no.filhos.append(No(LAMBDA))
                else:
                    no.filhos = [expandir(s) for s in corpo]
            return no

        return expandir(self.inicial)

    def aceita(self, cadeia: str) -> bool:
        return self.derivar(cadeia).aceita


def arvore_ascii(no: No, prefixo: str = "", ultimo: bool = True, raiz: bool = True) -> str:
    """Desenha a árvore de derivação em texto (formato 'tree')."""
    if raiz:
        linhas = [no.simbolo]
        novo_prefixo = ""
    else:
        linhas = [prefixo + ("└── " if ultimo else "├── ") + no.simbolo]
        novo_prefixo = prefixo + ("    " if ultimo else "│   ")
    for i, f in enumerate(no.filhos):
        linhas.append(arvore_ascii(f, novo_prefixo, i == len(no.filhos) - 1, False))
    return "\n".join(linhas)


def fronteira(no: No) -> str:
    """Concatenação das folhas (a cadeia derivada)."""
    if not no.filhos:
        return "" if no.simbolo == LAMBDA else no.simbolo
    return "".join(fronteira(f) for f in no.filhos)
