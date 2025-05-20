import pyaudio
import wave
import numpy as np
import keyboard
import threading
import os 
from inputs import get_gamepad
from pynput import keyboard, mouse
from typing import Callable, Dict, List
from set_keybindings import read_bindings
import threading

# Configuration
MIC_DEVICE_ID = 1
OUTPUT_DEVICE_ID = 5
MONITOR_DEVICE_ID = 4
CHUNK = 16
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
SOUND_DIR = "sounds"
KEYBIND_FILE = "keybinds.txt"


def open_stream(p, device_id, channels, rate, input=True, output=False):
    return p.open(
        format=FORMAT,
        channels=channels,
        rate=rate,
        input=input,
        output=output,
        input_device_index=device_id if input else None,
        output_device_index=device_id if output else None,
        frames_per_buffer=CHUNK,
    )


class InputHandler:
    def __init__(self):
        # Dictionary to store keybindings
        self.keybindings: Dict[str, Callable] = {}
        self.running = True

        # Start input threads
        threading.Thread(target=self._keyboard_listener, daemon=True).start()
        #threading.Thread(target=self._mouse_listener, daemon=True).start()
        threading.Thread(target=self._controller_listener, daemon=True).start()

    def bind_key(self, key: str, callback: Callable):
        """Bind a key or controller button to a callback."""
        self.keybindings[key] = callback

    def _keyboard_listener(self):
        def on_press(key):
            try:
                key_name = key.char.upper() if key.char else key.name.upper()
                if key_name in self.keybindings:
                    self.keybindings[key_name]()
            except AttributeError:
                pass

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    def _mouse_listener(self):
        def on_click(x, y, button, pressed):
            if pressed:
                button_name = f"MOUSE_{button.name.upper()}"
                if button_name in self.keybindings:
                    self.keybindings[button_name]()

        with mouse.Listener(on_click=on_click) as listener:
            listener.join()

    def _controller_listener(self):
        while self.running:
            events = get_gamepad()
            for event in events:
                if event.ev_type == "Key" and event.state == 1:  # Button pressed
                    button = event.code
                    if button in self.keybindings:
                        self.keybindings[button]()

    def stop(self):
        self.running = False



class AudioMixer:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.mic_stream = open_stream(self.p, MIC_DEVICE_ID, CHANNELS, RATE, input=True, output=False)
        self.output_stream = open_stream(self.p, OUTPUT_DEVICE_ID, CHANNELS, RATE, input=False, output=True)
        self.monitor_stream = open_stream(self.p, MONITOR_DEVICE_ID, CHANNELS, RATE, input=False, output=True)

        self.play_wav = False
        self.wav_stream = None
        self.sound_file = None

    def start(self):
        while True:
                # Read microphone data
                mic_data = self.mic_stream.read(CHUNK, exception_on_overflow=False)
                mic_array = np.frombuffer(mic_data, dtype=np.int16)
                if self.play_wav:
                    if not self.wav_stream:
                        self.wav_stream = wave.open(self.sound_file, 'rb')
                    wav_data = self.wav_stream.readframes(CHUNK)
                    if not wav_data:
                        mixed_array = mic_array.tobytes()                  
                        self.play_wav = False
                        self.wav_stream.close()
                        self.wav_stream = None
                    else:
                        wav_array = np.frombuffer(wav_data, dtype=np.int16)
                        self.monitor_stream.write(wav_array.tobytes())

                        min_len = min(len(mic_array), len(wav_array))
                        mic_array = mic_array[:min_len]
                        wav_array = wav_array[:min_len]
                        # Superpose audio
                        mixed_array = mic_array + wav_array
                        mixed_array = np.clip(mixed_array, -32768, 32767).astype(np.int16).tobytes()                    
                else: 
                    mixed_array = mic_array.tobytes()                  
                self.output_stream.write(mixed_array)



    def stop(self):
        self.mic_stream.stop_stream()
        self.mic_stream.close()
        self.output_stream.stop_stream()
        self.output_stream.close()
        self.monitor_stream.stop_stream()
        self.monitor_stream.close()
        self.p.terminate()
        print("Audio mixer stopped.")

    def trigger_wav(self, sound_file: str):
        self.wav_stream = None
        self.play_wav = True
        self.sound_file = sound_file

def main():
    keybinds = read_bindings()
    mixer = AudioMixer()
    input_handler = InputHandler()
    for key, sound_file in keybinds.items():
        def callback():
            mixer.trigger_wav(sound_file)
        input_handler.bind_key(key, callback)
        
    try:
        mixer.start()
    except KeyboardInterrupt:
        mixer.stop()
        input_handler.stop()
if __name__ == "__main__":
    main()