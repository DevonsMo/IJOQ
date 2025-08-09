#!/bin/bash

python3 -m venv ~/IJOQ-venv
pkexec apt install python3-tk
~/IJOQ-venv/bin/pip install "pillow" "numpy"

echo "[Desktop Entry]
Comment=
Exec=${HOME}/IJOQ-venv/bin/python '${PWD}/IJOQ.py'
GenericName=Junction Quantification Script
Icon=${PWD}/IJOQ_icon.png
Name=IJOQ
NoDisplay=false
Path=
StartupNotify=true
Terminal=false
TerminalOptions=
Type=Application
" | tee ~/.local/share/applications/IJOQ.desktop > /dev/null

echo Setup done!
