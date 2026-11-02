# SmartNet Analyzer

Ferramenta de análise de redes urbanas para cidades inteligentes. A cidade é modelada como um grafo, em que os vértices representam bairros ou pontos de interesse e as arestas representam vias ou conexões com seus respectivos custos ou distâncias. Sobre esse grafo, a aplicação executa quatro algoritmos clássicos: DFS, BFS, Dijkstra e Kruskal.

## Identificação

| Campo | Informação |
|---|---|
| Integrante | Yago Duarte de Andrade |
| Matrícula | 202402185314 |
| Curso | Engenharia de Software |
| Disciplina | Análise e Complexidade de Algoritmos (IBM3121) |
| Professor | Cassius Figueiredo |
| Instituição | IBMEC |
| Período | 2026.2 |

## Sobre a aplicação

A aplicação é dividida em duas camadas:

- **Back-end em Python**: a estrutura do grafo e os quatro algoritmos foram implementados do zero, sem bibliotecas de grafos. Um servidor Flask expõe essas funções para a interface.
- **Front-end em HTML, CSS e JavaScript**: interface web para inserir o grafo, visualizar a estrutura em memória, executar os algoritmos e ver os resultados.

### Funcionalidades

- Grafos direcionados ou não-direcionados, ponderados ou não ponderados.
- Três formas de entrada: formulário (uma aresta por vez), texto em lote e upload de arquivo `.txt`.
- Exibição da lista de adjacência exatamente como está armazenada em memória.
- Desenho do grafo com destaque do resultado de cada algoritmo (árvore de busca, rota mínima e árvore geradora mínima).
- Modo mapa, com vértices posicionados por latitude e longitude e pesos calculados pela distância real em km.
- Cenários prontos: grafo da prova, bairros do Rio de Janeiro e capitais do mundo.
- Botão para limpar o grafo atual e inserir um novo, mantendo a aplicação em loop interativo.
- Botão para finalizar a aplicação, que encerra o servidor.

### Algoritmos

| Algoritmo | Aplicação no contexto | Resultado exibido | Complexidade |
|---|---|---|---|
| DFS (busca em profundidade) | Auditoria de rotas e verificação de conectividade | Ordem de visita, árvore de busca, vértices inalcançáveis | O(V + E) |
| BFS (busca em largura) | Propagação de alertas de emergência | Fila de execução, nível (número de saltos) de cada vértice | O(V + E) |
| Dijkstra | Rota de menor custo para veículos de emergência | Distância e rota da origem até cada vértice | O((V + E) log V) |
| Kruskal | Rede de fibra óptica de menor custo | Arestas da árvore geradora mínima e custo total | O(E log E) |

Observações:

- A DFS foi implementada de forma recursiva. O dicionário de pais permite reconstruir a árvore de busca.
- O Dijkstra usa fila de prioridade (`heapq`) e não aceita pesos negativos.
- O Kruskal usa Union-Find com compressão de caminho. Em grafos desconexos, o resultado é uma floresta. Em grafos direcionados, a aplicação informa que a árvore geradora mínima não se aplica.

### Estrutura de dados escolhida: lista de adjacência

O grafo é armazenado em um dicionário em que cada vértice aponta para a lista de seus vizinhos, no formato `(vizinho, peso)`:

```python
{
    'O': [('A', 2), ('B', 5), ('C', 4)],
    'A': [('O', 2), ('B', 2), ('D', 7), ('F', 12)],
    ...
}
```

Justificativa:

- Uma rede urbana é um grafo esparso: cada bairro se conecta a poucos outros, então E é muito menor que V².
- A lista de adjacência ocupa O(V + E) de memória, enquanto a matriz de adjacência ocupa O(V²).
- Percorrer os vizinhos de todos os vértices custa O(V + E) na lista e O(V²) na matriz. Por isso BFS e DFS rodam em O(V + E).
- Verificar se um vértice existe custa O(1), já que o dicionário usa tabela hash.

## Organização dos arquivos

```
SmartNet-Analyser.AC/
├── grafo.py              Classe Grafo (lista de adjacência)
├── algoritmos.py         DFS, BFS, Dijkstra, reconstrução de rota e Kruskal
├── server.py             Servidor Flask que liga a interface ao código Python
├── requirements.txt      Dependências
├── exemplos/
│   └── grafo_prova.txt   Grafo de exemplo no formato de entrada
└── static/
    ├── index.html        Estrutura da página
    ├── style.css         Estilo
    ├── app.js            Lógica da interface
    ├── cenarios.js       Cenários prontos
    └── vendor/           Bibliotecas de visualização (Leaflet e vis-network)
```

## Como executar

### Pré-requisitos

- Python 3.10 ou superior
- Git

### Passo a passo

1. Clone o repositório:

```bash
git clone https://github.com/SEU_USUARIO/SmartNet-Analyser.AC.git
cd SmartNet-Analyser.AC
```

2. (Opcional) Crie e ative um ambiente virtual:

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Inicie o servidor:

```bash
python server.py
```

5. Abra o navegador em **http://localhost:5000**.

Para encerrar, use o botão "Finalizar aplicação" na interface ou pressione `Ctrl+C` no terminal.

As bibliotecas de visualização estão incluídas no projeto, então a aplicação funciona sem internet. Apenas o fundo do modo mapa (ruas do OpenStreetMap) e as fontes dependem de conexão.

## Como usar

1. **Defina o tipo do grafo** na seção 01: direcionado e/ou ponderado. Para trocar o tipo de um grafo existente, use "Limpar grafo" antes.
2. **Insira o grafo** de uma das formas:
   - **Formulário (seção 02):** origem, destino e peso. Deixar o destino vazio adiciona um vértice isolado.
   - **Lote (seção 03):** cole o texto no formato descrito abaixo e clique em "Carregar".
   - **Arquivo (seção 03):** clique em "Abrir .txt" e selecione um arquivo no mesmo formato.
   - **Cenários (seção 04):** carregam grafos prontos.
3. **Confira a estrutura** no painel "Memória", que mostra a lista de adjacência gerada pelo Python.
4. **Escolha o vértice de origem** e clique em DFS, BFS, Dijkstra ou Kruskal.
5. No **Dijkstra**, a tabela mostra a distância e a rota até todos os vértices. Clique em uma linha para destacar a rota até aquele destino.

### Formato do arquivo de entrada

Uma aresta por linha, no formato `origem destino peso`. A primeira linha é opcional e define o tipo do grafo. Linhas vazias e linhas iniciadas com `#` são ignoradas.

```
NAO_DIRECIONADO PONDERADO
O A 2
O B 5
A B 2
B C 1
Z
```

- Primeira linha: `DIRECIONADO` ou `NAO_DIRECIONADO`, seguido de `PONDERADO` ou `NAO_PONDERADO`. Se omitida, vale o tipo marcado na interface.
- Linha com um único nome (como `Z`): adiciona um vértice isolado.
- Em grafos não ponderados, o peso pode ser omitido (`A B`).
- Nomes com espaços podem ser separados por ponto e vírgula: `Barra da Tijuca; Recreio; 12`.

O arquivo `exemplos/grafo_prova.txt` contém um exemplo completo.

## Validação

Os algoritmos foram conferidos com o grafo da prova (`exemplos/grafo_prova.txt`), a partir da origem O:

| Algoritmo | Resultado |
|---|---|
| BFS | O, A, B, C, D, F, E, T |
| DFS | O, A, B, C, E, D, T, F |
| Dijkstra (O até T) | Distância 13, rota O → A → B → D → T |
| Kruskal | 7 arestas, custo total 20 |