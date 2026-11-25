"""Testes unitários. Execute com:  python -m unittest discover -s tests -v"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulador.ap import AutomatoPilha
from simulador.automato import AutomatoFinito
from simulador.glc import GLC, fronteira
from simulador.linguagens import Alfabeto, Linguagem, concatenar, potencia, tamanho
from simulador.turing import MaquinaTuring, soma_unaria

EX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exemplos")


class TestLinguagens(unittest.TestCase):
    def setUp(self):
        self.s = Alfabeto("ab")

    def test_validacao_e_tamanho(self):
        self.assertTrue(self.s.valida("abba"))
        self.assertFalse(self.s.valida("abc"))
        self.assertEqual(tamanho("abba"), 4)
        self.assertEqual(tamanho("λ"), 0)

    def test_sigma_estrela_e_mais(self):
        self.assertEqual(list(self.s.sigma_estrela(2)), ["", "a", "b", "aa", "ab", "ba", "bb"])
        self.assertEqual(list(self.s.sigma_mais(1)), ["a", "b"])
        self.assertEqual(len(list(self.s.cadeias_de_tamanho(5))), 2 ** 5)

    def test_concatenacao(self):
        self.assertEqual(concatenar("ab", "ba"), "abba")
        self.assertEqual(concatenar("λ", "ab"), "ab")
        self.assertEqual(concatenar("λ", "λ"), "λ")
        self.assertEqual(potencia("λ", 3), "λ")
        self.assertEqual(potencia("ab", 2), "abab")

    def test_linguagem(self):
        L = Linguagem(self.s, cadeias={"a", "ab"})
        self.assertTrue(L.pertence("ab"))
        self.assertFalse(L.pertence("b"))
        L2 = Linguagem(self.s, cadeias={"b"})
        self.assertEqual(L.concatenacao(L2, 3), ["ab", "abb"])


class TestAutomatos(unittest.TestCase):
    def test_afd_exemplo_do_enunciado(self):
        af = AutomatoFinito.de_json(os.path.join(EX, "afd_ab.json"))
        self.assertEqual(af.tipo, "AFD")
        r = af.executar("ab")
        self.assertTrue(r.aceita)
        self.assertEqual(r.caminho, ["q0", "q1", "q2"])
        self.assertFalse(af.aceita("a"))
        self.assertFalse(af.aceita("abb"))
        self.assertFalse(af.aceita("ba"))

    def test_simbolo_invalido(self):
        af = AutomatoFinito.de_json(os.path.join(EX, "afd_ab.json"))
        self.assertFalse(af.aceita("abc"))

    def test_afn_termina_com_ab(self):
        af = AutomatoFinito.de_json(os.path.join(EX, "afn_termina_ab.json"))
        self.assertEqual(af.tipo, "AFN")
        for w in ["ab", "abbab", "aab", "bab"]:
            self.assertTrue(af.aceita(w), w)
        for w in ["", "a", "b", "aba", "ba"]:
            self.assertFalse(af.aceita(w), w)

    def test_afn_lambda(self):
        af = AutomatoFinito.de_json(os.path.join(EX, "afn_lambda.json"))  # a+ ∪ b+
        for w in ["a", "aaa", "b", "bbb"]:
            self.assertTrue(af.aceita(w), w)
        for w in ["", "ab", "ba"]:
            self.assertFalse(af.aceita(w), w)

    def test_afn_para_afd_equivalentes(self):
        afn = AutomatoFinito.de_json(os.path.join(EX, "afn_termina_ab.json"))
        afd = afn.para_afd()
        self.assertTrue(afd.eh_deterministico)
        for w in ["", "a", "ab", "abab", "bba", "aabab", "abb"]:
            self.assertEqual(afn.aceita(w), afd.aceita(w), w)

    def test_json_invalido(self):
        with self.assertRaises(ValueError):
            AutomatoFinito(["a"], ["q0"], "qx", [], [])


class TestGLC(unittest.TestCase):
    def setUp(self):
        self.g = GLC.de_arquivo(os.path.join(EX, "glc_anbn.txt"))

    def test_aceita_anbn(self):
        for n in range(0, 8):
            self.assertTrue(self.g.aceita("a" * n + "b" * n), n)

    def test_rejeita(self):
        for w in ["a", "b", "ba", "aab", "abb", "aabbb", "abab"]:
            self.assertFalse(self.g.aceita(w), w)

    def test_derivacao_e_arvore(self):
        r = self.g.derivar("aaabbb")
        self.assertTrue(r.aceita)
        formas = [f for f, _ in r.derivacao]
        self.assertEqual(formas, ["S", "aSb", "aaSbb", "aaaSbbb", "aaabbb"])
        self.assertEqual(fronteira(r.arvore), "aaabbb")

    def test_palindromos(self):
        g = GLC.de_arquivo(os.path.join(EX, "glc_palindromos.txt"))
        for w in ["", "a", "abba", "abaaba", "bab"]:
            self.assertTrue(g.aceita(w), w)
        for w in ["ab", "abb", "aabb"]:
            self.assertFalse(g.aceita(w), w)

    def test_recursao_a_esquerda_termina(self):
        g = GLC.de_texto("S -> Sa | a")
        self.assertTrue(g.aceita("aaaa"))
        self.assertFalse(g.aceita("ab"))
        self.assertFalse(g.aceita(""))

    def test_glc_texto_invalido(self):
        with self.assertRaises(ValueError):
            GLC.de_texto("# só comentário")
        with self.assertRaises(ValueError):
            GLC.de_texto("S aSb")


class TestAP(unittest.TestCase):
    def test_anbn(self):
        ap = AutomatoPilha.an_bn()
        for n in range(1, 10):
            self.assertTrue(ap.aceita("a" * n + "b" * n), n)
        for w in ["", "a", "b", "ab" * 2, "aabbb", "aaabb", "ba", "abb"]:
            self.assertFalse(ap.aceita(w), repr(w))

    def test_json_equivale_ao_builtin(self):
        a = AutomatoPilha.de_json(os.path.join(EX, "ap_anbn.json"))
        b = AutomatoPilha.an_bn()
        for w in ["", "ab", "aabb", "aab", "abab", "bbaa"]:
            self.assertEqual(a.aceita(w), b.aceita(w), w)

    def test_passos_mostram_pilha(self):
        r = AutomatoPilha.an_bn().executar("aabb")
        self.assertTrue(r.aceita)
        pilhas = [p.pilha for p in r.passos]
        self.assertEqual(pilhas, ["Z", "AZ", "AAZ", "AZ", "Z", "Z"])

    def test_transicao_invalida(self):
        with self.assertRaises(ValueError):
            AutomatoPilha(["q0"], ["a"], ["Z"], "q0", "Z", ["q0"], [("q0", "x", "Z", "q0", "Z")])


class TestTuring(unittest.TestCase):
    def test_w_hash_w(self):
        mt = MaquinaTuring.reconhecedor_w_hash_w()
        for w in ["#", "a#a", "b#b", "ab#ab", "abba#abba", "baab#baab"]:
            self.assertTrue(mt.aceita(w), w)
        for w in ["", "a", "a#b", "ab#ba", "ab#a", "a#ab", "a##a", "ab", "#a", "a#"]:
            self.assertFalse(mt.aceita(w), w)

    def test_soma_unaria(self):
        self.assertEqual(soma_unaria("000100"), "00000")   # 3 + 2
        self.assertEqual(soma_unaria("1"), "")              # 0 + 0
        self.assertEqual(soma_unaria("0001"), "000")        # 3 + 0
        self.assertEqual(soma_unaria("100"), "00")          # 0 + 2

    def test_soma_json_equivale(self):
        mt = MaquinaTuring.de_json(os.path.join(EX, "mt_soma_unaria.json"))
        self.assertEqual(mt.executar("000100").fita_final, "00000")

    def test_nao_deterministica_rejeitada(self):
        with self.assertRaises(ValueError):
            MaquinaTuring(["q0"], ["a"], "q0", [], [("q0", "a", "q0", "a", "R"), ("q0", "a", "q0", "b", "R")])

    def test_final_invalido_e_alinhamento_cabeca(self):
        with self.assertRaises(ValueError):
            MaquinaTuring(["q0"], ["a"], "q0", ["qf"], [])
        r = MaquinaTuring.reconhecedor_w_hash_w().executar("a#a")
        linha_topo, linha_seta = r.passos[1].splitlines()
        self.assertEqual(linha_topo.index("#"), linha_seta.index("^"))


if __name__ == "__main__":
    unittest.main()
