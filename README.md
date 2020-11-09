# Cuju Deploy

遠端主機
---
* 先確認佈署主機的 kernel 版本能夠更換成 4.15.0-29-generic 或是到 Cuju 的 Github（https://github.com/Cuju-ft/Cuju/tree/support/kernel4.15 ）下載並安裝 ubuntu-18.04.1-live-server-amd64.iso (Ubuntu 18.04.1)

* 設定好佈署主機的網路並確認能夠用 ssh 進入

本機上
---

* 安裝 ansible
    ```
    $ sudo apt-get install software-properties-common
    $ sudo apt-add-repository ppa:ansible/ansible
    $ sudo apt-get update
    $ sudo apt-get install ansible
    ```

* 建立 inventory 放置需要部署的主機資料
    ```
    $ vim inventory
    ___
    [cuju]
    192.168.77.151 ansible_connection=ssh ansible_ssh_user=user ansible_ssh_pass=root ansible_sudo_pass=root
    ```
    ######  不建議將 ansible_ssh_pass, ansible_sudo_pass 放在這裡，可以參考官網（https://docs.ansible.com/ansible/2.9/user_guide/intro_inventory.html ）使用 ssh_key 和 vaults

* 下載 Cuju deploy
    ```
    $ git clone https://github.com/Mooseclown/Cuju-Deploy.git
    ```
    
* 更改 cuju.yml 內容
    ```
    更改 vars 下方三個變數
    install_machine_username: "遠端主機的 username"
    install_machine_ip_address: "遠端主機的 ip address"
    directory_path: "下載 cuju 的資料夾路徑"
    ```

* 開始佈署 Cuju 在遠端主機
    ```
    $ ansible-playbook -i inventory cuju.yml
    佈署步驟參考下方 cuju.yml
    ```

* Ubuntu-16.04 VM image file will be download, and the `account/password` is `root/root`
 
cuju.yml
---
# Cuju 在 Ubuntu18 安裝流程

* 讓 sudo 不用輸入密碼(在 /etc/sudoer 新增 [your username] ALL=(ALL) NOPASSWD: ALL)
    ```
    - name: "let {{ install_machine_username }} sudo without password on Ubuntu"
      become: yes       # like sudo
      lineinfile:       # add a line to a file if it does not exist, after validate.
        path: /etc/sudoers
        line: '{{ install_machine_username }} ALL=(ALL) NOPASSWD: ALL'
        validate: '/usr/sbin/visudo -cf %s'
    ---
    $ sudo visudo
    
    Add it to the last line
    [your username] ALL=(ALL) NOPASSWD: ALL
    
    Ctrl-X save change and done~
    ```

* 更換版本
    ```
    - name: install image and headers of linux 4.15.0-29-generic
      become: yes
      apt:        # like apt-get
        pkg:
          - linux-image-4.15.0-29-generic
          - linux-headers-4.15.0-29-generic
        update_cache: yes       # like apt-get update
    ---
    $ sudo apt-get install linux-image-4.15.0-29-generic
    $ sudo apt-get install linux-headers-4.15.0-29-generic
    
    ***
    - name: update GRUB_DEFAULT
      become: yes
      lineinfile:       # this module will search a file for a line, and ensure that it is present or absent. And this is primarily useful when you want to change a single line in a file only.
        path: /etc/default/grub
        regexp: '^GRUB_DEFAULT='
        line: 'GRUB_DEFAULT="Advanced options for Ubuntu>Ubuntu, with Linux 4.15.0-29-generic"'
        owner: root
        group: root
        mode: 0755
    ---
    $ sudo vim /etc/default/grub : 
        GRUB_DEFAULT="Advanced options for Ubuntu>Ubuntu, with Linux 4.15.0-29-generic"
    
    ***
    - name: update grub
      become: yes
      command: update-grub        # like type command on shell
    ---
    $ sudo update-grub
    
    ***
    - name: reboot
      become: yes
      reboot:       # reboot the node and wait 30s, then try to connection with the node. If not successful in 5s, break and try again. If still fail after 600s, return fail.
        connect_timeout: 5
        reboot_timeout: 600
        pre_reboot_delay: 0
        post_reboot_delay: 30
    ---
    $ reboot
    ```

* 下載 cuju 需要的 package
    ```
    - name: install cuju required package
      become: yes
      apt:
        pkg:
         - vim
         - gcc
         - make
         - gdb
         - fakeroot
         - build-essential
         - kernel-package
         - libncurses5
         - libncurses5-dev
         - zlib1g-dev
         - libglib2.0-dev
         - qemu
         - xorg
         - bridge-utils
         - openvpn
         - libelf-dev
         - libssl-dev
         - libpixman-1-dev
         - nfs-common
         - git
         - tigervnc-viewer
        update_cache: yes
    ---
    $ sudo apt-get update
    $ sudo apt-get install ssh vim gcc make gdb fakeroot build-essential \
    kernel-package libncurses5 libncurses5-dev zlib1g-dev \
    libglib2.0-dev qemu xorg bridge-utils openvpn libelf-dev \
    libssl-dev libpixman-1-dev nfs-common git tigervnc-viewer
    ```

* 開新資料夾 nfsfolder
    ```
    - name: creat directory nfsfolder
      file:
        path: "{{ directory_path }}"
        state: directory
        mode: 0755
    ---
    $ mkdir nfsfolder
    ```
    
* 在 nfs folder 下載 cuju
    ```
    - name: git clone cuju
      command: git clone https://github.com/Cuju-ft/Cuju.git
      args:
        chdir: "{{ directory_path }}"
    ---
    $ cd nfsfolder
    $ git clone https://github.com/Cuju-ft/Cuju.git
    ```
    
* Configure & Compile Cuju-ft
    ```
    - name: Cuju make
      command: "{{ item }}"       # execute command in order.
      with_items:
        - git checkout support/kernel4.15
        - ./configure --enable-cuju --enable-kvm --disable-pie --target-list=x86_64-softmmu
        - make clean
        - make -j8
      args:
        chdir: "{{ directory_path }}/Cuju"        # path
    ---
    $ cd Cuju
    $ git checkout support/kernel4.15
    $ ./configure --enable-cuju --enable-kvm --disable-pie --target-list=x86_64-softmmu
    $ make clean
    $ make -j8
    ```
    
* Configure, Compile & insmod Cuju-kvm module
    ```
    - name: KVM make
      command: "{{ item }}"
      with_items:
        - ./configure
        - make clean
        - make -j8
        - ./reinsmodkvm.sh
      args:
        chdir: "{{ directory_path }}/Cuju/kvm"
    ---
    $ cd kvm
    $ ./configure
    $ make clean
    $ make -j8
    $ ./reinsmodkvm.sh
    ```

* 回 Cuju 資料夾，製作使用 cuju 的 shell script
    ```
    - name: copy runvm.sh, recv.sh, ftmode.sh
      copy:         # the copy module copies a file from the local or remote machine to a location on the remote machine.
        src: "{{ item }}"
        dest: "{{ directory_path }}/Cuju"
        mode: 0755
      with_items:
        - ./cuju_sh/runvm.sh
        - ./cuju_sh/recv.sh
        - ./cuju_sh/ftmode.sh

    - name: change runvm.sh
      replace:        # This module will replace all instances of a pattern within a file.
        path: "{{ directory_path }}/Cuju/runvm.sh"
        regexp: '\[your username\]'
        replace: "{{ install_machine_username }}"

    - name: change ftmode.sh
      replace:
        path: "{{ directory_path }}/Cuju/ftmode.sh"
        regexp: '{{ item.regexp }}'
        replace: '{{ item.replace }}'
      with_items:
          - { regexp: '\[your username\]', replace: '{{ install_machine_username }}' }
          - { regexp: '\[your address\]', replace: '{{ install_machine_ip_address }}' }
    ---
    $ cd ..
    $ vim runvm.sh
        #!/bin/bash
        sudo ./x86_64-softmmu/qemu-system-x86_64 \
        -drive if=none,id=drive0,cache=none,format=raw,file=./Ubuntu20G-1604.img \
        -device virtio-blk,drive=drive0 \
        -m 1G -enable-kvm \
        -net tap,ifname=tap0 -net nic,model=virtio,vlan=0,macaddr=ae:df:00:00:00:79 \
        -cpu host \
        -vga std -chardev socket,id=mon,path=/home/user/vm1.monitor,server,nowait -mon chardev=mon,id=monitor,mode=readline

    $ vim recv.sh
        #!/bin/bash
        sed -e 's/mode=readline/mode=readline -incoming tcp\:0\:4441,ft_mode/g' -e 's/vm1.monitor/vm1r.monitor/g' -e 's/tap0/tap1/g' ./runvm.sh > tmp.sh
        chmod +x ./tmp.sh
        ./tmp.sh

    $ vim ftmode.sh
        #!/bin/bash
        sudo echo "migrate_set_capability cuju-ft on" | sudo nc -w 1 -U /home/user/vm1.monitor
        sudo echo "migrate -c tcp:192.168.77.151:4441" | sudo nc -w 1 -U /home/user/vm1.monitor
    ```
    ``$ chmod +x runvm.sh recv.sh ftmode.sh``

* 下載能夠使用的 VM image
    ```
    - name: download gdown.pl (download Ubuntu20G-1604.img)
      get_url:        # downloads files from HTTP, HTTPS, or FTP to the remote server. The remote server must have direct access to the remote resource.
        url: https://raw.githubusercontent.com/circulosmeos/gdown.pl/master/gdown.pl
        dest: "{{ directory_path }}"
        mode: 0775
    ---
    $ wget -nc https://raw.githubusercontent.com/circulosmeos/gdown.pl/master/gdown.pl
    $ chmod +x gdown.pl
    
    ***
    - name: download Ubuntu20G-1604.tar.gz (download Ubuntu20G-1604.img)
      command: ./gdown.pl https://drive.google.com/file/d/0B9au9R9FzSWKNjZpWUNlNDZLcEU/view Ubuntu20G-1604.tar.gz
      args:
        chdir: "{{ directory_path }}"
    ---
    $ ./gdown.pl https://drive.google.com/file/d/0B9au9R9FzSWKNjZpWUNlNDZLcEU/view Ubuntu20G-1604.tar.gz

    ***
    - name: unzip Ubuntu20G-1604.tar.gz (download Ubuntu20G-1604.img)
      unarchive:        # this module unpacks an archive. It will not unpack a compressed file that does not contain an archive.
        src: "{{ directory_path }}/Ubuntu20G-1604.tar.gz"
        dest: "{{ directory_path }}"
        remote_src: yes
    ---
    $ tar zxvf Ubuntu20G-1604.tar.gz
    ```

使用 cuju 步驟
---
設定網路
```
$ sudo vim /etc/netplan/50-cloud-init.yaml
    network:
    ethernets:
        lo:
            dhcp4: no
            dhcp6: no
        ens3:
            dhcp4: no
            dhcp6: no
    bridges:
        br0:
            interfaces: [ens3]
            addresses: [192.168.77.151/24]
            gateway4: 192.168.77.7
            nameservers:
                addresses: [8.8.8.8]
            dhcp4: no
            dhcp6: no

    version: 2
```

開啟一個 terminal-A
```
$ cd nfsfolder/Cuju/kvm
$ ./reinsmodkvm.sh
$ cd ..
$ ./runvm.sh
```

開啟另一個 terminal-B
```
$ cd nfsfolder/Cuju
看 Primary host 畫面
$ vncviewer :5900 &
* The default account/password is root/root if you use we provide guest image
```

確認開機成功後，再開另一個 terminal-C
```
$ cd nfsfolder/Cuju
$ ./recv.sh
```

使用 terminal-B
```
$ ./ftmode.sh
看 Backup host 畫面
$ vncviewer :5901 &
```

If you successfully start Cuju, you will see the following message show on Primary Host(terminal-A):
![](https://i.imgur.com/nUdwKkB.jpg)

If you want to test failover You can kill or ctrl-c VM on the Primary Host, and you will see the following message show on Backup Host(terminal-C):
![](https://i.imgur.com/JWIhtDz.png)