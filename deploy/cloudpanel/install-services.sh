#!/bin/bash
# Install systemd services
cd /home/penny/htdocs/penny.co-l.in
cp deploy/cloudpanel/penny-api.service /etc/systemd/system/
cp deploy/cloudpanel/penny-celery.service /etc/systemd/system/
cp deploy/cloudpanel/penny-celery-beat.service /etc/systemd/system/
cp deploy/cloudpanel/penny-webhook.service /etc/systemd/system/
sed -i 's/change-this-to-your-secret/cb0dcba6ad5a9de712202ff61f99fe7c343d78f26e9dfa5b00914e29222ccce7/' /etc/systemd/system/penny-webhook.service
systemctl daemon-reload
echo "Services installed!"
