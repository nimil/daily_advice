docker build --platform linux/amd64 -t wecom-kf:latest .
docker save -o wecom-kf.tar wecom-kf:latest

# linx部署
mv /home/lighthouse/wecom-kf.tar ./
docker load -i wecom-kf.tar
docker-compose up -d