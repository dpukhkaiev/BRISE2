#!/bin/bash


echo "root:root" | chpasswd
# adding possibility to login as root:root and changing default port to 2222
sed -i 's/#PermitRootLogin.*/PermitRootLogin\ yes/' /etc/ssh/sshd_config
sed -i 's/#Port\ 22.*/Port\ 2222/' /etc/ssh/sshd_config

# Adding own ssh keys
mkdir /root/.ssh
echo "AAAAB3NzaC1yc2EAAAADAQABA AABAQDQkM928jumaceO+QyLqtu0QtpImOD6y2sdyszxAqB18x3uWPU4TEQdmF2DPovJ7DGZViERYs8U1nyK5h/DxvT09esuq79wWusu0Ny17d32TrekFvxPRjV5Z+zzVXaAy1PTFWgOPys1KaCgHIwKrY1WiXtUiKpr8Kldbo1qpWIW/CJqo3KplTw7oEvLxye1eZNB4NnBemutB1ZyyTz2PwVTGSA86pcKFmpSdCHZKwkng4l3ko8wt+II2biME0+26Xadqf/fc1nKFOZFzn6wi6WdseZ72yb0wlQ/zF39NpVvA26OMweIGLd5M6o/2hIi9V1sx5v9SgnSmNWgz3wNENUD sem@SUbuntu" >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

# Generating new host keys: RSA1 RSA DSA ECDSA
ssh-keygen -A

#prepare run dir
#if [ ! -d "/var/run/sshd" ]; then
#  mkdir -p /var/run/sshd
#fi