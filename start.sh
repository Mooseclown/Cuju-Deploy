#!/bin/bash

BASEDIR=$(dirname "$0")

mkdir ~/cuju_nfsfolder
sudo apt-get install nfs-kernel-server
sudo sed -i '$a /home/'"$USER"'/cuju_nfsfolder *(rw,no_root_squash,no_subtree_check) ' /etc/exports
sudo /etc/init.d/nfs-kernel-server restart
sudo sed -i 's/\[user_name\]/'"$USER"'/g' $BASEDIR/inventory

ansible-playbook setup.yml