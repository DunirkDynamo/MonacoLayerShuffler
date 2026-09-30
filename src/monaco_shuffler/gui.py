"""PySide6 user interface for Monaco Shuffler.

This module provides a glassmorphism-inspired desktop window with stronger
color accents, layered cards, and the same preview/write-back workflow.
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from .core import (
    apply_target_layers,
    StructureRecord,
    build_preview_order,
    load_structure_file,
    write_structure_file,
)


def _og_copy_path(path: Path) -> Path:
    """Return the sibling path used for the original backup copy."""

    return path.with_name(f"{path.stem}_OG{path.suffix}")


class GlassCard(QFrame):
    """Rounded translucent panel used throughout the UI."""

    def __init__(self, parent=None, tone="neutral") -> None:
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setProperty("tone", tone)
        self.setFrameShape(QFrame.NoFrame)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 120))
        self.setGraphicsEffect(shadow)


class RowWidget(QFrame):
    """One structure row in the reorder table."""

    def __init__(self, record, layer_count, row_index=0, parent=None) -> None:
        super().__init__(parent)
        self.record = record
        self.setObjectName("RowWidget")
        self.setProperty("stripe", row_index % 2)

        layout = QGridLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setHorizontalSpacing(16)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        self.original_label = QLabel(str(record.original_layer))
        self.original_label.setObjectName("LayerBadge")
        self.name_label = QLabel(record.name)
        self.name_label.setWordWrap(False)
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.name_label.setObjectName("StructureLabel")

        self.combo = QComboBox()
        self.combo.addItems([str(index) for index in range(1, layer_count + 1)])
        self.combo.setCurrentText(str(record.original_layer))

        self.preview_label = QLabel("")
        self.preview_label.setObjectName("PreviewLabel")

        layout.addWidget(self.original_label, 0, 0)
        layout.addWidget(self.name_label, 0, 1)
        layout.addWidget(self.combo, 0, 2)
        layout.addWidget(self.preview_label, 0, 3)

    def selected_target(self):
        """Return the selected destination layer as an integer."""

        return int(self.combo.currentText())

    def reset(self):
        """Restore the combo box to the original layer index."""

        self.combo.setCurrentText(str(self.record.original_layer))
        self.preview_label.setText("")

    def set_preview(self, text):
        """Set the preview label text for this row."""

        self.preview_label.setText(text)


class MonacoShufflerApp(QMainWindow):
    """Main application window."""

    def __init__(self, initial_records=None, source_path=None) -> None:
        super().__init__()
        self.records = []
        self.row_widgets = []
        self.source_path = source_path

        self.setWindowTitle("Monaco Shuffler")
        self.resize(1180, 760)

        self._build_ui()
        self._apply_theme()
        if initial_records is not None:
            self.set_records(initial_records)

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("CentralShell")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(18)

        title_card = GlassCard(tone="hero")
        title_layout = QVBoxLayout(title_card)
        title_layout.setContentsMargins(24, 22, 24, 22)
        title_layout.setSpacing(8)

        title = QLabel("Monaco Layer Shuffler")
        title.setObjectName("TitleLabel")

        title_layout.addWidget(title)

        meta_row = QHBoxLayout()
        self.file_label = QLabel("No file loaded")
        self.file_label.setObjectName("FileLabel")
        self.status_label = QLabel("Load a Monaco-style file to begin.")
        self.status_label.setObjectName("StatusLabel")
        self.open_button = QPushButton("Open File")
        self.open_button.clicked.connect(self.open_file)

        meta_row.addWidget(self.file_label)
        meta_row.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        meta_row.addWidget(self.open_button)
        title_layout.addLayout(meta_row)

        root.addWidget(title_card)

        table_card = GlassCard(tone="surface")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(18, 18, 18, 18)
        table_layout.setSpacing(10)

        header = QGridLayout()
        header.setHorizontalSpacing(16)
        header.setContentsMargins(14, 0, 14, 0)
        for column, text in enumerate(("Layer", "Structure", "Target Index", "Preview")):
            label = QLabel(text)
            label.setObjectName("HeaderLabel")
            header.addWidget(label, 0, column)

        header.setColumnStretch(1, 1)
        header.setColumnStretch(3, 1)
        table_layout.addLayout(header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.table_container = QWidget()
        self.rows_layout = QVBoxLayout(self.table_container)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(10)

        self.scroll_area.setWidget(self.table_container)
        table_layout.addWidget(self.scroll_area)

        button_row = QHBoxLayout()
        self.reset_button = QPushButton("Reset")
        self.confirm_button = QPushButton("Confirm Reorder")
        self.apply_button = QPushButton("Apply Reorder")

        self.reset_button.clicked.connect(self.reset_values)
        self.confirm_button.clicked.connect(self.confirm_reorder)
        self.apply_button.clicked.connect(self.apply_reorder)

        button_row.addWidget(self.reset_button)
        button_row.addWidget(self.confirm_button)
        button_row.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        button_row.addWidget(self.apply_button)
        table_layout.addLayout(button_row)

        root.addWidget(table_card, 1)
        root.addWidget(self.status_label)

    def _apply_theme(self):
        app = QApplication.instance()
        if app is None:
            return

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(14, 18, 28))
        palette.setColor(QPalette.WindowText, QColor(245, 248, 255))
        palette.setColor(QPalette.Base, QColor(22, 28, 40, 200))
        palette.setColor(QPalette.AlternateBase, QColor(30, 36, 52, 210))
        palette.setColor(QPalette.Text, QColor(245, 248, 255))
        palette.setColor(QPalette.Button, QColor(255, 255, 255, 24))
        palette.setColor(QPalette.ButtonText, QColor(245, 248, 255))
        palette.setColor(QPalette.Highlight, QColor(100, 180, 255))
        palette.setColor(QPalette.HighlightedText, QColor(10, 14, 20))
        app.setPalette(palette)

        app.setStyleSheet(
            """
            QMainWindow {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                            stop: 0 #0b1020,
                                            stop: 0.55 #121a29,
                                            stop: 1 #09111d);
            }
            QWidget#CentralShell {
                background: transparent;
            }
            QFrame#GlassCard {
                background: rgba(255, 255, 255, 0.09);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 24px;
            }
            QFrame#GlassCard[tone="hero"] {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                            stop: 0 rgba(127, 87, 255, 0.30),
                                            stop: 0.55 rgba(89, 180, 255, 0.18),
                                            stop: 1 rgba(255, 255, 255, 0.06));
                border: 1px solid rgba(173, 197, 255, 0.28);
            }
            QFrame#GlassCard[tone="surface"] {
                background: rgba(16, 21, 35, 0.72);
                border: 1px solid rgba(100, 180, 255, 0.18);
            }
            QFrame#RowWidget {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 18px;
            }
            QFrame#RowWidget[stripe="0"] {
                background: rgba(95, 173, 255, 0.08);
            }
            QFrame#RowWidget[stripe="1"] {
                background: rgba(255, 255, 255, 0.06);
            }
            QLabel#TitleLabel {
                font-size: 28px;
                font-weight: 700;
                color: #f8faff;
            }
            QLabel#SubtitleLabel {
                font-size: 13px;
                color: rgba(238, 244, 255, 0.82);
            }
            QLabel#FileLabel, QLabel#StatusLabel, QLabel#HeaderLabel {
                color: rgba(245, 248, 255, 0.84);
            }
            QLabel#HeaderLabel {
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
                color: rgba(173, 219, 255, 0.95);
            }
            QLabel#LayerBadge {
                background: rgba(100, 180, 255, 0.22);
                color: #eef7ff;
                border: 1px solid rgba(100, 180, 255, 0.28);
                border-radius: 10px;
                padding: 4px 10px;
                font-weight: 700;
            }
            QLabel#StructureLabel {
                color: #f9fbff;
            }
            QLabel#PreviewLabel {
                color: #9ff0bf;
                font-weight: 600;
            }
            QLabel {
                color: #f5f8ff;
            }
            QPushButton {
                min-height: 40px;
                padding: 0 18px;
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                background: rgba(255, 255, 255, 0.10);
                color: #f5f8ff;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.16);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.22);
            }
            QPushButton#PrimaryButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                            stop: 0 rgba(86, 129, 255, 0.95),
                                            stop: 1 rgba(84, 223, 180, 0.85));
                border-color: rgba(157, 231, 255, 0.55);
                color: #08111c;
            }
            QPushButton#PrimaryButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                            stop: 0 rgba(104, 148, 255, 0.98),
                                            stop: 1 rgba(108, 236, 195, 0.92));
            }
            QComboBox {
                min-height: 34px;
                padding: 0 12px;
                border-radius: 12px;
                border: 1px solid rgba(137, 206, 255, 0.24);
                background: rgba(8, 12, 20, 0.44);
                color: #f5f8ff;
            }
            QComboBox:hover {
                border: 1px solid rgba(164, 223, 255, 0.42);
                background: rgba(12, 17, 28, 0.60);
            }
            QComboBox::drop-down {
                border: 0;
                width: 28px;
            }
            QComboBox QAbstractItemView {
                background: #101828;
                color: #f5f8ff;
                selection-background-color: #64b4ff;
                border: 1px solid rgba(255, 255, 255, 0.14);
                outline: 0;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            """
        )

        self.confirm_button.setObjectName("PrimaryButton")
        self.apply_button.setObjectName("PrimaryButton")

    def format_source_path(self, source_path):
        if source_path is None:
            return "No file loaded"
        return str(source_path)

    def set_status(self, text):
        self.status_label.setText(text)

    def set_source_label(self, text):
        self.file_label.setText(text)

    def set_records(self, records):
        self.records = list(records)
        self.set_source_label(self.format_source_path(self.source_path))
        self.set_status(f"Loaded {len(self.records)} structures.")
        self._rebuild_table()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _rebuild_table(self):
        self._clear_layout(self.rows_layout)
        self.row_widgets = []

        if not self.records:
            placeholder = QLabel("Open a file to populate the table.")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setObjectName("EmptyStateLabel")
            self.rows_layout.addWidget(placeholder)
            self.rows_layout.addStretch(1)
            return

        layer_count = len(self.records)
        for row_index, record in enumerate(self.records):
            row = RowWidget(record, layer_count, row_index)
            self.rows_layout.addWidget(row)
            self.row_widgets.append(row)

        self.rows_layout.addStretch(1)

    def open_file(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Monaco text file",
            str(Path.cwd()),
            "Text files (*.txt);;All files (*.*)",
        )
        if not file_name:
            return

        path = Path(file_name)
        try:
            records = load_structure_file(path)
        except ValueError as exc:
            QMessageBox.critical(self, "Could not load file", str(exc))
            return

        self.source_path = path
        self.set_source_label(self.format_source_path(path))
        self.set_records(records)

    def _selected_targets(self):
        return [row.selected_target() for row in self.row_widgets]

    def confirm_reorder(self):
        try:
            preview_records = build_preview_order(self.records, self._selected_targets())
        except ValueError as exc:
            QMessageBox.critical(self, "Invalid reorder", str(exc))
            return

        for row_widget, record in zip(self.row_widgets, preview_records):
            row_widget.set_preview(record.name)

        self.set_status("Preview updated. Use Apply Reorder when you are ready to save.")

    def reset_values(self):
        for row_widget in self.row_widgets:
            row_widget.reset()

        self.set_status("Dropdowns reset to the original file order.")

    def apply_reorder(self):
        if not self.records:
            QMessageBox.information(self, "Nothing to apply", "Load a file before applying a reorder.")
            return

        try:
            adjusted_records = apply_target_layers(self.records, self._selected_targets())
        except ValueError as exc:
            QMessageBox.critical(self, "Invalid reorder", str(exc))
            return

        ordered_records = sorted(adjusted_records, key=lambda record: record.original_layer)
        original_records = list(self.records)

        destination_path = self.source_path
        if destination_path is None:
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "Save reordered Monaco file",
                str(Path.cwd() / "ReorderedData.txt"),
                "Text files (*.txt);;All files (*.*)",
            )
            if not file_name:
                return
            destination_path = Path(file_name)
        else:
            response = QMessageBox.question(
                self,
                "Overwrite file?",
                f"This will overwrite:\n\n{destination_path}\n\nContinue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if response != QMessageBox.Yes:
                return

        try:
            write_structure_file(destination_path, ordered_records)
            write_structure_file(_og_copy_path(destination_path), original_records)
        except OSError as exc:
            QMessageBox.critical(self, "Could not save file", str(exc))
            return

        self.source_path = destination_path
        self.set_records(ordered_records)
        self.set_status(f"Saved reordered file to {destination_path}.")
