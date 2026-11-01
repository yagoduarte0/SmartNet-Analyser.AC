from collections import deque

def bfs(grafo, origem):
    visitados = set()
    fila = deque()
    ordem = []

    visitados.add(origem)
    fila.append(origem)

    while fila:
        vertice = fila.popleft()
        ordem.append(vertice)
        for vizinho, _ in grafo.adj[vertice]:
            if vizinho not in visitados:
                visitados.add(vizinho)
                fila.append(vizinho)

    return ordem

if __name__ == "__main__":
    from grafo import Grafo

    g = Grafo(direcionado=False, ponderado=True)
    arestas_prova = [
        ('O','A',2), ('O','B',5), ('O','C',4), ('A','B',2),
        ('A','D',7), ('A','F',12), ('B','C',1), ('B','D',4),
        ('B','E',3), ('C','E',4), ('D','E',4), ('D','T',5),
        ('E','T',7), ('F','T',3)
    ]
    for u, v, p in arestas_prova:
        g.adicionar_arestas(u, v, p)

    print("BFS:", bfs(g, 'O'))