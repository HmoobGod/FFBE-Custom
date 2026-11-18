'use strict';

// Public, synthetic source-only evidence checks. No emulator, APK, Frida,
// game data, native call, player save, reward credit, or runtime event.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const root = __dirname;
  async function sourceModule(name) {
    const text = fs.readFileSync(path.join(root, name), 'utf8');
    return import('data:text/javascript;base64,' + Buffer.from(text).toString('base64'));
  }
  const { REPEAT_OBSERVATION_SYMBOLS, classifyRepeatObservation } =
    await sourceModule('repeat_observation_guard.js');
  const { decideRepeatStop } = await sourceModule('repeat_stop_policy.js');
  const upstreamHook = fs.readFileSync(path.join(root, 'mission_repeat.js'), 'utf8');

  const expect = [
    ['start', 'repeat-start-observed'],
    ['end', 'repeat-stop-observed'],
    ['interrupt', 'repeat-stop-observed'],
    ['reset', 'repeat-stop-observed'],
    ['resetApp', 'repeat-stop-observed'],
    ['resultCtor1', 'result-constructor-observed'],
    ['resultCtor2', 'result-constructor-observed'],
    ['missionEndBody', 'mission-end-body-observed']
  ];
  assert.equal(expect.length, Object.keys(REPEAT_OBSERVATION_SYMBOLS).length);
  for (const [name, kind] of expect) {
    const symbol = REPEAT_OBSERVATION_SYMBOLS[name];
    // Every recognized event must exist in the actual unmodified hook source.
    assert.ok(upstreamHook.includes(symbol), 'Pinned upstream hook absent: ' + name);
    const state = classifyRepeatObservation(symbol);
    assert.deepEqual(state, {
      kind,
      outcomeVerified: false,
      settlementVerified: false,
      canInvokeNativeStop: false
    });
    assert.ok(Object.isFrozen(state));
    for (let i = 0; i < 4; i++)
      assert.deepEqual(classifyRepeatObservation(symbol), state);
  }

  // C1 and C2 are constructor variants, not two independently verified clears.
  assert.deepEqual(classifyRepeatObservation(REPEAT_OBSERVATION_SYMBOLS.resultCtor1),
    classifyRepeatObservation(REPEAT_OBSERVATION_SYMBOLS.resultCtor2));

  // "Interrupt" and "onRepeatEnd" are methods the original hook OBSERVES.
  // No source-only evidence establishes a safe native call-site or timing.
  for (const name of ['end', 'interrupt', 'reset', 'resetApp']) {
    assert.equal(classifyRepeatObservation(REPEAT_OBSERVATION_SYMBOLS[name]).canInvokeNativeStop,
      false);
  }

  // A constructor, a request-body creation, even a forged JS object claiming
  // success or failure is not authoritative for policy evaluation.
  for (const symbol of [REPEAT_OBSERVATION_SYMBOLS.resultCtor1,
                        REPEAT_OBSERVATION_SYMBOLS.missionEndBody]) {
    const state = classifyRepeatObservation(symbol);
    assert.equal(state.outcomeVerified, false);
    assert.equal(state.settlementVerified, false);
    assert.equal(state.canInvokeNativeStop, false);
  }
  for (const unrecognized of [undefined, null, 0, {}, [], 'BattleClear',
                              'MissionResultResponse', 'MissionRepeatUtil::stop',
                              {symbol: REPEAT_OBSERVATION_SYMBOLS.resultCtor1, cleared: true}]) {
    assert.deepEqual(classifyRepeatObservation(unrecognized), {
      kind: 'unrecognized-observation', outcomeVerified: false,
      settlementVerified: false, canInvokeNativeStop: false
    });
  }

  // The underlying policy safely reports missing clear/failure evidence as
  // unverified; the observation guard never upgrades constructor counts.
  assert.deepEqual(decideRepeatStop({maxCompletedRuns: 1}, {
    completedRuns: 1, lastCleared: undefined
  }), {stop: true, reason: 'unverified-result'});
  assert.deepEqual(decideRepeatStop({stopOnFailure: true}, {
    completedRuns: 2, lastCleared: 'BattleClear'
  }), {stop: true, reason: 'unverified-result'});
  assert.deepEqual(decideRepeatStop(undefined, undefined), {
    stop: false, reason: 'disabled'
  });

  // No native integration was added to the original hook or bootstrap.
  assert.ok(!upstreamHook.includes('repeat_observation_guard.js'));
  assert.ok(!upstreamHook.includes('repeat_stop_policy.js'));

  console.log('Repeat lifecycle evidence guard: 8 pinned hook symbols, constructor aliasing, '
    + 'stop-as-observation, unverified outcomes and disabled fallback passed.');
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
