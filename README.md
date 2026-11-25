# Simulador de Linguagens Formais e Modelos Computacionais

Projeto prático em dupla — **Aspectos Teóricos da Computação** (UNIFOR, AV3).

Ferramenta de console, em **Python 3.9+ (sem dependências externas)**, que modela, valida e simula:

| Módulo | Arquivo | O que faz |
|---|---|---|
| 1 | `simulador/linguagens.py` | Alfabeto Σ, linguagem L, validação de cadeias, Σ\*, Σ⁺, tamanho, concatenação |
| 2 | `simulador/automato.py` | AFD e AFN (com transições λ) carregados de JSON, execução passo a passo, conversão AFN→AFD |
| 3 | `simulador/glc.py` | Gramática livre de contexto: derivação passo a passo (mais à esquerda) e árvore de derivação |
| 4 | `simulador/ap.py` | Autômato com pilha (L = { aⁿbⁿ \| n ≥ 1 }), mostrando leitura, estado e pilha |
| 5 | `simulador/turing.py` | Máquina de Turing: **Opção A** (w#w) e **Opção B** (soma unária) |
| 6 | `simulador/complexidade.py` | Tabela O/Ω/Θ de todos os algoritmos + benchmark empírico |

## Como executar

```bash
git clone https://github.com/SamuelBenicio/simulador-teoria.git
cd simulador-teoria

python main.py                 # menu interativo
python main.py demo            # roda todos os exemplos do enunciado
python -m unittest discover -s tests -v    # 25 testes unitários
```

### Comandos diretos

```bash
python main.py linguagem --alfabeto ab --cadeia abba [--concatenar ba] [-k 3]
python main.py af   --arquivo exemplos/afd_ab.json --cadeia ab
python main.py glc  --arquivo exemplos/glc_anbn.txt --cadeia aaabbb
python main.py ap   --cadeia aaabbb [--arquivo exemplos/ap_anbn.json]
python main.py mt   --maquina w#w  --cadeia ab#ab
python main.py mt   --maquina soma --cadeia 000100 [--resumo]
python main.py complexidade [--benchmark]
```

## Exemplos de entrada e saída

### Módulo 1 — Linguagens formais
```
$ python main.py linguagem --alfabeto ab --cadeia abba --concatenar ba -k 2
Σ = {a, b}
Cadeia válida para Σ
Tamanho = 4
Σ* (até tamanho 2): {λ, a, b, aa, ab, ba, bb}
Σ+ (até tamanho 2): {a, b, aa, ab, ba, bb}
Concatenação: abba · ba = abbaba
```

### Módulo 2 — Autômato finito (JSON)
`exemplos/afd_ab.json` define q0 –a→ q1 e q1 –b→ q2 (final: q2).
```
$ python main.py af --arquivo exemplos/afd_ab.json --cadeia ab
Início em q0
1. δ(q0, a) = q1
2. δ(q1, b) = q2
q0 -> q1 -> q2
ACEITA
```
Formato do JSON (use `"λ"` em `"le"` para transições vazias; se houver λ ou não determinismo, o simulador trata como AFN):
```json
{
  "alfabeto": ["a", "b"],
  "estados": ["q0", "q1", "q2"],
  "inicial": "q0",
  "finais": ["q2"],
  "transicoes": [ {"de": "q0", "le": "a", "para": "q1"},
                  {"de": "q1", "le": "b", "para": "q2"} ]
}
```
Também há `afn_termina_ab.json` (AFN: cadeias que terminam em `ab`) e `afn_lambda.json` (AFN com λ: a⁺ ∪ b⁺).

### Módulo 3 — Gramática livre de contexto
`exemplos/glc_anbn.txt`: `S -> aSb | λ` (variáveis = lado esquerdo das setas; o restante são terminais).
```
$ python main.py glc --arquivo exemplos/glc_anbn.txt --cadeia aaabbb
S
=> aSb      [S -> aSb]
=> aaSbb    [S -> aSb]
=> aaaSbbb  [S -> aSb]
=> aaabbb   [S -> λ]
ACEITA

Árvore de derivação:
S
├── a
├── S
│   ├── a
│   ├── S
│   │   ├── a
│   │   ├── S
│   │   │   └── λ
│   │   └── b
│   └── b
└── b
```

### Módulo 4 — Autômato com pilha
```
$ python main.py ap --cadeia aabb
Leitura   Estado    Pilha (topo à esq.)       Ação
--------------------------------------------------
λ         q0        Z                         início
a         q0        AZ                        δ(q0,a,Z) = (q0,AZ)  [empilha A]
aa        q0        AAZ                       δ(q0,a,A) = (q0,AA)  [empilha A]
aab       q1        AZ                        δ(q0,b,A) = (q1,λ)  [desempilha A]
aabb      q1        Z                         δ(q1,b,A) = (q1,λ)  [desempilha A]
aabb      qf        Z                         δ(q1,λ,Z) = (qf,Z)
ACEITA
```

### Módulo 5 — Máquina de Turing
```
$ python main.py mt --maquina soma --cadeia 000100 --resumo     # 3 + 2
Fita final: 00000
Passos executados: 8
ACEITA
Resultado: 00000  (3 + 2 = 5 em unário)

$ python main.py mt --maquina w#w --cadeia ab#ab --resumo
Fita final: XX#YY
Passos executados: 24
ACEITA
```
Sem `--resumo`, cada configuração da fita é impressa com `^` indicando a posição da cabeça.

### Módulo 6 — Complexidade
`python main.py complexidade --benchmark` imprime a tabela de melhor/médio/pior caso (O, Ω, Θ) e mede o tempo real com n crescente (razão t(2n)/t(n) ≈ 2 → linear; ≈ 4 → quadrático).

## Estrutura do repositório

```
main.py                 interface de console (menu + subcomandos)
simulador/              módulos 1–6
exemplos/               JSON/TXT de autômatos, gramáticas e máquinas
tests/                  testes unitários (unittest)
docs/                   documento técnico e diagramas UML
```

## Autores
Samuel Ribeiro Benicio e Catarina Garcia Gurgel — Engenharia de Computação, UNIFOR.
