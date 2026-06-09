#!/bin/bash
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

echo "Downloading WhiteSur Themes via Git..."
mkdir -p ~/Downloads
cd ~/Downloads
if [ ! -d "WhiteSur-gtk-theme" ]; then
    git clone https://github.com/vinceliuice/WhiteSur-gtk-theme.git
fi
cd WhiteSur-gtk-theme
./install.sh -c Dark -t all

cd ~/Downloads
if [ ! -d "WhiteSur-icon-theme" ]; then
    git clone https://github.com/vinceliuice/WhiteSur-icon-theme.git
fi
cd WhiteSur-icon-theme
./install.sh

echo "Applying Themes via gsettings..."
gsettings set org.cinnamon.desktop.interface gtk-theme 'WhiteSur-Dark'
gsettings set org.cinnamon.desktop.wm.preferences theme 'WhiteSur-Dark'
gsettings set org.cinnamon.desktop.interface icon-theme 'WhiteSur'
gsettings set org.cinnamon.desktop.wm.preferences button-layout 'close,minimize,maximize:'
gsettings set org.cinnamon panels-enabled "['1:0:top']"

echo "Installing OBS Studio and Snapshot via Flatpak..."
sudo flatpak install --system -y flathub com.obsproject.Studio
sudo flatpak install --system -y flathub org.gnome.Snapshot
