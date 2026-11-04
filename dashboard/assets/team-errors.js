(() => {
  const panel = document.getElementById("team-errors");
  if (!panel) return;
  const chart = panel.querySelector(".errors-plot");
  const view = panel.querySelector("select");
  let pending;
  async function draw() {
    if (!panel.open) return;
    try {
      pending ??= fetch("assets/team-errors.json").then(response => {
        if (!response.ok) throw new Error("Team errors data unavailable");
        return response.json();
      });
      const data = await pending;
      const models = view.value === "models";
      const x = data.points.map(row => row[1]);
      const ends = [Math.min(...x), Math.max(...x)];
      const trace = models ? [{
        type: "scatter", mode: "markers", x: data.models.map(row => row[1][0]),
        y: data.models.map(row => row[0]),
        marker: {size: 10, color: "#f6c75e"},
        error_x: {
          type: "data", symmetric: false,
          array: data.models.map(([, [mean, , high]]) => high - mean),
          arrayminus: data.models.map(([, [mean, low]]) => mean - low)
        },
        hovertemplate: "%{y}<br>%{x:.2f} additional wins<extra></extra>"
      }] : [{
        type: "scatter", mode: "markers", x,
        y: data.points.map(row => row[2]),
        text: data.points.map((row, i) => data.clubs[i] + " · " + row[0]),
        marker: {size: 7, color: "#8fbce6", opacity: .65},
        hovertemplate: "%{text}<br>%{x:.1f} errors per 162 games<br>%{y:.1f} wins per 162 games<extra></extra>"
      }, {
        type: "scatter", mode: "lines", x: ends,
        y: ends.map(value => data.trend[0] * value + data.trend[1]),
        name: "Unadjusted trend", line: {color: "#f6c75e"}
      }];
      await Plotly.react(chart, trace, {
        height: 340, margin: {l: 22, r: 20, t: 12, b: 65},
        paper_bgcolor: "transparent", plot_bgcolor: "transparent",
        font: {color: "#e3eef8"}, showlegend: !models, legend: {orientation: "h"},
        xaxis: {
          title: models ? "Additional wins per 162 games<br>associated with 10 fewer errors" : "Errors per 162 games",
          zerolinecolor: "#8fbce6", gridcolor: "#28415a"
        },
        yaxis: {title: models ? "" : "Wins per 162 games", automargin: true,
                autorange: models ? "reversed" : true, gridcolor: "#28415a"}
      }, {responsive: true, displayModeBar: false});
    } catch {
      pending = undefined;
      chart.textContent = "Chart unavailable. The model result is shown above.";
    }
  }
  panel.addEventListener("toggle", draw);
  view.addEventListener("change", draw);
})();
