# Bounded duplicate screen — 2026-09-07

## Finding

No matching public issue or PR was found for the specific disagreement between linear/cubic coordinate interpolation and the nearest-resized eroded validity mask in `vesuvius.tifxyz.upsampling.upsample_coordinates`. This finding is limited to the search terms, references, and date recorded below.

The checked implementation uses OpenCV resize for XYZ and a separately resized validity mask. The proposed correction changes the validity calculation while preserving coordinate interpolation. It concerns the directly exported Python API; the local repository search found no active internal caller beyond exports and tests. Production use remains unestablished.

## Closest related work

| Reference | Verified overlap and distinction |
|---|---|
| [#1498 — Fix upsample_coordinates downsampling instead of upsampling](https://github.com/ScrollPrize/villa/pull/1498) | Merged August 22, 2026 as `7e87c22f5277ed2fae93c824ad2f55453b8e40d4`. The inspected full patch reverses the scale ratio and corrects its documentation. It does not change erosion, mask resizing, or interpolation support. |
| [#1694 — Full-resolution canvas truncation](https://github.com/ScrollPrize/villa/issues/1694) and [#1699 — canvas-size correction](https://github.com/ScrollPrize/villa/pull/1699) | Issue and PR were open at the check. They address full-resolution extent rounding and agreement with the C++ renderer. The PR explicitly leaves `upsampling.py` unchanged; this local change does not attempt its rounding work. |
| [#1264 — Final-quad bounds in geometry sampling](https://github.com/ScrollPrize/villa/pull/1264) | The inspected patch concerns C++ geometric bounds and interpolation validity at the final complete quad. It does not modify the Python resize mask. |
| [#701 — historical training/inference work](https://github.com/ScrollPrize/villa/pull/701) | A historical file change, not a pending correction. The file history showed four changes, with #1498 the latest and #701 the preceding change on February 9, 2026. |

## Search coverage

Read-only public GitHub searches covered open issues, open PRs, recent closed PRs, the file history, and these repository-scoped terms:

- `upsample_coordinates`: one result, #1498.
- `"upsampling.py"`: #1699 and historical #701.
- `upsampling mask`: #1699 and older broad PRs #942/#701.
- `resize erode`: no results.
- `"INTER_NEAREST" "mask"`: no results.
- `"erosion"`: related spiral/tracing records; no matching resize correction.
- `half-pixel` and `interpolation validity`: nearby geometry/data discussions were inspected for overlap, including #1699 and #1264.

The temporary API metadata cache from the broader screen is not part of this public evidence package. The specific public references above record the scoped findings. Search results and PR status can change; refresh the narrow screen before any eventual upstream posting.

## Other geometry work deliberately excluded

Generic self-intersection tools and a new sheet-switch checker would overlap existing contributions: [#1641](https://github.com/ScrollPrize/villa/issues/1641), [#1150](https://github.com/ScrollPrize/villa/issues/1150), and [July's awarded work](https://scrollprize.substack.com/p/335k-awarded-in-july). The [August awards update](https://github.com/ScrollPrize/villa/pull/1720) adds further patch-based unwrapping and tool improvements. Those references define work outside the resize-validity correction’s scope.

## Upstream contribution requirements

The preserved [upstream contribution policy](baseline/CONTRIBUTING.md) and [pull request template](baseline/pull_request_template.md) require personal use of scroll tools, human-written relevance commentary, code review, real-data evidence, and a personal-verification statement for an upstream PR. These external requirements remain preserved for review before an upstream submission. The local geometry measurements cover the evidence described in this repository.
