(() => {
  const panel = document.getElementById("player-errors");
  if (!panel) return;
  const [position, sort] = panel.querySelectorAll("select");
  const chart = panel.querySelector(".errors-plot");
  const table = panel.querySelector("tbody");
  let pending;
  const raw = row => 100 * row[1] / row[2];
  const fmt = value => value.toFixed(2);

  async function draw() {
    if (!panel.open) return;
    try {
      pending ??= fetch("assets/player-errors.json").then(response => {
        if (!response.ok) throw new Error("Player errors data unavailable");
        return response.json();
      });
      const data = (await pending)["2026"][position.value];
      const rows = [...data.rows].sort((a, b) => a[3] - b[3] || b[2] - a[2] || a[0].localeCompare(b[0]));
      const plotted = rows.filter(row => row[2] >= 50).slice(0, 12);
      const labels = plotted.map(([name, e, n]) => name + "<br>" + e + " errors / " + n + " chances");
      const estimates = plotted.map(row => row[3]);
      const key = sort.value;
      const sorted = [...rows].sort((a, b) =>
        key === "raw" ? raw(a) - raw(b) : key === "2" ? b[2] - a[2] : a[key] - b[key]);
      table.replaceChildren(...sorted.map(([name, e, n, estimate, low, high]) => {
        const row = document.createElement("tr");
        for (const value of [name, e, n, fmt(100 * e / n), fmt(estimate), fmt(low) + " to " + fmt(high)]) {
          row.insertCell().textContent = value;
        }
        return row;
      }));
      if (!plotted.length) {
        chart.textContent = "No players at this position reached 50 chances. See the table below.";
        return;
      }
      await Plotly.react(chart, [{
        type: "scatter", mode: "markers", name: "Estimated rate", x: estimates, y: labels,
        marker: {size: 9, color: "#f6c75e"},
        error_x: {type: "data", symmetric: false,
                  array: plotted.map(row => row[5] - row[3]),
                  arrayminus: plotted.map(row => row[3] - row[4])},
        hovertemplate: "%{y}<br>%{x:.2f} estimated errors per 100<extra></extra>"
      }, {
        type: "scatter", mode: "markers", name: "Observed rate", x: plotted.map(raw), y: labels,
        marker: {size: 11, symbol: "circle-open", color: "#8fbce6"},
        hovertemplate: "%{y}<br>%{x:.2f} observed errors per 100<extra></extra>"
      }], {
        height: 110 + plotted.length * 42, margin: {l: 15, r: 20, t: 10, b: 72},
        paper_bgcolor: "transparent", plot_bgcolor: "transparent", font: {color: "#e3eef8", size: 11},
        legend: {orientation: "h", y: -0.16},
        xaxis: {title: "Errors per 100 recorded chances", rangemode: "tozero", gridcolor: "#28415a"},
        yaxis: {automargin: true, autorange: "reversed", categoryorder: "array", categoryarray: labels},
        shapes: [{type: "line", x0: data.average, x1: data.average, yref: "paper",
                  y0: 0, y1: 1, line: {color: "#8fbce6", dash: "dot", width: 1}}]
      }, {responsive: true, displayModeBar: false});
    } catch {
      pending = undefined;
      chart.textContent = "Chart unavailable. If the table has loaded, its values are shown below.";
    }
  }
  panel.addEventListener("toggle", draw);
  position.addEventListener("change", draw);
  sort.addEventListener("change", draw);
})();
