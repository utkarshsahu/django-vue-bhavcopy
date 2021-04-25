### **Setup**

#### Redis Setup

On mac, install redis using
```
sudo mkdir -p /usr/local/lib/redis-stable
cd /usr/local/lib/redis-stable
curl -O http://download.redis.io/redis-stable.tar.gz
tar xzvf redis-stable.tar.gz
make
make test
sudo make install
rm redis-stable.tar.gz
```

**redis.conf**
```
port              6379
daemonize         yes
save              60 1
bind              127.0.0.1
tcp-keepalive     300
dbfilename        dump.rdb
dir               ./
rdbcompression    yes
```

Create redis.conf file using above content at /etc/redis/redis.conf<br>
Then, start redis server
```
redis-server /etc/redis/redis.conf
```

#### Application setup
1. Install all the requirements<br>
`pip install -r requirements.txt`
2. Create migrations<br>
`REDIS_URL=redis://127.0.0.1:6379 python manage.py migrate`
3. Serve the app<br>
`REDIS_URL=redis://127.0.0.1:6379 python manage.py runserver`