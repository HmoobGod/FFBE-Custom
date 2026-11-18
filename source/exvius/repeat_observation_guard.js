'use strict';

// Source-only evidence classifier for the original pinned GL9 repeat hooks.
// It does NOT install hooks, call any original native function, parse a
// BattleClear value, change player state, or request a gameplay stop.
//
// First-party source: source/exvius/mission_repeat.js at upstream-source.
// The hook only observes onRepeatStart, onRepeatEnd, onRepeatInterrupt,
// reset, onResetApp, MissionResultResponse constructors, and
// MissionEndRequest::createBody. None proves a cleared/failed outcome or
// that calling an observed stop method is safe.

export const REPEAT_OBSERVATION_SYMBOLS = Object.freeze({
  start: '_ZN23MissionRepeatResultInfo13onRepeatStartEv',
  end: '_ZN17MissionRepeatUtil11onRepeatEndEv',
  interrupt: '_ZN17MissionRepeatUtil17onRepeatInterruptEv',
  reset: '_ZN17MissionRepeatUtil5resetEv',
  resetApp: '_ZN17MissionRepeatUtil10onResetAppEv',
  resultCtor1: '_ZN21MissionResultResponseC1Ev',
  resultCtor2: '_ZN21MissionResultResponseC2Ev',
  missionEndBody: '_ZN17MissionEndRequest10createBodyEv'
});

const KINDS = new Map([
  [REPEAT_OBSERVATION_SYMBOLS.start, 'repeat-start-observed'],
  [REPEAT_OBSERVATION_SYMBOLS.end, 'repeat-stop-observed'],
  [REPEAT_OBSERVATION_SYMBOLS.interrupt, 'repeat-stop-observed'],
  [REPEAT_OBSERVATION_SYMBOLS.reset, 'repeat-stop-observed'],
  [REPEAT_OBSERVATION_SYMBOLS.resetApp, 'repeat-stop-observed'],
  [REPEAT_OBSERVATION_SYMBOLS.resultCtor1, 'result-constructor-observed'],
  [REPEAT_OBSERVATION_SYMBOLS.resultCtor2, 'result-constructor-observed'],
  [REPEAT_OBSERVATION_SYMBOLS.missionEndBody, 'mission-end-body-observed']
]);

/**
 * Classify a native symbol observed by the existing source, without treating
 * a result constructor as a verified clear, or an observed interrupt method
 * as permission to call it. Every classification is advisory and read-only.
 *
 * Importantly, the public source documents a client-reported BattleClear
 * field in MissionEndRequest, but NOT the native result-to-repeat-stop
 * ordering, validated receipt, or a safe call-site for stop/interrupt.
 */
export function classifyRepeatObservation(symbol) {
  const kind = typeof symbol === 'string' ? KINDS.get(symbol) : undefined;
  return Object.freeze({
    kind: kind || 'unrecognized-observation',
    outcomeVerified: false,
    settlementVerified: false,
    canInvokeNativeStop: false
  });
}
