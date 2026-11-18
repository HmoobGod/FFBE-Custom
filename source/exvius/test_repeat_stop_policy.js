'use strict';

// Synthetic, pure, offline tests: no original game assets, native hooks,
// player-state imports, save files, or reward transactions.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

(async () => {
  const source = fs.readFileSync(path.join(__dirname, 'repeat_stop_policy.js'), 'utf8');
  const { DEFAULT_REPEAT_STOP_OPTIONS, normalizeRepeatStopOptions, decideRepeatStop } =
    await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));

  const go = (options, completedRuns, lastCleared) =>
    decideRepeatStop(options, {completedRuns, lastCleared});

  // Disabled means the original autoplay flow is not restrained, regardless
  // of what a future caller might report. No save or global switch exists.
  assert.deepEqual(DEFAULT_REPEAT_STOP_OPTIONS, {maxCompletedRuns: null, stopOnFailure: false});
  assert.ok(Object.isFrozen(DEFAULT_REPEAT_STOP_OPTIONS));
  assert.deepEqual(normalizeRepeatStopOptions(), DEFAULT_REPEAT_STOP_OPTIONS);
  assert.deepEqual(normalizeRepeatStopOptions(null), DEFAULT_REPEAT_STOP_OPTIONS);
  assert.deepEqual(normalizeRepeatStopOptions({}), DEFAULT_REPEAT_STOP_OPTIONS);
  assert.deepEqual(decideRepeatStop(), {stop: false, reason: 'disabled'});
  assert.deepEqual(go({}, 7, false), {stop: false, reason: 'disabled'});
  assert.deepEqual(decideRepeatStop({maxCompletedRuns: null, stopOnFailure: false},
    {completedRuns: NaN, lastCleared: null}), {stop: false, reason: 'disabled'});

  // N counts confirmed COMPLETED results, not attempts scheduled; the first
  // run is eligible while completedRuns is zero. Failed runs also count.
  const maxOne = {maxCompletedRuns: 1};
  assert.deepEqual(go(maxOne, 0, null), {stop: false, reason: 'continue'});
  assert.deepEqual(go(maxOne, 1, true), {stop: true, reason: 'max-completed-runs'});
  assert.deepEqual(go(maxOne, 1, false), {stop: true, reason: 'max-completed-runs'});
  assert.deepEqual(go({maxCompletedRuns: 3}, 2, true), {stop: false, reason: 'continue'});
  assert.deepEqual(go({maxCompletedRuns: 3}, 3, true),
    {stop: true, reason: 'max-completed-runs'});
  assert.deepEqual(go({maxCompletedRuns: 3}, 4, false),
    {stop: true, reason: 'max-completed-runs'});

  // Failure stop remains independent of a maximum; successful runs continue
  // when there is no max or the chosen max has not been reached.
  const failOnly = {stopOnFailure: true};
  assert.deepEqual(go(failOnly, 0, null), {stop: false, reason: 'continue'});
  assert.deepEqual(go(failOnly, 1, true), {stop: false, reason: 'continue'});
  assert.deepEqual(go(failOnly, 1, false), {stop: true, reason: 'failure'});
  assert.deepEqual(go({maxCompletedRuns: 5, stopOnFailure: true}, 2, false),
    {stop: true, reason: 'failure'});
  assert.deepEqual(go({maxCompletedRuns: 5, stopOnFailure: true}, 5, true),
    {stop: true, reason: 'max-completed-runs'});
  assert.deepEqual(go({maxCompletedRuns: 5, stopOnFailure: true}, 5, false),
    {stop: true, reason: 'failure'});

  // Enabled policies stop on unverifiable or contradictory result data.
  for (const bad of [undefined, null, -1, 1.5, NaN, Infinity, '2', true]) {
    assert.deepEqual(decideRepeatStop(maxOne, {completedRuns: bad, lastCleared: null}),
      {stop: true, reason: 'unverified-progress'});
  }
  for (const [n, outcome] of [[0, true], [0, false], [1, null], [1, undefined],
                               [1, 'success'], [1, 1]]) {
    assert.deepEqual(go(failOnly, n, outcome),
      {stop: true, reason: 'unverified-result'});
  }
  assert.deepEqual(decideRepeatStop(failOnly), {stop: true, reason: 'unverified-progress'});

  // Invalid settings reject, rather than silently becoming unlimited runs.
  for (const bad of [0, -1, 1.1, NaN, Infinity, -Infinity, '3', false, {}, []]) {
    assert.throws(() => normalizeRepeatStopOptions({maxCompletedRuns: bad}),
      /maxCompletedRuns/);
  }
  for (const bad of [1, 'true', null, {}, []]) {
    assert.throws(() => normalizeRepeatStopOptions({stopOnFailure: bad}),
      /stopOnFailure/);
  }
  for (const bad of [true, 7, [], 'off']) {
    assert.throws(() => normalizeRepeatStopOptions(bad), /options/);
  }
  assert.throws(() => normalizeRepeatStopOptions({maxCompletedRun: 5}),
    /Unknown repeat-stop option/);

  // Pure and deterministic: do not mutate even frozen inputs or emit state.
  const options = Object.freeze({maxCompletedRuns: 3, stopOnFailure: true});
  const progress = Object.freeze({completedRuns: 2, lastCleared: true});
  const expected = {stop: false, reason: 'continue'};
  for (let i = 0; i < 100; i++) {
    assert.deepEqual(decideRepeatStop(options, progress), expected);
  }
  assert.deepEqual(options, {maxCompletedRuns: 3, stopOnFailure: true});
  assert.deepEqual(progress, {completedRuns: 2, lastCleared: true});

  console.log('Repeat-stop QoL policy: defaults, limits, failures, unknowns, validation, purity passed.');
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
