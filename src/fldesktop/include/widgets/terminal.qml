import QtQuick 2.9
import QtQuick.Controls 2.2
import QMLTermWidget 2.0

QMLTermWidget {
    id: terminal
    anchors.fill: parent
    focus: true
    
    colorScheme: "WhiteOnBlack"
    font.pixelSize: 15
    font.family: "JetBrainsMono Nerd Font"
    font.weight: Font.medium

    session: QMLTermSession {
        id: session
        initialWorkingDirectory: "$HOME"
        onFinished: Qt.quit()
    }

    Component.onCompleted: session.startShellProgram()
}
