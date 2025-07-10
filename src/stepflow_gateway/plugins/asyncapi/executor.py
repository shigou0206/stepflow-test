"""
AsyncAPI 执行器
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import uuid

from ...core.base.executor import BaseExecutor
from .specification import AsyncAPISpecification


class AsyncAPIExecutor(BaseExecutor):
    """AsyncAPI 执行器实现"""
    
    def __init__(self, spec: AsyncAPISpecification):
        self.spec = spec
        self.logger = logging.getLogger(__name__)
        self.connections = {}
        self.message_handlers = {}
        self.subscriptions = {}
        self.running = False
        
    def can_execute(self, endpoint: Dict[str, Any]) -> bool:
        """检查是否可以执行端点"""
        try:
            # 检查端点类型
            if endpoint.get('type') != 'async':
                return False
            
            # 检查操作类型
            operation_type = endpoint.get('operation_type')
            if operation_type not in ['publish', 'subscribe']:
                return False
            
            # 检查协议支持
            protocol = endpoint.get('protocol')
            if protocol == 'unknown':
                return False
            
            # 检查服务器配置
            servers = endpoint.get('servers', [])
            if not servers:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"检查执行能力失败: {e}")
            return False
    
    def get_supported_protocols(self) -> List[str]:
        """获取支持的协议"""
        return ['websocket', 'mqtt', 'amqp', 'kafka', 'nats']
    
    async def execute(self, endpoint: Dict[str, Any], params: Dict[str, Any] = None, 
                     data: Dict[str, Any] = None, headers: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行异步操作"""
        try:
            operation_type = endpoint.get('operation_type')
            
            if operation_type == 'publish':
                return await self._execute_publish(endpoint, params, data, headers)
            elif operation_type == 'subscribe':
                return await self._execute_subscribe(endpoint, params, data, headers)
            else:
                raise ValueError(f"不支持的操作类型: {operation_type}")
                
        except Exception as e:
            self.logger.error(f"执行异步操作失败: {e}")
            raise
    
    async def _execute_publish(self, endpoint: Dict[str, Any], params: Dict[str, Any] = None,
                             data: Dict[str, Any] = None, headers: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行发布操作"""
        try:
            channel_name = endpoint.get('channel_name')
            protocol = endpoint.get('protocol')
            servers = endpoint.get('servers', [])
            
            # 获取连接
            connection = await self._get_connection(protocol, servers[0] if servers else None)
            
            # 准备消息
            message = self._prepare_message(endpoint, params, data, headers)
            
            # 发送消息
            result = await self._send_message(connection, channel_name, message, protocol)
            
            return {
                'success': True,
                'operation': 'publish',
                'channel': channel_name,
                'protocol': protocol,
                'message_id': result.get('message_id'),
                'timestamp': datetime.now().isoformat(),
                'data': result
            }
            
        except Exception as e:
            self.logger.error(f"发布操作失败: {e}")
            return {
                'success': False,
                'operation': 'publish',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _execute_subscribe(self, endpoint: Dict[str, Any], params: Dict[str, Any] = None,
                               data: Dict[str, Any] = None, headers: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行订阅操作"""
        try:
            channel_name = endpoint.get('channel_name')
            protocol = endpoint.get('protocol')
            servers = endpoint.get('servers', [])
            
            # 获取连接
            connection = await self._get_connection(protocol, servers[0] if servers else None)
            
            # 设置消息处理器
            handler = data.get('handler') if data else None
            if handler:
                self.message_handlers[channel_name] = handler
            
            # 订阅通道
            subscription = await self._subscribe_channel(connection, channel_name, protocol)
            
            return {
                'success': True,
                'operation': 'subscribe',
                'channel': channel_name,
                'protocol': protocol,
                'subscription_id': subscription.get('subscription_id'),
                'timestamp': datetime.now().isoformat(),
                'data': subscription
            }
            
        except Exception as e:
            self.logger.error(f"订阅操作失败: {e}")
            return {
                'success': False,
                'operation': 'subscribe',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_connection(self, protocol: str, server: Dict[str, Any] = None) -> Any:
        """获取协议连接"""
        connection_key = f"{protocol}_{server.get('name', 'default')}" if server else protocol
        
        if connection_key in self.connections:
            return self.connections[connection_key]
        
        # 创建新连接
        connection = await self._create_connection(protocol, server)
        self.connections[connection_key] = connection
        
        return connection
    
    async def _create_connection(self, protocol: str, server: Dict[str, Any] = None) -> Any:
        """创建协议连接"""
        if protocol == 'websocket':
            return await self._create_websocket_connection(server)
        elif protocol == 'mqtt':
            return await self._create_mqtt_connection(server)
        elif protocol == 'amqp':
            return await self._create_amqp_connection(server)
        elif protocol == 'kafka':
            return await self._create_kafka_connection(server)
        elif protocol == 'nats':
            return await self._create_nats_connection(server)
        else:
            raise ValueError(f"不支持的协议: {protocol}")
    
    async def _create_websocket_connection(self, server: Dict[str, Any] = None) -> Any:
        """创建 WebSocket 连接"""
        try:
            import websockets
            
            url = server.get('url', 'ws://localhost:8080') if server else 'ws://localhost:8080'
            connection = await websockets.connect(url)
            
            self.logger.info(f"WebSocket 连接已建立: {url}")
            return connection
            
        except Exception as e:
            self.logger.error(f"创建 WebSocket 连接失败: {e}")
            raise
    
    async def _create_mqtt_connection(self, server: Dict[str, Any] = None) -> Any:
        """创建 MQTT 连接"""
        try:
            import paho.mqtt.client as mqtt
            
            client = mqtt.Client()
            
            # 设置认证
            if server and 'security' in server:
                # 这里可以添加认证逻辑
                pass
            
            # 连接到服务器
            url = server.get('url', 'localhost') if server else 'localhost'
            port = 1883  # 默认端口
            
            client.connect(url, port)
            client.loop_start()
            
            self.logger.info(f"MQTT 连接已建立: {url}:{port}")
            return client
            
        except Exception as e:
            self.logger.error(f"创建 MQTT 连接失败: {e}")
            raise
    
    async def _create_amqp_connection(self, server: Dict[str, Any] = None) -> Any:
        """创建 AMQP 连接"""
        try:
            import aio_pika
            
            url = server.get('url', 'amqp://localhost') if server else 'amqp://localhost'
            connection = await aio_pika.connect_robust(url)
            
            self.logger.info(f"AMQP 连接已建立: {url}")
            return connection
            
        except Exception as e:
            self.logger.error(f"创建 AMQP 连接失败: {e}")
            raise
    
    async def _create_kafka_connection(self, server: Dict[str, Any] = None) -> Any:
        """创建 Kafka 连接"""
        try:
            from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
            
            bootstrap_servers = server.get('url', 'localhost:9092') if server else 'localhost:9092'
            
            # 创建生产者
            producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
            await producer.start()
            
            self.logger.info(f"Kafka 连接已建立: {bootstrap_servers}")
            return producer
            
        except Exception as e:
            self.logger.error(f"创建 Kafka 连接失败: {e}")
            raise
    
    async def _create_nats_connection(self, server: Dict[str, Any] = None) -> Any:
        """创建 NATS 连接"""
        try:
            import nats
            
            url = server.get('url', 'nats://localhost:4222') if server else 'nats://localhost:4222'
            connection = await nats.connect(url)
            
            self.logger.info(f"NATS 连接已建立: {url}")
            return connection
            
        except Exception as e:
            self.logger.error(f"创建 NATS 连接失败: {e}")
            raise
    
    def _prepare_message(self, endpoint: Dict[str, Any], params: Dict[str, Any] = None,
                        data: Dict[str, Any] = None, headers: Dict[str, Any] = None) -> Dict[str, Any]:
        """准备消息"""
        message = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'channel': endpoint.get('channel_name'),
            'operation': endpoint.get('operation_type'),
            'headers': headers or {},
            'payload': data or {}
        }
        
        # 添加参数
        if params:
            message['params'] = params
        
        # 添加消息模式信息
        request_schema = endpoint.get('request_schema', {})
        if request_schema:
            message['schema'] = request_schema
        
        return message
    
    async def _send_message(self, connection: Any, channel_name: str, 
                          message: Dict[str, Any], protocol: str) -> Dict[str, Any]:
        """发送消息"""
        try:
            message_id = message['id']
            
            if protocol == 'websocket':
                await connection.send(json.dumps(message))
                return {'message_id': message_id, 'status': 'sent'}
                
            elif protocol == 'mqtt':
                connection.publish(channel_name, json.dumps(message))
                return {'message_id': message_id, 'status': 'published'}
                
            elif protocol == 'amqp':
                channel = await connection.channel()
                await channel.default_exchange.publish(
                    aio_pika.Message(body=json.dumps(message).encode()),
                    routing_key=channel_name
                )
                return {'message_id': message_id, 'status': 'published'}
                
            elif protocol == 'kafka':
                await connection.send_and_wait(channel_name, json.dumps(message).encode())
                return {'message_id': message_id, 'status': 'sent'}
                
            elif protocol == 'nats':
                await connection.publish(channel_name, json.dumps(message).encode())
                return {'message_id': message_id, 'status': 'published'}
                
            else:
                raise ValueError(f"不支持的协议: {protocol}")
                
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            raise
    
    async def _subscribe_channel(self, connection: Any, channel_name: str, 
                               protocol: str) -> Dict[str, Any]:
        """订阅通道"""
        try:
            subscription_id = str(uuid.uuid4())
            
            if protocol == 'websocket':
                # WebSocket 订阅通常通过发送订阅消息实现
                subscribe_message = {
                    'type': 'subscribe',
                    'channel': channel_name,
                    'subscription_id': subscription_id
                }
                await connection.send(json.dumps(subscribe_message))
                
            elif protocol == 'mqtt':
                connection.subscribe(channel_name)
                
            elif protocol == 'amqp':
                channel = await connection.channel()
                queue = await channel.declare_queue(channel_name)
                await queue.consume(self._handle_amqp_message)
                
            elif protocol == 'kafka':
                consumer = AIOKafkaConsumer(
                    channel_name,
                    bootstrap_servers='localhost:9092',
                    group_id=f'stepflow-{subscription_id}'
                )
                await consumer.start()
                asyncio.create_task(self._handle_kafka_messages(consumer))
                
            elif protocol == 'nats':
                await connection.subscribe(channel_name, cb=self._handle_nats_message)
                
            else:
                raise ValueError(f"不支持的协议: {protocol}")
            
            self.subscriptions[subscription_id] = {
                'channel': channel_name,
                'protocol': protocol,
                'connection': connection
            }
            
            return {'subscription_id': subscription_id, 'status': 'subscribed'}
            
        except Exception as e:
            self.logger.error(f"订阅通道失败: {e}")
            raise
    
    async def _handle_amqp_message(self, message):
        """处理 AMQP 消息"""
        try:
            body = message.body.decode()
            data = json.loads(body)
            await self._process_message(data)
        except Exception as e:
            self.logger.error(f"处理 AMQP 消息失败: {e}")
    
    async def _handle_kafka_messages(self, consumer):
        """处理 Kafka 消息"""
        try:
            async for message in consumer:
                data = json.loads(message.value.decode())
                await self._process_message(data)
        except Exception as e:
            self.logger.error(f"处理 Kafka 消息失败: {e}")
    
    def _handle_nats_message(self, msg):
        """处理 NATS 消息"""
        try:
            data = json.loads(msg.data.decode())
            asyncio.create_task(self._process_message(data))
        except Exception as e:
            self.logger.error(f"处理 NATS 消息失败: {e}")
    
    async def _process_message(self, data: Dict[str, Any]):
        """处理接收到的消息"""
        try:
            channel_name = data.get('channel')
            if channel_name in self.message_handlers:
                handler = self.message_handlers[channel_name]
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            
            self.logger.info(f"处理消息: {data.get('id')} on {channel_name}")
            
        except Exception as e:
            self.logger.error(f"处理消息失败: {e}")
    
    async def start(self):
        """启动执行器"""
        self.running = True
        self.logger.info("AsyncAPI 执行器已启动")
    
    async def stop(self):
        """停止执行器"""
        self.running = False
        
        # 关闭所有连接
        for connection in self.connections.values():
            try:
                if hasattr(connection, 'close'):
                    await connection.close()
                elif hasattr(connection, 'disconnect'):
                    connection.disconnect()
            except Exception as e:
                self.logger.error(f"关闭连接失败: {e}")
        
        self.connections.clear()
        self.subscriptions.clear()
        self.message_handlers.clear()
        
        self.logger.info("AsyncAPI 执行器已停止")
    
    def add_message_handler(self, channel_name: str, handler: Callable):
        """添加消息处理器"""
        self.message_handlers[channel_name] = handler
        self.logger.info(f"添加消息处理器: {channel_name}")
    
    def remove_message_handler(self, channel_name: str):
        """移除消息处理器"""
        if channel_name in self.message_handlers:
            del self.message_handlers[channel_name]
            self.logger.info(f"移除消息处理器: {channel_name}")
    
    def get_subscriptions(self) -> List[Dict[str, Any]]:
        """获取订阅列表"""
        return [
            {
                'subscription_id': sub_id,
                'channel': info['channel'],
                'protocol': info['protocol']
            }
            for sub_id, info in self.subscriptions.items()
        ]
    
    def get_connections(self) -> List[Dict[str, Any]]:
        """获取连接列表"""
        return [
            {
                'connection_key': key,
                'protocol': key.split('_')[0]
            }
            for key in self.connections.keys()
        ] 