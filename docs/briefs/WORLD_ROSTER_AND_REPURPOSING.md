# World roster and repurposing

What is playing, what could return, what stays closed, and some careful ideas for giving the closed worlds a second life. Read this when you forget which world is which, or when you want to propose something fun without breaking the rules.

**Boundary.** This document reactivates nothing. Enchanted Glen (`glen`) and Holiday Lights (`hlights`) were retired by the owner on 25 October 2026 and must keep no unlock, travel or supported-play offers. Only a new explicit instruction from the owner changes that. Everything under "Ideas" is a proposal that needs approval, not a plan of record.

Sources: `FarmVillage/macOS/Documentation/Worlds/THEMED_WORLDS.md`, [world readiness](../../WORLD_READINESS.md), and [Wave 3](<../../Wave 3.md>) sections 5 and 7. Counts below use each source's own denominator and must not be added together.

## The roster in five buckets

| Bucket | Worlds | State |
| --- | --- | --- |
| **A. Active (16)** | Home / October, English Countryside, Sunflower Meadows, Lighthouse Cove, Fields of El Dorado, Mediterranean Riviera, Fairytale Fields, Sweet Acres, Oasis Gardens, Emerald Valley, Toy Town, Horseman's Hollow, Australia, Mystical Groves, Mistletoe Lane, Atlantis | Playable. Five are the strongest (Home, England, Meadows, Cove, El Dorado); eleven are in documented basic mode. None is a complete recreation. |
| **B. Retired by the owner (2)** | `glen`, `hlights` | Source contracts are retained as research. Glen's record keeps a failed fallback sign artwork check. Holiday Lights' record keeps a failed later gift and loading follow-up. |
| **C. Dormant, with their own rule modules** | `hallow` (Haunted Hollow), `asia`, `hawaii` | Rules exist in source but were never accepted for play. Asia and Hawaii use world currencies; their conversion proposals are explicitly "not activation approval". Hawaii has one crafting cottage (`xhicraftingcottage`). Haunted Hollow is owned by a dormant track and "not wired here". |
| **D. Closed by a gate** | `yuletide`, `avalon`, `winterwonderland`, `space`, `village`, `angler`, `garden` | Yuletide: experiment served closed. Avalon: feature option and closed experiment. Winter Wonderland: general access ended on 18 February 2012, so a new unlock would bypass it. Space: no recovered expansion storage id. Village: no admitted basic items. Angler and Garden: no basic farm. |
| **E. Fixed or large scene layouts** | 44 worlds (43 earlier-listed keys plus `japan`) | Background art is recovered for all of them and the horizon for 42; `wildwest` and `treasuretides` lack the horizon. The original scene sizing, renderer and terrain contract must be recovered before any exposure. |

The full 70-world asset audit is a private historical reference and is not in this repository.

## Resurfaced, resurrectable, and not retrievable

- **Resurfaced.** Bucket A. These are playing today, with limits listed per world in [world readiness](../../WORLD_READINESS.md).
- **Could come back with work.** Bucket B needs an owner decision first, then its own acceptance. Bucket C has code but needs the same bounded browser cycle the active worlds received. Bucket E needs the scene contract recovered first.
- **Not retrievable right now.** Anything blocked by a *named missing artifact*, for example reward timing for Pantheon Isle, Daydream Island and the Unicorn Bridge owner fallback, the Port repeat-harvest loot table, shoreline and terrain masks, authentic populated starters, the missing horizon art for two worlds, and Space's storage id. Bucket D is different: those worlds are closed by their own original configuration, so opening them would override the original design and is an owner decision, not a recovery task.

"Not retrievable" means not with what the repository and its private inputs hold today. A newly found artifact can change a row.

## What already merges assets from closed worlds into stable ones

This exists today. `FarmVillage/heritage_pricing.py` makes ordinary items from catalogue-only worlds buyable on the Home Farm: **13,017 records considered, 4,721 derived overlays** (4,421 locked-world and 300 exclusive).

The rules, in short:

- Only ordinary item classes qualify, with no requirement other than a World entry and none of the blocking fields.
- A crop is admitted only when its whole Home loop works with existing server code: buy, plant, grow for its time, harvest.
- An item keeps its own recovered price and currency. A missing price is derived deterministically from the nearest priced sibling, so the market and the server always charge the same amount.
- Each World requirement is renamed to Home; date windows are removed for the overlay; crops keep their experiment gate.

Both retired worlds are in `RESERVED_WORLDS`, so their items are **not** rehomed today; they stay exactly as recovered. Mistletoe Lane, Fairytale Fields and the other active worlds are reserved for the same reason. Heritage handling "does not authorize restoring Glen or Holiday travel or enabling their special systems".

## Ideas, ranked from safest to most work

None of these exist. Each needs the approval route at the end.

1. **A Museum of Lost Worlds in God Barn.** A read-only exhibit for each closed world: its name, its original art, notable items, original prices, and why it is closed. Nothing to buy, place or travel to. It carries no gameplay risk. God Barn already builds item history and acquisition data in `GodBarn/encyclopedia.py`; whether a world chapter fits that pipeline is not verified here.
2. **A winter shelf in Mistletoe Lane.** Ordinary decorations from Holiday Lights, offered in the active Christmas world. Wave 3 records **591 Holiday-associated raw records, of which 379 pass only an ordinary-class screen**. Those are candidates before any gate, not approved items. A reward-gated piece such as `beatholidaylightsstatue` stays reward-gated.
3. **Fairy-tale decor from Glen.** Ordinary Glen-themed decorations for Fairytale Fields or Mystical Groves. Wave 3 records **172 Glen-associated raw records, of which 91 pass only the ordinary screen**, and names `cobblestonebridge` and `fairybed` as items to investigate.
4. **A seasonal window as disclosed local policy.** Show the winter shelf only in a chosen holiday window. The project already discloses local policy for the Mistletoe starter and theme, so this has a precedent. It is a new mechanic and needs approval of the dates and the wording.

## Never, whichever idea you pick

- Do not move a retired world's special systems: buildings, gifts, community or reward mechanics.
- Do not turn a reward-gated item into a sale or a free grant.
- Do not use a new shelf to get around an item's original date, level, prerequisite, terrain or experiment gate.
- Do not merge or remap original item codes. Keep names and codes; reference art by its original identity.
- Do not reactivate travel to either retired world.
- Do not claim an item works because its name or picture suggests it does.

## How a proposal gets approved

Wave 3 section 5 sets the bar. A proposal delivers a machine-readable disposition table, a human summary, the candidate engine family, the exact blocked parameters and one accepted sample per proposed family. The world owner and the integration reviewer approve each new admission.

A sensible first slice: pick one destination (for example Mistletoe Lane), list its ordinary candidates with every original gate, run five of them through the destination's real purchase, placement, storage and reload path on a new synthetic farm, and report PASS, FAIL or UNRUN for each.

## Decisions for the owner

1. May contributors explore ordinary retired-world decor for Mistletoe Lane, Fairytale Fields and Mystical Groves, as candidates only?
2. Is the Museum of Lost Worlds worth building, given it adds no gameplay?
3. If a shelf is built, should prices follow the heritage-style deterministic policy or each item's own recovered price?
4. Is a seasonal window acceptable as disclosed local policy?
5. Reactivating Holiday Lights or Glen is a separate decision and is not implied by any answer above.
