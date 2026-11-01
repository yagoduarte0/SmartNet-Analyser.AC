class Grafo:
    def __init__(self, direcionado=False, ponderado=True):
        self.direcionado = direcionado
        self.ponderado = ponderado
        self.adj = {}

        pass

    def adicionar_vertices(self, vertices):
        if vertices not in self.adj:
            self.adj[vertices] = []
        pass

    def adicionar_arestas(self, u, v, peso=None):
        self.adicionar_vertices(u)
        self.adicionar_vertices(v)

        if not self.ponderado:
            peso = 1
        elif peso is None:
            raise ValueError("Peso deve ser fornecido para grafos ponderados.")

        self.adj[u].append((v, peso))
        if not self.direcionado:
            self.adj[v].append((u, peso))
        pass

    def vertices(self):
        pass

    def arestas(self):
        pass

    def limpar(self):
        pass

    def __str__(self):
        pass