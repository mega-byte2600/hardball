// Presentation contracts run against every published figure at three widths.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'dashboard/index.html'), 'utf8');
const source = fs.readFileSync(path.join(root, 'dashboard/assets/chart-readability.js'), 'utf8');
function jsonAt(start) {
  while (/\s|,/.test(html[start])) start++;
  let depth = 0, quoted = false, escape = false;
  for (let i = start; i < html.length; i++) {
    const c = html[i];
    if (quoted) { if (escape) escape = false; else if (c === '\\') escape = true; else if (c === '"') quoted = false; }
    else if (c === '"') quoted = true;
    else if (c === '[' || c === '{') depth++;
    else if (c === ']' || c === '}') { if (--depth === 0) return [JSON.parse(html.slice(start, i + 1)), i + 1]; }
  }
  throw Error('Unclosed chart specification');
}
(async () => {
  let checked = 0;
  for (const width of [390, 768, 1280]) {
    const nodes = new Map(), calls = [];
    function element() { return {style: {}, appendChild() {}, insertBefore() {}, setAttribute() {}, insertAdjacentElement() {}}; }
    const P = {
      newPlot(target, data, layout, config) {
        calls.push({data, layout, config});
        return Promise.resolve({layout, querySelector() {return null;}, on() {}});
      },
      addFrames(target, frames) { return frames; }
    };
    const document = {documentElement: {clientWidth: width}, createElement: element, getElementById(id) {
      if (!nodes.has(id)) {
        const node = element(), panel = element(); panel.dataset = {figure: id.match(/^fig(\d+)/)[1]};
        panel.getAttribute = () => 'Figure'; node.id = id; node.parentNode = element(); node.closest = () => panel; nodes.set(id, node);
      }
      return nodes.get(id);
    }};
    const context = {window: {Plotly: P}, document};
    vm.runInNewContext(source, context);
    const regex = /Plotly.newPlot\(\s*"([^"]+)"\s*,/g;
    for (let match; (match = regex.exec(html));) {
      let [data, end] = jsonAt(regex.lastIndex), [layout] = jsonAt(end);
      const before = JSON.stringify(data);
      await P.newPlot(match[1], data, layout, {});
      const call = calls.at(-1);
      assert.equal(JSON.stringify(data), before, 'source traces mutated');
      assert.equal(call.layout.title.text, '', 'title must live outside the plotting region');
      assert.ok(call.layout.meta.hardballCaption, 'missing visible caption');
      assert.equal(call.config.responsive, true);
      data.forEach((t, i) => ['x', 'y', 'z', 'customdata', 'error_x', 'error_y'].forEach(k => assert.deepEqual(call.data[i][k], t[k], k + ' changed')));
      if (match[1].startsWith('fig7-')) assert.ok(call.layout.yaxis.domain[0] > call.layout.yaxis2.domain[1], 'KPI panels overlap');
      checked++;
    }
    const frames = P.addFrames('fig1-explorer', [{layout: {title: {text: 'Updated season'}}, data: [{x: [1], y: [2]}]}]);
    assert.equal(frames[0].layout.meta.hardballCaption, 'Updated season');
    assert.equal(frames[0].data[0].y[0], 2);
  }
  assert.equal(checked, 144);
  console.log('PASS: 48 figures × 3 viewport widths; trace values, captions, controls and animation title contracts');
})().catch(e => {console.error(e); process.exit(1);});
