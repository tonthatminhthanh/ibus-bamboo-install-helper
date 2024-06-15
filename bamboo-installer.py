import sys, os, subprocess
from PyQt6.QtCore import *
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
)

class Worker(QThread):
    output_signal = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command
    
    def run(self):
        user_name = os.getlogin()
        process = subprocess.Popen(self.command, shell=True, user=user_name,stdout=subprocess.PIPE, text=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self.output_signal.emit(output.strip())
        rc = process.poll()
        self.output_signal.emit(f'Hoàn thành cài đặt với return code {rc}')


class BambooInstallerApp(QWidget):
    def what_distro(self, str):
        if "debian" in str:
            return "debian"
        elif "arch" in str:
            return "arch"
        else:
            return "unsupported"

    def check_distro(self):
        with open('/etc/os-release','r') as file:
            os_release_info = file.readlines()

        for line in os_release_info:
            if line.startswith('ID_LIKE'):
                id_like = line.split('=')[1].strip().strip('=')
                return self.what_distro(id_like)
            elif line.startswith('ID'):
                id = line.split('=')[1].strip().strip('=')
                if self.what_distro(id) != "debian" and self.what_distro(id) != "arch":
                    continue
                else:
                    return self.what_distro(id)
        return "err"

    def check_bamboo_status(self):
        if os.path.exists('/usr/lib/ibus-bamboo') or os.path.exists('/usr/share/ibus-bamboo'):
            status = "Đã được cài đặt."
        else:
            status = "Chưa được cài đặt."
        return status

    def get_os_info_label(self):
        os_id = self.check_distro()

        match os_id:
            case "err":
                os_label = QLabel('<b style="color: red">Không tìm được file /etc/os-release </b>')
            case "unsupported":
                os_label = QLabel('<b style="color: yellow">Bản phân phối không được hỗ trợ.</b>')
            case _:
                os_label = QLabel("Bản phân phối Linux: " + os_id)
        return os_label

    def setStatusLabel(self):
        self.status_label.setText("Trạng thái của ibus-bamboo: " + self.check_bamboo_status())

    def initGUI(self):
        self.setWindowTitle('ibus-bamboo Setup')

        vLayout = QVBoxLayout()
        hLayout = QHBoxLayout()
        self.os_id = self.check_distro()
        self.os_info = self.get_os_info_label()
        self.status_label = QLabel("Trạng thái của ibus-bamboo: " + self.check_bamboo_status())
        if self.os_id == "debian" or self.os_id == "arch":
            self.install_button = QPushButton(text="Cài đặt")
            self.install_button.pressed.connect(lambda: self.run_command(self.os_id))
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        if self.os_id == "debian" or self.os_id == "arch":
            hLayout.addWidget(self.install_button)
        vLayout.addWidget(self.os_info)
        vLayout.addWidget(self.status_label)
        if self.os_id == "debian" or self.os_id == "arch":
            vLayout.addLayout(hLayout)
        vLayout.addWidget(self.output_area)
        vLayout.addWidget(QLabel("Phần mềm hỗ trợ cài đặt ibus-bamboo được phát triển bởi Tôn Thất Minh Thành, ibus-bamboo được phát triển bởi luongthanhlam."))
        self.setLayout(vLayout)

    def execute_command(self, command):
        self.install_button.setDisabled(True)
        self.output_area.clear()
        self.worker = Worker(command)
        self.worker.output_signal.connect(self.update_output)
        self.worker.finished.connect(lambda: self.activate_button())
        self.worker.start()

    def activate_button(self):
        self.install_button.setDisabled(False)
        self.setStatusLabel()

    def run_command(self, id):
        strA = "'BambooUs'"
        strB = "'Bamboo'"
        strC = "'xkb'"
        strD = "'us'"
        strE = "'ibus'"
        
        set_default_command = 'env DCONF_PROFILE=ibus dconf write /desktop/ibus/general/preload-engines "[' + strA + ', ' + strB + ']" && gsettings set org.gnome.desktop.input-sources sources "[(' + strC + ', ' + strD + '), (' + strE + ', ' + strB + ')]"'
        if id == "debian":
            command = "sudo add-apt-repository -y ppa:bamboo-engine/ibus-bamboo && sudo apt-get update && sudo apt-get install -y ibus ibus-bamboo --install-recommends && " + set_default_command + " && ibus restart"
            self.execute_command(command)
        elif id == "arch":
            command = "sudo pacman -S git base-devel && git clone https://aur.archlinux.org/ibus-bamboo.git && cd ibus-bamboo && makepkg -si && cd .. && rm -rf ibus-bamboo"
            self.execute_command(command)
    
    def update_output(self, text):
        self.output_area.append(text)

    def __init__(self):
        super().__init__()
        self.initGUI()

def main():
    app = QApplication(sys.argv)
    window = BambooInstallerApp()
    window.show()
    window.setFixedSize(window.size())
    sys.exit(app.exec())

if __name__ == "__main__":
    main()