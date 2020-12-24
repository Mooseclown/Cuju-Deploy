#!/bin/bash
host=$1
monitor=$2
output=$(./ssh_connect_primaryvm.sh $host $monitor)

if [ $? -eq 0 ];  then
    echo "Primary VM running result: $?"
else
    echo "Primary VM closed result: $?"
fi
exit $?