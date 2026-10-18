from fldesktop.include.uikit.widgets import (
    root, base, vlayout, hlayout, flayout, container, stretch,
    button, checkbox, radiobutton, slider,
    entry, textedit, label,
    icon, imageview,
    tabs, canvas, overlay, decoration,
    terminal, accelgraphicsview
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
    "decoration": decoration.Decoration,
    "accelgraphicsview": accelgraphicsview.AccelGraphicsView,
    "overlay": overlay.Overlay
}
