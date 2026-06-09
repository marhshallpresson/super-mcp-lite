#!/bin/bash
echo "Installing Developer Tools..."

# 1. Install Java, ADB, Fastboot for Android Dev
echo "Installing JDK and Android CLI tools..."
pkexec apt-get install -y openjdk-17-jdk adb fastboot

# 2. Install VS Code (Official .deb)
echo "Downloading and Installing VS Code..."
wget -qO /tmp/vscode.deb "https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64"
pkexec apt-get install -y /tmp/vscode.deb
rm /tmp/vscode.deb

# 3. Install Node.js Version Manager (NVM) for Web Dev
echo "Installing NVM (Node Version Manager)..."
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# 4. Install Android Studio (via Flatpak - best for Linux Mint)
echo "Installing Android Studio..."
flatpak install -y flathub com.google.AndroidStudio

echo "Developer Setup Complete!"
