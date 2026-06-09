#!/bin/bash
# Install Snapshot Camera via Flatpak (bypassing apt completely)
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user -y flathub org.gnome.Snapshot

# Install Node Version Manager & Gemini CLI
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install 20
npm install -g @google/gemini-cli

# Install Portable Java Compiler
wget -q -O ~/jdk.tar.gz https://download.java.net/java/GA/jdk17.0.2/dfd4a8d0985749f896bed50d7138ee7f/8/GPL/openjdk-17.0.2_linux-x64_bin.tar.gz
tar xf ~/jdk.tar.gz -C ~/
export JAVA_HOME=~/jdk-17.0.2
export PATH=$JAVA_HOME/bin:$PATH

# Install Android SDK Command-Line Tools
mkdir -p ~/Android/cmdline-tools
cd ~/Downloads
wget -q -O commandlinetools.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip -qo commandlinetools.zip -d ~/Android/cmdline-tools
mv ~/Android/cmdline-tools/cmdline-tools ~/Android/cmdline-tools/latest 2>/dev/null

echo 'export JAVA_HOME=~/jdk-17.0.2' >> ~/.bashrc
echo 'export ANDROID_HOME=$HOME/Android' >> ~/.bashrc
echo 'export PATH=$JAVA_HOME/bin:$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools' >> ~/.bashrc

yes | ~/Android/cmdline-tools/latest/bin/sdkmanager --licenses
~/Android/cmdline-tools/latest/bin/sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"

echo "DONE"
