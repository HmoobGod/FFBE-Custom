
"""Standalone offline HTML visual demo, generated from tested pure QoL helpers.

Usage: python -B source/exvius/qol_visual_preview.py > ffbe-qol-preview.html
Only fictional sample data; no saves, live server, master tables, network,
native hooks, or asset files. Browser state is temporary and not persisted.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from unit_roster_view import SORTS, STORAGE_FILTERS, select_roster_view
from party_preset_preview import preview_party_preset
from quest_favorites_view import preview_quest_favorites


def synthetic_inputs():
    units = [
        {"instance_id":"101","level":30,"favourite":0,"storage_state":0},
        {"instance_id":"102","level":65,"favourite":1,"storage_state":0},
        {"instance_id":"103","level":48,"favourite":0,"storage_state":1},
        {"instance_id":"104","level":50,"favourite":1,"storage_state":0},
    ]
    def member(iid, slot):
        return {"member_type":0,"disp_order":slot,"instance_id":iid}
    party = {"active_deck":0,"decks":[
        {"id":0,"name":"Story","members":[member("101",0),member("102",1)]},
        {"id":1,"name":"Boss","members":[member("104",0)]},
    ]}
    presets = {
        "original":{"id":0,"members":[member("101",0),member("102",1)]},
        "farming":{"id":0,"name":"Farming Preview","members":[member("102",0),member("101",1),member("103",2)]},
        "boss":{"id":1,"name":"Boss Preview","members":[member("104",0),member("103",1)]},
    }
    quests = [
        {"qo3PECw6":"1110100","gQR24kST":"1","U9iHsau3":"100"},
        {"qo3PECw6":"1110101","gQR24kST":"1","U9iHsau3":"100"},
        {"qo3PECw6":"8991106","gQR24kST":"50","U9iHsau3":"900"},
    ]
    return units, party, presets, quests


def preview_data():
    """Precompute all visible option combinations with source-only helpers."""
    units, party, presets, quests = synthetic_inputs()
    roster_views = {
        f"{sort}|{storage}|{fav}":select_roster_view(
            units,sort=sort,storage=storage,favorites_only=bool(fav))
        for sort in sorted(SORTS) for storage in sorted(STORAGE_FILTERS)
        for fav in (0,1)
    }
    party_views = {
        key:preview_party_preset(units,party,preset)
        for key,preset in presets.items()
    }
    mids = [r["qo3PECw6"] for r in quests]
    quest_views = {}
    for mask in range(1 << len(mids)):
        favorite_ids = [mid for i,mid in enumerate(mids) if mask & (1 << i)]
        for only in (0,1):
            for first in (0,1):
                for mode in ("all","1","50"):
                    for dungeon in ("all","100","900"):
                        view = preview_quest_favorites(
                            quests,favorite_ids,favorites_only=bool(only),
                            favorites_first=bool(first),
                            mode=None if mode=="all" else mode,
                            dungeon=None if dungeon=="all" else dungeon)
                        key=f"{mask}|{only}|{first}|{mode}|{dungeon}"
                        quest_views[key]={
                            "visible_count":view["visible_count"],
                            "visible_favorites":view["visible_favorites"],
                            "entries":[
                                {"id":r["mission_id"],"favorite":r["is_favorite"],
                                 "mode":r["mission"]["gQR24kST"],
                                 "dungeon":r["mission"]["U9iHsau3"]}
                                for r in view["entries"]
                            ]
                        }
    return {"fictional_samples_only":True,"roster":roster_views,
            "party":party_views,"quest_ids":mids,"quests":quest_views}


TEMPLATE = '''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; font-src 'none'; base-uri 'none'; form-action 'none'">
<meta name="color-scheme" content="dark"><title>FFBE-Custom · Offline QoL Preview</title>
<style>
:root{color-scheme:dark;font:16px/1.5 system-ui,sans-serif;background:#0d1425;color:#e8eefb}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(ellipse at top,#263956,#0d1425 65%)}
main{max-width:940px;margin:auto;padding:32px 22px 80px}
h1{font-size:clamp(2rem,5vw,3rem);letter-spacing:-.05em;line-height:1.1;margin:12px 0}h2{font-size:1.4rem;margin:0}
p{color:#b5c5da;margin:8px 0 24px}.eyebrow{font-size:.76rem;letter-spacing:.17em;text-transform:uppercase;color:#77d2cb;font-weight:750}
.badge{display:inline-block;border-radius:100px;padding:5px 12px;background:#133d42;color:#8ee6d9;font-size:.75rem;font-weight:700}
.notice{padding:15px 18px;border:1px solid #344760;border-radius:12px;background:#18243b;color:#bac9de;margin:22px 0}
.tabs{display:flex;flex-wrap:wrap;gap:8px;margin:24px 0 18px}.tab{background:#19243a;border:1px solid #40516a;color:#b9cae0;padding:11px 20px;border-radius:10px;font-weight:700;cursor:pointer}
.tab[aria-selected=true]{background:#4dd8ca;color:#071a26;border-color:#4dd8ca}
.panel{border:1px solid #35455e;border-radius:18px;background:#162238;padding:24px;box-shadow:0 20px 60px #060b1926}.panel[hidden]{display:none}
.controls{display:flex;flex-wrap:wrap;gap:14px;margin:22px 0 18px;align-items:end}
label{color:#d4e2f2;font-size:.9rem;font-weight:600;display:grid;gap:6px}
select{min-width:130px;background:#0e1a30;color:#f4f9ff;border:1px solid #40546f;border-radius:8px;padding:11px 12px;font:inherit}
.check{display:flex;align-items:center;gap:9px;background:#0e1a30;padding:10px 12px;border:1px solid #354760;border-radius:8px}
input[type=checkbox]{accent-color:#53ddce;width:18px;height:18px}
.summary{color:#9bb3cc;font-size:.88rem;margin:14px 0}.cards{display:grid;gap:10px}
.item{display:flex;gap:16px;align-items:center;justify-content:space-between;border:1px solid #32445c;background:#101c2e;border-radius:12px;padding:14px 16px}
.item strong{display:block;font-size:1.02rem}.muted{color:#a3b5cd;font-size:.83rem}
.number{font-size:1.3rem;color:#85e9dc;font-weight:750;white-space:nowrap}
.tag{border-radius:7px;background:#263b54;padding:4px 9px;color:#d6e7f8;font-size:.77rem}
.star{border:1px solid #5d6682;color:#aebbd1;background:#18263e;border-radius:8px;cursor:pointer;padding:8px 13px;font-size:1.25rem}
.star[aria-pressed=true]{color:#f7d77b;background:#453622;border-color:#ac8744}
.empty{padding:24px 14px;text-align:center;border:1px dashed #52617c;border-radius:10px;color:#a5b9d1}
footer{padding-top:24px;color:#849cb8;font-size:.82rem}button:focus-visible,select:focus-visible,input:focus-visible{outline:3px solid #85e9dc;outline-offset:2px}
@media(max-width:540px){main{padding:20px 13px 60px}.panel{padding:18px}.controls{display:grid;grid-template-columns:1fr 1fr}.controls label{min-width:0}.controls select{width:100%;min-width:0}.item{padding:11px}.tab{flex:1;min-width:90px}}
</style></head><body><main>
<div class="eyebrow">FFBE-Custom / Source-only lab</div>
<h1>Quality of Life <span style="color:#73e0d0">Preview</span></h1>
<p>Explore unit sorting, compare party layouts and bookmark missions with fictional data. Nothing connects to the game.</p>
<span class="badge">Fully offline · No saves · No network</span>
<div class="notice"><strong>Demonstration only.</strong> All data is synthetic and computed by the existing Python preview functions. No game assets, PlayerState, original client or native hooks. Bookmarks reset on reload.</div>
<nav class="tabs" role="tablist" aria-label="QoL demos">
<button type="button" class="tab" data-tab="roster" role="tab" aria-selected="true">Unit roster</button>
<button type="button" class="tab" data-tab="party" role="tab" aria-selected="false">Party comparison</button>
<button type="button" class="tab" data-tab="quests" role="tab" aria-selected="false">Quest favorites</button>
</nav>
<section id="panel-roster" class="panel" role="tabpanel">
<h2>Unit roster</h2><p>Sort or filter an illustrative roster. Default: original order.</p>
<div class="controls">
<label>Sort<select id="roster-sort"><option value="original">Original order</option><option value="favorites_first">Favorites first</option><option value="favorites_level_desc">Favorites + level</option><option value="level_desc">Highest level</option><option value="level_asc">Lowest level</option></select></label>
<label>Storage<select id="roster-storage"><option value="all">All units</option><option value="active">Active only</option><option value="warehouse">Warehouse only</option></select></label>
<label class="check"><input type="checkbox" id="roster-favorites"> Favorites only</label>
</div><div id="roster-summary" class="summary" aria-live="polite"></div><div id="roster-items" class="cards"></div>
</section>
<section id="panel-party" class="panel" role="tabpanel" hidden>
<h2>Party comparison</h2><p>Preview changes to existing owned decks. Nothing is applied.</p>
<div class="controls"><label>Proposed arrangement<select id="party-preset"><option value="original">Original party</option><option value="farming">Farming preview</option><option value="boss">Boss preview</option></select></label></div>
<div id="party-summary" class="summary" aria-live="polite"></div><div id="party-items" class="cards"></div>
</section>
<section id="panel-quests" class="panel" role="tabpanel" hidden>
<h2>Quest favorites</h2><p>Star fictional missions to temporarily bookmark them. Reload to reset.</p>
<div class="controls">
<label>Mode<select id="quest-mode"><option value="all">All modes</option><option value="1">Mode 1</option><option value="50">Mode 50</option></select></label>
<label>Dungeon<select id="quest-dungeon"><option value="all">All dungeons</option><option value="100">Dungeon 100</option><option value="900">Dungeon 900</option></select></label>
<label class="check"><input type="checkbox" id="quest-first"> Favorites first</label>
<label class="check"><input type="checkbox" id="quest-only"> Favorites only</label>
</div><div id="quest-summary" class="summary" aria-live="polite"></div><div id="quest-items" class="cards"></div>
</section>
<footer>Fictional source-only preview · No user data · No native execution · No storage or network calls</footer>
<script type="application/json" id="qol-fixtures">__QOL_FIXTURES__</script>
<script>
"use strict";
(() => {
  const data = JSON.parse(document.getElementById("qol-fixtures").textContent);
  const get = id => document.getElementById(id);
  let mask = 0;
  const make = (tag, cls, text) => {
    const el = document.createElement(tag);
    el.className = cls;
    if (text !== undefined) el.textContent = String(text);
    return el;
  };
  const display = (id, rows, empty) =>
    get(id).replaceChildren(...(rows.length ? rows : [make("div", "empty", empty)]));
  function renderRoster() {
    const key = [get("roster-sort").value,get("roster-storage").value,Number(get("roster-favorites").checked)].join("|");
    const rows = data.roster[key];
    get("roster-summary").textContent = `${rows.length} fictional unit(s)`;
    display("roster-items", rows.map(row => {
      const card=make("article","item"), info=make("div","");
      info.append(make("strong","",`Unit ${row.instance_id}`),
        make("span","muted",`${row.favourite ? "★ Favorite · " : ""}${row.storage_state ? "Warehouse" : "Active roster"}`));
      card.append(info,make("span","number",`Lv ${row.level}`));
      return card;
    }),"No units match.");
  }
  function renderParty() {
    const view=data.party[get("party-preset").value];
    get("party-summary").textContent=`Deck ${view.target_deck_id} · ${view.before.name} → ${view.proposed.name} · ${view.slot_changes.length} changed slot(s) · Active deck ${view.active_deck_id}`;
    display("party-items",view.slot_changes.map(row => {
      const card=make("article","item");
      card.append(make("strong","",`Slot ${row.slot+1}`),
        make("span","tag",`${row.before ? row.before.instance_id : "Empty"} → ${row.after ? row.after.instance_id : "Empty"}`));
      return card;
    }),"No changes to the current party.");
  }
  function renderQuests() {
    const key=[mask,Number(get("quest-only").checked),Number(get("quest-first").checked),
               get("quest-mode").value,get("quest-dungeon").value].join("|");
    const view=data.quests[key];
    get("quest-summary").textContent=`${view.visible_count} visible · ${view.visible_favorites} bookmarked`;
    display("quest-items",view.entries.map(entry => {
      const card=make("article","item"), info=make("div","");
      info.append(make("strong","",`Mission ${entry.id}`),
        make("span","muted",`Mode ${entry.mode} · Dungeon ${entry.dungeon}`));
      const star=make("button","star",entry.favorite ? "★" : "☆");
      star.type="button";
      star.setAttribute("aria-label",`Toggle temporary bookmark for mission ${entry.id}`);
      star.setAttribute("aria-pressed",String(entry.favorite));
      star.addEventListener("click",() => {
        const i=data.quest_ids.indexOf(entry.id);
        if(i>=0) mask ^= 1<<i;
        renderQuests();
      });
      card.append(info,star);
      return card;
    }),"No missions match.");
  }
  const views={roster:renderRoster,party:renderParty,quests:renderQuests};
  const tabs=Array.from(document.querySelectorAll("[data-tab]"));
  function activate(name) {
    tabs.forEach(button => button.setAttribute("aria-selected",String(button.dataset.tab===name)));
    Object.keys(views).forEach(tab => {get(`panel-${tab}`).hidden=tab!==name;});
    views[name]();
  }
  tabs.forEach(tab=>tab.addEventListener("click",()=>activate(tab.dataset.tab)));
  for(const id of ["roster-sort","roster-storage","roster-favorites"]) get(id).addEventListener("change",renderRoster);
  get("party-preset").addEventListener("change",renderParty);
  for(const id of ["quest-mode","quest-dungeon","quest-first","quest-only"]) get(id).addEventListener("change",renderQuests);
  activate("roster");
})();
</script></main></body></html>
'''


def build_html():
    seed=json.dumps(preview_data(),sort_keys=True,separators=(",",":"))
    if "<" in seed:
        raise ValueError("unsafe synthetic seed contains HTML delimiter")
    return TEMPLATE.replace("__QOL_FIXTURES__",seed)


if __name__=="__main__":
    sys.stdout.write(build_html())
