"""
AsyncAPI 协议适配器
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from abc import ABC, abstractmethod

from ...core.base.protocol import BaseProtocolAdapter


class AsyncAPIProtocolAdapter(BaseProtocolAdapter):
    """AsyncAPI 协议适配器实现"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {})
        self.connections = {}
        self.message_handlers = {}
        self.subscriptions = {}
        self.protocol_handlers = {
            'websocket': WebSocketHandler(),
            'mqtt': MQTTHandler(),
            'amqp': AMQPHandler(),
            'kafka': KafkaHandler(),
            'nats': NATSHandler()
        }
    
    @property
    def protocol_name(self) -> str:
        """协议名称"""
        return "asyncapi"
    
    def supports_protocol(self, protocol: str) -> bool:
        """检查是否支持协议"""
        return protocol in self.protocol_handlers
    
    async def connect(self, config: Dict[str, Any] = None):
        """建立连接"""
        try:
            protocol = config.get('protocol', 'websocket') if config else 'websocket'
            if not self.supports_protocol(protocol):
                raise ValueError(f"不支持的协议: {protocol}")
            
            handler = self.protocol_handlers[protocol]
            connection_id = await handler.connect(config or {})
            
            self.connections[connection_id] = {
                'protocol': protocol,
                'handler': handler,
                'config': config or {}
            }
            
            self._connected = True
            self._connection_info = {
                'protocol': protocol,
                'connection_id': connection_id
            }
            
            self.logger.info(f"建立 {protocol} 连接: {connection_id}")
            return connection_id
            
        except Exception as e:
            self.logger.error(f"建立连接失败: {e}")
            raise
    
    async def execute(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行操作"""
        try:
            if operation == 'send_message':
                return await self.send_message(
                    data.get('connection_id'),
                    data.get('channel'),
                    data.get('message', {})
                )
            elif operation == 'subscribe':
                return await self.subscribe(
                    data.get('connection_id'),
                    data.get('channel'),
                    data.get('handler')
                )
            elif operation == 'unsubscribe':
                return await self.unsubscribe(data.get('subscription_id'))
            else:
                raise ValueError(f"不支持的操作: {operation}")
                
        except Exception as e:
            return self.handle_error(e)
    
    async def disconnect(self):
        """断开连接"""
        try:
            await self.close_all()
            self._connected = False
            self._connection_info = {}
            
        except Exception as e:
            self.logger.error(f"断开连接失败: {e}")
            raise
    
    async def send_message(self, connection_id: str, channel: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """发送消息"""
        try:
            if connection_id not in self.connections:
                raise ValueError(f"连接不存在: {connection_id}")
            
            connection = self.connections[connection_id]
            handler = connection['handler']
            
            result = await handler.send_message(connection_id, channel, message)
            
            self.logger.info(f"发送消息到 {channel}: {result.get('message_id')}")
            return result
            
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            raise
    
    async def subscribe(self, connection_id: str, channel: str, handler: Callable) -> str:
        """订阅通道"""
        try:
            if connection_id not in self.connections:
                raise ValueError(f"连接不存在: {connection_id}")
            
            connection = self.connections[connection_id]
            protocol_handler = connection['handler']
            
            subscription_id = await protocol_handler.subscribe(connection_id, channel, handler)
            
            self.subscriptions[subscription_id] = {
                'connection_id': connection_id,
                'channel': channel,
                'handler': handler
            }
            
            self.logger.info(f"订阅通道 {channel}: {subscription_id}")
            return subscription_id
            
        except Exception as e:
            self.logger.error(f"订阅失败: {e}")
            raise
    
    async def unsubscribe(self, subscription_id: str):
        """取消订阅"""
        try:
            if subscription_id in self.subscriptions:
                subscription = self.subscriptions[subscription_id]
                connection_id = subscription['connection_id']
                
                if connection_id in self.connections:
                    connection = self.connections[connection_id]
                    handler = connection['handler']
                    await handler.unsubscribe(connection_id, subscription_id)
                
                del self.subscriptions[subscription_id]
                self.logger.info(f"取消订阅: {subscription_id}")
            
        except Exception as e:
            self.logger.error(f"取消订阅失败: {e}")
            raise
    
    def get_connections(self) -> List[Dict[str, Any]]:
        """获取连接列表"""
        return [
            {
                'connection_id': conn_id,
                'protocol': info['protocol'],
                'config': info['config']
            }
            for conn_id, info in self.connections.items()
        ]
    
    def get_subscriptions(self) -> List[Dict[str, Any]]:
        """获取订阅列表"""
        return [
            {
                'subscription_id': sub_id,
                'connection_id': info['connection_id'],
                'channel': info['channel']
            }
            for sub_id, info in self.subscriptions.items()
        ]
    
    async def close_all(self):
        """关闭所有连接"""
        try:
            # 取消所有订阅
            for subscription_id in list(self.subscriptions.keys()):
                await self.unsubscribe(subscription_id)
            
            # 断开所有连接
            for connection_id in list(self.connections.keys()):
                await self.disconnect_connection(connection_id)
            
            self.logger.info("所有连接已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭所有连接失败: {e}")
            raise
    
    async def disconnect_connection(self, connection_id: str):
        """断开连接"""
        try:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                handler = connection['handler']
                await handler.disconnect(connection_id)
                
                del self.connections[connection_id]
                self.logger.info(f"断开连接: {connection_id}")
            
        except Exception as e:
            self.logger.error(f"断开连接失败: {e}")
            raise
    
    def get_supported_operations(self) -> List[str]:
        """获取支持的操作"""
        return ['send_message', 'subscribe', 'unsubscribe', 'connect', 'disconnect']
    
    def get_operation_schema(self, operation: str) -> Dict[str, Any]:
        """获取操作的模式定义"""
        schemas = {
            'send_message': {
                'type': 'object',
                'properties': {
                    'connection_id': {'type': 'string'},
                    'channel': {'type': 'string'},
                    'message': {'type': 'object'}
                },
                'required': ['connection_id', 'channel', 'message']
            },
            'subscribe': {
                'type': 'object',
                'properties': {
                    'connection_id': {'type': 'string'},
                    'channel': {'type': 'string'},
                    'handler': {'type': 'function'}
                },
                'required': ['connection_id', 'channel']
            },
            'unsubscribe': {
                'type': 'object',
                'properties': {
                    'subscription_id': {'type': 'string'}
                },
                'required': ['subscription_id']
            }
        }
        return schemas.get(operation, {})


class ProtocolHandler(ABC):
    """协议处理器基类"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connections = {}
    
    @abstractmethod
    async def connect(self, config: Dict[str, Any]) -> str:
        """建立连接"""
        pass
    
    @abstractmethod
    async def disconnect(self, connection_id: str):
        """断开连接"""
        pass
    
    @abstractmethod
    async def send_message(self, connection_id: str, channel: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """发送消息"""
        pass
    
    @abstractmethod
    async def subscribe(self, connection_id: str, channel: str, handler: Callable) -> str:
        """订阅通道"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, connection_id: str, subscription_id: str):
        """取消订阅"""
        pass


class WebSocketHandler(ProtocolHandler):
    """WebSocket 处理器"""
    
    async def connect(self, config: Dict[str, Any]) -> str:
        try:
            import websockets
            
            url = config.get('url', 'ws://localhost:8080')
            connection = await websockets.connect(url)
            
            connection_id = f"ws_{len(self.connections)}"
            self.connections[connection_id] = connection
            
            return connection_id
            
        except Exception as e:
            self.logger.error(f"WebSocket 连接失败: {e}")
            raise
    
    async def disconnect(self, connection_id: str):
        try:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                await connection.close()
                del self.connections[connection_id]
                
        except Exception as e:
            self.logger.error(f"WebSocket 断开连接失败: {e}")
            raise
    
    async def send_message(self, connection_id: str, channel: str, message: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if connection_id not in self.connections:
                raise ValueError(f"WebSocket 连接不存在: {connection_id}")
            
            connection = self.connections[connection_id]
            
            # 添加通道信息到消息
            message['channel'] = channel
            message['timestamp'] = asyncio.get_event_loop().time()
            
            await connection.send(json.dumps(message))
            
            return {
                'message_id': message.get('id'),
                'status': 'sent',
                'protocol': 'websocket'
            }
            
        except Exception as e:
            self.logger.error(f"WebSocket 发送消息失败: {e}")
            raise
    
    async def subscribe(self, connection_id: str, channel: str, handler: Callable) -> str:
        try:
            if connection_id not in self.connections:
                raise ValueError(f"WebSocket 连接不存在: {connection_id}")
            
            connection = self.connections[connection_id]
            
            # 发送订阅消息
            subscribe_message = {
                'type': 'subscribe',
                'channel': channel,
                'subscription_id': f"sub_{len(self.connections)}"
            }
            
            await connection.send(json.dumps(subscribe_message))
            
            # 启动消息监听
            asyncio.create_task(self._listen_messages(connection, channel, handler))
            
            return subscribe_message['subscription_id']
            
        except Exception as e:
            self.logger.error(f"WebSocket 订阅失败: {e}")
            raise
    
    async def unsubscribe(self, connection_id: str, subscription_id: str):
        try:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                
                unsubscribe_message = {
                    'type': 'unsubscribe',
                    'subscription_id': subscription_id
                }
                
                await connection.send(json.dumps(unsubscribe_message))
                
        except Exception as e:
            self.logger.error(f"WebSocket 取消订阅失败: {e}")
            raise
    
    async def _listen_messages(self, connection, channel: str, handler: Callable):
        """监听消息"""
        try:
            async for message in connection:
                data = json.loads(message)
                if data.get('channel') == channel:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                        
        except Exception as e:
            self.logger.error(f"WebSocket 消息监听失败: {e}")


class MQTTHandler(ProtocolHandler):
    """MQTT 处理器"""
    
    async def connect(self, config: Dict[str, Any]) -> str:
        try:
            import paho.mqtt.client as mqtt
            
            client = mqtt.Client()
            
            # 设置认证
            if 'username' in config and 'password' in config:
                client.username_pw_set(config['username'], config['password'])
            
            # 连接到服务器
            host = config.get('host', 'localhost')
            port = config.get('port', 1883)
            
            client.connect(host, port)
            client.loop_start()
            
            connection_id = f"mqtt_{len(self.connections)}"
            self.connections[connection_id] = client
            
            return connection_id
            
        except Exception as e:
            self.logger.error(f"MQTT 连接失败: {e}")
            raise
    
    async def disconnect(self, connection_id: str):
        try:
            if connection_id in self.connections:
                client = self.connections[connection_id]
                client.disconnect()
                client.loop_stop()
                del self.connections[connection_id]
                
        except Exception as e:
            self.logger.error(f"MQTT 断开连接失败: {e}")
            raise
    
    async def send_message(self, connection_id: str, channel: str, message: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if connection_id not in self.connections:
                raise ValueError(f"MQTT 连接不存在: {connection_id}")
            
            client = self.connections[connection_id]
            
            # 发布消息到主题
            result = client.publish(channel, json.dumps(message))
            
            return {
                'message_id': message.get('id'),
                'status': 'published',
                'protocol': 'mqtt',
                'result': result.rc
            }
            
        except Exception as e:
            self.logger.error(f"MQTT 发送消息失败: {e}")
            raise
    
    async def subscribe(self, connection_id: str, channel: str, handler: Callable) -> str:
        try:
            if connection_id not in self.connections:
                raise ValueError(f"MQTT 连接不存在: {connection_id}")
            
            client = self.connections[connection_id]
            
            # 设置消息回调
            def on_message(client, userdata, msg):
                try:
                    data = json.loads(msg.payload.decode())
                    if asyncio.iscoroutinefunction(handler):
                        asyncio.create_task(handler(data))
                    else:
                        handler(data)
                except Exception as e:
                    self.logger.error(f"MQTT 消息处理失败: {e}")
            
            client.on_message = on_message
            
            # 订阅主题
            client.subscribe(channel)
            
            subscription_id = f"mqtt_sub_{len(self.connections)}"
            return subscription_id
            
        except Exception as e:
            self.logger.error(f"MQTT 订阅失败: {e}")
            raise
    
    async def unsubscribe(self, connection_id: str, subscription_id: str):
        try:
            if connection_id in self.connections:
                client = self.connections[connection_id]
                # MQTT 取消订阅需要知道主题，这里简化处理
                pass
                
        except Exception as e:
            self.logger.error(f"MQTT 取消订阅失败: {e}")
            raise


class AMQPHandler(ProtocolHandler):
    """AMQP 处理器"""
    
    async def connect(self, config: Dict[str, Any]) -> str:
        try:
            import aio_pika
            
            url = config.get('url', 'amqp://localhost')
            connection = await aio_pika.connect_robust(url)
            
            connection_id = f"amqp_{len(self.connections)}"
            self.connections[connection_id] = connection
            
            return connection_id
            
        except Exception as e:
            self.logger.error(f"AMQP 连接失败: {e}")
            raise
    
    async def disconnect(self, connection_id: str):
        try:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                await connection.close()
                del self.connections[connection_id]
                
        except Exception as e:
            self.logger.error(f"AMQP 断开连接失败: {e}")
            raise
    
    async def send_message(self, connection_id: str, channel: str, message: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if connection_id not in self.connections:
                raise ValueError(f"AMQP 连接不存在: {connection_id}")
            
            connection = self.connections[connection_id]
            channel_obj = await connection.channel()
            
            # 发布消息
            await channel_obj.default_exchange.publish(
                aio_pika.Message(body=json.dumps(message).encode()),
                routing_key=channel
            )
            
            return {
                'message_id': message.get('id'),
                'status': 'published',
                'protocol': 'amqp'
            }
            
        except Exception as e:
            self.logger.error(f"AMQP 发送消息失败: {e}")
            raise
    
    async def subscribe(self, connection_id: str, channel: str, handler: Callable) -> str:
        try:
            if connection_id not in self.connections:
                raise ValueError(f"AMQP 连接不存在: {connection_id}")
            
            connection = self.connections[connection_id]
            channel_obj = await connection.channel()
            
            # 声明队列
            queue = await channel_obj.declare_queue(channel)
            
            # 消费消息
            async def process_message(message):
                try:
                    data = json.loads(message.body.decode())
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    self.logger.error(f"AMQP 消息处理失败: {e}")
                finally:
                    await message.ack()
            
            await queue.consume(process_message)
            
            subscription_id = f"amqp_sub_{len(self.connections)}"
            return subscription_id
            
        except Exception as e:
            self.logger.error(f"AMQP 订阅失败: {e}")
            raise
    
    async def unsubscribe(self, connection_id: str, subscription_id: str):
        try:
            if connection_id in self.connections:
                # AMQP 取消订阅需要取消消费者，这里简化处理
                pass
                
        except Exception as e:
            self.logger.error(f"AMQP 取消订阅失败: {e}")
            raise


class KafkaHandler(ProtocolHandler):
    """Kafka 处理器"""
    
    async def connect(self, config: Dict[str, Any]) -> str:
        try:
            from aiokafka import AIOKafkaProducer
            
            bootstrap_servers = config.get('bootstrap_servers', 'localhost:9092')
            producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
            await producer.start()
            
            connection_id = f"kafka_{len(self.connections)}"
            self.connections[connection_id] = producer
            
            return connection_id
            
        except Exception as e:
            self.logger.error(f"Kafka 连接失败: {e}")
            raise
    
    async def disconnect(self, connection_id: str):
        try:
            if connection_id in self.connections:
                producer = self.connections[connection_id]
                await producer.stop()
                del self.connections[connection_id]
                
        except Exception as e:
            self.logger.error(f"Kafka 断开连接失败: {e}")
            raise
    
    async def send_message(self, connection_id: str, channel: str, message: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if connection_id not in self.connections:
                raise ValueError(f"Kafka 连接不存在: {connection_id}")
            
            producer = self.connections[connection_id]
            
            # 发送消息
            await producer.send_and_wait(channel, json.dumps(message).encode())
            
            return {
                'message_id': message.get('id'),
                'status': 'sent',
                'protocol': 'kafka'
            }
            
        except Exception as e:
            self.logger.error(f"Kafka 发送消息失败: {e}")
            raise
    
    async def subscribe(self, connection_id: str, channel: str, handler: Callable) -> str:
        try:
            from aiokafka import AIOKafkaConsumer
            
            bootstrap_servers = 'localhost:9092'  # 简化配置
            
            consumer = AIOKafkaConsumer(
                channel,
                bootstrap_servers=bootstrap_servers,
                group_id=f'stepflow-{len(self.connections)}'
            )
            
            await consumer.start()
            
            # 启动消息监听
            asyncio.create_task(self._consume_messages(consumer, handler))
            
            subscription_id = f"kafka_sub_{len(self.connections)}"
            return subscription_id
            
        except Exception as e:
            self.logger.error(f"Kafka 订阅失败: {e}")
            raise
    
    async def unsubscribe(self, connection_id: str, subscription_id: str):
        try:
            # Kafka 取消订阅需要停止消费者，这里简化处理
            pass
            
        except Exception as e:
            self.logger.error(f"Kafka 取消订阅失败: {e}")
            raise
    
    async def _consume_messages(self, consumer, handler: Callable):
        """消费消息"""
        try:
            async for message in consumer:
                data = json.loads(message.value.decode())
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
        except Exception as e:
            self.logger.error(f"Kafka 消息消费失败: {e}")


class NATSHandler(ProtocolHandler):
    """NATS 处理器"""
    
    async def connect(self, config: Dict[str, Any]) -> str:
        try:
            import nats
            
            url = config.get('url', 'nats://localhost:4222')
            connection = await nats.connect(url)
            
            connection_id = f"nats_{len(self.connections)}"
            self.connections[connection_id] = connection
            
            return connection_id
            
        except Exception as e:
            self.logger.error(f"NATS 连接失败: {e}")
            raise
    
    async def disconnect(self, connection_id: str):
        try:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                await connection.close()
                del self.connections[connection_id]
                
        except Exception as e:
            self.logger.error(f"NATS 断开连接失败: {e}")
            raise
    
    async def send_message(self, connection_id: str, channel: str, message: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if connection_id not in self.connections:
                raise ValueError(f"NATS 连接不存在: {connection_id}")
            
            connection = self.connections[connection_id]
            
            # 发布消息
            await connection.publish(channel, json.dumps(message).encode())
            
            return {
                'message_id': message.get('id'),
                'status': 'published',
                'protocol': 'nats'
            }
            
        except Exception as e:
            self.logger.error(f"NATS 发送消息失败: {e}")
            raise
    
    async def subscribe(self, connection_id: str, channel: str, handler: Callable) -> str:
        try:
            if connection_id not in self.connections:
                raise ValueError(f"NATS 连接不存在: {connection_id}")
            
            connection = self.connections[connection_id]
            
            # 设置消息回调
            def message_handler(msg):
                try:
                    data = json.loads(msg.data.decode())
                    if asyncio.iscoroutinefunction(handler):
                        asyncio.create_task(handler(data))
                    else:
                        handler(data)
                except Exception as e:
                    self.logger.error(f"NATS 消息处理失败: {e}")
            
            # 订阅主题
            subscription = await connection.subscribe(channel, cb=message_handler)
            
            subscription_id = f"nats_sub_{len(self.connections)}"
            return subscription_id
            
        except Exception as e:
            self.logger.error(f"NATS 订阅失败: {e}")
            raise
    
    async def unsubscribe(self, connection_id: str, subscription_id: str):
        try:
            if connection_id in self.connections:
                # NATS 取消订阅需要取消订阅对象，这里简化处理
                pass
                
        except Exception as e:
            self.logger.error(f"NATS 取消订阅失败: {e}")
            raise 