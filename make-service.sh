#! /bin/sh -
#
# Create a service file for OpenWebRX
#
# Run this script in the installation directory,
# then follow the displayed instructions.
#
# Norman Gray <https://nxg.me.uk>, 2019-02-13

service_file=openwebrx.service

rm -f $service_file

sed -e 's,@OPENWEBRXDIR@,'$PWD, <<EOD >$service_file
# Systemd service file for OpenWebRX.
#
#    sudo cp $service_file /usr/lib/systemd/system
#    sudo systemctl daemon-reload
#    sudo systemctl enable openwebrx
#    sudo systemctl start openwebrx

[Unit]
Description=OpenWebRX
After=network.target

[Service]
User=root
ExecStart=/usr/bin/python2 @OPENWEBRXDIR@/openwebrx.py
WorkingDirectory=@OPENWEBRXDIR@
RuntimeDirectory=openwebrx

[Install]
WantedBy=multi-user.target
EOD

# Tell the user what to do next.
cat <<EOD

Created $service_file

Now do:

    sudo cp $service_file /usr/lib/systemd/system
    sudo systemctl daemon-reload
    sudo systemctl enable openwebrx
    sudo systemctl start openwebrx

Thereafter

    sudo systemctl <command> openwebrx

where <command> is

  * start   : to start the process
  * stop    : to stop it
  * restart : to restart the running process
  * status  : to find its status

EOD
