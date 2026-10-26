# Game resources

**Public-resource installation is unfinished.** This repository contains source and resource-processing tools, but a fresh clone cannot yet download, prepare and run the complete game automatically. You can contribute code and run the [source-only checks](../README.md#get-started-with-the-source) without game resources.

## Original preservation sources

| Source | What it provides |
| --- | --- |
| [Pinned AcidCaos/FarmVillage revision](https://github.com/AcidCaos/farmvillage/tree/2dc25ca24032041a8b68d299b861eb2d4d449653) | Original base files under `embeds/`, `assethash/`, `xml/` and `patched/` |
| [Internet Archive: original-farmville](https://archive.org/details/original-farmville) | Archived artwork and other original web resources |
| [Upstream asset downloader and manifest](https://github.com/AcidCaos/farmvillage/blob/2dc25ca24032041a8b68d299b861eb2d4d449653/assets.py) | The exact four `.warc.gz` captures and expected identities used by the preservation project |
| [Archive file listing](https://archive.org/download/original-farmville/) | The collection’s download listing |

A WARC stores archived web responses. The four captures named by upstream end in `00000` through `00003`. Extracting them recovers original resource files, but still requires version selection and arrangement into this fork’s expected layout. These sources are preservation references, not a complete installation procedure or a new asset mirror.

Original resources retain their own rights. The source-code licence does not license the original game media. See [source and resource notices](../SOURCE_NOTICE.md).

## What a playable resource set needs

- Original client/configuration payloads and the versions expected by the compatibility patches.
- An extracted artwork tree, including the required environment and promotional resources.
- Generated God Barn item metadata, labels, skins, helpers and progression data.
- A reviewed, version-pinned Ruffle player for the browser/native wrapper.
- Resource identities and a complete layout accepted by the runtime and staging tools.

Downloading the upstream base files and four archives does not by itself supply all of these outputs. No previous player farm, authentication state or personal profile should be needed by the completed bootstrap.

## Existing tools and their limits

### Extract local archives

After obtaining the original archives and creating the external Python environment from the README, the existing extractor can read local WARCs:

```sh
FARMVILLAGE_NATIVE=1 "$FV_CHECK_ENV/bin/python" -B   FarmVillage/warc_extractor/warc_extractor.py   -path /absolute/path/to/local-warc-directory   -output_path /absolute/path/to/new-extraction-directory   -dump content
```

Run from the repository root with a new output directory outside source and install targets. The native flag enables output containment checks. This command does not select a complete accepted runtime layout or generate the companion data.

### Build the pinned player

The Ruffle source revision, patch, toolchain, lockfiles and output pins are retained in the [runtime build recipe](../FarmVillage/ruffle_runtime/0.7.1-farmvillage-gc1/provenance/README.md). The driver uses a clean checkout at commit `89a7049965f3090e706265670df309a5128233ac` and explicitly selected tools:

```sh
"$FV_CHECK_ENV/bin/python" -B   FarmVillage/ruffle_runtime/0.7.1-farmvillage-gc1/provenance/build-runtime.py   --source /absolute/path/to/clean/pinned-ruffle-source   --destination /absolute/path/to/new-player-output   --node /absolute/path/to/node   --npm-cli /absolute/path/to/npm/bin/npm-cli.js   --wasm-bindgen /absolute/path/to/wasm-bindgen
```

The driver checks output identities. Cross-host reproducibility remains an open task; the recorded build host was Apple Silicon macOS. Review differing outputs as a new resource baseline rather than weakening the pin to accept arbitrary files.

### Recover companion resources

Read [the catalogue pipeline](../GodBarn/Documentation/CATALOG_PIPELINE.md) before running generators. These are maintenance interfaces requiring their named inputs, not a from-scratch bootstrap sequence:

```sh
# Audit an existing prepared catalogue against original resources.
"$FV_CHECK_ENV/bin/python" -B GodBarn/scripts/recover_catalog.py   /absolute/path/to/prepared-game-archive --audit-only

# Recover labels from the original locale SWF.
"$FV_CHECK_ENV/bin/python" -B GodBarn/scripts/recover_labels.py   /absolute/path/to/en_US.swf /absolute/path/to/new-localized-labels.json

# Refresh archive-derived data using existing catalogue/provenance inputs.
"$FV_CHECK_ENV/bin/python" -B GodBarn/scripts/prepare_archive.py   /absolute/path/to/prepared-game-archive

# Requires a prepared catalogue and a source-identified pristine item cache.
"$FV_CHECK_ENV/bin/python" -B GodBarn/scripts/prepare_untabbed.py   /absolute/path/to/prepared-game-archive
```

Some generators write to the working checkout’s `GodBarn/` resource directories. Run them in a development checkout and inspect the resulting identities. Generated data stays outside the source export.

## Missing bootstrap work

1. Map extracted WARC content and versions into the accepted runtime layout.
2. Generate catalogues and companion artwork without a private cache or player-save seed. The older `prepare_assets.py` reads a hardcoded legacy save and writes a practice-save copy; do not use it unchanged for this release’s bootstrap.
3. Resolve the generators’ historical cache-layout and provenance assumptions. `prepare_untabbed.py` expects a pristine decode under the game’s `cache/`, while the older bootstrap expects `LocalData/cache/`.
4. Handle separately curated historical data explicitly. `prepare_encyclopedia.py` expects `historical-prizes.json`; item AMF alone does not reconstruct that curation.
5. Finish source-verified player builds and resource identities across macOS and Linux, connect external resource roots to the application and browser, and verify clean-clone gameplay and persistence.

An [unapplied draft patch](../RESOURCE_SETUP_RECOVERY.patch) preserves some resource automation work. It needs review and missing central helpers before integration. See [maintainer priorities](../HANDOVER_STATUS.md); commands mentioned only in the draft are not active setup tools.

## Existing matching-resource importer

For maintainers who already possess a compatible prepared set, `PrivateInputs.expected.json` records **1,843 files / 392,964,044 bytes** accepted by the current importer. The large extracted artwork tree is additional and is not included in that count. The manifest lists identities; it does not retrieve files.

The prepared game root contains the original payloads, selected templates and exact player distribution. The prepared companion root contains generated metadata and selected interface resources. Neither root should include farms, snapshots, credentials or another player’s profile.

Use the [development and build guide](DEVELOPMENT.md) for the checked import interface, native build and prepared browser staging. Independently regenerated files may require a reviewed new resource baseline; they are not interchangeable merely because their filenames match.

Actual native gameplay, browser gameplay and Ubuntu installation must each be checked after resource preparation. Keep the sixteen-world scope, original prices/timers and explicit unsupported-feature boundaries.
