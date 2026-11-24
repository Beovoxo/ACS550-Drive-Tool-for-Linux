# ABB Drive Tool for Linux

**Independent, community-developed Linux application inspired by the publicly described workflow of ABB DriveWindow Light 2.93. Not affiliated with or endorsed by ABB.**

A Debian/Linux desktop utility intended to run alongside LinuxCNC. It is a normal userspace application and does not execute in LinuxCNC's real-time motion thread.

## Current release: 0.1.0 (early prototype)

### Included
- PySide6 desktop interface with Connection, Drive Status, Parameter Browser, Monitor and Safety tabs.
- Serial Modbus RTU connection settings (device, baud rate, slave ID, parity, stop bits and timeout).
- Read-only Modbus function 03 polling for three holding registers (default view labelled 40004–40006).
- Offline parameter workspace with editable rows.
- JSON and CSV parameter-set import/export.
- Parameter-set comparison by parameter number.
- Debian installation helper and GPL-3.0-only licensing.

### Not implemented yet
- ABB OPCA-02 / panel-link protocol.
- ABB drive identification and automatic parameter dictionary retrieval.
- Online parameter upload/download or parameter writes.
- Drive start/stop, reference control, fault reset or control-word writes.
- Full signal plotting, step-response tests, wizards and sequence programming.
- Native LinuxCNC HAL integration.

These are deliberately not claimed as working. The supplied DriveWindow Light guide describes OPCA-02 as the required adapter for ACS/ACH550-family connections; generic Modbus RTU is not automatically equivalent to that interface. The register addresses in this prototype are a generic, configurable starting point and must be checked against the exact drive interface/profile before use.

## Requirements
- Debian 12/13 or a compatible Debian-based Linux distribution
- Python 3.10+
- PySide6, pyserial and pymodbus (installed by `run.sh`)
- A supported USB/RS-232/RS-485 serial adapter and the correct electrical interface for the drive

## Install and run

```bash
sudo apt update
sudo apt install -y python3-full python3-venv
# Optional: grant the current user access to serial devices
sudo usermod -aG dialout "$USER"
# Log out and back in after changing group membership
unzip abb-drive-tool-linux-v0.1.0.zip
cd abb-drive-tool-linux
./run.sh
```

The first run creates `.venv`, installs Python dependencies and launches the application. On some Debian installations, Qt platform plugins may require standard desktop packages from the distribution.

Danish installation notes: [`docs/DEBIAN_INSTALL_DA.md`](docs/DEBIAN_INSTALL_DA.md).

## Safety and limitations

This version is **read-only on the drive communication side**. It does not issue drive-control or parameter-write commands. Do not use it as a safety device or as a substitute for ABB commissioning documentation. Verify the drive model, firmware, adapter, bus wiring, termination, serial settings and register map before connecting. Test with the motor safely isolated where appropriate.

LinuxCNC's real-time motion and safety functions remain separate. Do not connect this prototype to motion-critical HAL pins or rely on desktop polling for machine safety.

## Tests

```bash
python -m unittest discover -s tests -v
```

## License

The original source code in this repository is licensed under **GNU General Public License v3.0 only**. See [`LICENSE`](LICENSE).

ABB names and product names are used only to identify compatibility targets. ABB's original installer, binaries, manuals, logos and proprietary source are not included in this repository and are not relicensed by this project. This is an independent implementation; no ABB source code has been copied into it.
