'use strict';

// SOURCE-ONLY PROTOTYPE. No native hooks call this module.
// This is a pure decision rule; it never starts/stops a mission, changes a
// player's save, or credits rewards. Runtime integration needs separate proof
// that the caller receives an authoritative completed mission result.
//
// Both controls are OFF by default. A null limit means no maximum.
export const DEFAULT_REPEAT_STOP_OPTIONS = Object.freeze({
  maxCompletedRuns: null,
  stopOnFailure: false
});

/**
 * Normalise one optional repeat-farming policy. Reject invalid/unknown
 * settings rather than guessing (a future caller must treat errors as STOP).
 */
export function normalizeRepeatStopOptions(options = undefined) {
  if (options == null) return DEFAULT_REPEAT_STOP_OPTIONS;
  if (typeof options !== 'object' || Array.isArray(options))
    throw new TypeError('Repeat-stop options must be an object');
  for (const key of Object.keys(options)) {
    if (key !== 'maxCompletedRuns' && key !== 'stopOnFailure')
      throw new TypeError('Unknown repeat-stop option: ' + key);
  }
  const maxCompletedRuns = options.maxCompletedRuns === undefined
    ? null : options.maxCompletedRuns;
  const stopOnFailure = options.stopOnFailure === undefined
    ? false : options.stopOnFailure;
  if (maxCompletedRuns !== null &&
      (!Number.isSafeInteger(maxCompletedRuns) || maxCompletedRuns < 1))
    throw new RangeError('maxCompletedRuns must be a positive safe integer or null');
  if (typeof stopOnFailure !== 'boolean')
    throw new TypeError('stopOnFailure must be a boolean');
  return { maxCompletedRuns, stopOnFailure };
}

/**
 * Evaluate what a FUTURE, independently verified client-side caller should do
 * after a mission result. Does not interact with upstream MissionRepeatUtil.
 *
 * progress.completedRuns: total confirmed results, including failed runs.
 * progress.lastCleared: true/false for the last CONFIRMED result; null only
 *                       before run 1 (or when a result is unverified).
 *
 * If any option is enabled, missing/contradictory evidence stops safely.
 * If both options are disabled, the original repeat behavior is untouched.
 *
 * Returns {stop, reason}, with reason stable for fixtures/diagnostics.
 */
export function decideRepeatStop(options = undefined, progress = undefined) {
  const policy = normalizeRepeatStopOptions(options);
  if (policy.maxCompletedRuns === null && !policy.stopOnFailure)
    return { stop: false, reason: 'disabled' };

  const completed = progress?.completedRuns;
  const cleared = progress?.lastCleared;
  if (!Number.isSafeInteger(completed) || completed < 0)
    return { stop: true, reason: 'unverified-progress' };
  if (completed === 0 ? cleared !== null : typeof cleared !== 'boolean')
    return { stop: true, reason: 'unverified-result' };

  if (policy.stopOnFailure && cleared === false)
    return { stop: true, reason: 'failure' };
  if (policy.maxCompletedRuns !== null && completed >= policy.maxCompletedRuns)
    return { stop: true, reason: 'max-completed-runs' };
  return { stop: false, reason: 'continue' };
}
