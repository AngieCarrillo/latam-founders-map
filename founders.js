/* Women founders view: Startupeable-style "where she started, where she builds today" globe. */
(() => {
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const flag = a2 => a2.toUpperCase().replace(/./g, ch => String.fromCodePoint(127397 + ch.charCodeAt(0)));
  const initials = n => { const w = n.replace(/[".]/g, "").split(/\s+/).filter(Boolean); return (w[0][0] + (w.length > 1 ? w[w.length - 1][0] : "")).toUpperCase(); };
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

  const FC = window.FC;
  const P = window.FW.map((r, i) => ({
    i, n: r[0], src: r[1], aurora: r[1] === 2, inv: r[9] === "I", o: r[2], co: r[3], dp: r[4], c: r[5], ll: r[6], desc: r[8] || "",
    u: /^https?:/.test(r[7]) ? r[7] : "https://www.startupeable.com" + r[7]
  }));
  const cname = id => FC[id][0];
  // Aurora's list names a country, not a city or a birthplace: place her at the country, no arc.
  P.forEach(p => { p.home = p.o === p.dp; if (p.aurora || p.src === 4) { p.c = cname(p.dp); p.ll = FC[p.dp][2]; } });
  const cls = p => p.inv ? "inv" : "";
  const inKind = p => st.kind === "all" || (st.kind === "inv") === p.inv;
  const NOTE = p => String(p.src === 2 ? 1 : p.src === 1 ? 2 : p.src);
  const cflag = id => flag(FC[id][1]);
  const byTopo = {}; Object.entries(FC).forEach(([id, v]) => { byTopo[v[3]] = id; });

  const st = { sel: null, dest: null, kind: "all", q: "", hot: null };
  const visible = () => P.filter(p => inKind(p) && (!st.sel || p.o === st.sel));

  /* ---------- globe ---------- */
  const W = 600, R0 = 282;
  const svg = d3.select("#globe");
  const proj = d3.geoOrthographic().scale(R0).translate([W / 2, W / 2]).clipAngle(90).rotate([80, -8]);
  const gp = d3.geoPath(proj);
  const land = topojson.feature(window.WORLD, window.WORLD.objects.countries).features;
  const gSphere = svg.append("path").attr("class", "g-sphere");
  const gGrat = svg.append("path").attr("class", "g-grat");
  const gLand = svg.append("g"), gLab = svg.append("g").attr("class", "i-labels");
  const grat = d3.geoGraticule10();
  // shaded like the Investors map: darker = more founders who started in that country
  const SHADE = n => !n ? null : n <= 3 ? "var(--map-1)" : n <= 15 ? "var(--map-2)" : n <= 40 ? "var(--map-3)" : "var(--map-4)";
  const startCount = id => P.filter(p => inKind(p) && p.o === id).length;
  const countries = gLand.selectAll("path").data(land).join("path")
    .attr("class", "i-land")
    .on("click", (e, d) => { const id = byTopo[d.properties.name]; if (id && startCount(id)) select(id); })
    .on("keydown", (e, d) => { const id = byTopo[d.properties.name]; if (id && startCount(id) && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); select(id); } });
  countries.append("title");
  const labelled = land.filter(f => byTopo[f.properties.name]).map(f => {
    let best = f;
    if (f.geometry.type === "MultiPolygon") best = f.geometry.coordinates.map(c => ({ type: "Polygon", coordinates: c })).sort((x, y) => d3.geoArea(y) - d3.geoArea(x))[0];
    return { id: byTopo[f.properties.name], ll: d3.geoCentroid(best) };
  });

  function drawGlobe() {
    gSphere.attr("d", gp({ type: "Sphere" }));
    gGrat.attr("d", gp(grat));
    const r = proj.rotate(), c = [-r[0], -r[1]];
    countries.attr("d", gp)
      .each(function (d) {
        const id = byTopo[d.properties.name], n = id ? startCount(id) : 0;
        d3.select(this).classed("has", !!n).style("fill", SHADE(n))
          .classed("sel", !!id && id === st.sel)
          .classed("dest", !!id && !!st.dest && id === st.dest && id !== st.sel)
          .attr("tabindex", n ? 0 : null).attr("role", n ? "button" : null)
          .attr("aria-label", n ? `${cname(id)}: ${n} women founders` : null)
          .select("title").text(d.properties.name + (n ? ` · ${n}` : ""));
      });
    const vis = labelled.filter(d => startCount(d.id) && d3.geoDistance(d.ll, c) < Math.PI / 2 - 0.05);
    gLab.selectAll("text").data(vis, d => d.id).join("text")
      .attr("transform", d => `translate(${proj(d.ll).join(",")})`)
      .attr("dy", "0.35em")
      .classed("on-sel", d => d.id === st.sel)
      .text(d => startCount(d.id));
  }

  function rotateTo(ll) {
    const from = proj.rotate(), to = [-ll[0], Math.max(-60, Math.min(60, -ll[1])), 0];
    if (reduce) { proj.rotate(to); drawGlobe(); return; }
    const it = d3.interpolate(from, to);
    d3.transition().duration(900).ease(d3.easeCubicInOut).tween("rot", () => t => { proj.rotate(it(t)); drawGlobe(); });
  }
  function focusFor(id) { return id ? FC[id][2] : [-72, 10]; }

  svg.call(d3.drag().on("drag", e => {
    const r = proj.rotate(), k = 75 / proj.scale();
    proj.rotate([r[0] + e.dx * k, Math.max(-80, Math.min(80, r[1] - e.dy * k)), 0]); drawGlobe();
  }));
  const zoom = f => { proj.scale(Math.max(R0 * 0.8, Math.min(R0 * 3, proj.scale() * f))); drawGlobe(); };
  document.getElementById("gZoomIn").onclick = () => zoom(1.3);
  document.getElementById("gZoomOut").onclick = () => zoom(1 / 1.3);
  document.getElementById("gWorld").onclick = () => { proj.scale(R0); select(null); };

  /* ---------- left column: search, kind, country list ---------- */
  const search = document.getElementById("fSearch");
  search.addEventListener("input", () => { st.q = search.value.trim().toLowerCase(); renderList(); });

  function renderList() {
    const base = P.filter(inKind);
    const counts = d3.rollups(base, v => v.length, p => p.o).sort((a, b) => b[1] - a[1] || cname(a[0]).localeCompare(cname(b[0])));
    const q = st.q;
    const nq = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
    const cs = counts.filter(([id]) => !q || nq(cname(id)).includes(nq(q)));
    let h = `<button class="f-country${!st.sel ? " on" : ""}" data-c=""><span>🌎 All countries</span><b>${base.length}</b></button>`;
    h += cs.map(([id, n]) => `<button class="f-country${st.sel === id ? " on" : ""}" data-c="${id}"><span>${cflag(id)} ${esc(cname(id))}</span><b>${n}</b></button>`).join("");
    if (q) {
      const ppl = base.filter(p => nq(p.n + " " + p.co).includes(nq(q))).slice(0, 8);
      if (ppl.length) h += `<p class="filter-label f-sub">Founders</p>` + ppl.map(p => `<button class="f-country" data-c="${p.o}" data-p="${p.i}"><span>${esc(p.n)}</span><small>${esc(p.co)}</small></button>`).join("");
      if (!cs.length && !ppl.length) h += `<p class="muted f-empty">No country or founder matches “${esc(search.value)}”.</p>`;
    }
    const box = document.getElementById("fCountries"); box.innerHTML = h;
  }
  document.getElementById("fCountries").addEventListener("click", e => {
    const b = e.target.closest(".f-country"); if (!b) return;
    select(b.dataset.c || null, b.dataset.p ? +b.dataset.p : null);
  });

  /* ---------- right panel ---------- */
  const panel = document.getElementById("fPanel");
  function row(p) {
    const route = p.src === 4 && p.home ? `${cflag(p.dp)} ${esc(p.c)}` : p.src === 4 ? `${esc(cname(p.o))} → ${esc(p.c)}` : p.aurora ? `${cflag(p.dp)} Builds in ${esc(p.c)}` : p.home ? `${cflag(p.o)} ${esc(p.c)}` : `${esc(cname(p.o))} → ${esc(p.c)}`;
    return `<a class="f-row ${cls(p)}${st.hot === p.i ? " hot" : ""}" href="${esc(p.u)}" target="_blank" rel="noopener" data-p="${p.i}">
      <span class="f-av" aria-hidden="true">${initials(p.n)}</span>
      <span class="f-who"><b>${esc(p.n)}<sup class="f-note" title="${["", "Startupeable Diaspora map", "Aurora Top 30", "Added from my network and research", "Forbes México 50 angels", "Harlem Capital Black & Latino Founder Report"][p.src]}">${NOTE(p)}</sup>${p.inv ? `<span class="f-role">Investor</span>` : ""}</b><small>${esc(p.co)}</small>${p.desc ? `<span class="f-desc">${esc(p.desc)}</span>` : ""}<span class="f-route">${route}</span></span>
      <span class="f-go" aria-hidden="true">↗</span></a>`;
  }
  function renderPanel() {
    const vis = visible();
    const listed = vis.filter(p => !st.dest || p.dp === st.dest);
    const founders = listed.filter(p => !p.inv), investors = listed.filter(p => p.inv);
    let h = "";
    if (st.sel) h += `<button class="f-back" id="fBack">← All countries</button>`;
    h += `<h3>${st.sel ? cflag(st.sel) + " " + esc(cname(st.sel)) : "Where she started, where she builds"}</h3>`;
    const nI = vis.filter(p => p.inv).length, nF = vis.length - nI;
    h += `<p>${nF} women founder${nF === 1 ? "" : "s"}</p>`;
    // destination chips
    const dests = d3.rollups(vis, v => v.length, p => p.dp).sort((a, b) => (a[0] === st.sel) - (b[0] === st.sel) || b[1] - a[1]);
    h += `<div class="chips f-dests">` + dests.map(([id, n]) => {
      const lbl = st.sel && id === st.sel ? `${cflag(id)} Stayed in ${esc(cname(id))}` : `${cflag(id)} ${esc(cname(id))}`;
      return `<button class="chip" data-d="${id}" aria-pressed="${st.dest === id}">${lbl} · ${n}</button>`;
    }).join("") + `</div>`;
    h += `<p class="f-hint">Click a name to open where she was listed.</p>`;
    if (founders.length) h += `<div class="group"><h4>Founders · ${founders.length}</h4>${founders.map(row).join("")}</div>`;
    if (!listed.length) h += `<p class="muted">Nobody here with this filter.</p>`;
    const notes = new Set(listed.map(NOTE));
    h += `<ol class="f-notes">` +
      (notes.has("1") ? `<li value="1">From Aurora’s <a href="https://www.auroratechaward.com/top-30-women-founders-latam" target="_blank" rel="noopener">Top 30 Women Founders to Watch in LatAm</a>. The list gives the country she builds in, not a city or birthplace.</li>` : "") +
      (notes.has("2") ? `<li value="2">Added from <a href="https://www.startupeable.com/diaspora/" target="_blank" rel="noopener">Startupeable’s Diaspora map</a>: women founders born in or building in Latin America. Founders only: executives left out, investors are on the Investors map.</li>` : "") +
      (notes.has("3") ? `<li value="3">Added from my own network and research. Her name links to her LinkedIn or a profile of her work.</li>` : "") +
      (notes.has("5") ? `<li value="5">From <a href="https://airtable.com/appTolMiRbOFudS3O/shrkMKANni00yoPru/tblRVApDjCyG3m028" target="_blank" rel="noopener">Harlem Capital and Crunchbase’s 2022 Black &amp; Latino Founder Report</a>, Latina founders of US companies. The report gives the US state, not her birthplace: unless I know where she was born, she starts and builds in the US. Her name links to the company on Crunchbase.</li>` : "") +
      (notes.has("4") ? `<li value="4">From <a href="https://forbes.com.mx/los-50-angeles-inversionistas-mas-influyentes-de-latinoamerica/" target="_blank" rel="noopener">Forbes México’s 50 most influential angel investors in Latin America</a> (with Pygma, October 2025). The list gives a country, not a city.</li>` : "") +
      `</ol>`;
    // bridge to the investor map
    if (st.sel && typeof counts !== "undefined" && counts[cname(st.sel)]) {
      h += `<div class="f-bridge"><p><b>${counts[cname(st.sel)]}</b> investors, programs and prizes back founders in ${esc(cname(st.sel))}.</p><button class="btn" id="fToInv">See them on the investor map</button></div>`;
    }
    panel.innerHTML = h;
    const back = document.getElementById("fBack"); if (back) back.onclick = () => select(null);
    const toInv = document.getElementById("fToInv"); if (toInv) toInv.onclick = () => { window.setMapMode("inv"); current = cname(st.sel); render(); };
  }
  panel.addEventListener("click", e => {
    const c = e.target.closest(".f-dests .chip"); if (c) setDest(st.dest === c.dataset.d ? null : c.dataset.d);
  });
  panel.addEventListener("mouseover", e => { const r = e.target.closest(".f-row"); hot(r ? +r.dataset.p : null); });
  panel.addEventListener("focusin", e => { const r = e.target.closest(".f-row"); hot(r ? +r.dataset.p : null); });
  panel.addEventListener("mouseleave", () => hot(null));
  function hot(i) { st.hot = i; }

  function setDest(d) { st.dest = d; renderPanel(); drawGlobe(); }
  function select(id, personIdx = null) {
    st.sel = id; st.dest = null; st.hot = personIdx;
    renderAll();
    rotateTo(personIdx != null ? P[personIdx].ll : focusFor(id));
    if (personIdx != null) {
      const el = panel.querySelector(`.f-row[data-p="${personIdx}"]`);
      if (el) el.scrollIntoView({ block: "nearest", behavior: reduce ? "auto" : "smooth" });
    }
  }
  function renderAll() { renderList(); renderPanel(); drawGlobe(); }

  document.getElementById("fTotal").textContent = P.length;
  renderAll();
})();
