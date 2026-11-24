from __future__ import annotations
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox,
    QGroupBox, QHeaderView, QStatusBar, QPlainTextEdit
)

from . import __version__
from .data import load_parameters, save_parameters, compare_sets
from .modbus import ModbusSettings, ReadOnlyModbus


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"ABB Drive Tool for Linux — v{__version__}")
        self.resize(1180, 760)
        self.bus = ReadOnlyModbus()
        self.parameter_rows = []
        self.loaded_path = None
        self.previous_set = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll_drive)
        self._build_ui()
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #202833; color: #e7edf4; }
            QTabWidget::pane { border: 1px solid #465464; }
            QTabBar::tab { background: #303c49; padding: 9px 18px; margin-right: 2px; }
            QTabBar::tab:selected { background: #1676a3; }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTableWidget {
                background: #141b23; color: #edf3f8; border: 1px solid #526273; padding: 5px;
                selection-background-color: #1676a3;
            }
            QPushButton { background: #176b91; border: 0; padding: 8px 14px; border-radius: 3px; }
            QPushButton:hover { background: #218bb8; }
            QPushButton:disabled { background: #48525d; color: #aab3bd; }
            QGroupBox { border: 1px solid #526273; margin-top: 10px; padding: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            QHeaderView::section { background: #344252; padding: 6px; border: 0; }
        """)

    def _build_ui(self):
        root = QWidget(); layout = QVBoxLayout(root)
        header = QHBoxLayout()
        title = QLabel("DRIVE COMMISSIONING & MONITORING")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #69c8ef;")
        self.connection_badge = QLabel("● OFFLINE")
        self.connection_badge.setStyleSheet("color: #e5b44c; font-weight: bold;")
        header.addWidget(title); header.addStretch(); header.addWidget(self.connection_badge)
        layout.addLayout(header)
        self.tabs = QTabWidget()
        self.tabs.addTab(self._connection_tab(), "Connection")
        self.tabs.addTab(self._status_tab(), "Drive status")
        self.tabs.addTab(self._parameters_tab(), "Parameter browser")
        self.tabs.addTab(self._monitor_tab(), "Monitor")
        self.tabs.addTab(self._about_tab(), "About / safety")
        layout.addWidget(self.tabs)
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Offline mode — no drive commands are sent")

    def _connection_tab(self):
        w = QWidget(); outer = QVBoxLayout(w)
        box = QGroupBox("Modbus RTU connection (read-only in this release)")
        form = QFormLayout(box)
        self.port = QComboBox(); self.port.setEditable(True); self.port.addItems(["/dev/ttyUSB0", "/dev/ttyS0", "/dev/ttyS1"])
        self.baud = QComboBox(); self.baud.addItems(["9600", "19200", "38400", "57600", "115200"])
        self.slave = QSpinBox(); self.slave.setRange(1, 247); self.slave.setValue(1)
        self.parity = QComboBox(); self.parity.addItems(["N", "E", "O"])
        self.stopbits = QComboBox(); self.stopbits.addItems(["1", "2"])
        self.timeout = QDoubleSpinBox(); self.timeout.setRange(.2, 10); self.timeout.setValue(1.0); self.timeout.setSuffix(" s")
        form.addRow("Serial device", self.port); form.addRow("Baud rate", self.baud)
        form.addRow("Modbus slave ID", self.slave); form.addRow("Parity", self.parity)
        form.addRow("Stop bits", self.stopbits); form.addRow("Timeout", self.timeout)
        outer.addWidget(box)
        buttons = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_drive)
        self.disconnect_btn = QPushButton("Disconnect"); self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.clicked.connect(self.disconnect_drive)
        buttons.addWidget(self.connect_btn); buttons.addWidget(self.disconnect_btn); buttons.addStretch()
        outer.addLayout(buttons)
        note = QLabel("Important: ACS550 panel-port communication may require the ABB OPCA-02 adapter and its supported protocol. This generic Modbus RTU reader is not a replacement for that adapter/protocol. Verify the selected physical interface, baud rate, parity and node ID against the drive and adapter manuals.")
        note.setWordWrap(True); note.setStyleSheet("background:#3b3030; padding:12px; border-left:4px solid #d49b42;")
        outer.addWidget(note); outer.addStretch()
        return w

    def _status_tab(self):
        w = QWidget(); layout = QVBoxLayout(w)
        box = QGroupBox("Drive status — standard Modbus register view (configurable offsets in source)")
        form = QFormLayout(box)
        self.status_values = {}
        for key, label in [("status", "Status word (4xxxx register 40004)"), ("actual1", "Actual value 1 (40005)"), ("actual2", "Actual value 2 (40006)")]:
            value = QLabel("—"); value.setStyleSheet("font-size:18px; color:#72d4a2; font-weight:bold;")
            self.status_values[key] = value; form.addRow(label, value)
        layout.addWidget(box)
        self.poll_label = QLabel("Polling is stopped")
        layout.addWidget(self.poll_label)
        refresh = QPushButton("Read once"); refresh.clicked.connect(self.poll_drive)
        layout.addWidget(refresh); layout.addStretch()
        return w

    def _parameters_tab(self):
        w = QWidget(); layout = QVBoxLayout(w)
        intro = QLabel("Offline parameter workspace. Import a parameter export or create your own set. No values are assumed to be safe defaults.")
        intro.setWordWrap(True); layout.addWidget(intro)
        self.parameter_table = QTableWidget(0, 5)
        self.parameter_table.setHorizontalHeaderLabels(["Parameter", "Name", "Value", "Unit", "Notes"])
        self.parameter_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.parameter_table.setAlternatingRowColors(True)
        layout.addWidget(self.parameter_table)
        buttons = QHBoxLayout()
        for label, fn in [("Add row", self.add_parameter), ("Remove selected", self.remove_parameter), ("Open JSON/CSV", self.open_parameters), ("Save backup", self.save_parameters_file), ("Compare with…", self.compare_parameters)]:
            b = QPushButton(label); b.clicked.connect(fn); buttons.addWidget(b)
        layout.addLayout(buttons)
        return w

    def _monitor_tab(self):
        w = QWidget(); layout = QVBoxLayout(w)
        note = QLabel("Live trend plotting is planned for a later release. This initial build provides a safe register-read test and a numeric status view.")
        note.setWordWrap(True); layout.addWidget(note)
        self.monitor_log = QPlainTextEdit(); self.monitor_log.setReadOnly(True)
        layout.addWidget(self.monitor_log)
        controls = QHBoxLayout()
        self.poll_interval = QSpinBox(); self.poll_interval.setRange(250, 10000); self.poll_interval.setValue(1000); self.poll_interval.setSuffix(" ms")
        start = QPushButton("Start polling"); start.clicked.connect(self.start_polling)
        stop = QPushButton("Stop polling"); stop.clicked.connect(self.timer.stop)
        controls.addWidget(QLabel("Interval")); controls.addWidget(self.poll_interval); controls.addWidget(start); controls.addWidget(stop); controls.addStretch()
        layout.addLayout(controls)
        return w

    def _about_tab(self):
        w = QWidget(); layout = QVBoxLayout(w)
        text = QLabel("<b>Independent community project — not an ABB product.</b><br><br>Designed for Debian-based Linux systems, including systems running LinuxCNC. It runs as a normal desktop application and does not run inside LinuxCNC's real-time motion thread.<br><br><b>Safety:</b> This release is read-only on the drive communication side. It does not start/stop a drive, change parameters, reset faults, or write control words. Do not rely on this application as a safety device. Use the drive's approved documentation, hardware interlocks and commissioning procedures.<br><br><b>Compatibility:</b> The uploaded DriveWindow Light 2.93 guide lists ACS/ACH550 among supported drive families and describes an OPCA-02 adapter for ACS/ACH550. That does not establish that generic Modbus RTU on an arbitrary serial port can perform all DriveWindow functions. Protocol and adapter support must be validated separately.")
        text.setWordWrap(True); text.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(text); layout.addStretch()
        return w

    def connect_drive(self):
        try:
            settings = ModbusSettings(
                port=self.port.currentText().strip(), baudrate=int(self.baud.currentText()),
                slave_id=self.slave.value(), parity=self.parity.currentText(),
                stopbits=int(self.stopbits.currentText()), timeout=self.timeout.value())
            self.bus.connect(settings)
            self.connection_badge.setText("● CONNECTED — READ ONLY")
            self.connection_badge.setStyleSheet("color:#72d4a2; font-weight:bold;")
            self.connect_btn.setEnabled(False); self.disconnect_btn.setEnabled(True)
            self.statusBar().showMessage(f"Connected to {settings.port} — read-only")
            self.poll_drive()
        except Exception as exc:
            QMessageBox.critical(self, "Connection failed", str(exc))

    def disconnect_drive(self):
        self.timer.stop(); self.bus.close()
        self.connection_badge.setText("● OFFLINE"); self.connection_badge.setStyleSheet("color:#e5b44c; font-weight:bold;")
        self.connect_btn.setEnabled(True); self.disconnect_btn.setEnabled(False)
        self.statusBar().showMessage("Disconnected")

    def poll_drive(self):
        if not self.bus.connected:
            self.poll_label.setText("Not connected")
            return
        try:
            # Modbus PDU addresses are zero-based: 40004 -> address 3.
            regs = self.bus.read_holding(3, 3)
            self.status_values["status"].setText(f"0x{regs[0]:04X}  ({regs[0]})")
            self.status_values["actual1"].setText(str(regs[1]))
            self.status_values["actual2"].setText(str(regs[2]))
            line = f"Read OK — status=0x{regs[0]:04X}, actual1={regs[1]}, actual2={regs[2]}"
            self.poll_label.setText(line); self.monitor_log.appendPlainText(line)
        except Exception as exc:
            self.poll_label.setText(f"Read error: {exc}")
            self.monitor_log.appendPlainText(f"ERROR — {exc}")

    def start_polling(self):
        if not self.bus.connected:
            QMessageBox.information(self, "Offline", "Connect to a drive first."); return
        self.timer.start(self.poll_interval.value()); self.poll_drive()

    def add_parameter(self):
        row = self.parameter_table.rowCount(); self.parameter_table.insertRow(row)
        for col in range(5): self.parameter_table.setItem(row, col, QTableWidgetItem(""))

    def remove_parameter(self):
        rows = sorted({i.row() for i in self.parameter_table.selectedIndexes()}, reverse=True)
        for row in rows: self.parameter_table.removeRow(row)

    def _table_rows(self):
        rows = []
        for r in range(self.parameter_table.rowCount()):
            vals = []
            for c in range(5):
                item = self.parameter_table.item(r, c); vals.append(item.text() if item else "")
            rows.append(dict(zip(("number", "name", "value", "unit", "note"), vals)))
        return rows

    def _set_rows(self, rows):
        self.parameter_table.setRowCount(0)
        for data in rows:
            row = self.parameter_table.rowCount(); self.parameter_table.insertRow(row)
            vals = [data.get(k, "") for k in ("number", "name", "value", "unit", "note")]
            for c, val in enumerate(vals): self.parameter_table.setItem(row, c, QTableWidgetItem(str(val)))

    def open_parameters(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open parameter set", "", "Parameter files (*.json *.csv)")
        if not path: return
        try:
            rows = load_parameters(path); self._set_rows(rows); self.loaded_path = path
            self.statusBar().showMessage(f"Loaded {len(rows)} parameters from {Path(path).name}")
        except Exception as exc: QMessageBox.critical(self, "Open failed", str(exc))

    def save_parameters_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save parameter backup", "drive-parameters.json", "JSON (*.json);;CSV (*.csv)")
        if not path: return
        try:
            save_parameters(path, self._table_rows()); self.statusBar().showMessage(f"Saved {path}")
        except Exception as exc: QMessageBox.critical(self, "Save failed", str(exc))

    def compare_parameters(self):
        path, _ = QFileDialog.getOpenFileName(self, "Compare with parameter set", "", "Parameter files (*.json *.csv)")
        if not path: return
        try:
            other = load_parameters(path); changes = compare_sets(self._table_rows(), other)
            lines = [f"{num}: current={a.get('value') if a else '<missing>'} | comparison={b.get('value') if b else '<missing>'}" for num, a, b in changes]
            QMessageBox.information(self, "Parameter comparison", "No differences found." if not lines else "\n".join(lines[:100]))
        except Exception as exc: QMessageBox.critical(self, "Compare failed", str(exc))

    def closeEvent(self, event):
        self.timer.stop(); self.bus.close(); event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ABB Drive Tool for Linux")
    win = MainWindow(); win.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
