# Installation på Debian / LinuxCNC

Programmet er en almindelig Qt-applikation. Det skal ikke køres i LinuxCNC's realtids-tråd.

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-pyside6.qtwidgets python3-serial
cd abb-drive-tool-linux
./run.sh
```

Hvis Debian-pakken til PySide6 mangler eller er for gammel, kan du bruge projektets virtuelle miljø:

```bash
sudo apt install -y python3-full python3-venv
./run.sh
```

For adgang til serielport uden `sudo` (log ud/ind efter ændringen):

```bash
sudo usermod -aG dialout "$USER"
```

Kontrollér portnavnet med `ls -l /dev/ttyUSB* /dev/ttyS*`.

**Vigtigt:** Første version kan kun læse Modbus holding registers. Den kan ikke uploade ABB's komplette parameterliste via OPCA-02, skrive parametre eller styre start/stop. ACS550 via panelstikket kan kræve OPCA-02 og ABB's specifikke kommunikationsprotokol. Bekræft interface og protokol før tilslutning.
