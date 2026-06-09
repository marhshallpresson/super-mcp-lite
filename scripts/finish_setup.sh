#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

echo "Starting Kali Linux Distrobox Container..."
distrobox create --image docker.io/kalilinux/kali-rolling --name kali-linux -Y

echo "Installing Flatpak Apps..."
sudo flatpak install --system -y flathub com.obsproject.Studio
sudo flatpak install --system -y flathub org.gnome.Snapshot

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

echo "DONE!"
