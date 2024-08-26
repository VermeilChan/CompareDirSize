import os
import sys
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QFileDialog, QPushButton, QTextEdit, QSizePolicy

class DirectoryComparerWorker(QThread):
    update_results = Signal(str)
    update_status = Signal(str)

    def __init__(self, old_dir, new_dir):
        super().__init__()
        self.old_dir = old_dir
        self.new_dir = new_dir

    def run(self):
        self.update_status.emit("Comparing directories...")
        result = self.compare_directories()
        self.update_results.emit(result)

    def human_readable_size(self, size_bytes):
        if size_bytes < 0:
            return f"-{self.human_readable_size(-size_bytes)}"
        for unit in ['bytes', 'kB', 'MB', 'GB']:
            if size_bytes < 1000:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1000

    def list_files(self, directory):
        file_info = {}
        total_size = 0
        for root, _, files in os.walk(directory):
            for file in files:
                path = os.path.join(root, file)
                relative_path = os.path.relpath(path, directory)
                size = os.path.getsize(path)
                file_info[relative_path] = size
                total_size += size
        return file_info, total_size

    def compare_directories(self):
        old_files, old_total_size = self.list_files(self.old_dir)
        new_files, new_total_size = self.list_files(self.new_dir)

        missing_files = old_files.keys() - new_files.keys()
        added_files = new_files.keys() - old_files.keys()
        common_files = old_files.keys() & new_files.keys()

        results = [f"<b>Old Directory Size:</b> {self.human_readable_size(old_total_size)}",
                    f"<b>New Directory Size:</b> {self.human_readable_size(new_total_size)}",
                    f"<b>Size Difference:</b> {self.human_readable_size(new_total_size - old_total_size)}<br>"]

        if missing_files:
            results.append("<b>Missing files:</b>")
            results.extend(f"<span style='color: #FF6F61;'>{file}</span>" for file in sorted(missing_files))

        if added_files:
            results.append("<b>Added files:</b>")
            results.extend(f"<span style='color: #61FF73;'>{file}</span>" for file in sorted(added_files))

        for file in common_files:
            if old_files[file] != new_files[file]:
                results.append(f"<b>Modified:</b> <span style='color: #FFB86C;'>{file}</span> "
                                f"(Old: {self.human_readable_size(old_files[file])}, New: {self.human_readable_size(new_files[file])})")

        if not missing_files and not added_files and not any(old_files[file] != new_files[file] for file in common_files):
            results.append("<span style='color: #8BE9FD;'>No differences found between the directories.</span>")

        return "<br>".join(results)

class DirectoryComparer(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Directory Size Comparer")
        self.setGeometry(100, 100, 600, 400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.old_dir_label = QLabel("Old Directory: Not selected")
        self.new_dir_label = QLabel("New Directory: Not selected")

        layout.addWidget(self.old_dir_label)
        layout.addWidget(self.new_dir_label)

        self.compare_button = QPushButton("Compare")
        self.compare_button.clicked.connect(self.select_directories)
        layout.addWidget(self.compare_button)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

    def select_directories(self):
        old_dir = QFileDialog.getExistingDirectory(self, "Select Old Directory")
        if not old_dir:
            return

        new_dir = QFileDialog.getExistingDirectory(self, "Select New Directory")
        if not new_dir:
            return

        self.old_dir_label.setText(f"Old Directory: {os.path.basename(old_dir)}")
        self.new_dir_label.setText(f"New Directory: {os.path.basename(new_dir)}")

        self.result_text.clear()
        self.worker = DirectoryComparerWorker(old_dir, new_dir)
        self.worker.update_results.connect(self.result_text.setHtml)
        self.worker.update_status.connect(self.result_text.setHtml)
        self.worker.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    comparer = DirectoryComparer()
    comparer.show()
    sys.exit(app.exec())
