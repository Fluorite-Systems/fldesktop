from PySide6.QtWidgets import QPushButton, QSizePolicy


class KeyboardIndicator:
    def __init__(self, comm):
        self.comm = comm

        print(self.comm.request("inputmgr", "get_current_locale"))

        self.btn = QPushButton(
            self.comm.request("inputmgr", "get_current_locale")
        )
        self.btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn.clicked.connect(self.cycle)
        self.btn.setObjectName("traybtn")

    def cycle(self):

        l = self.comm.request("inputmgr", "cycle_locale")
        self.btn.setText(l)
