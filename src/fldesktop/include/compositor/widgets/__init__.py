from fldesktop.include.compositor.widgets import (
    button, canvas, checkbox, container, entry, filetree, flayout,
    hlayout, icon, imageview, label, listview, radiobutton, root,
    slider, stretch, tabs, terminal, textedit, vlayout,
    accelgraphicsview
)


widgets = {
    "root": root.RootWidget,
    "vlayout": vlayout.VLayout,
    "hlayout": hlayout.HLayout,
    "flayout": flayout.FLayout,
    "container": container.Container,
    "stretch": stretch.Stretch,
    "button": button.Button,
    "checkbox": checkbox.CheckBox,
    "filetree": filetree.FileTree,
    "icon": icon.Icon,
    "imageview": imageview.ImageView,
    "label": label.Label,
    "listview": listview.ListView,
    "radiobutton": radiobutton.RadioButton,
    "slider": slider.Slider,
    "entry": entry.Entry,
    "tabs": tabs.Tabs,
    "terminal": terminal.Terminal,
    "textedit": textedit.TextEdit,
    "canvas": canvas.Canvas,
    "accelgraphicsview": accelgraphicsview.AccelGraphicsView
}
