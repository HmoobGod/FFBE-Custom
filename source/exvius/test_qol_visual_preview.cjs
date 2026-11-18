
'use strict';
// Test real embedded browser event handlers using an inert DOM stand-in.
// No jsdom, Playwright install, network, save access or native runtime.
const assert = require('node:assert/strict');
const path = require('node:path');
const vm = require('node:vm');
const {spawnSync} = require('node:child_process');

const scriptPath = path.join(__dirname, 'qol_visual_preview.py');
const response = spawnSync('python', ['-B', scriptPath], {
  encoding: 'utf8', maxBuffer: 4 * 1024 * 1024, timeout: 12000
});
assert.equal(response.status, 0, response.stderr);
const html = response.stdout;
assert.ok(html.startsWith('<!doctype html>'));
assert.ok(html.includes("connect-src 'none'"));
assert.ok(!html.includes('src="http'));
assert.ok(!html.includes('href="http'));
const fixture = html.match(/<script type="application\/json" id="qol-fixtures">([\s\S]*?)<\/script>/);
const executable = html.match(/<script>\s*([\s\S]*?)<\/script>/);
assert.ok(fixture, 'missing embedded immutable sample results');
assert.ok(executable, 'missing interactive client script');
const data = JSON.parse(fixture[1]);
assert.equal(data.fictional_samples_only, true);

class FakeElement {
  constructor(tag) {
    this.tag = tag;
    this.children = [];
    this.events = {};
    this.attributes = {};
    this.dataset = {};
    this.textContent = '';
    this.value = '';
    this.checked = false;
    this.hidden = false;
    this.className = '';
  }
  setAttribute(name, value) {this.attributes[name] = String(value);}
  getAttribute(name) {return this.attributes[name];}
  append(...nodes) {this.children.push(...nodes);}
  replaceChildren(...nodes) {this.children = nodes;}
  addEventListener(name, cb) {this.events[name] = cb;}
  fire(name) {
    assert.equal(typeof this.events[name], 'function',
      `Expected ${name} handler on ${this.tag}`);
    this.events[name]();
  }
}
function mount() {
  const els = {};
  const create = (id, val='') => {
    const el = new FakeElement(id);
    el.value = val;
    els[id] = el;
    return el;
  };
  create('qol-fixtures').textContent = fixture[1];
  for (const name of ['roster-summary','roster-items',
    'party-summary','party-items','quest-summary','quest-items',
    'panel-roster','panel-party','panel-quests',
    'roster-favorites','quest-only','quest-first']) create(name);
  create('roster-sort', 'original');
  create('roster-storage', 'all');
  create('party-preset', 'original');
  create('quest-mode', 'all');
  create('quest-dungeon', 'all');
  const tabs = ['roster','party','quests'].map(name => {
    const tab = new FakeElement('tab');
    tab.dataset.tab = name;
    return tab;
  });
  const document = {
    getElementById(id) {
      assert.ok(els[id], `Unexpected document lookup ${id}`);
      return els[id];
    },
    querySelectorAll(sel) {
      assert.equal(sel, '[data-tab]');
      return tabs;
    },
    createElement(tag) {return new FakeElement(tag);}
  };
  vm.runInNewContext(executable[1], {document, JSON, Number, String, Array, Object},
                     {timeout: 2000, filename: 'offline-preview-script.js'});
  return {els, tabs};
}
const cards = el => el.children;
const unitIds = el => cards(el).map(row => row.children[0].children[0].textContent);
const questIds = el => cards(el).map(row => row.children[0].children[0].textContent);

let {els,tabs} = mount();
assert.deepEqual(unitIds(els['roster-items']),
  ['Unit 101','Unit 102','Unit 103','Unit 104']);
assert.equal(els['panel-roster'].hidden, false);
assert.equal(els['panel-party'].hidden, true);
els['roster-sort'].value = 'level_desc';
els['roster-sort'].fire('change');
assert.deepEqual(unitIds(els['roster-items']),
  ['Unit 102','Unit 104','Unit 103','Unit 101']);
els['roster-storage'].value = 'warehouse';
els['roster-storage'].fire('change');
assert.deepEqual(unitIds(els['roster-items']), ['Unit 103']);
els['roster-storage'].value = 'all';
els['roster-storage'].fire('change');
els['roster-favorites'].checked = true;
els['roster-favorites'].fire('change');
assert.deepEqual(unitIds(els['roster-items']), ['Unit 102','Unit 104']);

tabs[1].fire('click');
assert.equal(els['panel-roster'].hidden, true);
assert.equal(els['panel-party'].hidden, false);
assert.equal(tabs[1].getAttribute('aria-selected'), 'true');
assert.ok(els['party-items'].children[0].textContent.includes('No changes'));
els['party-preset'].value = 'farming';
els['party-preset'].fire('change');
assert.equal(els['party-items'].children.length, 3);
assert.ok(els['party-summary'].textContent.includes('Farming Preview'));
assert.ok(els['party-summary'].textContent.includes('Active deck 0'));
els['party-preset'].value = 'boss';
els['party-preset'].fire('change');
assert.equal(els['party-items'].children.length, 1);
assert.ok(els['party-summary'].textContent.includes('Deck 1'));
assert.ok(els['party-summary'].textContent.includes('Active deck 0'));

tabs[2].fire('click');
assert.equal(els['panel-quests'].hidden, false);
assert.deepEqual(questIds(els['quest-items']),
 ['Mission 1110100','Mission 1110101','Mission 8991106']);
assert.equal(els['quest-summary'].textContent, '3 visible · 0 bookmarked');
const firstStar = els['quest-items'].children[0].children[1];
assert.equal(firstStar.getAttribute('aria-pressed'), 'false');
firstStar.fire('click');
assert.equal(els['quest-items'].children[0].children[1].getAttribute('aria-pressed'), 'true');
assert.equal(els['quest-summary'].textContent, '3 visible · 1 bookmarked');
els['quest-first'].checked = true;
els['quest-first'].fire('change');
els['quest-items'].children[2].children[1].fire('click');
assert.deepEqual(questIds(els['quest-items']),
 ['Mission 1110100','Mission 8991106','Mission 1110101']);
els['quest-mode'].value = '50';
els['quest-mode'].fire('change');
assert.deepEqual(questIds(els['quest-items']), ['Mission 8991106']);
els['quest-only'].checked = true;
els['quest-only'].fire('change');
assert.equal(els['quest-summary'].textContent, '1 visible · 1 bookmarked');
els['quest-dungeon'].value = '100';
els['quest-dungeon'].fire('change');
assert.equal(els['quest-summary'].textContent, '0 visible · 0 bookmarked');
assert.ok(els['quest-items'].children[0].textContent.includes('No missions'));
els['quest-mode'].value = 'all';
els['quest-mode'].fire('change');
assert.deepEqual(questIds(els['quest-items']), ['Mission 1110100']);

// Browser refresh creates an independent zero-bookmark session.
({els,tabs} = mount());
tabs[2].fire('click');
assert.equal(els['quest-summary'].textContent, '3 visible · 0 bookmarked');
assert.equal(els['quest-items'].children[0].children[1].getAttribute('aria-pressed'), 'false');
assert.ok(!/\b(?:fetch|XMLHttpRequest|localStorage|sessionStorage|indexedDB|WebSocket)\b/.test(executable[1]));
assert.ok(!/PlayerState|NativeFunction|Interceptor|Android/.test(executable[1]));
console.log('Offline QoL visual: interactive roster sort/filter, party compare, quest toggle/filter, session reset and no network/persistence passed.');
