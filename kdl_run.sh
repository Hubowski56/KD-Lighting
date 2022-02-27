#!/bin/bash 
cd /home/pi/Kd_lighting
export FLASK_APP=app.py
sudo flask run --host 0.0.0.0 --port 5000
