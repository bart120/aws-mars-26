#!/bin/bash
dnf -y update
dnf -y install nginx
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
echo "<h1>TP EC2 / ASG / ALB</h1><p>Instance: ${INSTANCE_ID}</p>" > /usr/share/nginx/html/index.html
systemctl enable nginx
systemctl start nginx