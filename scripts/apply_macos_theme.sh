#!/bin/bash
# Install GTK Theme (requires sassc which should be installed now)
cd /home/mobot/WhiteSur-gtk-theme
./install.sh -c dark

# Apply GTK Theme, Icons, and Borders
gsettings set org.cinnamon.theme name 'WhiteSur-dark'
gsettings set org.cinnamon.desktop.interface gtk-theme 'WhiteSur-dark'
gsettings set org.cinnamon.desktop.interface icon-theme 'WhiteSur-dark'
gsettings set org.cinnamon.desktop.wm.preferences theme 'WhiteSur-dark'

# Move Cinnamon Panel to the top
gsettings set org.cinnamon panels-enabled "['1:0:top']"

# Move Window Controls to the left
gsettings set org.cinnamon.desktop.interface gtk-decoration-layout 'close,minimize,maximize:'

# Modify the clock format (using Python)
python3 -c "
import json, glob, os
dirs = [
    os.path.expanduser('~/.cinnamon/configs/calendar@cinnamon.org'),
    os.path.expanduser('~/.config/cinnamon/spices/calendar@cinnamon.org')
]
for d in dirs:
    for f in glob.glob(os.path.join(d, '*.json')):
        try:
            with open(f, 'r') as file:
                data = json.load(file)
            if 'use-custom-format' in data and 'custom-format' in data:
                data['use-custom-format']['value'] = True
                data['custom-format']['value'] = '%a %b %e  %H:%M'
            with open(f, 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            pass
"

# Start Plank (silently in background)
nohup plank > /dev/null 2>&1 &

echo "macOS Transformation Complete!"
