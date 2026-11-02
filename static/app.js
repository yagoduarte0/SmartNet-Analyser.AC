// ════════════════════════════════════════════════════════════════
// SmartNet Analyzer — front-end
// O site só guarda a lista de arestas e desenha. Quem monta a lista de
// adjacência e roda os algoritmos é o Python (server.py → grafo.py / algoritmos.py).
// ════════════════════════════════════════════════════════════════

const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];

const COR = { tinta: "#0a0a0a", papel: "#efece4", base: "#0a0a0a", rota: "#ff4d00", arvore: "#1f3fff", mst: "#00a35c", acido: "#d4ff00" };

const state = {
  direcionado: false,
  ponderado: true,
  vertices: [],          // nomes, na ordem de inserção
  coords: {},            // nome → [lat, lng] (só no mapa)
  arestas: [],           // [u, v, peso]
  modo: "grafo",
  resultado: null,       // { algo, dados }
  destaque: { arestas: new Set(), cor: null },
};

// ─────────────────────────── utilidades ───────────────────────────
function toast(msg, erro = false) {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "toast show" + (erro ? " err" : "");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => (t.className = "toast"), 2600);
}

const fmt = (x) => (x === null || x === undefined ? "∞" : Number.isInteger(x) ? x : Math.round(x * 10) / 10);
const chave = (u, v) => (state.direcionado ? `${u}→${v}` : [u, v].sort().join("↔"));
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function haversineKm([lat1, lon1], [lat2, lon2]) {
  const R = 6371, rad = Math.PI / 180;
  const dLat = (lat2 - lat1) * rad, dLon = (lon2 - lon1) * rad;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(dLon / 2) ** 2;
  return Math.round(2 * R * Math.asin(Math.sqrt(a)) * 10) / 10;
}

async function api(rota, corpo) {
  const r = await fetch(rota, {
    method: corpo ? "POST" : "GET",
    headers: { "Content-Type": "application/json" },
    body: corpo ? JSON.stringify(corpo) : undefined,
  });
  const json = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(json.erro || `Erro ${r.status}`);
  return json;
}

const payload = () => ({
  direcionado: state.direcionado,
  ponderado: state.ponderado,
  vertices: state.vertices,
  arestas: state.arestas,
});

// ─────────────────────────── edição do grafo ───────────────────────────
function addVertice(nome, coord) {
  if (!state.vertices.includes(nome)) state.vertices.push(nome);
  if (coord) state.coords[nome] = coord;
}

function addAresta(u, v, peso) {
  addVertice(u);
  addVertice(v);
  if (state.ponderado && (peso === null || peso === undefined || isNaN(peso))) {
    if (state.coords[u] && state.coords[v]) peso = haversineKm(state.coords[u], state.coords[v]);
    else throw new Error("Peso deve ser fornecido para grafos ponderados.");
  }
  if (peso < 0) throw new Error("Pesos negativos não são permitidos (quebram o Dijkstra).");
  const k = chave(u, v);
  const i = state.arestas.findIndex(([a, b]) => chave(a, b) === k);
  const aresta = [u, v, state.ponderado ? Number(peso) : null];
  if (i >= 0) state.arestas[i] = aresta;   // atualiza o peso em vez de duplicar
  else state.arestas.push(aresta);
}

function removerAresta(u, v) {
  const k = chave(u, v);
  state.arestas = state.arestas.filter(([a, b]) => chave(a, b) !== k);
  invalidar();
}

function limpar() {
  state.vertices = [];
  state.coords = {};
  state.arestas = [];
  invalidar();
}

function invalidar() {
  state.resultado = null;
  state.destaque = { arestas: new Set(), cor: null };
  $$(".algo").forEach((b) => b.classList.remove("active"));
  $("#resultado").innerHTML = '<p class="muted">Escolha uma origem e execute um algoritmo.</p>';
  atualizar();
}

function setTipo(direcionado, ponderado) {
  state.direcionado = direcionado;
  state.ponderado = ponderado;
  $("#chk-dir").checked = direcionado;
  $("#chk-pond").checked = ponderado;
}

// Formato do texto: "u v peso" por linha. Aceita separador espaço, vírgula ou ponto e vírgula
// (use ; ou , quando o nome tiver espaços: "Barra da Tijuca; Recreio; 12").
function lerTexto(texto) {
  let linhas = texto.split(/\r?\n/).map((l) => l.trim()).filter((l) => l && !l.startsWith("#"));
  let dir = state.direcionado, pond = state.ponderado;
  if (linhas.length && /^(NAO_)?DIRECIONADO\b/i.test(linhas[0])) {
    const t = linhas[0].toUpperCase().split(/\s+/);
    dir = t.includes("DIRECIONADO");
    pond = !t.includes("NAO_PONDERADO");
    linhas = linhas.slice(1);
  }
  limpar();
  setTipo(dir, pond);
  linhas.forEach((linha, n) => {
    const partes = (/[;,]/.test(linha) ? linha.split(/[;,]/) : linha.split(/\s+/)).map((p) => p.trim()).filter(Boolean);
    if (partes.length === 1) addVertice(partes[0]);
    else if (partes.length === 2) addAresta(partes[0], partes[1], pond ? null : 1);
    else if (partes.length === 3) {
      const p = Number(partes[2].replace(",", "."));
      if (isNaN(p)) throw new Error(`Linha ${n + 1}: peso inválido "${partes[2]}"`);
      addAresta(partes[0], partes[1], p);
    } else throw new Error(`Linha ${n + 1} inválida: "${linha}"`);
  });
}

function carregarCenario(id) {
  const c = CENARIOS[id];
  limpar();
  setTipo(c.direcionado, c.ponderado);
  Object.entries(c.vertices).forEach(([nome, coord]) => addVertice(nome, coord));
  c.arestas.forEach(([u, v, p]) => addAresta(u, v, p ?? null));
  setModo(c.modo);
  invalidar();
  toast(`Cenário carregado: ${c.nome}`);
  if (c.modo === "mapa") setTimeout(enquadrarMapa, 50);
}

// ─────────────────────────── sincroniza com o Python ───────────────────────────
async function atualizar() {
  const vazio = state.vertices.length === 0;
  $("#chk-dir").disabled = !vazio;
  $("#chk-pond").disabled = !vazio;
  $("#lock-hint").hidden = vazio;
  $("#in-peso").disabled = !state.ponderado;
  $("#seta-form").textContent = state.direcionado ? "→" : "—";
  $("#empty").hidden = !vazio;

  // listas de vértices (datalist e select de origem)
  $("#lista-vertices").innerHTML = state.vertices.map((v) => `<option value="${esc(v)}">`).join("");
  const sel = $("#sel-origem"), atual = sel.value;
  sel.innerHTML = state.vertices.map((v) => `<option>${esc(v)}</option>`).join("");
  if (state.vertices.includes(atual)) sel.value = atual;

  desenhar();

  if (vazio) {
    $("#st-v").textContent = 0;
    $("#st-e").textContent = 0;
    $("#st-conexo").textContent = "—";
    $("#mem-lista").innerHTML = '<p class="hint">Vazio: <code>self.adj = {}</code></p>';
    $("#mem-str").textContent = "";
    return;
  }

  try {
    const { memoria, conexo } = await api("/api/grafo", payload());
    $("#st-v").textContent = memoria.num_vertices;
    $("#st-e").textContent = memoria.num_arestas;
    $("#st-conexo").textContent = conexo ? "Sim" : "Não";
    $("#st-conexo-box").classList.toggle("bad", !conexo);
    renderMemoria(memoria);
  } catch (e) {
    toast(e.message, true);
  }
}

function renderMemoria(mem) {
  $("#mem-lista").innerHTML = Object.entries(mem.adj).map(([u, viz]) => `
    <div class="mem-item">
      <div class="mem-key" title="${esc(u)}">${esc(u)}</div>
      <div class="mem-arrow">→</div>
      <div class="mem-vals">${
        viz.length
          ? viz.map(([v, p]) => `<span class="del" data-u="${esc(u)}" data-v="${esc(v)}" title="clique para remover a aresta">(${esc(v)}, ${fmt(p)})</span>`).join("")
          : "<em>[ ]</em>"
      }</div>
    </div>`).join("");
  $("#mem-str").textContent = mem.texto;
}

// ─────────────────────────── visualização: modo grafo (vis-network) ───────────────────────────
let rede = null;
const nos = new vis.DataSet();
const arestasDS = new vis.DataSet();

function iniciarRede() {
  rede = new vis.Network($("#rede"), { nodes: nos, edges: arestasDS }, {
    nodes: {
      shape: "box", margin: { top: 7, bottom: 7, left: 10, right: 10 },
      color: { background: COR.tinta, border: COR.tinta, highlight: { background: COR.acido, border: COR.tinta }, hover: { background: COR.acido, border: COR.tinta } },
      font: { color: COR.papel, face: "IBM Plex Mono", size: 15, bold: { color: COR.papel } },
      borderWidth: 2, shapeProperties: { borderRadius: 0 },
      shadow: { enabled: true, color: COR.tinta, size: 0, x: 4, y: 4 },
    },
    edges: {
      color: { color: COR.base, highlight: COR.rota, hover: COR.rota }, width: 1.5,
      font: { color: COR.tinta, face: "IBM Plex Mono", size: 12, strokeWidth: 0, background: "#ffffff", align: "middle" },
      smooth: false,
    },
    physics: { solver: "forceAtlas2Based", forceAtlas2Based: { gravitationalConstant: -60, springLength: 110 }, stabilization: { iterations: 200 } },
    interaction: { hover: true },
  });
}

function desenharRede() {
  const ids = new Set(state.vertices);
  nos.remove(nos.getIds().filter((id) => !ids.has(id)));
  nos.update(state.vertices.map((v) => ({ id: v, label: v })));

  const novas = state.arestas.map(([u, v, p]) => {
    const marcada = state.destaque.arestas.has(chave(u, v));
    return {
      id: chave(u, v), from: u, to: v,
      label: state.ponderado ? String(fmt(p)) : undefined,
      arrows: state.direcionado ? { to: { enabled: true, scaleFactor: .7 } } : undefined,
      color: { color: marcada ? state.destaque.cor : COR.base },
      width: marcada ? 6 : 1.5,
    };
  });
  const idsArestas = new Set(novas.map((a) => a.id));
  arestasDS.remove(arestasDS.getIds().filter((id) => !idsArestas.has(id)));
  arestasDS.update(novas);
}

// ─────────────────────────── visualização: modo mapa (Leaflet) ───────────────────────────
let mapa = null, camada = null, ferramenta = null, selecionado = null;

function iniciarMapa() {
  mapa = L.map("mapa", { worldCopyJump: true, zoomControl: true }).setView([-22.95, -43.3], 11);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; OpenStreetMap', maxZoom: 19,
}).addTo(mapa);
  camada = L.layerGroup().addTo(mapa);

  mapa.on("click", (e) => {
    if (ferramenta !== "add") return;
    const nome = prompt("Nome do ponto (bairro, cidade, local):");
    if (!nome || !nome.trim()) return;
    addVertice(nome.trim(), [Math.round(e.latlng.lat * 1e4) / 1e4, Math.round(e.latlng.lng * 1e4) / 1e4]);
    invalidar();
    toast(`+ ${nome.trim()}`);
  });
}

function desenharMapa() {
  if (!mapa) return;
  camada.clearLayers();

  state.arestas.forEach(([u, v, p]) => {
    if (!state.coords[u] || !state.coords[v]) return;
    const marcada = state.destaque.arestas.has(chave(u, v));
    const linha = L.polyline([state.coords[u], state.coords[v]], {
      color: marcada ? state.destaque.cor : COR.tinta,
      weight: marcada ? 6 : 2,
      opacity: 1,
      dashArray: state.direcionado && !marcada ? "8 6" : null,
    }).addTo(camada);
    // rótulo do peso: fixo quando o mapa tem poucos pontos, no hover quando tem muitos
    if (state.ponderado) linha.bindTooltip(`${fmt(p)} km`, { permanent: state.vertices.length <= 10 || marcada, className: "elabel", direction: "center" });
  });

  state.vertices.forEach((v) => {
    if (!state.coords[v]) return;
    const sel = selecionado === v;
    L.circleMarker(state.coords[v], {
      radius: sel ? 10 : 7, color: COR.tinta, weight: 3,
      fillColor: sel ? COR.acido : COR.papel, fillOpacity: 1,
    })
      .bindTooltip(v, { permanent: true, direction: "top", offset: [0, -8], className: "vlabel" })
      .on("click", (e) => { L.DomEvent.stopPropagation(e); clicarPonto(v); })
      .addTo(camada);
  });

  const semCoord = state.vertices.filter((v) => !state.coords[v]).length;
  $("#map-hint").textContent =
    ferramenta === "add" ? "Clique no mapa para criar um ponto." :
    ferramenta === "ligar" ? (selecionado ? `Origem: ${selecionado}. Clique no destino.` : "Clique no ponto de origem.") :
    semCoord ? `${semCoord} vértice(s) sem localização aparecem só no modo Grafo.` :
    "Use as ferramentas para criar pontos e ligações.";
}

function clicarPonto(v) {
  if (ferramenta !== "ligar") return;
  if (!selecionado) { selecionado = v; desenharMapa(); return; }
  if (selecionado === v) { selecionado = null; desenharMapa(); return; }
  try {
    addAresta(selecionado, v, state.ponderado ? haversineKm(state.coords[selecionado], state.coords[v]) : 1);
    toast(`${selecionado} ${state.direcionado ? "→" : "—"} ${v}`);
  } catch (e) { toast(e.message, true); }
  selecionado = null;
  invalidar();
}

function enquadrarMapa() {
  const pts = state.vertices.map((v) => state.coords[v]).filter(Boolean);
  if (pts.length) mapa.fitBounds(pts, { padding: [40, 40] });
}

function setModo(modo) {
  state.modo = modo;
  $$(".mode").forEach((b) => b.classList.toggle("active", b.dataset.modo === modo));
  $("#rede").hidden = modo !== "grafo";
  $("#mapa").hidden = modo !== "mapa";
  $("#map-tools").hidden = modo !== "mapa";
  $("#canvas-wrap").dataset.label = modo === "mapa" ? "vista: mapa" : "vista: grafo";
  if (modo === "mapa") {
    if (!mapa) iniciarMapa();
    setTimeout(() => { mapa.invalidateSize(); desenharMapa(); }, 30);
  } else if (rede) {
    setTimeout(() => rede.fit(), 30);
  }
}

function desenhar() {
  desenharRede();
  if (state.modo === "mapa") desenharMapa();
  const leg = $("#legend");
  if (state.destaque.cor) {
    const nomes = { [COR.rota]: "rota mais curta", [COR.arvore]: "árvore de busca", [COR.mst]: "árvore geradora mínima" };
    leg.innerHTML = `<i style="background:${state.destaque.cor}"></i>${nomes[state.destaque.cor]}`;
    leg.hidden = false;
  } else leg.hidden = true;
}

// ─────────────────────────── algoritmos ───────────────────────────
const COMPLEXIDADE = {
  dfs: "O(V + E)", bfs: "O(V + E)", dijkstra: "O((V + E) log V)", kruskal: "O(E log E)",
};

async function executar(algo) {
  if (!state.vertices.length) return toast("Carregue um grafo primeiro.", true);
  $$(".algo").forEach((b) => b.classList.toggle("active", b.dataset.algo === algo));
  try {
    const dados = await api("/api/executar", { ...payload(), algoritmo: algo, origem: $("#sel-origem").value });
    state.resultado = { algo, dados };
    renderResultado();
  } catch (e) {
    $("#resultado").innerHTML = `<div class="alert err">${esc(e.message)}</div>`;
    state.destaque = { arestas: new Set(), cor: null };
    desenhar();
  }
}

const seq = (lista) => `<div class="seq">${lista.map((v) => `<span class="node">${esc(v)}</span>`).join('<span class="sep">→</span>')}</div>`;
const titulo = (nome, origem, algo) => `
  <div class="res-title"><h3>${nome}</h3>
    ${origem ? `<span class="pill">origem: ${esc(origem)}</span>` : ""}
    <span class="pill cx">${COMPLEXIDADE[algo]}</span></div>`;

function arvoreTexto(raiz, pai) {
  const filhos = {};
  Object.entries(pai).forEach(([f, p]) => { if (p !== null) (filhos[p] ??= []).push(f); });
  const linhas = [raiz];
  (function rec(no, pre) {
    (filhos[no] || []).forEach((f, i, arr) => {
      const ult = i === arr.length - 1;
      linhas.push(pre + (ult ? "└── " : "├── ") + f);
      rec(f, pre + (ult ? "    " : "│   "));
    });
  })(raiz, "");
  return linhas.join("\n");
}

function arestasArvore(pai) {
  return new Set(Object.entries(pai).filter(([, p]) => p !== null).map(([f, p]) => chave(p, f)));
}

function renderResultado(destinoDijkstra) {
  const { algo, dados } = state.resultado;
  const origem = $("#sel-origem").value;
  let html = "";

  if (algo === "dfs") {
    state.destaque = { arestas: arestasArvore(dados.pai), cor: COR.arvore };
    html = titulo("Busca em Profundidade (DFS)", origem, algo) +
      `<p class="label">Ordem de visita</p>${seq(dados.ordem)}` +
      (dados.inalcancaveis.length
        ? `<div class="alert warn">${dados.inalcancaveis.length} vértice(s) inalcançável(is) a partir de ${esc(origem)}: <b>${dados.inalcancaveis.map(esc).join(", ")}</b>. Grafo não conexo.</div>`
        : `<div class="alert ok">Todos os ${dados.ordem.length} vértices alcançáveis a partir de ${esc(origem)}.</div>`) +
      `<div class="grid2">
        <div class="box"><h4>Árvore de busca</h4><pre>${esc(arvoreTexto(origem, dados.pai))}</pre></div>
        <div class="box"><h4>Pai de cada vértice</h4><table><tr><th>Vértice</th><th>Descoberto por</th></tr>
          ${Object.entries(dados.pai).map(([v, p]) => `<tr><td>${esc(v)}</td><td>${p === null ? "— raiz" : esc(p)}</td></tr>`).join("")}
        </table></div></div>`;
  }

  if (algo === "bfs") {
    state.destaque = { arestas: arestasArvore(dados.pai), cor: COR.arvore };
    const ondas = {};
    dados.ordem.forEach((v) => (ondas[dados.nivel[v]] ??= []).push(v));
    html = titulo("Busca em Largura (BFS)", origem, algo) +
      `<p class="label">Fila de execução</p>${seq(dados.ordem)}` +
      (dados.inalcancaveis.length ? `<div class="alert warn">O alerta não chega em: <b>${dados.inalcancaveis.map(esc).join(", ")}</b></div>` : "") +
      `<div class="grid2">
        <div class="box"><h4>Propagação em ondas</h4>${Object.entries(ondas).map(([n, vs]) =>
          `<div class="wave"><span class="pill">onda ${n}</span>${vs.map(esc).join(", ")}</div>`).join("")}</div>
        <div class="box"><h4>Saltos até a origem (caminho mais curto sem peso)</h4><table><tr><th>Vértice</th><th>Saltos</th></tr>
          ${dados.ordem.map((v) => `<tr><td>${esc(v)}</td><td>${dados.nivel[v]}</td></tr>`).join("")}
        </table></div></div>`;
  }

  if (algo === "dijkstra") {
    const alcancaveis = state.vertices.filter((v) => v !== origem && dados.dist[v] !== null);
    const destino = destinoDijkstra ?? alcancaveis.reduce((m, v) => (m === null || dados.dist[v] > dados.dist[m] ? v : m), null);
    const rota = destino ? dados.rotas[destino] : null;
    state.destaque = { arestas: new Set((rota || []).slice(1).map((v, i) => chave(rota[i], v))), cor: COR.rota };
    const un = state.coords[origem] && state.ponderado ? " km" : "";
    html = titulo("Dijkstra / rota mínima", origem, algo) +
      (destino ? `<div class="grid2" style="margin-bottom:1rem">
        <div class="box"><h4>Custo ${esc(origem)} → ${esc(destino)}</h4><div class="big">${fmt(dados.dist[destino])}<small>${un}</small></div></div>
        <div class="box"><h4>Rota destacada</h4>${seq(rota)}</div></div>` : "") +
      `<div class="box"><h4>Distâncias a partir de ${esc(origem)} · clique numa linha para destacar a rota</h4>
        <table><tr><th>Destino</th><th>Distância</th><th>Rota</th></tr>
        ${state.vertices.map((v) => {
          const r = dados.rotas[v];
          return `<tr class="${r && v !== origem ? "click" : ""} ${v === destino ? "sel" : ""}" data-dest="${esc(v)}">
            <td>${esc(v)}</td><td>${fmt(dados.dist[v])}${dados.dist[v] !== null ? un : ""}</td>
            <td>${r ? r.map(esc).join(" → ") : '<span class="muted">sem rota</span>'}</td></tr>`;
        }).join("")}</table></div>`;
  }

  if (algo === "kruskal") {
    state.destaque = { arestas: new Set(dados.arestas.map(([u, v]) => chave(u, v))), cor: COR.mst };
    const un = Object.keys(state.coords).length ? " km" : "";
    html = titulo("Kruskal / árvore geradora mínima", null, algo) +
      (dados.floresta ? `<div class="alert warn">Grafo desconexo: o resultado é uma floresta (uma árvore por componente).</div>` : "") +
      `<div class="grid2">
        <div class="box"><h4>Custo total da rede</h4><div class="big">${fmt(dados.custo)}<small>${un}</small></div>
          <p class="hint">${dados.arestas.length} arestas selecionadas para ${state.vertices.length} vértices</p></div>
        <div class="box"><h4>Arestas selecionadas (em ordem)</h4><table><tr><th>#</th><th>Aresta</th><th>Custo</th></tr>
          ${dados.arestas.map(([u, v, p], i) => `<tr><td>${i + 1}</td><td>${esc(u)} — ${esc(v)}</td><td>${fmt(p)}</td></tr>`).join("")}
        </table></div></div>`;
  }

  $("#resultado").innerHTML = html;
  $$("#resultado tr.click").forEach((tr) => tr.addEventListener("click", () => renderResultado(tr.dataset.dest)));
  desenhar();
}

// ─────────────────────────── eventos ───────────────────────────
$("#form-aresta").addEventListener("submit", (e) => {
  e.preventDefault();
  const u = $("#in-u").value.trim(), v = $("#in-v").value.trim();
  const pesoTxt = $("#in-peso").value.trim();
  try {
    if (!v) { addVertice(u); toast(`+ ${u} (isolado)`); }
    else {
      addAresta(u, v, state.ponderado ? (pesoTxt === "" ? null : Number(pesoTxt)) : 1);
      toast(`${u} ${state.direcionado ? "→" : "—"} ${v}`);
    }
    $("#in-u").value = ""; $("#in-v").value = ""; $("#in-peso").value = "";
    $("#in-u").focus();
    invalidar();
  } catch (err) { toast(err.message, true); }
});

$("#btn-lote").addEventListener("click", () => {
  try {
    lerTexto($("#in-lote").value);
    invalidar();
    toast(`Grafo carregado: ${state.vertices.length} vértices, ${state.arestas.length} arestas`);
    if (rede) setTimeout(() => rede.fit(), 400);
  } catch (e) { toast(e.message, true); }
});

$("#in-arquivo").addEventListener("change", async (e) => {
  const f = e.target.files[0];
  if (!f) return;
  $("#in-lote").value = await f.text();
  $("#btn-lote").click();
  e.target.value = "";
});

$$(".preset").forEach((b) => b.addEventListener("click", () => carregarCenario(b.dataset.preset)));
$$(".mode").forEach((b) => b.addEventListener("click", () => { setModo(b.dataset.modo); if (b.dataset.modo === "mapa") enquadrarMapa(); }));
$$(".algo").forEach((b) => b.addEventListener("click", () => executar(b.dataset.algo)));

$("#chk-dir").addEventListener("change", (e) => { state.direcionado = e.target.checked; atualizar(); });
$("#chk-pond").addEventListener("change", (e) => { state.ponderado = e.target.checked; atualizar(); });

$("#sel-origem").addEventListener("change", () => {
  if (state.resultado && state.resultado.algo !== "kruskal") executar(state.resultado.algo);
});

$("#mem-lista").addEventListener("click", (e) => {
  const s = e.target.closest("span.del");
  if (s && confirm(`Remover a aresta ${s.dataset.u} ${state.direcionado ? "→" : "—"} ${s.dataset.v}?`)) removerAresta(s.dataset.u, s.dataset.v);
});

["add", "ligar"].forEach((t) => $(`#tool-${t}`).addEventListener("click", () => {
  ferramenta = ferramenta === t ? null : t;
  selecionado = null;
  $("#tool-add").classList.toggle("on", ferramenta === "add");
  $("#tool-ligar").classList.toggle("on", ferramenta === "ligar");
  $("#mapa").style.cursor = ferramenta === "add" ? "crosshair" : "";
  desenharMapa();
}));

$("#btn-limpar").addEventListener("click", () => {
  if (state.vertices.length && !confirm("Apagar o grafo atual?")) return;
  limpar();
  toast("Grafo apagado");
});

$("#btn-finalizar").addEventListener("click", async () => {
  if (!confirm("Finalizar a aplicação? O servidor será encerrado.")) return;
  try { await api("/api/finalizar", {}); } catch (_) { /* servidor já caiu */ }
  $("#overlay").hidden = false;
});

// ─────────────────────────── início ───────────────────────────
iniciarRede();
api("/api/status").then((s) => {
  const b = $('.algo[data-algo="kruskal"]');
  b.disabled = !s.kruskal;
  if (!s.kruskal) b.title = "Implemente kruskal(grafo) em algoritmos.py";
}).catch(() => {});
atualizar();
