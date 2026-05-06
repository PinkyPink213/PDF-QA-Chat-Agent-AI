from redis import Redis
from rq import Worker, Queue

redis_conn = Redis(
    host="valkey",
    port=6379
)

queue = Queue(connection=redis_conn)

worker = Worker(
    [queue],
    connection=redis_conn
)

worker.work()