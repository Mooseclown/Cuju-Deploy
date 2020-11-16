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
    primary_node ansible_ssh_host=192.168.77.151 ansible_connection=ssh ansible_ssh_user=user ansible_ssh_pass=root ansible_sudo_pass=root
    ```
    ######  不建議將 ansible_ssh_pass, ansible_sudo_pass 放在這裡，可以參考官網（https://docs.ansible.com/ansible/2.9/user_guide/intro_inventory.html ）使用 ssh_key 和 vaults

* 下載 Cuju deploy
    ```
    $ git clone https://github.com/Mooseclown/Cuju-Deploy.git
    ```

* 切換 branch
    ```
    $ git checkout nfs_server_remote
    ```

* 更改 deploy_cuju.yml 內容
    ```
    更改 vars 下方一個變數
    nfs_folder_path: "要被 mount 的資料夾路徑"
    ```

* 更改 start_cuju.tml 內容
    ```
    更改 vars 下方一個變數
    primary_vm_ip: "ip address of Primary VM"
    ```

* 開始在遠端主機佈署 Cuju 
    ```
    $ ansible-playbook -i inventory deploy_cuju.yml
    佈署步驟參考下方 deploy_cuju.yml
    ```

* 將遠端主機上使用 bridge
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

* 更改 Ubuntu-16.04 VM image 的網路設定，確認網路能夠連外且對外ip要是[primary_vm_ip]
    ```
    $ sudo vim /etc/network/interfaces
    $ sudo /etc/init.d/networking restart
    ```

* 啟用 Cuju
    ```
    $ ansible-playbook -i inventory start_cuju.yml
    啟用步驟參考下方 start_cuju.yml
    ```


* Ubuntu-16.04 VM image file will be download, and the `account/password` is `root/root`
 
deploy_cuju.yml
---
# Cuju 在 Ubuntu18 安裝流程

* 讓 sudo 不用輸入密碼(在 /etc/sudoer 新增 [your username] ALL=(ALL) NOPASSWD: ALL)
    ```
    < ansible >
    - name: "let {{ ansible_ssh_user }} sudo without password on Ubuntu"
      become: yes       # like sudo
      lineinfile:       # add a line to a file if it does not exist, after validate.
        path: /etc/sudoers
        line: '{{ ansible_ssh_user }} ALL=(ALL) NOPASSWD: ALL'
        validate: '/usr/sbin/visudo -cf %s'
    ---
    < script >
    $ sudo visudo
    
    Add it to the last line
    [your username] ALL=(ALL) NOPASSWD: ALL
    
    Ctrl-X save change and done~
    ```

* 更換版本
    ```
    < ansible >
    - name: install image and headers of linux 4.15.0-29-generic
      become: yes
      apt:        # like apt-get
        pkg:
          - linux-image-4.15.0-29-generic
          - linux-headers-4.15.0-29-generic
        update_cache: yes       # like apt-get update
    ---
    < script >
    $ sudo apt-get install linux-image-4.15.0-29-generic
    $ sudo apt-get install linux-headers-4.15.0-29-generic
    
    ***
    < ansible >
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
    < script >
    $ sudo vim /etc/default/grub : 
        GRUB_DEFAULT="Advanced options for Ubuntu>Ubuntu, with Linux 4.15.0-29-generic"
    
    ***
    < ansible >
    - name: update grub
      become: yes
      command: update-grub        # like type command on shell
    ---
    < script >
    $ sudo update-grub
    
    ***
    < ansible >
    - name: reboot
      become: yes
      reboot:       # reboot the node and wait 30s, then try to connection with the node. If not successful in 5s, break and try again. If still fail after 600s, return fail.
        connect_timeout: 5
        reboot_timeout: 600
        pre_reboot_delay: 0
        post_reboot_delay: 30
    ---
    < script >
    $ reboot
    ```

* 下載 cuju 需要的 package
    ```
    < ansible >
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
         - nfs-kernel-server
        update_cache: yes
    ---
    < script >
    $ sudo apt-get update
    $ sudo apt-get install ssh vim gcc make gdb fakeroot build-essential \
    kernel-package libncurses5 libncurses5-dev zlib1g-dev \
    libglib2.0-dev qemu xorg bridge-utils openvpn libelf-dev \
    libssl-dev libpixman-1-dev nfs-common git tigervnc-viewer
    ```

* 開新資料夾 /mnt/nfs 和 nfsfolder
    ```
    < ansible >
    - name: creat directory /mnt/nfs
      become: yes
      file:       # creat a directory with path and access permissions is 755
        path: /mnt/nfs
        state: directory
        mode: 0755
    ---
    < script >
    $ sudo mkdir /mnt/nfs
    
    ***
    < ansible >
    - name: creat directory nfsfolder
      file:
        path: "{{ nfs_folder_path }}/nfsfolder"
        state: directory
        mode: 0755
    ---
    < script >
    $ mkdir nfsfolder
    ```

* 設定和啟動 nfs server
    ```
    < ansible >
    - name: add line to /etc/exports
      become: yes
      lineinfile:
        path: /etc/exports
        regexp: "^/home/{{ ansible_ssh_user }}/nfsfolder *(rw,no_root_squash,no_subtree_check)"
        line: "/home/{{ ansible_ssh_user }}/nfsfolder *(rw,no_root_squash,no_subtree_check)"
    ---
    < script >
    Insert this line in /etc/exports to add your NFS folder:

     /home/[ansible_ssh_user]/nfsfolder *(rw,no_root_squash,no_subtree_check) 
    
    ***
    < ansible >
    - name: restart nfs kernel server
      become: yes
      command: /etc/init.d/nfs-kernel-server restart
    ---
    < script >
    $ sudo /etc/init.d/nfs-kernel-server restart
    ```

* mount the nfs folder
    ```
    < ansible >
    - name: mount remote nfsfolder to remote /mnt/nfs
      become: yes
      mount:        # This module controls active and configured mount points in /etc/fstab .
        path: /mnt/nfs
        src: "{{ ansible_ssh_host }}:/home/{{ansible_ssh_user }}/nfsfolder"
        fstype: nfs
        state: mounted
    ---
    < script >
    $ sudo mount -t nfs [ansible_ssh_host]:/home/[ansible_ssh_user]/nfsfolder /mnt/nfs
    ```
    
* 在 nfs folder 下載 cuju
    ```
    < ansible >
    - name: git clone cuju
      command: git clone https://github.com/Cuju-ft/Cuju.git
      args:
        chdir: /mnt/nfs
    ---
    < script >
    $ cd /mnt/nfs
    $ git clone https://github.com/Cuju-ft/Cuju.git
    ```
    
* Configure & Compile Cuju-ft
    ```
    < ansible >
    - name: Cuju make
      command: "{{ item }}"       # execute command in order.
      with_items:
        - git checkout support/kernel4.15
        - ./configure --enable-cuju --enable-kvm --disable-pie --target-list=x86_64-softmmu
        - make clean
        - make -j8
      args:
        chdir: /mnt/nfs/Cuju        # path
    ---
    < script >
    $ cd Cuju
    $ git checkout support/kernel4.15
    $ ./configure --enable-cuju --enable-kvm --disable-pie --target-list=x86_64-softmmu
    $ make clean
    $ make -j8
    ```
    
* Configure, Compile & insmod Cuju-kvm module
    ```
    < ansible >
    - name: KVM make
      command: "{{ item }}"
      with_items:
        - ./configure
        - make clean
        - make -j8
        - ./reinsmodkvm.sh
      args:
        chdir: /mnt/nfs/Cuju/kvm
    ---
    < script >
    $ cd Cuju/kvm
    $ ./configure
    $ make clean
    $ make -j8
    $ ./reinsmodkvm.sh
    ```

* 回 Cuju 資料夾，製作使用 cuju 的 shell script
    ```
    < ansible >
    - name: copy runvm.sh, recv.sh, ftmode.sh
      copy:         # the copy module copies a file from the local or remote machine to a location on the remote machine.
        src: "{{ item }}"
        dest: /mnt/nfs/Cuju
        mode: 0755
      with_items:
        - ./cuju_sh/runvm.sh
        - ./cuju_sh/recv.sh
        - ./cuju_sh/ftmode.sh

    - name: change runvm.sh
      replace:        # This module will replace all instances of a pattern within a file.
        path: /mnt/nfs/Cuju/runvm.sh
        regexp: '\[your username\]'
        replace: "{{ ansible_ssh_user }}"

    - name: change ftmode.sh
      replace:
        path: /mnt/nfs/Cuju/ftmode.sh
        regexp: '{{ item.regexp }}'
        replace: '{{ item.replace }}'
      with_items:
          - { regexp: '\[your username\]', replace: '{{ ansible_ssh_user }}' }
          - { regexp: '\[your address\]', replace: '{{ ansible_ssh_host }}' }
    ---
    < script >
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
    < ansible >
    - name: download gdown.pl (download Ubuntu20G-1604.img)
      get_url:        # downloads files from HTTP, HTTPS, or FTP to the remote server. The remote server must have direct access to the remote resource.
        url: https://raw.githubusercontent.com/circulosmeos/gdown.pl/master/gdown.pl
        dest: /mnt/nfs
        mode: 0775
    ---
    < script >
    $ wget -nc https://raw.githubusercontent.com/circulosmeos/gdown.pl/master/gdown.pl
    $ chmod +x gdown.pl
    
    ***
    < ansible >
    - name: download Ubuntu20G-1604.tar.gz (download Ubuntu20G-1604.img)
      command: ./gdown.pl https://drive.google.com/file/d/0B9au9R9FzSWKNjZpWUNlNDZLcEU/view Ubuntu20G-1604.tar.gz
      args:
        chdir: /mnt/nfs
    ---
    < script >
    $ ./gdown.pl https://drive.google.com/file/d/0B9au9R9FzSWKNjZpWUNlNDZLcEU/view Ubuntu20G-1604.tar.gz

    ***
    < ansible >
    - name: unzip Ubuntu20G-1604.tar.gz (download Ubuntu20G-1604.img)
      unarchive:        # this module unpacks an archive. It will not unpack a compressed file that does not contain an archive.
        src: /mnt/nfs/Ubuntu20G-1604.tar.gz
        dest: /mnt/nfs
        remote_src: yes
    ---
    < script >
    $ tar zxvf Ubuntu20G-1604.tar.gz
    ```

start_cuju.yml
---
# 啟用 Cuju

* 將包含 Cuju 的 nfs 資料夾 mount 到 /mnt/nfs
    ```
    < ansible >
    - name: mount remote nfsfolder to remote /mnt/nfs
      become: yes
      mount:        # This module controls active and configured mount points in /etc/fstab .
        path: /mnt/nfs
        src: "{{ ansible_ssh_host }}:/home/{{ansible_ssh_user }}/nfsfolder"
        fstype: nfs
        state: mounted
    ---
    < script >
    $ sudo mount -t nfs [ansible_ssh_host]:/home/[ansible_ssh_user]/nfsfolder /mnt/nfs 
    ```

* 換成 Cuju 的 kvm
    ```
    < ansible >
    - name: change to Cuju's kvm module
      become: yes
      command: ./reinsmodkvm.sh
      args:
        chdir: /mnt/nfs/Cuju/kvm
    ---
    < script >
    $ cd /mnt/nfs/Cuju/kvm
    $ ./reinsmodkvm.sh
    ```

* 安裝 expect
    ```
    < ansible >
    - name: install expect
      become: yes
      apt:
        pkg:
          - expect
        update_cache: yes
    ---
    < script >
    $ sudo apt-get update
    $ sudo apt-get install expect
    ```

* 開啟 Primary VM (用 tmux 防止 ansible 完成後關閉 VM)
    ```
    < ansible >
    - name: execute runvm.sh
      command: "{{ item }}"
      with_items:
        - tmux new-session -d -s cuju -n runvm
        - tmux send-keys -t cuju:runvm "cd /mnt/nfs/Cuju" Enter
        - tmux send-keys -t cuju:runvm "./runvm.sh" Enter
    ---
    < script >
    $ tmux new-session -d -s cuju -n runvm
    $ tmux send-keys -t cuju:runvm "cd /mnt/nfs/Cuju" Enter
    $ tmux send-keys -t cuju:runvm "./runvm.sh" Enter
    ```

* 檢查 Primary VM 是否啟動 (用 ssh 連線測試)
    ```
    < ansible >
    - name: copy check_ssh.sh ssh_connet_primaryvm.sh
      copy:
        src: "{{ item }}"
        dest: /mnt/nfs/Cuju
        mode: 0755
      with_items:
        - ./cuju_sh/check_ssh.sh
        - ./cuju_sh/ssh_connect_primaryvm.sh

    ***
    < ansible >
    - name: sleep 20s
      pause:
        seconds: 20
    ---
    < script >
    $ sleep 20

    ***
    < ansible >
    - name: check primary vm is setup
      command: "./check_ssh.sh {{ primary_vm_ip }} /mnt/nfs/vm1.monitor"
      args:
        chdir: /mnt/nfs/Cuju
      register: check_ssh # new variable
    ---
    < script >
    $ cd /mnt/nfs/Cuju
    $ ./check_ssh.sh [primary_vm_ip] /mnt/nfs/vm1.monitor
    ```

* 如果有開機成功，開啟 Backup VM 並且打入 ftmode (用 tmux 防止 ansible 完成後關閉 VM)
    ```
    < ansible >
    - name: execute recv.sh
      command: "{{ item }}"
      with_items:
        - tmux new-window -d -t cuju -n recv
        - tmux send-keys -t cuju:recv "cd /mnt/nfs/Cuju" Enter
        - tmux send-keys -t cuju:recv "./recv.sh" Enter
      when: check_ssh.stdout.find('0') != -1  # 判斷是否開機成功
    ---
    < script >
    $ tmux new-window -d -t cuju -n recv
    $ tmux send-keys -t cuju:recv "cd /mnt/nfs/Cuju" Enter
    $ tmux send-keys -t cuju:recv "./recv.sh" Enter

    ***
    < ansible >
    - name: execute fdmode.sh
      command: "{{ item }}"
      with_items:
        - tmux new-window -d -t cuju -n ftmode
        - tmux send-keys -t cuju:ftmode "cd /mnt/nfs/Cuju" Enter
        - tmux send-keys -t cuju:ftmode "./ftmode.sh" Enter
      when: check_ssh.stdout.find('0') != -1  # 判斷是否開機成功
    ---
    < script >
    $ tmux new-window -d -t cuju -n ftmode
    $ tmux send-keys -t cuju:ftmode "cd /mnt/nfs/Cuju" Enter
    $ tmux send-keys -t cuju:ftmode "./ftmode.sh" Enter
    ```

If you successfully start Cuju, you will see the following message show on Primary Host(terminal-A):
![](https://i.imgur.com/nUdwKkB.jpg)

If you want to test failover You can kill or ctrl-c VM on the Primary Host, and you will see the following message show on Backup Host(terminal-C):
![](https://i.imgur.com/JWIhtDz.png)