#!/bin/bash
sudo echo "migrate_set_capability cuju-ft on" | sudo nc -w 1 -U /home/[your username]/vm1.monitor
sudo echo "migrate -c tcp:[your address]:4441" | sudo nc -w 1 -U /home/[your username]/vm1.monitor

