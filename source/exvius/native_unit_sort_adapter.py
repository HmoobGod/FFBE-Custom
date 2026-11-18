"""Pure, default-off policy for a future original-client unit sort adapter.

SOURCE ONLY. No native hooks, ELF reads, game imports, roster access, response
mutation, persistence, UI changes, or effects. A later, separately authorized
integration must independently attest the ELF digest and live scene identity.

The verified original Global v9.0.0 comparator uses regular level PLUS
limit-EX level, optional party priority, and native tie-break rules. It is not
equivalent to the standalone roster-view helper's plain level_desc mode.
"""
from __future__ import annotations

PINNED_ELF_SHA256 = (
    "a127654037f2f28a70cce7c64ff0a9d291770ea9"
    "04cdf5bcba59a7af9a6937e4"
)
UNIT_LIST_SCENE = "UnitListScene"
NATIVE_LEVEL_LIKE_DESC_MODE = "native_level_like_desc"
NATIVE_LEVEL_LIKE_DESC_PAIR = (0, 1)


def choose_native_unit_sort(
    *,
    enabled: bool = False,
    mode: str = "original",
    elf_sha256: str | None = None,
    scene_name: str | None = None,
    scene_identity_verified: bool = False,
) -> tuple[int, int] | None:
    """Return the sole approved (type, order) pair, or None for original fallback.

    This function is NOT a fingerprint reader or native scene verifier. Both
    facts must be established by a future separately authorized integration.
    False, missing, malformed, unsupported, or ambiguous facts fail closed.
    Returning None means do nothing: do not write a default sort setting.

    Filtering, warehouse/party/favorite state, and the current native sort
    settings are intentionally outside this pure policy's inputs and outputs.
    """
    if enabled is not True or scene_identity_verified is not True:
        return None
    if type(elf_sha256) is not str or elf_sha256 != PINNED_ELF_SHA256:
        return None
    if type(scene_name) is not str or scene_name != UNIT_LIST_SCENE:
        return None
    if type(mode) is not str or mode != NATIVE_LEVEL_LIKE_DESC_MODE:
        return None
    return NATIVE_LEVEL_LIKE_DESC_PAIR
