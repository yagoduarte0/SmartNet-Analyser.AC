"""
SmartNet Analyzer — servidor (Flask).

O "cérebro" continua em Python:
  - grafo.py       → classe Grafo (lista de adjacência)
  - algoritmos.py  → DFS, BFS, Dijkstra, Kruskal

Este arquivo só faz a ponte: recebe o grafo do site em JSON, monta um objeto
Grafo, roda o algoritmo pedido e devolve o resultado em JSON.

Rodar:  python server.py   →  abrir http://localhost:5000
"""
import math
import os
import threading

from flask import Flask, jsonify, request, send_from_directory

import algoritmos
from grafo import Grafo

app = Flask(__name__, static_folder="static")
app.json.sort_keys = False  # manter a ordem de inserção dos vértices (como no self.adj)


# ─────────────────────────────────────────────────────────────
# Montagem do grafo a partir do JSON enviado pelo site
# ─────────────────────────────────────────────────────────────
def montar_grafo(dados):
    """dados = {direcionado, ponderado, vertices: [...], arestas: [[u, v, peso], ...]}"""
    g = Grafo(direcionado=dados.get("direcionado", False),
              ponderado=dados.get("ponderado", True))
    for v in dados.get("vertices", []):
        g.adicionar_vertices(v)
    for u, v, peso in dados.get("arestas", []):
        g.adicionar_arestas(u, v, peso if g.ponderado else None)
    return g


def num(x):
    """JSON não tem infinito: devolve None para inalcançável."""
    return None if x == math.inf else x


def descricao_memoria(g):
    """Como o grafo está guardado em self.adj."""
    return {
        "adj": {u: [[v, p] for v, p in vizinhos] for u, vizinhos in g.adj.items()},
        "texto": str(g),
        "num_vertices": len(g.vertices()),
        "num_arestas": len(g.arestas()),
    }


def eh_conexo(g):
    verts = g.vertices()
    if not verts:
        return True
    ordem, _ = algoritmos.dfs(g, verts[0])
    return len(ordem) == len(verts)


# ─────────────────────────────────────────────────────────────
# Rotas
# ─────────────────────────────────────────────────────────────
@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.post("/api/grafo")
def api_grafo():
    """Devolve a estrutura de memória (lista de adjacência) do grafo atual."""
    try:
        g = montar_grafo(request.get_json())
    except (ValueError, TypeError) as e:
        return jsonify(erro=str(e)), 400
    return jsonify(memoria=descricao_memoria(g), conexo=eh_conexo(g))


@app.post("/api/executar")
def api_executar():
    dados = request.get_json()
    algoritmo = dados.get("algoritmo")
    origem = dados.get("origem")

    try:
        g = montar_grafo(dados)
    except (ValueError, TypeError) as e:
        return jsonify(erro=str(e)), 400

    if algoritmo in ("dfs", "bfs", "dijkstra") and origem not in g.adj:
        return jsonify(erro="Escolha um vértice de origem válido."), 400

    if algoritmo == "dfs":
        ordem, pai = algoritmos.dfs(g, origem)
        return jsonify(ordem=ordem, pai=pai,
                       inalcancaveis=[v for v in g.vertices() if v not in pai])

    if algoritmo == "bfs":
        ordem, nivel = algoritmos.bfs(g, origem)
        # árvore da BFS (só para desenhar): o pai de x é o 1º da ordem, no nível anterior, que liga em x
        pai = {origem: None}
        for x in ordem[1:]:
            pai[x] = next(u for u in ordem
                          if nivel[u] == nivel[x] - 1 and any(w == x for w, _ in g.adj[u]))
        return jsonify(ordem=ordem, nivel=nivel, pai=pai,
                       inalcancaveis=[v for v in g.vertices() if v not in nivel])

    if algoritmo == "dijkstra":
        dist, pai = algoritmos.dijkstra(g, origem)
        rotas = {v: (algoritmos.reconstruir_caminho(pai, v) if dist[v] != math.inf else None)
                 for v in g.vertices()}
        return jsonify(dist={v: num(d) for v, d in dist.items()}, pai=pai, rotas=rotas)

    if algoritmo == "kruskal":
        if not hasattr(algoritmos, "kruskal"):
            return jsonify(erro="Kruskal ainda não implementado em algoritmos.py"), 501
        if g.direcionado:
            return jsonify(erro="Kruskal (árvore geradora mínima) é definido para grafos não-direcionados."), 400
        arestas, custo = algoritmos.kruskal(g)
        return jsonify(arestas=[list(a) for a in arestas], custo=custo,
                       floresta=len(arestas) < len(g.vertices()) - 1)

    return jsonify(erro=f"Algoritmo desconhecido: {algoritmo}"), 400


@app.get("/api/status")
def api_status():
    return jsonify(kruskal=hasattr(algoritmos, "kruskal"))


@app.post("/api/finalizar")
def api_finalizar():
    """Botão 'Finalizar aplicação': encerra o servidor logo após responder."""
    threading.Timer(0.5, lambda: os._exit(0)).start()
    return jsonify(ok=True)


if __name__ == "__main__":
    print("\n  SmartNet Analyzer rodando em http://localhost:5000\n")
    app.run(debug=False, port=5000)
