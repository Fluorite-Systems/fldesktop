from PySide6.QtWidgets import QApplication


class QApp:
    def __init__(self, _):
        self.app = QApplication()

    def srv_cleanup(self):
        QApplication.instance().exit()

    def exec(self):
        QApplication.instance().exec()
        

class PostInit:
    def __init__(self, comm):
        self.comm = comm

        self.comm.send("lockscreen", "show")
        self.comm.send("fade_effect", "fadein")

    def srv_cleanup(self):
        self.comm.send("fade_effect", "fadeout")

