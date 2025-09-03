#!/bin/bash

pkexec apt install python3-venv python3-tk
python3 -m venv ~/IJOQ-venv
~/IJOQ-venv/bin/pip install "pillow" "numpy" "requests"

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
Categories=Science;
" | tee ~/.local/share/applications/IJOQ.desktop > /dev/null

echo Setup done!
