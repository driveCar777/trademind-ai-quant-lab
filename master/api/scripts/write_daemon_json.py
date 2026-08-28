import json
d = {'registry-mirrors': ['https://docker.m.daocloud.io', 'https://registry.cn-hangzhou.aliyuncs.com']}
with open('/etc/docker/daemon.json', 'w') as f:
    json.dump(d, f, indent=2)
print(json.dumps(d, indent=2))