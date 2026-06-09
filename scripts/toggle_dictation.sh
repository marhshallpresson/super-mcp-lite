#!/bin/bash
if pgrep -f "nerd-dictation" > /dev/null
then
    /home/mobot/Downloads/nerd-dictation/nerd-dictation end
else
    /home/mobot/Downloads/nerd-dictation/nerd-dictation begin --vosk-model-dir=/home/mobot/Downloads/nerd-dictation/model &
fi
