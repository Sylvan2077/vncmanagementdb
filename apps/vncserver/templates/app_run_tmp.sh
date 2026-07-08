#!/bin/bash
export OPENBOX_DIR=OD
export VIRTUALGL_DIR=VD
export XDG_DATA_DIRS=$OPENBOX_DIR/share:/usr/share
export XDG_CONFIG_DIRS=$OPENBOX_DIR/etc/xdg:/etc/xdg
$OPENBOX_DIR/bin/openbox-session & PID=$!
$VIRTUALGL_DIR/bin/vglrun BP
kill $PID
