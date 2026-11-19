/* Shared presentation layer. Data, fits, filters and animation values stay intact. */
(function () {
  'use strict';
  if (!window.Plotly) return;
  var P = window.Plotly, originalPlot = P.newPlot, originalFrames = P.addFrames;
  function caption(layout) {
    if (!layout || !layout.title) return;
    var text = typeof layout.title === 'string' ? layout.title : layout.title.text;
    if (!text) return;
    layout.meta = Object.assign({}, layout.meta, {hardballCaption: text});
    layout.title = {text: ''};
  }
  function controls(layout) {
    (layout.updatemenus || []).forEach(function (menu) {
      (menu.buttons || []).forEach(function (button) {
        if (button.method === 'update' && button.args && button.args[1]) caption(button.args[1]);
        if (button.method === 'relayout' && button.args && typeof button.args[0] === 'object') caption(button.args[0]);
      });
    });
  }
  function axes(layout) {
    Object.keys(layout).filter(function (key) { return /^[xy]axis\d*$/.test(key); }).forEach(function (key) {
      var axis = layout[key];
      axis.automargin = true;
      axis.tickfont = Object.assign({}, axis.tickfont, {size: 13});
      if (axis.title && axis.title.text) axis.title = Object.assign({}, axis.title, {standoff: 24, font: Object.assign({}, axis.title.font, {size: 14})});
    });
  }
  function kpi(layout, data) {
    // Five full-width small multiples replace five cramped columns.
    layout.height = 1320;
    layout.margin = Object.assign({}, layout.margin, {l: 60, r: 24, t: 58, b: 130});
    for (var i = 0; i < 5; i++) {
      var suffix = i ? String(i + 1) : '', top = 1 - i * 0.21;
      layout['xaxis' + suffix].domain = [0, 1];
      layout['yaxis' + suffix].domain = [top - 0.13, top];
      var values = data.filter(function (trace) { return (trace.yaxis || 'y') === 'y' + suffix; }).flatMap(function (trace) { return trace.y || []; });
      layout['yaxis' + suffix].range = [0, Math.max.apply(null, values) * 1.25];
      (layout.annotations || [])[i] = Object.assign({}, layout.annotations[i], {
        x: 0, xanchor: 'left', y: top, yanchor: 'bottom', yshift: 14,
        font: {size: 16, color: '#FFFFFF'}
      });
    }
    layout.legend = Object.assign({}, layout.legend, {y: -0.06, font: {size: 13, color: '#B9D8F3'}});
  }
  function narrowPanels(layout) {
    if (document.documentElement.clientWidth >= 800) return;
    var pairs = Object.keys(layout).filter(function (key) {
      return /^xaxis\d*$/.test(key) && layout[key].domain && layout[key].anchor &&
        layout['yaxis' + layout[key].anchor.slice(1)];
    }).map(function (key) {
      var x = layout[key], ykey = 'yaxis' + x.anchor.slice(1);
      return {x: x, y: layout[ykey], oldX: x.domain.slice(), oldY: layout[ykey].domain.slice()};
    });
    if (pairs.length < 2 || !pairs.some(function (p) { return p.oldX[1] - p.oldX[0] < 0.8; })) return;
    pairs.sort(function (a, b) { return b.oldY[1] - a.oldY[1] || a.oldX[0] - b.oldX[0]; });
    var step = 1 / pairs.length, gap = Math.min(0.09, step * 0.3);
    pairs.forEach(function (p, i) {
      var top = 1 - i * step;
      p.x.domain = [0, 1]; p.y.domain = [top - step + gap, top];
      (layout.annotations || []).forEach(function (a) {
        if (a.xref === 'paper' && a.yref === 'paper' && !a.showarrow &&
            Math.abs(a.y - p.oldY[1]) < 0.005 && a.x >= p.oldX[0] && a.x <= p.oldX[1]) {
          a.x = 0; a.xanchor = 'left'; a.y = top; a.yshift = 12; a.yanchor = 'bottom';
        }
      });
    });
    layout.height = Math.max(layout.height || 480, pairs.length * 340 + 180);
  }
  P.newPlot = function (target, data, layout, config) {
    var node = typeof target === 'string' ? document.getElementById(target) : target;
    var panel = node && node.closest('.panel[data-figure]');
    if (!panel) return originalPlot.apply(P, arguments);
    layout = JSON.parse(JSON.stringify(layout || {}));
    caption(layout); controls(layout); axes(layout);
    layout.margin = Object.assign({}, layout.margin, {t: 64});
    narrowPanels(layout);
    if (layout.legend && layout.legend.y < 0) {
      layout.legend.y = -0.25;
      layout.margin = Object.assign({}, layout.margin, {b: Math.max((layout.margin || {}).b || 0, 170)});
    }
    layout.height = Math.max(layout.height || 480, 600);
    data = (data || []).map(function (trace) { return trace.type === 'bar' ? Object.assign({}, trace, {textfont: Object.assign({}, trace.textfont, {size: 14})}) : trace; });
    if (panel.dataset.figure === '7') kpi(layout, data);
    if (panel.dataset.figure === '3') {
      data = data.map(function (trace) { return Object.assign({}, trace, {type: 'scatter', mode: 'markers',
        marker: Object.assign({}, trace.marker, {size: 11}),
        hovertemplate: '%{y}<br>Season-pair correlation: %{x:.3f}<extra></extra>'}); });
      layout.xaxis.range = [0, 1];
    }
    var notes = (layout.annotations || []).filter(function (a) { return a.yref === 'paper' && a.y < -0.15 && !a.showarrow; });
    layout.annotations = (layout.annotations || []).filter(function (a) { return notes.indexOf(a) < 0; });
    node.style.height = (layout.height || 480) + 'px';
    node.parentNode.style.height = 'auto';
    var heading = document.createElement('h4');
    heading.className = 'chart-caption'; heading.id = node.id + '-caption';
    heading.innerHTML = (layout.meta || {}).hardballCaption || panel.getAttribute('aria-label');
    node.parentNode.insertBefore(heading, node); panel.setAttribute('aria-labelledby', heading.id);
    if (panel.dataset.figure === '14') {
      var evidence = document.createElement('a'); evidence.className = 'chart-research-link';
      evidence.href = '../docs/EVIDENCE.html'; evidence.textContent = 'What the Evidence Says Now: read the injury and recovery research';
      heading.insertAdjacentElement('afterend', evidence);
    }
    if (notes.length || panel.dataset.figure === '3') {
      var note = document.createElement('p'); note.className = 'chart-note';
      note.innerHTML = (panel.dataset.figure === '3' ? 'Each dot represents one season pair. Correlations are shown separately, never added.<br>' : '') + notes.map(function (a) { return a.text; }).join('<br>');
      node.insertAdjacentElement('afterend', note);
    }
    var tools = document.createElement('div'); tools.className = 'chart-tools js-plotly-plot';
    var toolSurface = document.createElement('div'); toolSurface.className = 'plotly';
    tools.appendChild(toolSurface); node.parentNode.insertBefore(tools, node);
    config = Object.assign({}, config, {responsive: true, displaylogo: false, displayModeBar: true,
      modeBarButtonsToRemove: ['select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'toggleSpikelines', 'hoverCompareCartesian', 'hoverClosestCartesian']});
    return originalPlot.call(P, target, data, layout, config).then(function (gd) {
      function sync() {
        var text = (gd.layout.meta || {}).hardballCaption;
        if (text && heading.innerHTML !== text) heading.innerHTML = text;
        var bar = gd.querySelector('.modebar-container');
        if (bar) toolSurface.appendChild(bar);
      }
      sync(); gd.on('plotly_relayout', sync); gd.on('plotly_update', sync); gd.on('plotly_buttonclicked', function () { window.requestAnimationFrame(sync); }); gd.on('plotly_afterplot', sync); gd.on('plotly_animated', sync);
      return gd;
    });
  };
  P.addFrames = function (target, frames) {
    frames = JSON.parse(JSON.stringify(frames));
    frames.forEach(function (frame) { caption(frame.layout); });
    return originalFrames.call(P, target, frames);
  };
})();
