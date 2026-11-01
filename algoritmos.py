from collections import deque
import heapq

def bfs(grafo, origem):
    visitados = set()
    fila = deque()
    ordem = []
    nivel = {}

    visitados.add(origem)
    fila.append(origem)
    nivel[origem] = 0

    while fila:
        vertice = fila.popleft()
        ordem.append(vertice)
        for vizinho, _ in grafo.adj[vertice]:
            if vizinho not in visitados:
                visitados.add(vizinho)
                nivel[vizinho] = nivel[vertice] + 1
                fila.append(vizinho)

    return ordem, nivel

def dfs(grafo, origem):
    visitados = set()
    ordem = []
    pai = {origem: None}

    def visitar(vertice):
        visitados.add(vertice)
        ordem.append(vertice)

        for vizinho, _ in grafo.adj[vertice]:
            if vizinho not in visitados:
                pai[vizinho] = vertice
                visitar(vizinho)

    visitar(origem)
    return ordem, pai

def dijkstra(grafo, origem):
    distancia = {v: float('inf') for v in grafo.vertices()}
    pai = {v: None for v in grafo.vertices()}
    distancia[origem] = 0
    heap = [(0, origem)]

    while heap:
        distancia_atual, vertice = heapq.heappop(heap)

        if distancia_atual > distancia[vertice]:
            continue

        for vizinho, peso in grafo.adj[vertice]:
            nova_distancia = distancia[vertice] + peso
            if nova_distancia < distancia[vizinho]:
                distancia[vizinho] = nova_distancia
                pai[vizinho] = vertice
                heapq.heappush(heap, (nova_distancia, vizinho))
    return distancia, pai

def reconstruir_caminho(pai, destino):
    caminho = []
    atual = destino

    while atual is not None:
        caminho.append(atual)
        atual = pai[atual]

    caminho.reverse()
    return caminho


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
    print("BFS níveis:", bfs(g, 'O')[1])

    ordem, pai = dfs(g, 'O')
    print("DFS ordem:", ordem)
    print("DFS pais:", pai)

    dist, pai = dijkstra(g, 'O')
    print("Dijkstra distâncias:", dist)
    print("Dijkstra pais:", pai)

    print("Rota até T:", reconstruir_caminho(pai, 'T'))