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
        comm.send("lockscreen", "show")
        comm.send("fade_effect", "fadein") 

