#!/bin/bash
dnf -y update
dnf -y install nginx

TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

INSTANCE_ID=$(curl -s \
  -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id)

if [ -z "$INSTANCE_ID" ]; then
  INSTANCE_ID="metadata-unavailable"
fi

cat > /usr/share/nginx/html/index.html <<EOF
<h1>TP EC2 / ASG / ALB</h1>
<p>Instance: ${INSTANCE_ID}</p>
EOF

systemctl enable nginx
systemctl start nginx