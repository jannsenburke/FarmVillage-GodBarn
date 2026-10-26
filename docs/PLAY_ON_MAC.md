# Play on your Mac

The game is a sixteen-world alpha with incomplete regional features; see [world readiness](../WORLD_READINESS.md).

This path is for people who want the native Mac app and are comfortable keeping a large game installation on their own computer. A separate server is not required.

**Current status: a fresh-download Mac installation is not ready yet.** The repository provides source code, not a complete public Mac installer. The app needs additional prepared client files, God Barn data, native artwork and a pinned compiled player before it can be built. The new setup wizard is a **readiness guide**; it will not pretend those files are available or start a large download to work around them.

## Start with the readiness guide

1. On the repository page, choose **Code → Download ZIP**, or use your existing clone.
2. Extract the ZIP and open the resulting folder.
3. Double-click **START_MAC.command**. You can also run `bash START_MAC.command` from a Terminal opened in that folder.
4. Read the status and download explanation. The guide checks only the selected source folder; it does not search your Mac for someone else’s installation or ask for an owner’s checkpoint.
5. If required resources are missing, it stops and names the missing groups. Follow the linked resource/status documents if you want to help finish setup. This is not an “installed successfully” result.

The guide does not install Python, developer tools, packages or game files. It does not create game data or modify saves. If a compatible Python is unavailable, the launcher explains that and points back to this document instead of automatically invoking Apple’s developer-tool installer. Python is already a prerequisite of the current game runtime; the guide does not supply it.

For a read-only machine-readable check with an existing Python interpreter:

```sh
python3 -I -B tools/player-setup.py --audience mac --check --json
```

A not-ready result is expected for today’s source-only clone. A source resource check is also separate from testing a built app on a Mac.

## What a complete Mac app does

These steps describe the existing native app **after a complete, compatible app bundle has been built**. They are not a way to turn today’s source ZIP into that bundle.

| Step | What happens | Network and storage |
| --- | --- | --- |
| Install prerequisites | The current runtime requires macOS 14+ and an already installed Python 3.10+ | Python is not installed automatically |
| Open **Settings → Setup** and choose **Prepare Runtime** | Creates or replaces its dedicated Python environment, installs five pinned Python packages, and copies the reviewed player included in the app | Python packages come from PyPI; the player must already be bundled locally |
| Choose **Create Farm** or **Open Farm** | Starts the local game server; if artwork is missing, downloads and extracts the four original game archives | Archives come from Internet Archive’s `original-farmville` collection |
| Watch **Activity** | Shows download, verification, extraction and startup progress | The first start can take an hour or more |
| Create your farm and play | Follow the app’s farm-creation prompts after startup completes | The game and saves remain on this Mac |

The normal Prepare Runtime path does **not** fetch the missing original client, God Barn catalogue, native artwork or the pinned player needed to build the app. It installs the player already included in a complete bundle. An older official-player download helper in the source is not the normal preparation path.

## The 20+ GB commitment

The four recorded archive files total **19,126,111,395 bytes — 19.13 GB / 17.81 GiB**. That is the compressed download alone. Extracted artwork, temporary extraction, the runtime and saves require more space. **20 GB free is not an adequate installation promise.**

A complete fresh-install peak-space requirement has not yet been qualified. The existing native downloader has no full-install disk-space preflight or guaranteed maximum. The readiness guide reports that limitation; it does not invent a precise storage guarantee or start those downloads.

A complete app normally stores its data at:

```text
~/Library/Application Support/FarmVillage/
```

That folder holds the runtime, Python environment, artwork, caches, temporary archives, saves, logs and God Barn history. Original archives are temporary inputs: successful extraction/publication cleans the owned archive/extraction cache. If a download is interrupted, **Stop Farm** preserves partial downloads and verified archives for retry. A partial file can resume when the archive server supports byte ranges; otherwise that file starts again. Interrupted extraction starts again from the retained archives; it is not an extraction resume. An existing incomplete artwork folder may be preserved separately, using additional disk space.

## What is still needed before this is a normal player install

The public resource pipeline must produce the complete app inputs from their original sources, verify them, build/package the app, and pass a fresh-Mac installation plus real farming/save/restart checks. See [resource setup](RESOURCE_SETUP.md) and [development priorities](../HANDOVER_STATUS.md).

If you are contributing that work, use the [development and build guide](DEVELOPMENT.md). If you would rather host the game once and let people connect through browsers, use [the server path](PLAY_ON_SERVER.md).
