# Host the game on a server

The game is a sixteen-world alpha with incomplete regional features; see [world readiness](../WORLD_READINESS.md).

This path is for people who have an Ubuntu/Linux server and want to run the game there. The server stores the game resources and farms. Players connect through a browser; they do not install the full archive collection on every computer. Their browsers still download the player and individual game files as needed.

**Current status: automatic setup from a fresh public clone is unfinished.** The existing server installer requires a complete prepared release and already-extracted artwork. It does not retrieve and assemble all game resources from the public sources. A server or folder with a particular personal name is not a prerequisite.

## Start with the readiness guide

1. Put the source checkout on the Ubuntu/Linux machine you intend to use as the host.
2. Open a terminal in that source folder and run `bash START_HERE.sh`.
3. The public-source entry opens the **server readiness guide**. It explains what is missing and which later steps use the network or modify an installation.
4. If resources are missing, stop at that result. The guide will not ask you to obtain the project owner’s Mac, private checkpoint or authentication files.

With an existing Python interpreter, you can also run:

```sh
python3 -I -B tools/player-setup.py --audience server --check --json
```

This is a read-only source-readiness check, not a successful server installation. Running it on a Mac does not qualify Ubuntu hosting or deploy anything to another computer.

## Who downloads and stores what?

| Component | Server owner | Browser players |
| --- | --- | --- |
| Original archive collection and extracted artwork | Prepare/store the resources on the host; the compressed archives alone are 19.13 GB and extraction needs additional space | No full archive installation |
| Client/configuration, God Barn data and pinned player | Must be in the prepared release before installation | Served by the host as needed |
| Python dependencies | The prepared-release installer creates a fresh environment and downloads five pinned packages from PyPI | No local Python installation |
| Farms and God Barn history | Stored in the host’s managed data directory | Accessed through the game |

The supported prepared-release installer **does not automatically download WARCs or extract artwork**. That missing public setup work is distinct from the native Mac app’s later first-start artwork downloader. The older raw server downloader is not a substitute for the complete reviewed server release.

During a clean replacement, the installer stages another copy of the selected artwork before deleting the old managed target. Both copies can exist temporarily. It checks the staging space it needs; archive acquisition/extraction is a separate storage cost.

## When you already have a complete prepared release

The managed installer runs on the host itself, using a normal user login with Python 3.10+ and systemd user services. Extract the prepared bundle outside the installation target and run its `bash START_HERE.sh`. This bundle entry is separate from the source clone’s readiness guide.

The installer’s eight steps are:

1. **Check the tools:** verify the Ubuntu login, Python and user services.
2. **Choose the home for the game:** review the managed installation folder and select a private/loopback address and unused port.
3. **Bring the artwork:** select an already-extracted assets folder containing `Environment/` and `xpromoSupport/`.
4. **Name the clean slate:** review the exact installation target and enter the explicit wipe confirmation.
5. **Make room for a new season:** stage verified resources and artwork, then replace only the positively identified managed installation.
6. **Prepare the fresh engine:** create a new Python environment and install the pinned packages.
7. **Choose a new key to the gate:** create a fresh browser password privately on the server.
8. **Open the gate:** start the managed service, verify its sign-in page and show the browser address.

The current release is a clean start. If an existing managed installation is replaced, its old farms, snapshots, history, environment and authentication are erased after the named confirmation. The installer refuses unrelated, system, source and linked paths. No previous farms or passwords are bundled.

The default managed target is `~/farmvillage-server`. Its `release/` holds the game environment; `data/` holds artwork, farms and other game data. Use the [prepared-release installer reference](../BIFROST_SETUP.md) for the matching detailed sequence. The historical filename does not require that server name or access to the owner’s host.

## Connecting players

The current hosting layer accepts private/loopback IPv4 addresses. Use the exact browser URL printed by the running installer/service, sign in with the new server password, then create a farm. Loopback (`127.0.0.1`) works only on the server itself; other computers need the host’s reachable private-network address.

General public-internet hosting, reverse-proxy/TLS deployment and actual Ubuntu installation/gameplay still need their own qualification. A local fixture test or a browser scene on a Mac does not establish those results.

For the unfinished original-source acquisition and resource assembly, start with [resource setup](RESOURCE_SETUP.md) and [development priorities](../HANDOVER_STATUS.md). For the all-local native app, use [the Mac path](PLAY_ON_MAC.md).
