from PyQt5 import QtWidgets, uic, QtGui, QtMultimedia, QtCore
from PyQt5.QtWidgets import *
import datetime
import mutagen
import random
from mutagen.mp4 import MP4
import os
import sys


def path_dilation(path):
    return os.path.join(os.path.dirname(__file__), path)


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()

        self.playlist = {}
        self.playlist_path = None
        self.current_uniq_id = None

        uic.loadUi(path_dilation("ui/max.ui"), self)

        self.treeWidget.setColumnWidth(0, 43)
        self.treeWidget.setSortingEnabled(True)
        self.treeWidget.itemDoubleClicked['QTreeWidgetItem*',
                                          'int'].connect(self.tree_item_double_click)
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.generateMenu)

        self.mediaPlayer = QtMultimedia.QMediaPlayer(None)
        self.mediaPlayer.mediaStatusChanged.connect(self.media_status_handler)
        self.mediaPlayer.positionChanged.connect(self.position_changed_handler)
        self.mediaPlayer.durationChanged.connect(self.duration_changed_handler)
        self.positionSlider.sliderMoved.connect(self.slider_moved_handler)
        # self.mediaPlayer.positionChanged.

        self.playPauseButton.clicked.connect(self.playPauseHandler)
        self.nextButton.clicked.connect(self.next)
        self.previousButton.clicked.connect(self.previous)

        # self.progessBar.timeout.connect()

        self.actionOpen_File.triggered.connect(self.Open_File)
        self.actionOpen_Folder.triggered.connect(self.Open_Folder)
        self.actionSave.triggered.connect(self.Save)
        self.actionSave_As.triggered.connect(self.Save_As)
        self.actionExit.triggered.connect(self.Exit)
        self.actionOpen_Playlist.triggered.connect(self.Open_playlist)

        # Where tree item click is a self defined slot function
        self.searchbar.textChanged.connect(self.search)

        self.artlabel.mouseDoubleClickEvent = self.launch_pop

    def launch_pop(self, event):
        print("pic")
        dlg = QDialog(self)
        track = self.playlist[self.current_uniq_id]
        dlg.label = QLabel("Label", dlg)
        dlg.setWindowTitle(dlg.label.setText(track["title"]))
        dlg.setGeometry(0, 0, 600, 600)
        dlg.label.resize(600, 600)
        px = QtGui.QPixmap()
        px.loadFromData(track["album_art"])
        dlg.label.setPixmap(px.scaled(dlg.label.size(
        ), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        window = dlg.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        window.moveCenter(centerPoint)
        dlg.move(window.topLeft())
        dlg.show()
        dlg.exec_()

    def Open_File(self):
        print("open file")
        dialog = QtWidgets.QFileDialog()
        paths, _ = dialog.getOpenFileNames(self, 'Open File', os.getenv(
            'MUSIC_PATH'), 'Sound Files (*.mp3 *.ogg *.wav *.m4a *.aac)')
        for path in paths:
            if path != '':
                self.add_to_plalist(path)

    def Open_Folder(self):
        print("open folder")
        dialog = QtWidgets.QFileDialog()
        path = dialog.getExistingDirectory(
            self, 'Open Directory', os.getenv('MUSIC_PATH'))
        if path != '':
            print("Folder path: " + path)
            self.add_to_plalist(path)

    def Open_playlist(self):
        print("Open playlist")
        dialog = QtWidgets.QFileDialog()
        path, _ = dialog.getOpenFileName(
            self, 'Open Playlist', '', 'PLAYLIST Files (*.m3u *.m3u8)')

        for l in open(path).readlines():
            l = l.strip()
            if l and not l.startswith("#"):
                if not os.path.isabs(l):
                    l = os.path.join(os.path.dirname(path), l)
                self.add_to_plalist(l)

    def reserve_uniq_slot(self):
        available = None
        while not available or available in self.playlist:
            available = ''.join(random.choice('0123456789abcdef')
                                for i in range(64))
        self.playlist[available] = {}
        return (available, self.playlist[available])

    def get_uniq_index(self, uniq_id=None):
        uniq_id = uniq_id or self.current_uniq_id
        index = -1
        if uniq_id:
            index = self.treeWidget.indexFromItem(
                self.playlist[uniq_id]["item"]).row()
        return index

    def uniq_from_index(self, index):
        return self.treeWidget.topLevelItem(index).uniq_id

    def getAllTrackItems(self):
        return [
            self.treeWidget.topLevelItem(index)
            for index in range(0, self.treeWidget.topLevelItemCount())
        ]

    def get_status_label(self, item):
        return self.treeWidget.itemWidget(item, 0)

    def add_to_plalist(self, path):
        if os.path.isdir(path):
            for file in sorted(os.listdir(path)):
                self.add_to_plalist(os.path.join(path, file))
            return

        if os.path.splitext(path)[1] not in [".mp3", ".ogg", ".wav", ".m4a", ".aac"]:
            return

        print("File path: " + path)
        try:
            # gets song from path and gets metadata
            metadata = self.metadata(path)
        except:
            return
        content = QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(path))

        (uniq_id, track) = self.reserve_uniq_slot()

        track.update({
            **metadata,
            "path": path,
            "media": content,
            "item": QtWidgets.QTreeWidgetItem(self.treeWidget)
        })
        track["item"].uniq_id = uniq_id

        # this inputs the required slots in place on the tree widget
        statuslabel = QtWidgets.QLabel()
        statuslabel.setAlignment(QtCore.Qt.AlignCenter)
        self.treeWidget.setItemWidget(track["item"], 0, statuslabel)

        track["item"].setText(1, f'{(track["trackn"].split("/")[0]):0>2}')
        track["item"].setText(2, track["title"])
        track["item"].setText(3, track["album"])
        track["item"].setText(4, track["artist"])
        track["item"].setText(5, self.humanify_seconds(track["duration"]))
        try:
            track["item"].setText(
                6, str(datetime.date.fromisoformat(track["date"]).year))
        except:
            pass

        # gets data from mtigen and prints all on consol
        # Audio = mutagen.File(content)
        # Audio.pprint() gets all data from mutagen and prints on consol
        # print ("data of selected musuc")

    def saveHandler(self, path):
        if path != '':
            file, ext = os.path.splitext(path)
            path = file + (ext or ".m3u")
            print("path : " + path)
            with open(path, 'w') as f:
                for trackItem in self.getAllTrackItems():
                    track = self.playlist[trackItem.uniq_id]
                    # f.write("# " + track["title"] + "\n")
                    f.write(track["path"] + "\n")
            self.playlist_path = path

    def Save(self):
        print("save")
        # impliments save as and also saves the changes to the files
        if self.playlist_path:
            self.saveHandler(self.playlist_path)
        else:
            self.Save_As()

    def Save_As(self):
        print("save as")
        # saves the files in list view so i can import list whenever i want
        dialog = QtWidgets.QFileDialog()
        path, _ = dialog.getSaveFileName(
            self, "Save file", "", "Playlist File(*.m3u *.m3u8)")
        self.saveHandler(path)

    def Exit(self):
        print("Exit")
        self.close()

    def playPauseHandler(self):
        # print("play/pause")
        if self.current_uniq_id != None:
            if self.mediaPlayer.state() == QtMultimedia.QMediaPlayer.PlayingState:
                self.mediaPlayer.pause()
                self.playPauseButton.setText("Play")
                self.playingStatus.setText("Paused")
                # playPauseButton.setText("Pause")
                icon = QtGui.QIcon.fromTheme("media-playback-pause")
                self.get_status_label(self.playlist[self.current_uniq_id]["item"]).setPixmap(
                    icon.pixmap(icon.actualSize(QtCore.QSize(16, 16))))
                print("pause")
            else:
                self.mediaPlayer.play()
                self.playPauseButton.setText("Pause")
                self.playingStatus.setText("Now Playing")
                # playPauseButton.setText("Play")
                icon = QtGui.QIcon.fromTheme("media-playback-start")
                self.get_status_label(self.playlist[self.current_uniq_id]["item"]).setPixmap(
                    icon.pixmap(icon.actualSize(QtCore.QSize(16, 16))))
                print("play")

    def media_status_handler(self, status):
        if status == QtMultimedia.QMediaPlayer.EndOfMedia:
            print("song has finished playing")
            self.next(self.repeatButton.isChecked())

    def indicate_now_playing(self, track, brush=None):
        if brush:
            icon = QtGui.QIcon.fromTheme("media-playback-start")
            self.get_status_label(track["item"]).setPixmap(icon.pixmap(
                icon.actualSize(QtCore.QSize(16, 16))))
        else:
            self.get_status_label(track["item"]).clear()
        for index in range(7):
            if not brush:
                track["item"].setData(index, QtCore.Qt.BackgroundRole, None)
            else:
                track["item"].setBackground(index, brush)

    def next(self, repeat=False):
        if self.current_uniq_id != None and len(self.playlist) > 0:
            self.indicate_now_playing(self.playlist[self.current_uniq_id])
            current_index = self.get_uniq_index(self.current_uniq_id)
            self.current_uniq_id = self.uniq_from_index((current_index +
                                                         (not repeat)) % len(self.playlist))
            self.album_content_handler()
            self.album_art_handler()
            self.mediaPlayer.play()

    def previous(self):
        if self.current_uniq_id != None and len(self.playlist) > 0:
            self.indicate_now_playing(self.playlist[self.current_uniq_id])
            current_index = self.get_uniq_index(self.current_uniq_id)
            self.current_uniq_id = self.uniq_from_index((current_index +
                                                         len(self.playlist) - 1) % len(self.playlist))
            self.album_content_handler()
            self.album_art_handler()
            self.mediaPlayer.play()

    def tree_item_double_click(self, item):
        print("tree item clicked")
        if self.current_uniq_id != None:
            self.indicate_now_playing(self.playlist[self.current_uniq_id])
        self.current_uniq_id = item.uniq_id
        self.album_content_handler()
        self.playPauseButton.click()
        self.album_art_handler()

    def generateMenu(self, pos):
        print(pos)
        # Get index
        for i in self.treeWidget.selectionModel().selection().indexes():
            # If the selected row index is less than 1, the context menu will pop up
            rownum = i.row()
        if rownum >= 0:
            menu = QMenu()
            item1 = menu.addAction("delete")
        # Make the menu display in the normal position
        screenPos = self.treeWidget.mapToGlobal(pos)
        # Click on a menu item to return, making it blocked
        action = menu.exec(screenPos)
        if action == item1:
            print('Deleted')
            self.del_item()
        else:
            return

    def del_item(self):
        root = self.treeWidget.invisibleRootItem()
        for item in self.treeWidget.selectedItems():
            if item.uniq_id == self.current_uniq_id:
                self.next()
            (item.parent() or root).removeChild(item)
            del self.playlist[item.uniq_id]

    def album_art_handler(self):
        track = self.playlist[self.current_uniq_id]  # links current
        if track["album_art"]:
            px = QtGui.QPixmap()
            px.loadFromData(track["album_art"])
            self.artlabel.setPixmap(px.scaled(self.artlabel.size(
            ), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

    def album_content_handler(self):
        track = self.playlist[self.current_uniq_id]  # links current
        self.indicate_now_playing(track, QtGui.QBrush(QtGui.QColor("#168479")))
        content = track["media"]
        self.mediaPlayer.setMedia(content)
        self.nameStatus.setText(track["title"])
        self.albumStatus.setText(track["album"])
        self.artistStatus.setText(track["artist"])

    def humanify_seconds(self, seconds):
        parts = []
        for (index, part) in enumerate(reversed(self.convert(seconds))):
            part = int(part)
            if index < 2 or part > 0:
                parts.append(f"{part:02}")

        return ":".join(reversed(parts))

    def position_changed_handler(self, position):
        # print("position_changed_handler:", position)
        seconds = position / 1000
        self.positionTimer.setText(self.humanify_seconds(seconds))
        try:
            self.positionSlider.setValue(
                int(position / self.mediaPlayer.duration() * 100))
        except:
            pass

    def duration_changed_handler(self, duration):
        self.fixedTimer.setText(self.humanify_seconds(
            self.mediaPlayer.duration() / 1000))

    def slider_moved_handler(self, value):
        self.mediaPlayer.setPosition(
            int((value / 100) * float(self.mediaPlayer.duration())))

    def statusView(self, state):
        if self.mediaPlaer.state() == QtMultimedia.QMediaPlayer.PlayingState:
            self.playPauseButton.setText(str("Play"))
            self.playingStatus.setText("Now Playing:")
        else:
            self.playPauseButton.setText(str("Pause"))
            self.playingStatus.setText("Paused:")

    def convert(self, seconds):
        hours = seconds // 3600
        seconds %= 3600
        mins = seconds // 60
        seconds %= 60
        return hours, mins, seconds

    def metadata(self, path):
        audio = mutagen.File(path, easy=True)

        return {
            "trackn": audio.get("tracknumber", ["<no data>"])[0],
            "title": audio.get("title", ["<no data>"])[0],
            "album": audio.get("album", ["<no data>"])[0],
            "artist": audio.get("artist", ["<no data>"])[0],
            "date": audio.get("date", ["<no data>"])[0],
            "album_art": MP4(path).get("covr", [None])[0],
            "duration": int(audio.info.length)
        }

    def search(self, query):
        print("search", query)

        query = query.lower().split(" ")
        query = [*filter(bool, query)]
        for trackItem in self.getAllTrackItems():
            track = self.playlist[trackItem.uniq_id]
            base = [track["title"], track["album"],
                    track["artist"], track["date"]]
            base = " ".join(base).lower()
            base = base.split(" ")
            base = [*filter(bool, base)]
            print(query, base, all(word in base for word in query))
            if all(any(word in entry for entry in base) for word in query):
                track["item"].setHidden(False)
            else:
                track["item"].setHidden(True)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = Ui()
    main_window.show()
    app.exec_()
