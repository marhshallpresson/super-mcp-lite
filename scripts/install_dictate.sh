#!/bin/bash
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

echo "Installing Dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-pyaudio git xdotool libportaudio2
pip3 install --break-system-packages vosk

echo "Installing Nerd Dictation..."
cd ~/Downloads
if [ ! -d "nerd-dictation" ]; then
    git clone https://github.com/ideasman42/nerd-dictation.git
fi
cd nerd-dictation
if [ ! -d "model" ]; then
    wget -q -O vosk-model.zip https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    unzip -q vosk-model.zip
    mv vosk-model-small-en-us-0.15 model
fi

echo "Setting up Hotkey..."
chmod +x /home/mobot/toggle_dictation.sh
gsettings set org.cinnamon.desktop.keybindings custom-list "['custom0']"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom0/ name 'Toggle Voice Dictation'
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom0/ command '/home/mobot/toggle_dictation.sh'
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom0/ binding 'Alt_R'

echo "Done!"
