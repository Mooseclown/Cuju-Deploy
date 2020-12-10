#!/usr/bin/expect
set timeout 10

set host [lindex $argv 0]
set username "root"
set password "root"

spawn ssh -l $username $host -p 22
expect "password:" {send "$password\r"}
expect ":~# " {send "sudo poweroff\r"}
expect eof
exit