# Python Soundboard

## Requirements

- python3
- install python packages :
```sh
pip3 install -r requirements.txt
```
- Virtual audio cable (VB audio or anykind of audio cable)
  - For the soundboard to work we need an output device which is linked to an input device. Virtual audio cable provides just that

## Sound location

Sounds must be as `.wav` format and placed inside the sounds folder

## Keybinds setup

`set_keybindings.py` is used to setup keybinds

- run the script
- follow the instructions for each of the sound you want to bind
- CTRL + C to exit

## Audio device setup

- run `display_audio_devices.py` script to see the list of your audio devices and their id
- edit the device id variable of `soundboard.py` :
  - MIC_DEVICE_ID should  be set to the device id of your microphone
  - OUTPUT_DEVICE_ID should be set to the device id of the input of the audiocable
  - MONITOR_DEVICE_ID should be set to your headphones or speaker

## Runing the soundboard

- simply run `soundboard.py`, the keybinds should work even if the window is not selected