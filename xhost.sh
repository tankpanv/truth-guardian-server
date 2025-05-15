google-chrome --display=:0.0
xhost +
sudo xhost +
xhost +local:
vncserver :1
export DISPLAY=localhost:1
xhost +
xtigervncviewer -SecurityTypes VncAuth -passwd /home/ubuntu/.vnc/passwd :1
sudo apt install tigervnc-viewer
xtigervncviewer -SecurityTypes VncAuth -passwd /home/ubuntu/.vnc/passwd :1
xhost +
vncserver :1
xhost +