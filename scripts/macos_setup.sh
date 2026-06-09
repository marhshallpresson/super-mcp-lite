#!/bin/bash
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus

echo "Installing prerequisites..."
sudo apt-get update
sudo apt-get install -y git plank sassc

echo "Downloading WhiteSur GTK Theme..."
mkdir -p ~/Downloads
cd ~/Downloads
if [ ! -d "WhiteSur-gtk-theme" ]; then
    git clone https://github.com/vinceliuice/WhiteSur-gtk-theme.git
fi
cd WhiteSur-gtk-theme
./install.sh -c Dark -t all

echo "Downloading WhiteSur Icon Theme..."
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

echo "Moving Window Buttons to Left..."
gsettings set org.cinnamon.desktop.wm.preferences button-layout 'close,minimize,maximize:'

echo "Moving Cinnamon Panel to Top..."
gsettings set org.cinnamon panels-enabled "['1:0:top']"

echo "Done! macOS transformation complete."
