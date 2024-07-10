# -*- coding: utf8 -*-

import json
import time
import random
from pykafka import KafkaClient

from app import app, kafka_logger


class Kafka(object):

    topic = None
    producer_pool = dict()

    @staticmethod
    def init():
        try:
            client = KafkaClient(zookeeper_hosts=app.config['KAFKA_ZK_HOSTS'])
            Kafka.topic = client.topics[app.config['KAFKA_TOPIC_NAME']]
            for i in range(app.config['KAFKA_PRODUCER_POOL_SIZE']):
                producer = Kafka.topic.get_producer(sync=True)
                Kafka.producer_pool[i] = producer
        except Exception, e:
            kafka_logger.exception("init error: %s", e)

    @staticmethod
    def produce(data):
        if not Kafka.producer_pool:
            Kafka.init()
        kafka_logger.info('produce data: {}'.format(data))
        producer = Kafka.producer_pool.get(random.randrange(app.config['KAFKA_PRODUCER_POOL_SIZE']))
        if producer:
            kafka_logger.info('got producer')
            try:
                result = producer.produce(json.dumps(data))
                kafka_logger.info('produce complete')
                return result
            except Exception, e:
                kafka_logger.exception('produce exception: %s', e)

    @staticmethod
    def get_partition_info():
        if not Kafka.topic:
            Kafka.init()
        return Kafka.topic.partitions
