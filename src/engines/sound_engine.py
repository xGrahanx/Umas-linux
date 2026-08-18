import datetime

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QMediaDevices, QSoundEffect
from PySide6.QtWidgets import QWidget

from ..resources import ResourceRegistry
from ..settings import Preferences
from ..states import State


class SoundEngine:
    def __init__(self, window: QWidget):
        self.player = QSoundEffect(window)
        self.player.setVolume(Preferences.Volume)

        # Configure Audio Output Device
        target_device = Preferences.AudioDevice
        if target_device and target_device != "Default":
            for device in QMediaDevices.audioOutputs():
                if device.description() == target_device:
                    self.player.setAudioDevice(device)
                    print(f"Audio Output set to: {target_device}")
                    break

    def play(self, state: State, delay_seconds=0):
        # get sound data if exists
        try:
            data = ResourceRegistry.get_sound(state)
        except ValueError:
            return

        # check cooldown
        if delay_seconds > 0:
            delay_duration = datetime.timedelta(seconds=delay_seconds)
            if datetime.datetime.now() - data.last_played < delay_duration:
                return
            data.last_played = datetime.datetime.now()

        # play sound
        self.player.setSource(QUrl.fromLocalFile(data.sound_path))
        self.player.play()
