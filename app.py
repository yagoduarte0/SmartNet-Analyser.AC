"""
SmartNet Analyzer — interface (Streamlit).

A interface só CHAMA a classe Grafo (grafo.py) e os algoritmos (algoritmos.py).
Toda a lógica de grafo fica nos outros dois arquivos.

Rodar:  streamlit run app.py
"""
import os
import time

import pandas as pd
import streamlit as st

import algoritmos
from grafo import Grafo

# ─────────────────────────────────────────────────────────────
# Configuração da página e estilo
# ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="SmartNet Analyzer", page_icon="🏙️", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    .hero h1 { font-size: 2.2rem; margin-bottom: 0; }
    .hero p  { color: #8b949e; margin-top: .25rem; }
    .card {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 12px; padding: 1rem 1.2rem;
    }
    .pill {
        display: inline-block; padding: .15rem .6rem; border-radius: 999px;
        background: #1f6feb22; color: #58a6ff; font-size: .8rem;
        border: 1px solid #1f6feb55; margin-right: .3rem;
    }
    div[data-testid="stMetric"] {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 12px; padding: .8rem 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

ARESTAS_PROVA = [
    ("O", "A", 2), ("O", "B", 5), ("O", "C", 4), ("A", "B", 2),
    ("A", "D", 7), ("A", "F", 12), ("B", "C", 1), ("B", "D", 4),
    ("B", "E", 3), ("C", "E", 4), ("D", "E", 4), ("D", "T", 5),
    ("E", "T", 7), ("F", "T", 3),
]

# ─────────────────────────────────────────────────────────────
# Estado (sobrevive entre os cliques — é o "loop interativo")
# ─────────────────────────────────────────────────────────────
if "grafo" not in st.session_state:
    st.session_state.grafo = Grafo(direcionado=False, ponderado=True)
if "resultado" not in st.session_state:
    st.session_state.resultado = None  # (nome_algoritmo, dados)

g: Grafo = st.session_state.grafo


def novo_grafo(direcionado, ponderado):
    st.session_state.grafo = Grafo(direcionado=direcionado, ponderado=ponderado)
    st.session_state.resultado = None


def ler_arquivo(texto):
    """Formato do .txt:
    1ª linha (opcional): DIRECIONADO ou NAO_DIRECIONADO, e PONDERADO ou NAO_PONDERADO
    demais linhas: u v peso   (peso opcional se não ponderado)
    Linhas vazias e começando com # são ignoradas.
    """
    linhas = [l.strip() for l in texto.splitlines() if l.strip() and not l.strip().startswith("#")]
    direcionado, ponderado = False, True
    if linhas and linhas[0].split()[0].upper() in ("DIRECIONADO", "NAO_DIRECIONADO"):
        tokens = {t.upper() for t in linhas[0].split()}
        direcionado = "DIRECIONADO" in tokens
        ponderado = "NAO_PONDERADO" not in tokens
        linhas = linhas[1:]

    novo = Grafo(direcionado=direcionado, ponderado=ponderado)
    for n, linha in enumerate(linhas, start=1):
        partes = linha.split()
        if len(partes) == 1:
            novo.adicionar_vertices(partes[0])  # vértice isolado
        elif len(partes) == 2:
            novo.adicionar_arestas(partes[0], partes[1], None if ponderado else 1)
        elif len(partes) == 3:
            novo.adicionar_arestas(partes[0], partes[1], float(partes[2]))
        else:
            raise ValueError(f"Linha {n} inválida: '{linha}'")
    return novo


def fmt(x):
    """Mostra 2.0 como 2 e infinito como ∞."""
    if x == float("inf"):
        return "∞"
    return int(x) if float(x).is_integer() else round(x, 2)


def desenhar(grafo, destaque=None, cor_destaque="#f78166"):
    """Gera o grafo em DOT (Graphviz). 'destaque' = conjunto de arestas (u, v) para pintar."""
    destaque = destaque or set()
    seta = "->" if grafo.direcionado else "--"
    tipo = "digraph" if grafo.direcionado else "graph"
    dot = [
        f"{tipo} G {{",
        'bgcolor="transparent"; rankdir=LR; layout=neato; overlap=false; splines=true;',
        'node [shape=circle style=filled fillcolor="#1f6feb" fontcolor="white" '
        'color="#58a6ff" fontname="Helvetica" width=0.5 fixedsize=true];',
        'edge [color="#6e7681" fontcolor="#c9d1d9" fontname="Helvetica" fontsize=11];',
    ]
    for v in grafo.vertices():
        dot.append(f'"{v}";')
    for u, v, p in grafo.arestas():
        marcado = (u, v) in destaque or (not grafo.direcionado and (v, u) in destaque)
        label = f'label="{fmt(p)}"' if grafo.ponderado else ""
        estilo = f'color="{cor_destaque}" penwidth=3' if marcado else ""
        dot.append(f'"{u}" {seta} "{v}" [{label} {estilo}];')
    dot.append("}")
    return "\n".join(dot)


def arestas_do_caminho(caminho):
    return {(caminho[i], caminho[i + 1]) for i in range(len(caminho) - 1)}


# ─────────────────────────────────────────────────────────────
# SIDEBAR — entrada de dados
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Mapa da cidade")

    vazio = len(g.vertices()) == 0
    direcionado = st.toggle("Direcionado (vias de mão única)", value=g.direcionado, disabled=not vazio)
    ponderado = st.toggle("Ponderado (custos/distâncias)", value=g.ponderado, disabled=not vazio)
    if vazio and (direcionado != g.direcionado or ponderado != g.ponderado):
        novo_grafo(direcionado, ponderado)
        st.rerun()
    if not vazio:
        st.caption("🔒 Limpe o grafo para trocar o tipo.")

    st.markdown("#### ➕ Nova conexão")
    with st.form("form_aresta", clear_on_submit=True):
        c1, c2 = st.columns(2)
        u = c1.text_input("Origem", placeholder="ex: A").strip()
        v = c2.text_input("Destino", placeholder="ex: B").strip()
        peso = st.number_input("Peso", min_value=0.0, value=1.0, step=1.0, disabled=not g.ponderado)
        if st.form_submit_button("Adicionar aresta", width="stretch", type="primary"):
            if not u:
                st.error("Informe pelo menos a origem.")
            elif not v:
                g.adicionar_vertices(u)
                st.session_state.resultado = None
                st.toast(f"Bairro {u} adicionado (isolado)", icon="📍")
            else:
                try:
                    g.adicionar_arestas(u, v, peso)
                    st.session_state.resultado = None
                    st.toast(f"Conexão {u} — {v} adicionada", icon="✅")
                except ValueError as e:
                    st.error(str(e))

    st.markdown("#### 📁 Importar arquivo")
    arquivo = st.file_uploader("Arquivo .txt", type=["txt"], label_visibility="collapsed")
    if arquivo and st.button("Carregar arquivo", width="stretch"):
        try:
            st.session_state.grafo = ler_arquivo(arquivo.read().decode("utf-8"))
            st.session_state.resultado = None
            st.rerun()
        except ValueError as e:
            st.error(f"Erro no arquivo: {e}")

    if st.button("🎯 Carregar grafo da prova", width="stretch"):
        novo_grafo(direcionado=False, ponderado=True)
        for a, b, p in ARESTAS_PROVA:
            st.session_state.grafo.adicionar_arestas(a, b, p)
        st.rerun()

    st.divider()
    if st.button("🗑️ Limpar grafo", width="stretch"):
        g.limpar()
        st.session_state.resultado = None
        st.rerun()

    if st.button("⛔ Finalizar aplicação", width="stretch"):
        st.session_state.finalizar = True

# ─────────────────────────────────────────────────────────────
# Finalizar aplicação
# ─────────────────────────────────────────────────────────────
if st.session_state.get("finalizar"):
    st.markdown("## 👋 SmartNet Analyzer finalizado")
    st.write("O servidor foi encerrado. Pode fechar esta aba.")
    time.sleep(1)  # dá tempo da mensagem aparecer
    os._exit(0)   # encerra o processo do Streamlit

# ─────────────────────────────────────────────────────────────
# CABEÇALHO
# ─────────────────────────────────────────────────────────────
st.markdown(
    '<div class="hero"><h1>🏙️ SmartNet Analyzer</h1>'
    "<p>Infraestrutura de cidades inteligentes — conectividade e roteamento</p></div>",
    unsafe_allow_html=True,
)

verts = g.vertices()
if not verts:
    st.info("👈 Comece adicionando conexões na barra lateral, importando um arquivo ou carregando o grafo da prova.")
    st.stop()

_, pais_dfs = algoritmos.dfs(g, verts[0])
conexo = len(pais_dfs) == len(verts)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Bairros (V)", len(verts))
m2.metric("Conexões (E)", len(g.arestas()))
m3.metric("Tipo", ("Dir." if g.direcionado else "Não-dir.") + (" · Pond." if g.ponderado else ""))
m4.metric("Conexo", "Sim ✅" if conexo else "Não ⚠️",
          help="Verificado com DFS a partir do primeiro bairro" + (" (alcançabilidade, em grafo direcionado)" if g.direcionado else ""))

# ─────────────────────────────────────────────────────────────
# MAPA + MEMÓRIA
# ─────────────────────────────────────────────────────────────
resultado = st.session_state.resultado
destaque, cor = set(), "#f78166"
if resultado:
    nome, dados = resultado
    if nome == "Dijkstra" and dados.get("rota"):
        destaque, cor = arestas_do_caminho(dados["rota"]), "#f78166"
    elif nome == "Kruskal":
        destaque, cor = {(a, b) for a, b, _ in dados["arestas"]}, "#3fb950"
    elif nome in ("DFS", "BFS"):
        destaque, cor = {(p, f) for f, p in dados["pai"].items() if p is not None}, "#d29922"

col_mapa, col_mem = st.columns([3, 2], gap="large")

with col_mapa:
    st.markdown("### 🗺️ Mapa")
    st.graphviz_chart(desenhar(g, destaque, cor), width="stretch")

with col_mem:
    st.markdown("### 🧠 Memória — lista de adjacência")
    st.caption("Como o grafo está armazenado em `self.adj` (dicionário de listas)")
    tabela = [
        {"Vértice": u,
         "Vizinhos (vizinho, peso)": "  →  ".join(f"({x}, {fmt(p)})" for x, p in g.adj[u]) or "∅"}
        for u in verts
    ]
    st.dataframe(pd.DataFrame(tabela), hide_index=True, width="stretch")
    with st.expander("Ver saída do __str__()"):
        st.code(str(g), language="text")

st.divider()

# ─────────────────────────────────────────────────────────────
# ALGORITMOS
# ─────────────────────────────────────────────────────────────
st.markdown("### ⚡ Módulo de inteligência")

c_origem, c_b1, c_b2, c_b3, c_b4 = st.columns([2, 1, 1, 1, 1], vertical_alignment="bottom")
origem = c_origem.selectbox("Bairro de origem", verts)

if c_b1.button("🔍 DFS", width="stretch"):
    ordem, pai = algoritmos.dfs(g, origem)
    st.session_state.resultado = ("DFS", {"origem": origem, "ordem": ordem, "pai": pai})
    st.rerun()

if c_b2.button("📡 BFS", width="stretch"):
    ordem, nivel = algoritmos.bfs(g, origem)
    # pai da BFS: reconstruído a partir dos níveis só para desenhar a árvore
    pai = {origem: None}
    for x in ordem[1:]:
        pai[x] = next(u for u in ordem if nivel[u] == nivel[x] - 1 and any(w == x for w, _ in g.adj[u]))
    st.session_state.resultado = ("BFS", {"origem": origem, "ordem": ordem, "nivel": nivel, "pai": pai})
    st.rerun()

if c_b3.button("🚑 Dijkstra", width="stretch"):
    dist, pai = algoritmos.dijkstra(g, origem)
    st.session_state.resultado = ("Dijkstra", {"origem": origem, "dist": dist, "pai": pai, "rota": None})
    st.rerun()

tem_kruskal = hasattr(algoritmos, "kruskal")
if c_b4.button("🌐 Kruskal", width="stretch", disabled=not tem_kruskal,
               help=None if tem_kruskal else "Implemente kruskal(grafo) em algoritmos.py"):
    mst, custo = algoritmos.kruskal(g)
    st.session_state.resultado = ("Kruskal", {"arestas": mst, "custo": custo})
    st.rerun()

# ─────────────────────────────────────────────────────────────
# RESULTADOS
# ─────────────────────────────────────────────────────────────
if not resultado:
    st.caption("Escolha uma origem e execute um algoritmo.")
    st.stop()

nome, dados = resultado
st.markdown(f"#### Resultado — {nome}" + (f"  <span class='pill'>origem: {dados['origem']}</span>" if "origem" in dados else ""),
            unsafe_allow_html=True)

if nome == "DFS":
    st.markdown("**Ordem de visita:** " + " → ".join(dados["ordem"]))
    alcancados = len(dados["ordem"])
    if alcancados < len(verts):
        faltam = [x for x in verts if x not in dados["pai"]]
        st.warning(f"⚠️ {len(faltam)} bairro(s) inalcançável(is) a partir de {dados['origem']}: {', '.join(faltam)}")
    else:
        st.success(f"✅ Todos os {len(verts)} bairros são alcançáveis a partir de {dados['origem']}.")

    def arvore(no, prefixo=""):
        filhos = [f for f, p in dados["pai"].items() if p == no]
        linhas = []
        for i, f in enumerate(filhos):
            ultimo = i == len(filhos) - 1
            linhas.append(prefixo + ("└── " if ultimo else "├── ") + f)
            linhas += arvore(f, prefixo + ("    " if ultimo else "│   "))
        return linhas

    c1, c2 = st.columns(2)
    c1.markdown("**Árvore de busca em profundidade**")
    c1.code("\n".join([dados["origem"]] + arvore(dados["origem"])), language="text")
    c2.markdown("**Tabela de pais**")
    c2.dataframe(pd.DataFrame([{"Vértice": k, "Descoberto por": p or "— (raiz)"} for k, p in dados["pai"].items()]),
                 hide_index=True, width="stretch")

elif nome == "BFS":
    st.markdown("**Fila de execução (ordem de visita):** " + " → ".join(dados["ordem"]))
    c1, c2 = st.columns(2)
    c1.dataframe(pd.DataFrame([{"Vértice": x, "Saltos até a origem": dados["nivel"][x]} for x in dados["ordem"]]),
                 hide_index=True, width="stretch")
    ondas = {}
    for x, n in dados["nivel"].items():
        ondas.setdefault(n, []).append(x)
    c2.markdown("**Propagação em ondas**")
    for n in sorted(ondas):
        c2.markdown(f"<span class='pill'>onda {n}</span> " + ", ".join(ondas[n]), unsafe_allow_html=True)
    nao = [x for x in verts if x not in dados["nivel"]]
    if nao:
        st.warning(f"⚠️ Não alcançados pelo alerta: {', '.join(nao)}")

elif nome == "Dijkstra":
    linhas = []
    for x in verts:
        d = dados["dist"][x]
        rota = algoritmos.reconstruir_caminho(dados["pai"], x) if d != float("inf") else None
        linhas.append({"Destino": x, "Distância": fmt(d), "Rota": " → ".join(rota) if rota else "sem rota"})
    c1, c2 = st.columns([3, 2])
    c1.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")
    with c2:
        alcancaveis = [x for x in verts if x != dados["origem"] and dados["dist"][x] != float("inf")]
        if alcancaveis:
            destino = st.selectbox("Destacar rota até", alcancaveis,
                                   index=len(alcancaveis) - 1, key="destino_dijkstra")
            rota = algoritmos.reconstruir_caminho(dados["pai"], destino)
            if rota != dados["rota"]:
                dados["rota"] = rota
                st.rerun()
            st.metric(f"🚑 {dados['origem']} → {destino}", fmt(dados["dist"][destino]))
            st.caption(" → ".join(rota))

elif nome == "Kruskal":
    c1, c2 = st.columns([3, 2])
    c1.dataframe(pd.DataFrame([{"Aresta": f"{a} — {b}", "Custo": fmt(p)} for a, b, p in dados["arestas"]]),
                 hide_index=True, width="stretch")
    c2.metric("💰 Custo total da rede de fibra", fmt(dados["custo"]))
    c2.caption(f"{len(dados['arestas'])} arestas selecionadas")
    if len(dados["arestas"]) < len(verts) - 1:
        c2.warning("⚠️ Grafo desconexo: o resultado é uma floresta, não uma árvore única.")