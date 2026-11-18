'use strict';
// Independent Chromium smoke test of the already-implemented offline visual QoL
// page. Browser sees only generated fictional HTML via a local file:// URL.
// CDP is loopback-only test control; the PAGE may not make network requests.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawn, spawnSync} = require('node:child_process');
const {pathToFileURL} = require('node:url');

const generator = path.join(__dirname, 'qol_visual_preview.py');

function findBrowser() {
  const choices = [process.env.CHROME_PATH, 'google-chrome', 'google-chrome-stable',
    'chromium', 'chromium-browser'].filter(Boolean);
  for (const choice of choices) {
    const found = choice.includes('/') ? choice : spawnSync('which', [choice], {encoding:'utf8'}).stdout.trim();
    if (found && fs.existsSync(found)) return found;
  }
  return null;
}

function delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

async function until(work, explanation, limit=16000) {
  const began = Date.now();
  let error;
  while (Date.now() - began < limit) {
    try {
      const result = await work();
      if (result) return result;
    } catch (exc) { error = exc; }
    await delay(100);
  }
  throw new Error(explanation + (error ? ': ' + error.message : ''));
}

async function run() {
  const binary = findBrowser();
  if (!binary) {
    console.log('SKIP: no installed Chromium/Chrome executable; existing DOM-handler tests remain authoritative for synthetic JS interactions.');
    return;
  }
  assert.equal(typeof WebSocket, 'function', 'Node 22 WebSocket required');
  const generated = spawnSync('python', ['-B', generator], {
    encoding:'utf8', maxBuffer:6*1024*1024, timeout:12000
  });
  assert.equal(generated.status, 0, generated.stderr);
  assert.ok(generated.stdout.startsWith('<!doctype html>'));
  const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'ffbe-offline-qol-browser-'));
  const file = path.join(scratch, 'qol-visual-fixture.html');
  const profile = path.join(scratch, 'chrome-profile');
  fs.writeFileSync(file, generated.stdout, {mode:0o600});
  let browser;
  let socket;
  const pending = new Map();
  let nextId = 0;
  const errors = [];
  const externalRequests = [];

  function send(method, params={}) {
    const id = ++nextId;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        pending.delete(id);
        reject(new Error('CDP timeout: '+method));
      }, 11000);
      pending.set(id, {resolve, reject, timer});
      socket.send(JSON.stringify({id,method,params}));
    });
  }

  async function evaluate(expression) {
    const data = await send('Runtime.evaluate', {
      expression, returnByValue:true, awaitPromise:true
    });
    if (data.exceptionDetails) throw new Error('Browser JS exception: ' + JSON.stringify(data.exceptionDetails));
    return data.result.value;
  }

  try {
    browser = spawn(binary, [
      '--headless=new', '--no-sandbox', '--disable-gpu',
      '--disable-background-networking', '--disable-extensions',
      '--disable-component-extensions-with-background-pages',
      '--disable-default-apps', '--disable-sync', '--no-first-run',
      '--no-default-browser-check', '--disable-features=MediaRouter,Translate',
      '--remote-debugging-port=0', '--user-data-dir='+profile,
      'about:blank'
    ], {stdio:['ignore','ignore','pipe']});
    let stderr = '';
    browser.stderr.on('data', chunk => { stderr += chunk.toString().slice(0,1024); });
    const portFile = path.join(profile, 'DevToolsActivePort');
    const port = await until(() => {
      if (browser.exitCode !== null) throw new Error('Chromium exited: '+stderr.slice(-500));
      if (!fs.existsSync(portFile)) return 0;
      const p = Number(fs.readFileSync(portFile,'utf8').split('\n')[0]);
      return Number.isInteger(p) && p > 0 ? p : 0;
    }, 'Chromium CDP never started');
    const page = await until(async () => {
      const response = await fetch('http://127.0.0.1:'+port+'/json');
      const tabs = await response.json();
      return tabs.find(tab => tab.type==='page' && tab.webSocketDebuggerUrl);
    }, 'No debug page found');
    socket = new WebSocket(page.webSocketDebuggerUrl);
    await new Promise((resolve,reject) => {
      socket.addEventListener('open',resolve,{once:true});
      socket.addEventListener('error',reject,{once:true});
    });
    socket.addEventListener('message', evt => {
      const event = JSON.parse(evt.data);
      if (event.id !== undefined && pending.has(event.id)) {
        const p = pending.get(event.id);
        pending.delete(event.id);
        clearTimeout(p.timer);
        if (event.error) p.reject(new Error(JSON.stringify(event.error)));
        else p.resolve(event.result || {});
      } else if (event.method === 'Runtime.exceptionThrown') {
        errors.push(JSON.stringify(event.params.exceptionDetails || {}));
      } else if (event.method === 'Network.requestWillBeSent') {
        const url = event.params.request?.url || '';
        if (/^https?:/i.test(url)) externalRequests.push(url);
      }
    });
    await send('Runtime.enable');
    await send('Network.enable');
    await send('Page.enable');
    await send('Page.navigate', {url:pathToFileURL(file).href});
    await until(async () => (await evaluate('document.readyState === "complete" && document.querySelectorAll("#roster-items .item").length===4')), 'UI did not render');

    const unitIds = 'Array.from(document.querySelectorAll("#roster-items .item strong"),n=>n.textContent)';
    const questIds = 'Array.from(document.querySelectorAll("#quest-items .item strong"),n=>n.textContent)';
    assert.deepEqual(await evaluate(unitIds),['Unit 101','Unit 102','Unit 103','Unit 104']);
    await evaluate('document.getElementById("roster-sort").value="level_desc";document.getElementById("roster-sort").dispatchEvent(new Event("change"));');
    assert.deepEqual(await evaluate(unitIds),['Unit 102','Unit 104','Unit 103','Unit 101']);
    await evaluate('document.getElementById("roster-storage").value="warehouse";document.getElementById("roster-storage").dispatchEvent(new Event("change"));');
    assert.deepEqual(await evaluate(unitIds),['Unit 103']);
    await evaluate('document.querySelector("[data-tab=party]").click()');
    assert.equal(await evaluate('document.getElementById("panel-party").hidden'), false);
    await evaluate('document.getElementById("party-preset").value="farming";document.getElementById("party-preset").dispatchEvent(new Event("change"));');
    assert.equal(await evaluate('document.querySelectorAll("#party-items .item").length'),3);
    assert.equal(await evaluate('document.getElementById("party-summary").textContent.includes("Active deck 0")'),true);
    await evaluate('document.querySelector("[data-tab=quests]").click()');
    assert.deepEqual(await evaluate(questIds),['Mission 1110100','Mission 1110101','Mission 8991106']);
    await evaluate('document.querySelector("#quest-items .star").click()');
    assert.equal(await evaluate('document.getElementById("quest-summary").textContent.includes("1 bookmarked")'),true);
    await evaluate('document.getElementById("quest-first").checked=true;document.getElementById("quest-first").dispatchEvent(new Event("change"));');
    assert.equal(await evaluate('document.querySelector("#quest-items .star").getAttribute("aria-pressed")'), 'true');
    await send('Page.reload', {ignoreCache:true});
    await until(async () => await evaluate('document.readyState === "complete" && document.querySelectorAll("#roster-items .item").length === 4'), 'Page did not recover after reload');
    await evaluate('document.querySelector("[data-tab=quests]").click()');
    assert.equal(await evaluate('document.getElementById("quest-summary").textContent.includes("0 bookmarked")'),true);
    assert.equal(await evaluate('document.getElementById("qol-fixtures").textContent.includes("fictional_samples_only")'),true);

    // Visual usability check at 320x740 responsive viewport.
    await send('Emulation.setDeviceMetricsOverride', {width:320,height:740,
      deviceScaleFactor:1,mobile:true});
    assert.equal(await evaluate('document.documentElement.scrollWidth <= window.innerWidth'),true);
    assert.deepEqual(externalRequests, [], 'Offline HTML attempted external HTTP request');
    assert.deepEqual(errors, [], 'Browser threw JavaScript runtime errors');
    console.log('BROWSER PASS: Chromium file:// local page; roster sorting, party preview, quest bookmarking, reload reset, 320px viewport, no external requests or runtime exceptions.');
  } finally {
    for (const job of pending.values()) {clearTimeout(job.timer);job.reject(new Error('Browser cleanup')); }
    pending.clear();
    if (socket) socket.close();
    if (browser) {
      browser.kill('SIGTERM');
      await delay(120);
      if (browser.exitCode===null) browser.kill('SIGKILL');
    }
    fs.rmSync(scratch,{recursive:true,force:true});
  }
}

run().catch(err => {console.error(err.stack||err);process.exitCode=1;});
