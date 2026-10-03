from fldesktop.include.appserver.ui.widgets import accelgraphicsview, base, button, canvas, checkbox, container, entry, filetree, flayout, hlayout, icon, imageview, label, listview, overlay, radiobutton, root, slider, stretch, tabs, terminal, textedit
from fldesktop.include.appserver.ui.widgets import (
    vlayout
)


widgets = {
    "root": root.RootWidget,
    "widget": base.Widget,
    "vlayout": vlayout.VLayout,
    "hlayout": hlayout.HLayout,
    "flayout": flayout.FLayout,
    "container": container.Container,
    "stretch": stretch.Stretch,
    "button": button.Button,
    "checkbox": checkbox.CheckBox,
    #"filetree": filetree.FileTree,
    "icon": icon.Icon,
    "imageview": imageview.ImageView,
    "label": label.Label,
    #"listview": listview.ListView,
    "radiobutton": radiobutton.RadioButton,
    "slider": slider.Slider,
    "entry": entry.Entry,
    "tabs": tabs.Tabs,
    "terminal": terminal.Terminal,
    "textedit": textedit.TextEdit,
    "canvas": canvas.Canvas,
    "accelgraphicsview": accelgraphicsview.AccelGraphicsView,
    "overlay": overlay.Overlay
}
