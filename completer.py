import json
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtCore import QObject, QTimer, QEvent, QPoint, QMetaObject
from PyQt5.QtWidgets import QTreeWidget, QLineEdit, QFrame, QTreeWidgetItem
from PyQt5.QtNetwork import QNetworkAccessManager,QNetworkRequest, QNetworkReply
from PyQt5.QtGui import QPalette
from constants import WIDTH_WIDGET_RIGHT


class SuggestCompletion(QObject):

    def __init__(self, parent):
        QObject.__init__(self, parent)
        self._parent = parent

        self._editor = parent

        self._popup = QTreeWidget();
        self._popup.setWindowFlags(Qt.Popup)
        self._popup.setFocusProxy(self._parent)
        self._popup.setMouseTracking(True);
        self._popup.setColumnCount(1);
        self._popup.setUniformRowHeights(True);
        self._popup.setRootIsDecorated(False);
        self._popup.setEditTriggers(QTreeWidget.NoEditTriggers);
        self._popup.setSelectionBehavior(QTreeWidget.SelectRows);
        self._popup.setFrameStyle(QFrame.Box | QFrame.Plain);
        self._popup.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);
        self._popup.header().hide();

        self._timer = None
        self._timer = QTimer(self);
        self._timer.setSingleShot(True);
        self._timer.setInterval(500);

        self._network_manager = QNetworkAccessManager(self)

        self._popup.installEventFilter(self);
        self._popup.itemClicked.connect(self.done_completion)
        self._timer.timeout.connect(self.auto_suggest)
        self._editor.textEdited.connect(self._timer.start)
        self._network_manager.finished.connect(self.handle_network_data)

    def eventFilter(self, object, event):
        if object != self._popup:
            return False

        if event.type() == QEvent.MouseButtonPress:
            self._popup.hide()
            self._editor.setFocus()
            return True

        if event.type() == QEvent.KeyPress:
            consumed = False
            key = event.key()
            if key in [Qt.Key_Enter, Qt.Key_Return]:
                self.done_completion()
                consumed = True
            elif key == Qt.Key_Escape:
                self._editor.setFocus()
                self._popup.hide()
                consumed = True
            elif key in [Qt.Key_Up, Qt.Key_Down, Qt.Key_Home, Qt.Key_End, Qt.Key_PageUp, Qt.Key_PageDown]:
                pass
            else:
                self._editor.setFocus()
                self._editor.event(event)
                self._popup.hide()
            return consumed

        return False

    def show_completion(self, choices):
        if not choices:
            return

        pallete = self._editor.palette()
        color = pallete.color(QPalette.Disabled, QPalette.WindowText)

        self._popup.setUpdatesEnabled(False)
        self._popup.clear()

        for choice in choices:
            item = QTreeWidgetItem(self._popup)
            item.setText(0, choice)

        self._popup.setCurrentItem(self._popup.topLevelItem(0))
        self._popup.resizeColumnToContents(0)
        self._popup.setUpdatesEnabled(True)

        self._popup.move(self._editor.mapToGlobal(QPoint(0, self._editor.height())))
        self._popup.setFocus()
        self._popup.show()

    def done_completion(self):
        self._timer.stop()
        self._popup.hide()
        self._editor.setFocus()

        item = self._popup.currentItem()

        if item:
            self._editor.setText(item.text(0))
            QMetaObject.invokeMethod(self._editor, 'returnPressed')

    def auto_suggest(self):
        text = self._editor.text()

        req = "https://commons.wikimedia.org/w/api.php?action=query&list=prefixsearch&format=json"
        req += "&pssearch=" + "Category:" + text

        url = QUrl(req)
        self._network_manager.get(QNetworkRequest(url))

    def prevent_suggest(self):
        self._timer.stop()

    def handle_network_data(self, network_reply):
        choices = []
        if network_reply.error() == QNetworkReply.NoError:
            data = json.loads(network_reply.readAll().data())

            for location in data['query']['prefixsearch']:
                choice = location['title']
                choices.append(choice.replace("Category:", ""))
            self.show_completion(choices)
        network_reply.deleteLater();


class SearchBox(QLineEdit):
    def __init__(self, parent=None):
        super(SearchBox, self).__init__(parent)
        self._completer = SuggestCompletion(self);
        self.setFixedWidth(WIDTH_WIDGET_RIGHT / 2)
        self.setStyleSheet("background-color: lightgray; color: black ")
        self.setClearButtonEnabled(True)

''' 
    https://stackoverflow.com/questions/55027186/pyqt5-autocomplete-qlineedit-google-places-autocomplete 
    https://github.com/ismailsunni/scripts/blob/master/autocomplete_from_url.py
'''



