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
        return list(self.adj.keys())

    def arestas(self):
        lista = []
        for u in self.adj:
            for v, peso in self.adj[u]:
                if self.direcionado or (u < v):
                    lista.append((u, v, peso))
        return lista

    def limpar(self):
        self.adj.clear()
        pass

    def __str__(self):
        linhas = []
        for u in self.adj:              # ← percorre cada vértice
            textos = []                 # ← zera a lista para CADA vértice
            for v, peso in self.adj[u]:
                textos.append(f"{v}: {peso}")
            linhas.append(f"{u} -> " + ", ".join(textos))
        return "\n".join(linhas)
