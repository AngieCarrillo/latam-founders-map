/* Investors view on a globe: countries shaded by number of players, click one to list who's there. */
(() => {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const W = 600, R0 = 282;
  const svg = d3.select("#invGlobe");
  const proj = d3.geoOrthographic().scale(R0).translate([W / 2, W / 2]).clipAngle(90).rotate([70, 15]);
  const gp = d3.geoPath(proj);
  const land = topojson.feature(window.WORLD, window.WORLD.objects.countries).features;
  const sphere = svg.append("path").attr("class", "g-sphere");
  const grat = svg.append("path").attr("class", "g-grat");
  const gLand = svg.append("g"), gLab = svg.append("g").attr("class", "i-labels");
  const g10 = d3.geoGraticule10();
  const ALIAS = { "United States of America": "United States" };
  const nm = f => ALIAS[f.properties.name] || f.properties.name;
  // counts follow the type and stage filters, so the shading matches the list on the right
  let live = {};
  const recount = () => {
    live = {};
    D.forEach(p => {
      if ((activeCats.size && !activeCats.has(p.c)) || (stageSel && !(STAGE[p.n] || "").includes(stageSel))) return;
      live[p.k] = (live[p.k] || 0) + 1;
    });
  };
  const n = f => live[nm(f)] || 0;
  const paths = gLand.selectAll("path").data(land).join("path")
    .attr("class", "i-land")
    .on("click", (e, f) => { if (n(f)) { current = nm(f); render(); } })
    .on("keydown", (e, f) => { if (n(f) && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); current = nm(f); render(); } });
  paths.append("title");
  const labelled = land.filter(f => counts[nm(f)]).map(f => {
    // label at the centre of the country's largest piece (keeps Chile's label on the mainland)
    let best = f;
    if (f.geometry.type === "MultiPolygon") {
      best = f.geometry.coordinates.map(c => ({ type: "Polygon", coordinates: c })).sort((a, b) => d3.geoArea(b) - d3.geoArea(a))[0];
    }
    return { f, ll: d3.geoCentroid(best) };
  });

  const center = () => { const r = proj.rotate(); return [-r[0], -r[1]]; };
  function draw() {
    sphere.attr("d", gp({ type: "Sphere" }));
    grat.attr("d", gp(g10));
    paths.attr("d", gp).classed("sel", f => nm(f) === current)
      .classed("has", f => !!n(f)).style("fill", f => n(f) ? shade(n(f)) : null)
      .attr("tabindex", f => n(f) ? 0 : null).attr("role", f => n(f) ? "button" : null)
      .attr("aria-label", f => n(f) ? `${nm(f)}: ${n(f)} players` : null)
      .select("title").text(f => nm(f) + (n(f) ? ` · ${n(f)}` : ""));
    const vis = labelled.filter(d => n(d.f) && d3.geoDistance(d.ll, center()) < Math.PI / 2 - 0.05);
    gLab.selectAll("text").data(vis, d => nm(d.f)).join("text")
      .attr("transform", d => `translate(${proj(d.ll).join(",")})`)
      .attr("dy", "0.35em")
      .classed("on-sel", d => nm(d.f) === current)
      .text(d => n(d.f));
  }
  function rotateTo(name) {
    const d = labelled.find(x => nm(x.f) === name); if (!d) return;
    const from = proj.rotate(), to = [-d.ll[0], Math.max(-60, Math.min(60, -d.ll[1])), 0];
    if (reduce) { proj.rotate(to); draw(); return; }
    const it = d3.interpolate(from, to);
    d3.transition().duration(800).ease(d3.easeCubicInOut).tween("rot", () => t => { proj.rotate(it(t)); draw(); });
  }
  svg.call(d3.drag().on("drag", e => {
    const r = proj.rotate(), k = 75 / proj.scale();
    proj.rotate([r[0] + e.dx * k, Math.max(-80, Math.min(80, r[1] - e.dy * k)), 0]); draw();
  }));
  const zoom = f => { proj.scale(Math.max(R0 * 0.8, Math.min(R0 * 4, proj.scale() * f))); draw(); };
  document.getElementById("iZoomIn").onclick = () => zoom(1.3);
  document.getElementById("iZoomOut").onclick = () => zoom(1 / 1.3);
  document.getElementById("iWorld").onclick = () => { proj.scale(R0); rotateTo("Colombia"); };

  // keep the globe in step with the investor panel
  const base = render;
  let lastCurrent = null;
  render = function () {
    base(); recount(); draw();
    // only spin the globe when the country changes, not when a filter changes
    if (current !== "Global" && current !== lastCurrent) rotateTo(current);
    lastCurrent = current;
  };
  render();
})();
