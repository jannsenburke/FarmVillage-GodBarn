# Development status and maintainer priorities

**Updated 26 October 2026.** The application source and engineering documentation are available for community development. A complete public-resource installation is still unfinished: a fresh clone cannot yet acquire, prepare and run the whole game automatically.

The continuing targets are the native macOS desktop app and browser hosting on Ubuntu/Linux. The active alpha has sixteen worlds with different feature limits. iPad/iOS development is discontinued; Enchanted Glen and Holiday Lights are excluded. See [world readiness](WORLD_READINESS.md).

## Available now

- The Python game server, native macOS app source, browser hosting tools and God Barn companion.
- Source integrity, syntax and documentation checks, plus selected tests using synthetic data.
- Resource identity manifests, extraction tools, Ruffle build provenance and catalogue recovery utilities.
- [Architecture notes](TAKEOVER.md), [engineering contracts](FarmVillage/macOS/Documentation/ENGINEERING_INDEX.md) and a [restoration backlog](<Wave 3.md>).

The application source baseline is FarmVillage `62809de497404588f133e38740242864717af0c0` and God Barn `31245bb8bc2848908667ae0cf95af8244531bff5`. `SOURCE_MANIFEST.json` identifies the exact files in this source release. The public Git history is inherited from AcidCaos/FarmVillage through commit `2dc25ca24032041a8b68d299b861eb2d4d449653`; the current tree uses the reviewed source layout.

## Two player paths

- [Mac players](docs/PLAY_ON_MAC.md) keep a large local native installation. A complete app downloads the original artwork on first Create/Open Farm, but the fresh-source app/resource bootstrap is still incomplete.
- [Server owners](docs/PLAY_ON_SERVER.md) prepare the full game on Ubuntu/Linux. Players use browsers; the existing installer requires pre-extracted artwork and a prepared release.

`START_MAC.command` and the public-source `START_HERE.sh` open a read-only readiness guide. This is not a complete game installer or a new clean-clone gameplay pass. The prepared-bundle server installer remains a separate, explicitly scoped flow.

## First priority: independent resource setup

1. Retrieve the original files from the documented public preservation sources, with resumable downloads and verified identities.
2. Extract and select the required resource versions into an external game-resource directory.
3. Generate God Barn metadata and interface resources without using a previous player farm or private cache as a seed.
4. Build and verify the pinned Ruffle player. The recovered public build work reproduced outputs on two macOS paths; Linux output identity remains unresolved because the compiled output includes Apple Clang-produced code.
5. Connect the resulting resource directory to browser staging, native builds and Ubuntu installation.
6. Validate the complete path from a clean clone with a new synthetic farm, a real farming cycle and normal save/restart persistence. Test native macOS and actual Ubuntu separately.

See [resource setup](docs/RESOURCE_SETUP.md) for the original sources and existing interfaces.

## Draft resource work

[RESOURCE_SETUP_RECOVERY.patch](RESOURCE_SETUP_RECOVERY.patch) preserves **unapplied, incomplete resource automation work**. It includes resource manifests, generator changes, native resource handling and build-provenance changes. Its documentation references central helpers that are not implemented in the active source. It is not an installation script or a release-ready patch.

Review and integrate it in a separate development branch. Match it to the source baseline recorded in its provenance, implement the missing downloader/orchestrator and browser launcher, and update resource identities through review rather than accepting arbitrary files. Do not apply the draft wholesale and treat its commands as working setup instructions.

## Other open work

- Repeat the remaining native gameplay checks and qualify installation, service operation and gameplay on an actual Ubuntu host.
- Restore regional production, progression, treasures and expansion systems in bounded, source-supported steps.
- Keep unsupported features unavailable until their real rules and outcomes are known.
- Preserve original prices and timers, and test with fresh synthetic profiles. The current release policy uses new farms rather than migrating old saves.

[ACCEPTANCE.md](ACCEPTANCE.md) records historical testing with prepared resources. It is separate from clean-clone resource qualification, signing/notarization and long-session stability. Source-only tests, native builds, browser graphics and actual Ubuntu execution are distinct checks.
