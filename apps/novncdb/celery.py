# project/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.novncdb.settings')

app = Celery('novncdb')

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# 👇 关键修改：在 Celery 实例化后，强制为 Redis 连接注入 RESP2 协议参数
# 这能确保 Celery 在连接 Redis 5.x 时，不会发送 HELLO 3 命令
app.conf.broker_transport_options = {
    'redis_client_cls': 'celery.app.backends.redis.RedisClient',
    'protocol': 2,  # 强制使用 RESP2 协议
}
app.conf.result_backend_transport_options = {
    'protocol': 2,  # 结果后端也强制使用 RESP2
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')