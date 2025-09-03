#!/bin/bash

pkexec apt remove python3-venv python3-tk

rm -r ~/IJOQ-venv
rm ~/.local/share/applications/IJOQ.desktop

echo Setup done!
