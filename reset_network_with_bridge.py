import sys
import re

net_card = sys.argv[1]
bridges_num = sys.argv[2]

bridges_config = ''
eth_title_space_num = 0
net_card_title_space_num = 0
net_card_space_num = 0
is_ethernet = False
is_net_card = False
is_write = True

read_f = open('/etc/netplan/50-cloud-init.yaml.backup', 'r')
write_f = open('/etc/netplan/50-cloud-init.yaml', 'w')

for line in read_f.readlines():
    is_write = True
    if re.match(r'\s+ethernets:$', line):
        eth_title_space_num = len(line) - len('ethernets:\n')
        for i in range(eth_title_space_num):
            bridges_config = bridges_config + ' '
        bridges_config = bridges_config + 'bridges:\n'
        is_ethernet = True
    elif is_ethernet:
        if re.match(r'\s{' + str(eth_title_space_num+1) + r',999}\S', line):
            if re.match(r'\s+' + net_card + ':$', line):
                net_card_title_space_num = len(line) - (len(net_card)+2)    # +2 is ':\n'
                for i in range(net_card_title_space_num):
                    bridges_config = bridges_config + ' '
                bridges_config = bridges_config + 'br' + str(bridges_num) + ':\n'
                is_net_card = True
            elif is_net_card and re.match(r'\s{' + str(net_card_title_space_num+1) + r',999}\S', line):
                if net_card_space_num == 0:
                    net_card_space_num = len(line) - len(re.search(r'\S.*\n', line).group(0))
                    for i in range(net_card_space_num):
                        bridges_config = bridges_config + ' '
                    bridges_config = bridges_config + 'interfaces: [' + net_card + ']\n'
                bridges_config = bridges_config + line
                is_write = False
            else:
                if is_net_card:
                    for i in range(net_card_space_num):
                        write_f.write(' ')
                    write_f.write('dhcp4: false\n')
                    for i in range(net_card_space_num):
                        write_f.write(' ')
                    write_f.write('dhcp6: false\n')
                is_net_card = False
        else:
            if is_net_card:
                for i in range(net_card_space_num):
                    write_f.write(' ')
                write_f.write('dhcp4: false\n')
                for i in range(net_card_space_num):
                    write_f.write(' ')
                write_f.write('dhcp6: false\n')
            write_f.write(bridges_config)
            is_ethernet = False
            is_net_card = False

    if is_write:
        write_f.write(line)
    

write_f.close()
read_f.close()