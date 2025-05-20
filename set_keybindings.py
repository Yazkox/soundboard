import keyboard
import threading
import os
from inputs import get_gamepad
from pynput import keyboard, mouse
from typing import Callable, Dict, List
import traceback
import threading
import glob

SOUND_DIR = "sounds"
KEYBIND_FILE = "keybinds.txt"


class InputHandler:
    def __init__(self):
        self.running = True
        self.listening_for_input = False

        # Start input threads
        threading.Thread(target=self._keyboard_listener, daemon=True).start()
        threading.Thread(target=self._mouse_listener, daemon=True).start()
        threading.Thread(target=self._controller_listener, daemon=True).start()

        self.last_input = None

    def listen_for_next_input(self):
        """Listen for the next input event and call the callback with the input identifier."""
        self.listening_for_input = True

    def _handle_input_event(self, key: str):
        if self.listening_for_input:
            self.listening_for_input = False
            self.last_input = key

    def _keyboard_listener(self):
        def on_press(key):
            try:
                key_name = key.char.upper() if key.char else key.name.upper()
                self._handle_input_event(key_name)
            except AttributeError:
                pass

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    def _mouse_listener(self):
        def on_click(x, y, button, pressed):
            if pressed:
                button_name = f"MOUSE_{button.name.upper()}"
                self._handle_input_event(button_name)

        with mouse.Listener(on_click=on_click) as listener:
            listener.join()

    def _controller_listener(self):
        while self.running:
            events = get_gamepad()
            for event in events:
                if event.ev_type == "Key" and event.state == 1:  # Button pressed
                    button = event.code
                    self._handle_input_event(button)

    def stop(self):
        self.running = False


def read_bindings() -> Dict[str, str]:
    keybinds = {}
    with open(KEYBIND_FILE, "r") as f:
        for line in f:
            key, filename = line.split(";")
            keybinds[key] = filename[:-1]
    return keybinds


def write_keybinds(keybinds: Dict[str, str]):
    with open(KEYBIND_FILE, "w") as f:
        for key, filename in keybinds.items():
            f.write(f"{key};{filename}\n")


def reverse_dict(input: Dict[str, str]) -> Dict[str, str]:
    new_dict = {}
    for key, value in input.items():
        new_dict[value] = key
    return new_dict

def remove_duplicate(input: Dict[str, str], filename: str):
    key_to_pop = []
    for key, value in input.items():
        if value == filename:
            key_to_pop.append(key)
        
    for key in key_to_pop:
        input.pop(key)

def print_files(wav_files: List[str], keybinds: Dict[str, str]):
    reversed_binds = reverse_dict(keybinds)
    for k, filename in enumerate(wav_files):
        if filename in reversed_binds:
            print(f"{k:<3} - {os.path.basename(filename):<20} - {reversed_binds[filename]}")
        else:
            print(f"{k:<3} - {os.path.basename(filename):<20}")


def main():
    listener = InputHandler()
    keybinds = read_bindings()
    wav_files = glob.glob(os.path.join(SOUND_DIR, "*.wav"))

    try:
        while True:
            print_files(wav_files, keybinds)
            sound_number = int(input("Choose the sound to which you want to add a keybind by typing its number : "))
            print("Press your key")
            listener.listen_for_next_input()
            while listener.listening_for_input:
                pass
            remove_duplicate(keybinds, wav_files[sound_number])
            keybinds[listener.last_input] = wav_files[sound_number]
            print("Added keybind !")
    except KeyboardInterrupt:
        write_keybinds(keybinds)
        print("Exited")


if __name__ == "__main__":
    main()
