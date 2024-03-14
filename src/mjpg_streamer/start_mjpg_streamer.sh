#!/bin/bash

export LD_LIBRARY_PATH=/usr/local/lib

# mjpg-streamer config
WIDTH=1280
HEIGHT=720
FPS=30
QUALITY=10
PORT=8080

# Kill process that is already running
pkill mjpg_streamer

# Run mjpg-streamer
/usr/local/bin/mjpg_streamer \
    -i "input_raspicam.so -x $WIDTH -y $HEIGHT -fps $FPS -quality $QUALITY" \
    -o "output_http.so -w /usr/local/share/mjpg-streamer/www -p $PORT"

exit 0
