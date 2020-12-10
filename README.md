# Cuju Deploy on Ubuntu 18

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

* 下載 Cuju deploy
    ```
    $ git clone https://github.com/Mooseclown/Cuju-Deploy.git
    ```

* 更改 inventory 參數
    ```
    $ vim inventory
    ___
    [cuju:vars]
    # primary host 相關資訊
    primary_host_ip = 192.168.77.151
    primary_host_user_name = cuju
    primary_host_password = cujuft
    primary_host_nic = ens3   # 網卡名稱
    # backup host 相關資訊
    backup_host_ip = 192.168.77.153
    backup_host_user_name = cuju
    backup_host_password = cujuft
    backup_host_nic = ens3    # 網卡名稱
    # 本機 ip
    local_host_ip = 192.168.77.155
    # 執行在 primary host 的 vm 網路設定
    guest_ip = 192.168.77.152
    guset_netmask = 255.255.255.0
    guest_network = 192.168.77.0
    guest_broadcast = 192.168.77.255
    guest_gateway = 192.168.77.7
    guest_dns_nameservers = 140.96.254.98 8.8.8.8
    nfs_folder_path = "/home/[user_name]/cuju_nfsfolder"    # modify [user_name] to your local user name
    ```
    ######  不建議將 ansible_ssh_pass, ansible_sudo_pass 放在這裡，可以參考官網（https://docs.ansible.com/ansible/2.9/user_guide/intro_inventory.html ）使用 ssh_key 和 vaults

* 開始在遠端主機佈署 Cuju 
    ```
    cd Cuju-Deploy
    $ ./start.sh
    ```
    佈署步驟請看下方 cuju.yml

* 執行並檢測 Cuju 是否執行成功，並將 vm 關機
    ```
    $ ansible-playbook -i inventory check_cuju.yml
    ```
    檢測步驟請看下方 check_cuju.yml

* Ubuntu-16.04 VM image file will be download, and the `account/password` is `root/root`

cuju.yml
---
## set enviroment
hosts: cuju (primary host and backup host)
become: yes     # like sudo

* 讓 sudo 不用輸入密碼(在 /etc/sudoer 新增 [your username] ALL=(ALL) NOPASSWD: ALL)
    ```
    < ansible >
    - name: "let {{ ansible_ssh_user }} sudo without password on Ubuntu"
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
      command: update-grub        # like type command on shell
    ---
    < script >
    $ sudo update-grub
    ```

* 下載並安裝 cuju 需要的 package
    ```
    < ansible >
    - name: install cuju required package
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
         - expect
        update_cache: yes
    ---
    < script >
    $ sudo apt-get update
    $ sudo apt-get install ssh vim gcc make gdb fakeroot build-essential \
    kernel-package libncurses5 libncurses5-dev zlib1g-dev \
    libglib2.0-dev qemu xorg bridge-utils openvpn libelf-dev \
    libssl-dev libpixman-1-dev nfs-common git tigervnc-viewer expect
    ```

* 更改遠端主機網路設定 (加入 bridge)
    ```
    < ansible >
    - name: backup old network config
      copy:
        src: /etc/netplan/50-cloud-init.yaml
        dest: /etc/netplan/50-cloud-init.yaml.backup
        remote_src: yes
    ---
    < script >
    $ sudo cp /etc/netplan/50-cloud-init.yaml /etc/netplan/50-cloud-init.yaml.backup

    ***
    < ansible >
    - name: copy network.py
      copy:
        src: reset_network_with_bridge.py
        dest: /etc/netplan/reset_network_with_bridge.py
        mode: '0744'
    ---
    < script >
    $ scp -P 22 ./reset_network_with_bridge.py {{ ansible_ssh_user }}@{{ ansible_ssh_host }}:/etc/netplan/

    ***
    < ansible >
    # 只在 primary host 執行
    - name: change primary network config
      command: "python reset_network_with_bridge.py {{ primary_host_nic }} {{ ansible_ssh_host[ansible_ssh_host|length-1] }}"
      args:
        chdir: /etc/netplan
      when: ansible_ssh_host == primary_host_ip   # like if

    # 只在 backup host 執行
    - name: change backup network config
      become: yes
      command: "python reset_network_with_bridge.py {{ backup_host_nic }} {{ ansible_ssh_host[ansible_ssh_host|length-1] }}"
      args:
        chdir: /etc/netplan
      when: ansible_ssh_host == backup_host_ip    # like if
    ---
    < script >
    $ sudo python /etc/netplan/reset_network_with_bridge.py {{ backup_host_nic }} {{ bridge_number }}
    ```

* 重新開機
    ```
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

## download and make cuju
hosts: primary_host (only primary host)
become: yes     # like sudo

* 開新資料夾 /mnt/nfs
    ```
    < ansible >
    - name: creat directory /mnt/nfs
      file:       # creat a directory with path and access permissions is 755
        path: /mnt/nfs
        state: directory
        mode: 0755
    ---
    < script >
    $ sudo mkdir /mnt/nfs
    ```

* mount the nfs folder
    ```
    < ansible >
    - name: mount remote nfsfolder to remote /mnt/nfs
      mount:        # This module controls active and configured mount points in /etc/fstab .
        path: /mnt/nfs
        src: "{{ local_host_ip }}:{{ nfs_folder_path }}"
        fstype: nfs
        state: mounted
    ---
    < script >
    $ sudo mount -t nfs {{ local_host_ip }}:{{ nfs_folder_path }} /mnt/nfs
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
    $ cd /mnt/nfs/Cuju
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
    $ cd /mnt/nfs/Cuju/kvm
    $ ./configure
    $ make clean
    $ make -j8
    $ ./reinsmodkvm.sh
    ```

* 回 Cuju 資料夾，複製並修改 cuju 要使用的 shell script
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

    - name: change ftmode.sh
      replace:
        path: /mnt/nfs/Cuju/ftmode.sh
        regexp: '\[backup address\]'
        replace: '{{ backup_host_ip }}'
    ---
    < script >
    $ cd /mnt/nfs/Cuju
    $ scp -P 22 ./cuju_sh/runvm.sh {{ ansible_ssh_user }}@{{ ansible_ssh_host }}:/mnt/nfs/Cuju/
    $ scp -P 22 ./cuju_sh/recv.sh {{ ansible_ssh_user }}@{{ ansible_ssh_host }}:/mnt/nfs/Cuju/
    $ scp -P 22 ./cuju_sh/ftmode.sh {{ ansible_ssh_user }}@{{ ansible_ssh_host }}:/mnt/nfs/Cuju/
    $ sed -i 's/\[backup address\]/{{ backup_host_ip }}/g' ./ftmode.sh
    ```

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

## mount guset raw image
hosts: primary_host (only primary host)
become: yes     # like sudo

* 下載並安裝 kpartx
    ```
    < ansible >
    - name: install kpartx
      apt:
        pkg:
         - kpartx
        update_cache: yes
    ---
    < script >
    $ sudo apt-get update
    $ sudo apt-get install kpartx
    ```

* 開新資料夾 /mnt/vm
    ```
    < ansible >
    - name: creat directory /mnt/vm
      file:       # creat a directory with path and access permissions is 755
        path: /mnt/vm
        state: directory
        mode: 0755
    ---
    < script >
    $ sudo mkdir /mnt/vm
    ```

* 掛載 raw image 至 primary host 的 /mnt/vm
    ```
    < ansible >
    - name: lookup whick /dev/loop can use
      command: losetup -f
      register: dev_loop    # variable

    - name: add to loop and partation
      command: "{{ item }}"
      with_items:
        - losetup -f /mnt/nfs/Ubuntu20G-1604.img 
        - "kpartx -a {{ dev_loop['stdout'] }}"
    
    - name: find partation map
      command: "kpartx -l {{ dev_loop['stdout'] }}"
      register: loop_part

    - name: mount
      command: "mount /dev/mapper/{{ loop_part['stdout'].split(' ')[0] }} /mnt/vm"
    ---
    < script >
    $ sudo losetup -f
    > /dev/loop6
    $ sudo losetup -f /mnt/nfs/Ubuntu20G-1604.img
    $ sudo kpartx -a /dev/loop6
    $ sudo kpartx -l /dev/loop6
    > loop6p1 : 0 41938944 /dev/loop6 2048
    $ sudo mount /dev/mapper/loop6p1 /mnt/vm
    ```

## change guest network
hosts: primary_host (only primary host)
become: yes     # like sudo

* 設定 raw image 的網路設定檔
    ```
    < ansible >
    - name: change address
      lineinfile:
        path: /mnt/vm/etc/network/interfaces
        regexp: '^address.*'
        line: "address {{ guest_ip }}"

    - name: change netmask
      lineinfile:
        path: /mnt/vm/etc/network/interfaces
        regexp: '^netmask.*'
        line: "netmask {{ guset_netmask }}"

    - name: change network
      lineinfile:
        path: /mnt/vm/etc/network/interfaces
        regexp: '^network.*'
        line: "network {{ guest_network }}"

    - name: change broadcast
      lineinfile:
        path: /mnt/vm/etc/network/interfaces
        regexp: '^broadcast.*'
        line: "broadcast {{ guest_broadcast }}"

    - name: change gateway
      lineinfile:
        path: /mnt/vm/etc/network/interfaces
        regexp: '^gateway.*'
        line: "gateway {{ guest_gateway }}"

    - name: change dns-nameservers
      lineinfile:
        path: /mnt/vm/etc/network/interfaces
        regexp: '^dns-nameservers.*'
        line: "dns-nameservers {{ guest_dns_nameservers }}"
    ---
    < script >
    $ sudo vim /mnt/vm/etc/network/interfaces:
        address {{ guest_ip }}
        netmask {{ guset_netmask }}
        network {{ guest_network }}
        broadcast {{ guest_broadcast }}
        gateway {{ guest_gateway }}
        dns-nameservers {{ guest_dns_nameservers }}
    ```

## unmount guest raw image
hosts: primary_host (only primary host)
become: yes     # like sudo

* 卸載 primary host 上的 raw image 並刪除 /mnt/vm
    ```
    < ansible >
    - name: unmount guest image
      command: "{{ item }}"
      with_items:
        - umount /mnt/vm
        - sync
        - "kpartx -d {{ dev_loop['stdout'] }}"
        - sync
        - "losetup -d {{ dev_loop['stdout'] }}"
        - sync
        - rm -r /mnt/vm
    ---
    < script >
    $ sudo umount /mnt/vm
    $ sync
    $ sudo kpartx -d /dev/loop6
    $ sync
    $ sudo losetup -d /dev/loop6
    $ sync
    $ sudo rm -r /mnt/vm
    ```

check_cuju.yml
---
# start Cuju
hosts: cuju (primary host and backup host)
become: yes     # like sudo

* mount the nfs folder
    ```
    < ansible >
    - name: mount remote nfsfolder to remote /mnt/nfs
      mount:        # This module controls active and configured mount points in /etc/fstab .
        path: /mnt/nfs
        src: "{{ local_host_ip }}:{{ nfs_folder_path }}"
        fstype: nfs
        state: mounted
    ---
    < script >
    $ sudo mount -t nfs {{ local_host_ip }}:{{ nfs_folder_path }} /mnt/nfs
    ```

* 換成 Cuju 的 kvm
    ```
    < ansible >
    - name: replace kvm module to Cuju's kvm module
      command: ./reinsmodkvm.sh
      args:
        chdir: /mnt/nfs/Cuju/kvm
    ---
    < script >
    $ cd /mnt/nfs/Cuju/kvm
    $ ./reinsmodkvm.sh
    ```

* 開啟 Primary VM (用 tmux 防止 ansible 完成後關閉 VM)
    ```
    < ansible >
    - name: boot vm on primary host(execute runvm.sh)
      command: "{{ item }}"
      with_items:
        - tmux new-session -d -s cuju -n runvm
        - tmux send-keys -t cuju:runvm "cd /mnt/nfs/Cuju" Enter
        - tmux send-keys -t cuju:runvm "./runvm.sh" Enter
      when: ansible_ssh_host == primary_host_ip   # like if
    ---
    < script >
    On primary host
    $ sudo tmux new-session -d -s cuju -n runvm
    $ sudo tmux send-keys -t cuju:runvm "cd /mnt/nfs/Cuju" Enter
    $ sudo tmux send-keys -t cuju:runvm "./runvm.sh" Enter
    ```

* 留時間給 Primary VM 完成開機
    ```
    < ansible >
    - name: sleep 40s
      pause:
        seconds: 40
    ---
    < script >
    $ sleep 40
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
    ---
    < script >
    $ scp -P 22 ./cuju_sh/check_ssh.sh {{ ansible_ssh_user }}@{{ ansible_ssh_host }}:/mnt/nfs/Cuju/
    $ scp -P 22 ./cuju_sh/ssh_connect_primaryvm.sh {{ ansible_ssh_user }}@{{ ansible_ssh_host }}:/mnt/nfs/Cuju/

    ***
    < ansible >
    - name: check primary vm is on
      command: "./check_ssh.sh {{ guest_ip }} /mnt/nfs/vm1.monitor"
      args:
        chdir: /mnt/nfs/Cuju
      register: check_in_primary   # new variable

    - name: if primary vm off, quit this ansible
      fail:       # it will interrupt and return fial message
        msg: primary vm boot unsuccessfully.
      when: check_in_primary.stdout.find('0') == -1
    ---
    < script >
    $ cd /mnt/nfs/Cuju
    $ ./check_ssh.sh [primary_vm_ip] /mnt/nfs/vm1.monitor
    看到這個表示 VM 啟動成功 -> 繼續測試
    ok: [backup_host] => {
      "msg": "Primary VM running result: 0"
    }

    看到這個表示 VM 啟動失敗 -> 結束測試
    ok: [backup_host] => {
      "msg": "Primary VM closed result: $x"   # $x != 0
    }
    ```

* 如果開機成功，開啟 Backup VM 並且打入 ftmode (用 tmux 防止 ansible 完成後關閉 VM)
    ```
    < ansible >
    - name: start receiver(execute recv.sh)
      command: "{{ item }}"
      with_items:
        - tmux new-session -d -s cuju -n recv
        - tmux send-keys -t cuju:recv "cd /mnt/nfs/Cuju" Enter
        - tmux send-keys -t cuju:recv "./recv.sh" Enter
      when: ansible_ssh_host == backup_host_ip
    ---
    < script >
    $ sudo tmux new-window -d -t cuju -n recv
    $ sudo tmux send-keys -t cuju:recv "cd /mnt/nfs/Cuju" Enter
    $ sudo tmux send-keys -t cuju:recv "./recv.sh" Enter

    ***
    < ansible >
    - name: sleep 40s
      pause:
        seconds: 40
    ---
    < script >
    $ sleep 40

    ***
    < ansible >
    - name: enter FT mode(execute fdmode.sh)
      command: ./ftmode.sh
      args:
        chdir: /mnt/nfs/Cuju
      when: ansible_ssh_host == primary_host_ip
    ---
    < script >
    $ sudo tmux new-window -d -t cuju -n ftmode
    $ sudo tmux send-keys -t cuju:ftmode "cd /mnt/nfs/Cuju" Enter
    $ sudo tmux send-keys -t cuju:ftmode "./ftmode.sh" Enter
    ```

## check cuju start successfully
hosts: cuju (primary host and backup host)
become: yes     # like sudo

* Backup host call failover
    ```
    < ansible >
    - name: call failover
      shell: echo "cuju-failover" | nc -w 1 -U vm1r.monitor
      args:
        chdir: /mnt/nfs
      when: ansible_ssh_host == backup_host_ip    # like if
    ---
    < script >
    On backup host
    $ cd /mnt/nfs
    $ echo "cuju-failover" | sudo nc -w 1 -U vm1r.monitor
    ```

* 關閉 primary host 開啟 VM 的 tmux
    ```
    < ansible >
    - name: kill tmux session
      command: tmux kill-session -t cuju
      when: ansible_ssh_host == primary_host_ip
    ---
    < script >
    On primary host
    $ sudo tmux kill-session -t cuju
    ```

* 休息一下
    ```
    < ansible >
    - name: sleep 10s
      pause:
        seconds: 10
    ---
    < script >
    $ sleep 10
    ```

* Backup host 確認 VM 是否存活
    ```
    < ansible >
    - name: check vm is alive
      command: "./check_ssh.sh {{ guest_ip }} /mnt/nfs/vm1r.monitor"
      args:
        chdir: /mnt/nfs/Cuju
      register: check_in_backup
      when: ansible_ssh_host == backup_host_ip
    ---
    < script >
    On backup host
    $ cd /mnt/nfs/Cuju
    $ ./check_ssh.sh [primary_vm_ip] /mnt/nfs/vm1.monitor
    看到這個表示 ftmode 啟動成功 -> 繼續執行將 VM 關機
    ok: [backup_host] => {
      "msg": "Primary VM running result: 0"
    }

    看到這個表示 ftmode 啟動失敗 -> 跳至"關閉啟動 VM 的 tumx"
    ok: [backup_host] => {
      "msg": "Primary VM closed result: $x"   # $x != 0
    }
    ```

* Backup host 將 VM 關機
    ```
    < ansible >
    - name: copy poweroff_vm.sh
      copy:
        src: ./cuju_sh/poweroff_vm.sh
        dest: /mnt/nfs/Cuju
        mode: 0755
      when: ansible_ssh_host == backup_host_ip and check_in_backup.stdout.find('0') != -1   # 確認 ftmode 成功
    ---
    < script >
    On local host
    $ scp -P 22 ./cuju_sh/poweroff_vm.sh {{ ansible_ssh_user }}@{{ ansible_ssh_host }}:/mnt/nfs/Cuju/

    ***
    < ansible>
    - name: poweroff vm
      command: "./poweroff_vm.sh {{ guest_ip }}"
      args:
        chdir: /mnt/nfs/Cuju
      when: ansible_ssh_host == backup_host_ip and check_in_backup.stdout.find('0') != -1   # 確認 ftmode 成功
    ---
    < script >
    On backup host
    $ cd /mnt/nfs/Cuju
    $ ./poweroff_vm.sh {{ guest_ip }}
    ```

* 休息一下
    ```
    < ansible >
    - name: sleep 30s
      pause:
        seconds: 30
    ---
    < script >
    $ sleep 30
    ```

* 關閉啟動 VM 的 tumx
    ```
    < ansible >
    - name: kill tmux session
      command: tmux kill-session -t cuju
      when: ansible_ssh_host == backup_host_ip
    ---
    < script >
    On backup host
    $ sudo tmux kill-session -t cuju
    ```

* 顯示檢測結果
    ```
    < ansible >
    - name: if primary vm off, quit this ansible
      fail:       # it will interrupt and return fial message
        msg: primary vm boot unsuccessfully.
      when: check_in_primary.stdout.find('0') == -1
    
    - name: show the vm state
      debug:
        msg: "{{ check_in_backup.stdout }}"
      when: ansible_ssh_host == backup_host_ip
    ---
    看到這個表示 ftmode 成功:
    ok: [backup_host] => {
      "msg": "Primary VM running result: 0"
    }

    看到這個表示 ftmode 失敗:
    fatal: [backup_host]: FAILED! => {"changed": false, "msg": "Cuju ftmode unsuccessfully."}
    ```

If you successfully start Cuju, you will see the following message show on Primary Host(terminal-A):
![](https://i.imgur.com/nUdwKkB.jpg)

If you want to test failover You can kill or ctrl-c VM on the Primary Host, and you will see the following message show on Backup Host(terminal-C):
![](https://i.imgur.com/JWIhtDz.png)