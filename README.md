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
    $ ansible-galaxy collection install gluster.gluster
    $ ansible-galaxy collection install community.general
    ```

* 下載 Cuju deploy
    ```
    $ git clone https://github.com/Mooseclown/Cuju-Deploy.git
    ```

* 更改 inventory 參數
    ```
    cuju 為一個 group，包含 primary 和 backup 兩個子 group。
    [cuju:vars] 是 cuju group 底下的 global variable
    primary 為一個 group，包含 primary_host 一個主機
    [primary:vars] 是 primary group 底下的 global variable
    backup 為一個 group，包含 backup_host 一個主機
    [backup:vars] 是 backup group 底下的 global variable
    ```
    *** 只需更改 cuju group 的 global variable 即可 ***
    ```
    $ vim inventory
    ___
    [cuju:vars]
    # choose type of share disk:
    share_disk = "gluster"     # please input 'gluster' or 'nfs'
    use_heartbeat = "yes"         # please input 'yes' or 'no'

    # primary host information:
    primary_host_ip_1G = 192.168.77.151
    primary_host_ip_10G = 192.168.123.100
    primary_host_user_name = cuju
    primary_host_password = cujuft
    primary_host_gluster_machine_name = FTGlusterFS1
    primary_host_cuju_machine_name = cujuft-machine1
    primary_host_bridge_nic_1G = ens3
    primary_free_disk = /dev/vdb

    # backup host information:
    backup_host_ip_1G = 192.168.77.153
    backup_host_ip_10G = 192.168.123.101
    backup_host_user_name = cuju
    backup_host_password = cujuft
    backup_host_gluster_machine_name = FTGlusterFS2
    backup_host_cuju_machine_name = cujuft-machine2
    backup_host_bridge_nic_1G = ens3
    backup_free_disk = /dev/vdb

    # if share_disk is nfs
    nfs_server_ip = 192.168.77.155
    nfs_server_machine_name = cuju_nfs_server
    nfs_folder_path = "/home/[user_name]/cuju_nfsfolder"    # modify [user_name] to your local user name

    # if use_heart_beat is yes
    bind_network = "192.168.77.0"     # primary and backup host ip network
    external_ip = "192.168.77.155"    # to check network is health

    # the vm network config
    guest_ip = 192.168.77.152
    guset_netmask = 255.255.255.0
    guest_network = 192.168.77.0
    guest_broadcast = 192.168.77.255
    guest_gateway = 192.168.77.7
    guest_dns_nameservers = 140.96.254.98 8.8.8.8

    share_disk_path = /mnt/nfs
    [cuju:children]
    primary
    backup

    [primary:vars]
    gluster_machine_name = "{{ primary_host_gluster_machine_name }}"
    cuju_machine_name = "{{ primary_host_cuju_machine_name }}"
    bridge_nic = "{{ primary_host_bridge_nic_1G }}"
    free_disk = "{{ primary_free_disk }}"
    cuju_script_path = "/home/{{ primary_host_user_name }}/cuju_script"

    [primary]
    primary_host ansible_ssh_host="{{ primary_host_ip_1G }}" ansible_connection=ssh ansible_ssh_user="{{ primary_host_user_name }}" ansible_ssh_pass="{{ primary_host_password }}" ansible_sudo_pass="{{ primary_host_password }}"

    [backup:vars]
    gluster_machine_name = "{{ backup_host_gluster_machine_name }}"
    cuju_machine_name = "{{ backup_host_cuju_machine_name }}"
    bridge_nic = "{{ backup_host_bridge_nic_1G }}"
    free_disk = "{{ backup_free_disk }}"
    cuju_script_path = "/home/{{ backup_host_user_name }}/cuju_script"

    [backup]
    backup_host ansible_ssh_host="{{ backup_host_ip_1G }}" ansible_connection=ssh ansible_ssh_user="{{ backup_host_user_name }}" ansible_ssh_pass="{{ backup_host_password }}" ansible_sudo_pass="{{ backup_host_password }}"
    ```
    ######  不建議將 ansible_ssh_pass, ansible_sudo_pass 放在這裡，可以參考官網（https://docs.ansible.com/ansible/2.9/user_guide/intro_inventory.html ）使用 ssh_key 和 vaults

* 開始在遠端主機佈署 Cuju 
    ```
    cd Cuju-Deploy
    $ ./start.sh
    ```

* 佈署步驟
    ```
    # 更換成適合 CUJU 的環境
    1. set_environment.yml
    # 使用 share disk （ nfs 或 gluster ）
    2. gluster.yml or nfs.yml
    # 使用 heartbeat （選用）
    3. heartbeat.yml
    # 下載 CUJU 並編譯
    4. download_cuju.yml
    # 設定 VM 網路
    5. set_vm_network.yml
    # 確認 CUJU 是否能用
    6. check_cuju.yml
    ```

* Ubuntu-16.04 VM image file will be download, and the `account/password` is `root/root`


##### 以下所有的 module 都可以用 `ansible-doc -s $module_name` 查詢如何使用
ex: `ansible-doc -s lineinfile` or `ansible-doc -s apt`

set_environment.yml
---
hosts: cuju (primary host and backup host)
become: yes     # like sudo

#### set enviroment
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
    ###### reference: 
    lineinfile: https://docs.ansible.com/ansible/2.4/lineinfile_module.html

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
    ###### reference:
    lineinfile: https://docs.ansible.com/ansible/2.4/lineinfile_module.html
    apt: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/apt_module.html

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
    ###### reference:
    apt: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/apt_module.html

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
        src: ./files/reset_network_with_bridge.py
        dest: /etc/netplan/reset_network_with_bridge.py
        mode: '0744'
    ---
    < script >
    $ scp -P 22 ./reset_network_with_bridge.py {{ ansible_ssh_user }}@{{ ansible_ssh_host }}:/etc/netplan/

    ***
    < ansible >
    - name: change network config
      command: "python reset_network_with_bridge.py {{ bridge_nic }} {{ ansible_ssh_host[ansible_ssh_host|length-1] }}"
      args:
        chdir: /etc/netplan
    ---
    < script >
    $ sudo python /etc/netplan/reset_network_with_bridge.py {{ backup_host_nic }} {{ bridge_number }}
    ```
    ###### reference:
    copy: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/copy_module.html
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html

* 設定 host name
    ```
    < ansible >
    - name: set /etc/hostname
      become: yes
      replace:
        path: /etc/hostname
        regexp: "^(.+)$"
        replace: "{{ cuju_machine_name }}"
    ---
    < script >
    $ sudo vim /etc/hostname
        {{ cuju_machine_name }}
    ```
    ###### reference:
    replace: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/replace_module.html

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
    ###### reference:
    reboot: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/reboot_module.html


nfs.yml
---
hosts: cuju (primary host and backup host)

#### mount with nfs
* 設定 cuju hosts
    ```
    < ansible >
    - name: set /etc/hosts
      become: yes
      lineinfile:
        path: /etc/hosts
        line: "{{ nfs_server_ip }} {{ nfs_server_machine_name }}"
        insertbefore: '^\n'
        firstmatch: yes
    ---
    < script >
    $ sudo vim /etc/hosts
        {{ nfs_server_ip }} {{ nfs_server_machine_name }}
    ```
    ###### reference:
    lineinfile: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/lineinfile_module.html


* 建立 nfs 要 mount 的資料夾
    ```
    < ansible >
    - name: creat directory with share disk path
      become: yes
      file:       # creat a directory with path and access permissions is 755
        path: "{{ share_disk_path }}"
        state: directory
        owner: "{{ ansible_ssh_user }}"
        group: "{{ ansible_ssh_user }}"
        mode: 0755
    ---
    < script >
    $ sudo mkdir {{ share_disk_path }}
    $ sudo chown -R {{ ansible_ssh_user }}:{{ ansible_ssh_user }} {{ share_disk_path }}
    ```
    ###### reference:
    file: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/file_module.html

* mount nfs folder on remote host
    ```
    < ansible >
    - name: mount local share disk to remote host
      become: yes
      mount:
        path: "{{ share_disk_path }}"
        src: "{{ nfs_server_machine_name }}:{{ nfs_folder_path }}"
        fstype: nfs
        state: mounted
    ---
    < script >
    $ sudo mount -t nfs {{ nfs_server_machine_name }}:{{ nfs_folder_path }} {{ share_disk_path }}
    ```
    ###### reference:
    mount: https://docs.ansible.com/ansible/latest/collections/ansible/posix/mount_module.html


gluster.yml
---
hosts: cuju (primary host and backup host) 
vars :
  - gluster_path : /glusterfs
  - gluster_volume_name : gvol0

#### gluster
* 安裝 gluster
    ```
    < ansible >
    - name: install gluster
      become: yes
      apt:
        pkg:
          - glusterfs-server
        state: latest
        update-cache: yes
    ---
    < script >
    $ sudo apt upgrade
    $ sudo apt update
    $ sudo apt install gluster
    ```
    ###### reference:
    apt: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/apt_module.html

* 建立 gluster mount 的資料夾
    ```
    < ansible >
    - name: creat gluster folder
      become: yes
      file:
        path: "{{ gluster_path }}"
        state: directory
        owner: "{{ ansible_ssh_user }}"
        group: "{{ ansible_ssh_user }}"
        mode: "0755"
    ---
    < script >
    $ sudo mkdir {{ gluster_path }}
    $ sudo chown -R {{ ansible_ssh_user }}:{{ ansible_ssh_user }} {{ gluster_path }}
    ```
    ###### reference:
    file: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/file_module.html

* 格式化硬碟
    ```
    < ansible >
    - name: create a ext4 filesystem on free disk
      become: yes
      community.general.filesystem:
        fstype: ext4
        dev: "{{ free_disk }}"
    ---
    < script >
    $ sudo mkfs -t ext4 {{ free_disk }}
    ```
    ###### reference:
    community.general.filesystem: https://docs.ansible.com/ansible/latest/collections/community/general/filesystem_module.html

* mount 硬碟至指定資料夾
    ```
    < ansible >
    - name: mount gluster
      become: yes
      mount:
        path: "{{ gluster_path }}"
        src: "{{ free_disk }}"
        fstype: ext4
        state: mounted
    ---
    < script >
    $ sudo mount -t ext4 {{ free_disk }} {{ gluster_path }}
    ```
    ###### reference:
    mount: https://docs.ansible.com/ansible/latest/collections/ansible/posix/mount_module.html

* 設定 cuju hosts
    ```
    < ansible >
    - name: set /etc/hosts
      become: yes
      lineinfile:
        path: /etc/hosts
        line: "{{ item }}"
        insertbefore: '^\n'
        firstmatch: yes
      with_items:
        - "{{ primary_host_ip_10G }} {{ primary_host_gluster_machine_name }}"
        - "{{ backup_host_ip_10G }} {{ backup_host_gluster_machine_name }}"
    ---
    < script >
    $ sudo vim /etc/hosts
        {{ primary_host_ip_10G }} {{ primary_host_gluster_machine_name }}
        {{ backup_host_ip_10G }} {{ backup_host_gluster_machine_name }}
    ```
    ###### reference:
    lineinfile: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/lineinfile_module.html

* start gluster service
    ```
    < ansible >
    - name: start gluster
      become: yes
      command: "{{ item }}"
      with_items:
        - systemctl start glusterd.service
        - systemctl enable glusterd.service
        - systemctl status glusterd.service
    ---
    < script >
    $ sudo systemctl start glusterd.service
    $ sudo systemctl enable glusterd.service
    $ sudo systemctl status glusterd.service
    ```
    ###### reference:
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html

* 建立 gluster peer
    ```
    < ansible >
    - name: gluster peer
      become: yes
      gluster.gluster.gluster_peer:
        state: present
        nodes:
          - "{{ primary_host_gluster_machine_name }}"
          - "{{ backup_host_gluster_machine_name }}"
      when: ansible_ssh_host == primary_host_ip_1G
    ---
    < script >
    *** primary ***
    $ sudo gluster peer probe {{ backup_host_gluster_machine_name }}
    > peer probe success.
    ```
    ###### reference:
    gluster.gluster.gluster_peer: https://docs.ansible.com/ansible/latest/collections/gluster/gluster/gluster_peer_module.html

* 配置 gluster volume
    ```
    < ansible >
    - name: creat gluster volume folder
      become: yes
      file:
        path: "{{ gluster_path }}/{{ gluster_volume_name }}"
        state: directory
        owner: "{{ ansible_ssh_user }}"
        group: "{{ ansible_ssh_user }}"
        mode: "0755"
    ---
    < script >
    $ sudo mkdir {{ gluster_path }}/{{ gluster_volume_name }}
    $ sudo chown -R {{ ansible_ssh_user }}:{{ ansible_ssh_user }} {{ gluster_path }}/{{ gluster_volume_name }}
    
    ***
    < ansible >
    - name: set gluster volume
      become: yes
      gluster.gluster.gluster_volume:
        state: present
        name: "{{ gluster_volume_name }}"
        bricks: "{{ gluster_path }}/{{ gluster_volume_name }}"
        cluster:
          - "{{ primary_host_gluster_machine_name }}"
          - "{{ backup_host_gluster_machine_name }}"
        replicas: 2
      when: ansible_ssh_host == primary_host_ip_1G
    ---
    < script >
    *** primary ***
    $ sudo gluster volume create {{ gluster_volume_name }} replica 2 {{ primary_host_gluster_machine_name }}:{{ gluster_path }}/{{ gluster_volume_name }} {{ backup_host_gluster_machine_name }}:{{ gluster_path }}/{{ gluster_volume_name }}
    $ sudo gluster volume start {{ gluster_volume_name }}
    ```
    ###### reference:
    file: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/file_module.html
    gluster.gluster.gluster_volume: https://docs.ansible.com/ansible/latest/collections/gluster/gluster/gluster_volume_module.html

* 掛載 share disk
    ```
    < ansible >
    - name: creat share disk directory
      become: yes
      file:
        path: "{{ share_disk_path }}"
        state: directory
        owner: "{{ ansible_ssh_user }}"
        group: "{{ ansible_ssh_user }}"
        mode: "0755"
    ---
    < script >
    $ sudo mkdir {{ share_disk_path }}
    $ sudo chown -R {{ ansible_ssh_user }}:{{ ansible_ssh_user }} {{ share_disk_path }}

    ***
    < ansible >
    - name: mount gluster volume to share disk directory
      become: yes
      mount:
        path: "{{ share_disk_path }}"
        src: "{{ gluster_machine_name }}:/{{ gluster_volume_name }}"
        fstype: glusterfs
        opts: defaults,_netdev,noauto,x-systemd.automount
        state: mounted
    ---
    < script >
    $ sudo mount -t glusterfs {{ gluster_machine_name }}:/{{ gluster_volume_name }} {{ share_disk_path }}
    $ sudo vim /etc/fstab
        {{ gluster_machine_name }}:/{{ gluster_volume_name }} {{ share_disk_path }} glusterfs defaults,_netdev,noauto,x-systemd.automount 0 0
    ```
    ###### reference:
    file: file: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/file_module.html
    mount: mount: https://docs.ansible.com/ansible/latest/collections/ansible/posix/mount_module.html

* 設定 gluster timeout
    ```
    < ansible >
    - name: set gluster timeout
      become: yes
      command: "gluster volume set {{ gluster_volume_name }} network.ping-timeout 1"
      when: ansible_ssh_host == primary_host_ip_1G
    ---
    < script >
    *** primary ***
    $ sudo gluster volume set {{ gluster_volume_name }} network.ping-timeout 1
    ```
    ###### reference:
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html


heartbeat.yml
---
hosts: cuju (primary host and backup host)

#### heartbeat
* git clone pacescript
    ```
    < ansible >
    - name: git clone pacescript
      git:
        repo: https://github.com/kester-lin/heartbeat_script.git
        dest: "{{ share_disk_path }}/pacescript"
        version: ubuntu1804
      when: ansible_ssh_host == primary_host_ip_1G
    ---
    < script >
    *** primary ***
    $ cd {{ share_disk_path }}
    $ mv heartbeat_script pacescript
    $ cd pacescript
    $ git checkout ubuntu1804
    ```
    ###### reference:
    git: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/git_module.html

* 更改 heartbeat 配置
    ```
    < ansible >
    - name: change ip in corosync.conf
      replace: 
        path: "{{ share_disk_path }}/pacescript/corosync.conf"
        regexp: "{{ item.regex }}"
        replace: "{{ item.replace }}"
      with_items:
        - { regex: "192.168.125.0", replace: "{{ bind_network }}"}
        - { regex: "192.168.125.210", replace: "{{ primary_host_ip_1G }}"}
        - { regex: "192.168.125.211", replace: "{{ backup_host_ip_1G }}"}
      when: ansible_ssh_host == primary_host_ip_1G
    ---
    < script >
    *** primary ***
    $ vim corosync.conf
        bindnetaddr: 192.168.125.0 -> bindnetaddr: {{ bind_network }}
        ring0_addr: 192.168.125.210 -> ring0_addr: {{ primary_host_ip_1G }}
        ring0_addr: 192.168.125.211 -> ring0_addr: {{ backup_host_ip_1G }}

    ***
    < ansible >
    - name: change environment.sh
      replace:
        path: "{{ share_disk_path }}/pacescript/environment.sh"
        regexp: "{{ item.regex }}"
        replace: "{{ item.replace }}"
      with_items:
        - { regex: "^primary_name=.*$", replace: "primary_name={{ primary_host_user_name }}"}
        - { regex: "^backup_name=.*$", replace: "backup_name={{ backup_host_user_name }}"}
        - { regex: "^primary_host=.*$", replace: "primary_host={{ primary_host_cuju_machine_name }}"}
        - { regex: "^backup_host=.*$", replace: "backup_host={{ backup_host_cuju_machine_name }}"}
        - { regex: "^external_ip=.*$", replace: "external_ip={{ external_ip }}"}
      when: ansible_ssh_host == primary_host_ip_1G
    ---
    < script >
    *** primary ***
    $ sudo vim environment.sh
        primary_name=cujuft -> primary_name={{ primary_host_user_name }}
        backup_name=cujuft -> backup_name={{ backup_host_user_name }}
        primary_host=cujuft-machine1 -> primary_host={{ primary_host_cuju_machine_name }}
        backup_host=cujuft-machine2 -> backup_host={{ backup_host_cuju_machine_name }}
        external_ip=192.168.125.237 -> external_ip={{ external_ip }}
    ```
    ###### reference:
    replace: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/replace_module.html

* 設定 cuju hosts
    ```
    < ansible >
    - name: set /etc/hosts
      become: yes
      lineinfile:
        path: /etc/hosts
        line: "{{ item }}"
        insertbefore: '^\n'
        firstmatch: yes
      with_items:
        - "{{ primary_host_ip_1G }} {{ primary_host_cuju_machine_name }}"
        - "{{ backup_host_ip_1G }} {{ backup_host_cuju_machine_name }}"
    ---
    < script >
    $ sudo vim /etc/hosts
        {{ primary_host_ip_1G }} {{ primary_host_cuju_machine_name }}
        {{ backup_host_ip_1G }} {{ backup_host_cuju_machine_name }}
    ```
    ###### reference:
    lineinfile: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/lineinfile_module.html

* 安裝 auto script
    ```
    < ansible >
    - name: install auto script
      become: yes
      command: ./install.sh
      args:
        chdir: "{{ share_disk_path }}/pacescript"
    ---
    < script >
    $ ./install.sh
    ```
    ###### reference:
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html


download_cuju.yml
---
hosts: cuju (primary host and backup host)

#### download and make cuju
* 建立 cuju script 的資料夾
    ```
    < ansible >
    - name: creat cuju script folder
      file:
        path: "{{ cuju_script_path }}"
        state: directory
        owner: "{{ ansible_ssh_user }}"
        group: "{{ ansible_ssh_user }}"
        mode: 0755
    ---
    < script >
    $ sudo mkdir {{ cuju_script_path }}
    $ sudo chown -R {{ ansible_ssh_user }}:{{ ansible_ssh_user }} {{ cuju_script_path }}
    ```
    ###### reference:
    file: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/file_module.html
    
* 在 nfs folder 下載 cuju
    ```
    - name: clone cuju
      git:
        repo: https://github.com/Cuju-ft/Cuju.git
        dest: "{{ share_disk_path }}/Cuju"
        version: support/kernel4.15
      when: ansible_ssh_host == primary_host_ip_1G
    ---
    < script >
    *** primary ***
    $ cd {{ share_disk_path }}
    $ git clone https://github.com/Cuju-ft/Cuju.git
    $ git checkout support/kernel4.15
    ```
    ###### reference:
    git: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/git_module.html
    
* Configure & Compile Cuju-ft
    ```
    < ansible >
    - name: Cuju make
      command: "{{ item }}"       # execute command in order.
      with_items:           # loop to do
        - ./configure --enable-cuju --enable-kvm --disable-pie --target-list=x86_64-softmmu
        - make clean
        - make -j8
      args:
        chdir: "{{ share_disk_path }}/Cuju"        # path
      when: ansible_ssh_host == primary_host_ip_1G
    ---
    < script >
    *** primary ***
    $ cd {{ share_disk_path }}/Cuju
    $ ./configure --enable-cuju --enable-kvm --disable-pie --target-list=x86_64-softmmu
    $ make clean
    $ make -j8
    ```
    ###### reference:
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html
    
* Configure, Compile & insmod Cuju-kvm module
    ```
    < ansible >
    - name: KVM make
      command: "{{ item }}"
      with_items:
        - ./configure
        - make clean
        - make -j8
        - sudo ./reinsmodkvm.sh
      args:
        chdir: "{{ share_disk_path }}/Cuju/kvm"
      when: ansible_ssh_host == primary_host_ip_1G
    ---
    < script >
    *** primary ***
    $ cd {{ share_disk_path }}/Cuju/kvm
    $ ./configure
    $ make clean
    $ make -j8
    $ sudo ./reinsmodkvm.sh
    ```
    ###### reference:
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html

* 回 Cuju 資料夾，複製並修改 cuju 要使用的 shell script
    ```
    < ansible >
    - name: copy runvm.sh, recv.sh, ftmode.sh
      template:         # the copy module copies a file from the local or remote machine to a location on the remote machine.
        src: "./templates/{{ item }}.j2"
        dest: "{{ cuju_script_path }}/{{ item }}"
        mode: 0755
      with_items:
        - runvm.sh
        - recv.sh
        - ftmode.sh
    ---
    < script >
    *** local ***
    $ scp -P 22 ./templates/runvm.sh {{ ansible_ssh_user }}@{{ ansible_ssh_host }}:{{ cuju_script_path }}/runvm.sh
    $ scp -P 22 ./templates_sh/recv.sh {{ ansible_ssh_user }}@{{ ansible_ssh_host }}:{{ cuju_script_path }}/recv.sh
    $ scp -P 22 ./templates/ftmode.sh {{ ansible_ssh_user }}@{{ ansible_ssh_host }}:{{ cuju_script_path }}/ftmode.sh
    *** remote ***
    更改 ftmode.sh
    將 {{ backup_host_ip_10G }}(純文字) 更改為 {{ backup_host_ip_10G }}(變數)
    將 {{ ansible_ssh_user }}(純文字) 更改為 {{ ansible_ssh_user }}(變數)
    更改 runvm.sh
    將 {{ ansible_ssh_user }}(純文字) 更改為 {{ ansible_ssh_user }}(變數)
    ```
    ###### reference:
    template: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/template_module.html

* 下載能夠使用的 VM image
    ```
    < ansible >
     - name: download gdown.pl (download Ubuntu20G-1604.img)
      get_url:        # downloads files from HTTP, HTTPS, or FTP to the remote server. The remote server must have direct access to the remote resource.
        url: https://raw.githubusercontent.com/circulosmeos/gdown.pl/master/gdown.pl
        dest: "{{ share_disk_path }}"
        mode: 0775
      when: ansible_ssh_host == primary_host_ip_1G
    ---
    < script >
    *** primary ***
    $ cd {{ share_disk_path }}
    $ wget -nc https://raw.githubusercontent.com/circulosmeos/gdown.pl/master/gdown.pl
    $ chmod +x gdown.pl
    
    ***
    < ansible >
    - name: download Ubuntu20G-1604.tar.gz (download Ubuntu20G-1604.img)
      command: ./gdown.pl https://drive.google.com/file/d/0B9au9R9FzSWKNjZpWUNlNDZLcEU/view Ubuntu20G-1604.tar.gz
      args:
        chdir: "{{ share_disk_path }}"
      when: ansible_ssh_host == primary_host_ip_1G
    ---
    < script >
    *** primary ***
    $ ./gdown.pl https://drive.google.com/file/d/0B9au9R9FzSWKNjZpWUNlNDZLcEU/view Ubuntu20G-1604.tar.gz

    ***
    < ansible >
    - name: unzip Ubuntu20G-1604.tar.gz (download Ubuntu20G-1604.img)
      unarchive:        # this module unpacks an archive. It will not unpack a compressed file that does not contain an archive.
        src: "{{ share_disk_path }}/Ubuntu20G-1604.tar.gz"
        dest: "{{ share_disk_path }}"
        remote_src: yes
      when: ansible_ssh_host == primary_host_ip_1G
    ---
    < script >
    *** primary ***
    $ tar zxvf Ubuntu20G-1604.tar.gz
    ```
    ###### reference:
    get_url: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/get_url_module.html
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html
    unarchive: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/unarchive_module.html


set_vm_network.yml
---
hosts: primary_host (only primary host)
become: yes     # like sudo

#### mount guset raw image
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
    $ sudo apt-get install kpartx
    ```
    ###### reference:
    apt: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/apt_module.html

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
    ###### reference:
    file: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/file_module.html

* 掛載 raw image 至 primary host 的 /mnt/vm
    ```
    < ansible >
    - name: lookup whick /dev/loop can use
      command: losetup -f
      register: dev_loop    # variable

    - name: add to loop and partation
      command: "{{ item }}"
      with_items:
        - "losetup -f {{ share_disk_path }}/Ubuntu20G-1604.img"
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
    $ sudo losetup -f {{ share_disk_path }}/Ubuntu20G-1604.img
    $ sudo kpartx -a /dev/loop6
    $ sudo kpartx -l /dev/loop6
    > loop6p1 : 0 41938944 /dev/loop6 2048
    $ sudo mount /dev/mapper/loop6p1 /mnt/vm
    ```
    ###### reference:
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html

#### change guest network
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
    ###### reference:
    lineinfile: https://docs.ansible.com/ansible/2.4/lineinfile_module.html
    
#### unmount guest raw image
hosts: primary_host (only primary host)
become: yes     # like sudo

* 卸載 primary host 上的 raw image 並刪除 /mnt/vm
    ```
    < ansible >
    - name: unmount /mnt/vm
      mount:
        path: /mnt/vm
        state: unmounted

    - name: remove /mnt/vm
      file:
        path: /mnt/vm
        state: absent

    - name: delete device loop
      command: "{{ item }}"
      with_items:
        - sync
        - "kpartx -d {{ dev_loop['stdout'] }}"
        - sync
        - "losetup -d {{ dev_loop['stdout'] }}"
    ---
    < script >
    $ sudo umount /mnt/vm
    $ sudo rm -r /mnt/vm
    $ sync
    $ sudo kpartx -d /dev/loop6
    $ sync
    $ sudo losetup -d /dev/loop6
    ```
    ###### reference:
    mount: https://docs.ansible.com/ansible/latest/collections/ansible/posix/mount_module.html
    file: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/file_module.html
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html


check_cuju.yml
---
hosts: cuju (primary host and backup host)
become: yes     # like sudo

#### start Cuju
* 換成 Cuju 的 kvm
    ```
    < ansible >
    - name: replace kvm module to Cuju's kvm module
      become: yes
      command: ./reinsmodkvm.sh
      args:
        chdir: "{{ share_disk_path }}/Cuju/kvm"
    ---
    < script >
    $ cd {{ share_disk_path }}/Cuju/kvm
    $ sudo ./reinsmodkvm.sh
    ```
    ###### reference:
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html

* 開啟 Primary VM (用 tmux 防止 ansible 完成後關閉 VM)
    ```
    < ansible >
    - name: boot vm on primary host(execute runvm.sh)
      command: "{{ item }}"
      with_items:
        - tmux new-session -d -s cuju -n runvm
        - tmux send-keys -t cuju:runvm "cd {{ cuju_script_path }}" Enter
        - tmux send-keys -t cuju:runvm "./runvm.sh" Enter
      when: ansible_ssh_host == primary_host_ip_1G   # like if
    ---
    < script >
    *** primary ***
    $ sudo tmux new-session -d -s cuju -n runvm
    $ sudo tmux send-keys -t cuju:runvm "cd {{ cuju_script_path }}/Cuju" Enter
    $ sudo tmux send-keys -t cuju:runvm "./runvm.sh" Enter
    ```
    ###### reference:
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html

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
    ###### reference:
    sleep: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/pause_module.html

* 檢查 Primary VM 是否啟動 (用 ssh 連線測試)
    ```
    < ansible >
    - name: copy check_ssh.sh ssh_connet_primaryvm.sh
      copy:
        src: "{{ item }}"
        dest: "{{ cuju_script_path }}"
        mode: 0755
      with_items:
        - ./files/check_ssh.sh
        - ./files/ssh_connect_primaryvm.sh
    ---
    < script >
    *** local ***
    $ scp -P 22 ./files/check_ssh.sh {{ ansible_ssh_user }}@{{ ansible_ssh_host }}:{{ cuju_script_path }}/Cuju/check_ssh.sh
    $ scp -P 22 ./files/ssh_connect_primaryvm.sh {{ ansible_ssh_user }}@{{ ansible_ssh_host }}:{{ cuju_script_path }}/Cuju/ssh_connect_primaryvm.sh

    ***
    < ansible >
    - name: check primary vm is on
      command: "./check_ssh.sh {{ guest_ip }} /home/{{ ansible_ssh_user }}/vm1.monitor"
      args:
        chdir: "{{ cuju_script_path }}"
      register: check_primary_vm        # new local variable
      when: ansible_ssh_host == primary_host_ip_1G

    - name: if primary vm off, quit this ansible
      fail:       # it will interrupt and return fial message
        msg: primary vm boot unsuccessfully.
      when: hostvars['primary_host']['check_primary_vm'].stdout.find('0') == -1
    ---
    < script >
    *** primary ***
    $ cd {{ cuju_script_path }}
    $ ./check_ssh.sh [primary_vm_ip] ~/vm1.monitor
    *** local ***
    看到這個表示 VM 啟動成功 -> 繼續測試
    ok: [backup_host] => {
      "msg": "Primary VM running result: 0"
    }

    看到這個表示 VM 啟動失敗 -> 結束測試
    ok: [backup_host] => {
      "msg": "Primary VM closed result: $x"   # $x != 0
    }
    ```
    ###### reference:
    copy: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/copy_module.html
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html
    fail: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/fail_module.html

* 如果開機成功，開啟 Backup VM 並且打入 ftmode (用 tmux 防止 ansible 完成後關閉 VM)
    ```
    < ansible >
    - name: start receiver(execute recv.sh)
      command: "{{ item }}"
      with_items:
        - tmux new-session -d -s cuju -n recv
        - tmux send-keys -t cuju:recv "cd {{ cuju_script_path }}" Enter
        - tmux send-keys -t cuju:recv "./recv.sh" Enter
      when: ansible_ssh_host == backup_host_ip_1G
    ---
    < script >
    *** backup ***
    $ sudo tmux new-window -d -t cuju -n recv
    $ sudo tmux send-keys -t cuju:recv "cd {{ cuju_script_path }}" Enter
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
        chdir: "{{ cuju_script_path }}"
      when: ansible_ssh_host == primary_host_ip_1G
    ---
    < script >
    *** primary ***
    $ sudo tmux new-window -d -t cuju -n ftmode
    $ sudo tmux send-keys -t cuju:ftmode "cd {{ cuju_script_path }}" Enter
    $ sudo tmux send-keys -t cuju:ftmode "./ftmode.sh" Enter
    
    ***
    < ansible >
    - name: wait ft start
      pause:
        seconds: 60
    ---
    < script >
    $ sleep 60
    ```
    ###### reference:
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html
    sleep: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/pause_module.html


#### check cuju start successfully
hosts: cuju (primary host and backup host)
become: yes     # like sudo

* Backup host call failover
    ```
    < ansible >
    - name: call failover
      become: yes
      shell: echo "cuju-failover" | nc -w 1 -U vm1r.monitor
      args:
        chdir: "/home/{{ ansible_ssh_user }}"
      when: ansible_ssh_host == backup_host_ip_1G    # like if
    ---
    < script >
    *** backup ***
    $ cd ~
    $ echo "cuju-failover" | sudo nc -w 1 -U vm1r.monitor
    ```
    ###### reference:
    shell: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/shell_module.html

* 關閉 primary host 開啟 VM 的 tmux
    ```
    < ansible >
    - name: kill tmux session
      command: tmux kill-session -t cuju
      when: ansible_ssh_host == primary_host_ip_1G
    ---
    < script >
    *** primary ***
    $ sudo tmux kill-session -t cuju
    ```
    ###### reference:
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html

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
    ###### reference:
    sleep: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/pause_module.html

* Backup host 確認 VM 是否存活
    ```
    < ansible >
    - name: check vm is alive
      command: "./check_ssh.sh {{ guest_ip }} /home/{{ ansible_ssh_user }}/vm1r.monitor"
      args:
        chdir: "{{ cuju_script_path }}"
      register: check_backup_vm
      when: ansible_ssh_host == backup_host_ip_1G
    ---
    < script >
    *** backup ***
    $ cd {{ cuju_script_path }}
    $ ./check_ssh.sh [primary_vm_ip] ~/vm1.monitor
    看到這個表示 ftmode 啟動成功 -> 繼續執行將 VM 關機
    ok: [backup_host] => {
      "msg": "Primary VM running result: 0"
    }

    看到這個表示 ftmode 啟動失敗 -> 跳至"關閉啟動 VM 的 tumx"
    ok: [backup_host] => {
      "msg": "Primary VM closed result: $x"   # $x != 0
    }
    ```
    ###### reference:
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html

* Backup host 將 VM 關機
    ```
    < ansible >
    - name: copy poweroff_vm.sh
      copy:
        src: ./files/poweroff_vm.sh
        dest: "{{ cuju_script_path }}"
        mode: 0755
      when: ansible_ssh_host == backup_host_ip_1G and check_backup_vm.stdout.find('0') != -1   # 確認 ftmode 成功
    ---
    < script >
    *** local ***
    $ scp -P 22 ./cuju_sh/poweroff_vm.sh {{ ansible_ssh_user }}@{{ ansible_ssh_host }}:{{ cuju_script_path }}

    ***
    < ansible>
    - name: poweroff vm
      command: "./poweroff_vm.sh {{ guest_ip }}"
      args:
        chdir: "{{ cuju_script_path }}"
      when: ansible_ssh_host == backup_host_ip_1G and check_backup_vm.stdout.find('0') != -1   # 確認 ftmode 成功
    ---
    < script >
    *** backup ***
    $ cd {{ cuju_script_path }}
    $ ./poweroff_vm.sh {{ guest_ip }}
    ```
    ###### reference:
    copy: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/copy_module.html
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html

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
    ###### reference:
    sleep: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/pause_module.html

* 關閉啟動 VM 的 tumx
    ```
    < ansible >
    - name: kill tmux session
      command: tmux kill-session -t cuju
      when: ansible_ssh_host == backup_host_ip_1G
    ---
    < script >
    *** backup ***
    $ sudo tmux kill-session -t cuju
    ```
    ###### reference:
    command: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html

* 顯示檢測結果
    ```
    < ansible >
    - name: if Cuju ftmode unsuccessfully,show this
      fail:
        msg: Cuju ftmode unsuccessfully.
      when: hostvars['backup_host']['check_backup_vm'].stdout.find('0') == -1
    
    - name: show the vm state
      debug:
        msg: "{{ check_backup_vm.stdout }}"
      when: hostvars['backup_host']['check_backup_vm'].stdout.find('0') != -1
    ---
    *** local ***
    看到這個表示 ftmode 成功:
    ok: [backup_host] => {
      "msg": "Primary VM running result: 0"
    }

    看到這個表示 ftmode 失敗:
    fatal: [backup_host]: FAILED! => {"changed": false, "msg": "Cuju ftmode unsuccessfully."}
    ```
    ###### reference:
    fail: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/fail_module.html
    debug: https://docs.ansible.com/ansible/latest/collections/ansible/builtin/debug_module.html
