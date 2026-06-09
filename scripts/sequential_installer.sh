#!/bin/bash
export DEBIAN_FRONTEND=noninteractive

echo "Clearing locks..."
sudo killall -9 apt apt-get dpkg flatpak 2>/dev/null
sudo rm -f /var/lib/apt/lists/lock /var/lib/dpkg/lock /var/lib/dpkg/lock-frontend
sudo rm -rf /var/lib/dpkg/updates/*

echo "Installing Native Packages (Cheese Camera, Node, Git, Distrobox)..."
sudo apt-get install -y nodejs npm distrobox podman python3-pip python3-pyaudio git xdotool libportaudio2 cheese

echo "Installing Gemini CLI..."
sudo npm install -g @google/gemini-cli

echo "Starting Kali Sandbox..."
distrobox create --image docker.io/kalilinux/kali-rolling --name kali-linux -Y

echo "Setting up Voice Dictation..."
pip3 install --break-system-packages vosk
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
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus
gsettings set org.cinnamon.desktop.keybindings custom-list "['custom0']"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom0/ name 'Toggle Voice Dictation'
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom0/ command '/home/mobot/toggle_dictation.sh'
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom0/ binding 'Alt_R'

echo "Installing Android SDK..."
cd ~/Downloads
wget -q -O commandlinetools.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
mkdir -p ~/Android/cmdline-tools
unzip -qo commandlinetools.zip -d ~/Android/cmdline-tools
mv ~/Android/cmdline-tools/cmdline-tools ~/Android/cmdline-tools/latest 2>/dev/null
yes | ~/Android/cmdline-tools/latest/bin/sdkmanager --licenses
~/Android/cmdline-tools/latest/bin/sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"

echo "ALL OPERATIONS COMPLETED"
