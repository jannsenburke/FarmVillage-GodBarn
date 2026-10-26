# Development and builds

This guide is for contributors working beyond the source-only checks. Start with the [README](../README.md#get-started-with-the-source) to create the external Python environment. Its examples set `FV_CHECK_ENV`; set that variable to the same environment path in each new terminal.

**A complete public-resource bootstrap is not implemented yet.** The commands below require an already prepared, compatible resource set. They do not download or reconstruct that set. See [game resources](RESOURCE_SETUP.md) before attempting an app build or server install.

## Compatible prepared resources

`PrivateInputs.expected.json` records the paths, sizes and hashes accepted by the existing importer. It does not contain the original files or provide a download source. With compatible game and companion resources already available, import them from separate local directories:

```sh
"$FV_CHECK_ENV/bin/python" -B tools/private-inputs.py import   --runtime-source /absolute/path/to/prepared/Runtime   --godbarn-source /absolute/path/to/prepared/GodBarn
"$FV_CHECK_ENV/bin/python" -B tools/private-inputs.py check
"$FV_CHECK_ENV/bin/python" -B tools/check-source.py --with-private-inputs
```

The importer checks the complete expected set before copying, refuses links and mismatches, and does not import player farms. The extracted `assets/` artwork tree is an additional external input, including `Environment/` and `xpromoSupport/`. Keep resource work in a development checkout; use a clean source checkout for publication checks.

The recorded prepared set is a compatibility baseline, not a promise that independently generated resources will have identical hashes. Review and validate a new resource baseline when completing the public bootstrap.

## Native macOS

Requirements: macOS 14+, Xcode with its macOS SDK, and Python 3.10+ with venv/pip. The recorded build used Xcode 27.1; other toolchains need their own validation. Import and check resources first, then run from the repository root:

```sh
bash FarmVillage/macOS/Scripts/build.sh Release
```

The unsigned app output is `FarmVillage/macOS/.build/DerivedData/Build/Products/Release/FarmVillage.app`. Alternatively, open `FarmVillage/macOS/FarmVillage.xcodeproj`, select the shared **FarmVillage** scheme and **My Mac**, then build.

In the app, complete **Prepare Runtime** and create a new synthetic farm for testing. Verify actual window interactions, save/reload, God Barn return and process restart separately from compilation. Signing/notarization and execution on Intel hardware require separate qualification.

## Browser hosting and Ubuntu

Once the complete matching resource set is present, the existing staging tool can create a new external browser release directory:

```sh
"$FV_CHECK_ENV/bin/python" -B tools/prepare-browser-runtime.py   --output /absolute/path/to/new-browser-release
```

The output must be new and outside the source checkout. Staging verifies inputs; it does not deploy or qualify a server.

The existing prepared-release installer is documented in [BIFROST_SETUP.md](../BIFROST_SETUP.md). That historical filename refers to a managed release workflow, not a host every contributor must have. It requires a complete prepared bundle and extracted artwork; running `START_HERE.sh` in an unprepared source clone is not a public setup solution.

The current release policy uses fresh farms. The installer must identify its managed installation, request explicit confirmation before wiping it, and refuse unrelated, system, source and linked paths. Do not run destructive installation steps to test documentation. Actual Ubuntu installation, managed-service operation and gameplay remain separate open qualification tasks.

## God Barn

Read [God Barn’s README](../GodBarn/README.md) and [integration contracts](../GodBarn/Documentation/INTEGRATION_CONTRACTS.md). The integrated editor operates through the game server’s ownership and transaction boundaries. Standalone mode edits explicitly imported copies in its own workspace and does not attach to a running farm.

With compatible companion resources prepared, run standalone mode from `GodBarn/`:

```sh
"$FV_CHECK_ENV/bin/python" -B launcher.py --no-browser
```

Use fresh synthetic data for testing. No example player farm is bundled.

## Resource-dependent regression suites

The source-only tests in the README cover selected synthetic contracts. Full application and companion suites require matching resources and, for some tools, Node.js. Do not interpret missing resource errors as a completed game test.

From the repository root, the active-release runner selects the current sixteen-world suite and lists retired-only cases separately:

```sh
mkdir -p "$HOME/farmvillage-test-results"
WAVE2_GODBARN_ROOT="$(pwd)/GodBarn"   "$FV_CHECK_ENV/bin/python" -I -B -W error::ResourceWarning   FarmVillage/macOS/Scripts/run-active-release-regressions.py   --report "$HOME/farmvillage-test-results/new-active-release-result.json"
```

Choose a new report filename. `--list-only` lists the selected tests and still needs the matching inputs. Complete God Barn tests run from `GodBarn/` with `"$FV_CHECK_ENV/bin/python" -B -m unittest discover -s tests -v` after its resources are available.

Record source revision, resource identities, command, platform, result and unrun checks. Keep native macOS, browser, actual Ubuntu and synthetic fixtures distinct. [ACCEPTANCE.md](../ACCEPTANCE.md) is a historical validation record, not evidence that a new checkout or build has passed those checks.
