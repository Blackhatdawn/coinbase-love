#!/usr/bin/env python3
"""
Socket.IO Client Test for CryptoVault
Tests direct Socket.IO connectivity and real-time price updates
"""

import socketio
import asyncio
import time
import json
from datetime import datetime

class CryptoVaultSocketIOTester:
    def __init__(self, server_url: str = "https://cryptovault-api.onrender.com"):
        self.server_url = server_url
        self.sio = None
        self.connected = False
        self.messages_received = []
        self.connection_events = []
        
    async def connect_and_test(self):
        """Connect to Socket.IO server and test functionality"""
        print(f"🔌 Connecting to Socket.IO server: {self.server_url}")
        
        # Create Socket.IO client
        self.sio = socketio.AsyncClient(
            reconnection=True,
            reconnection_attempts=3,
            reconnection_delay=1,
            logger=False,
            engineio_logger=False
        )
        
        # Setup event handlers
        self.setup_handlers()
        
        try:
            # Connect to server
            await self.sio.connect(
                self.server_url,
                socketio_path='/socket.io/',
                transports=['websocket', 'polling']
            )
            
            # Wait for connection confirmation
            await asyncio.sleep(2)
            
            if self.sio.connected:
                print("✅ Successfully connected to Socket.IO server")
                self.connected = True
                
                # Test ping-pong
                await self.test_ping()
                
                # Subscribe to price updates
                await self.test_price_subscription()
                
                # Wait for some messages
                await asyncio.sleep(10)
                
                # Test stats
                await self.test_stats()
                
                return True
            else:
                print("❌ Failed to connect to Socket.IO server")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
        finally:
            if self.sio and self.sio.connected:
                await self.sio.disconnect()
                print("🔌 Disconnected from Socket.IO server")
    
    def setup_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        async def connect():
            print("🟢 Socket.IO connected")
            self.connection_events.append(("connect", datetime.now()))
        
        @self.sio.event
        async def disconnect():
            print("🔴 Socket.IO disconnected")
            self.connection_events.append(("disconnect", datetime.now()))
        
        @self.sio.event
        async def connected(data):
            print(f"✅ Server welcome: {data}")
            self.messages_received.append(("connected", data))
        
        @self.sio.event
        async def pong(data):
            print(f"🏓 Pong received: {data}")
            self.messages_received.append(("pong", data))
        
        @self.sio.event
        async def price_update(data):
            print(f"💰 Price update received: {len(data.get('prices', {}))} prices")
            self.messages_received.append(("price_update", data))
        
        @self.sio.event
        async def subscribed(data):
            print(f"📡 Subscribed to channels: {data}")
            self.messages_received.append(("subscribed", data))
    
    async def test_ping(self):
        """Test ping-pong functionality"""
        print("🏓 Testing ping-pong...")
        try:
            await self.sio.emit('ping')
            await asyncio.sleep(1)
            print("✅ Ping sent successfully")
        except Exception as e:
            print(f"❌ Ping failed: {e}")
    
    async def test_price_subscription(self):
        """Test price channel subscription"""
        print("📡 Testing price channel subscription...")
        try:
            await self.sio.emit('subscribe', {'channels': ['prices']})
            await asyncio.sleep(1)
            print("✅ Price subscription sent")
        except Exception as e:
            print(f"❌ Subscription failed: {e}")
    
    async def test_stats(self):
        """Test getting server stats via HTTP"""
        print("📊 Checking server stats...")
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.server_url}/api/socketio/stats") as resp:
                    if resp.status == 200:
                        stats = await resp.json()
                        print(f"✅ Stats retrieved: {stats}")
                        return stats
                    else:
                        print(f"❌ Stats request failed: {resp.status}")
        except Exception as e:
            print(f"❌ Stats request error: {e}")
        return None
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📋 SOCKET.IO TEST SUMMARY")
        print("="*60)
        print(f"🔗 Server URL: {self.server_url}")
        print(f"📡 Connection Status: {'✅ Connected' if self.connected else '❌ Failed'}")
        print(f"📨 Messages Received: {len(self.messages_received)}")
        print(f"🔄 Connection Events: {len(self.connection_events)}")
        
        if self.messages_received:
            print("\n📬 MESSAGES RECEIVED:")
            for msg_type, data in self.messages_received:
                print(f"  - {msg_type}: {str(data)[:100]}...")
        
        if self.connection_events:
            print("\n🔄 CONNECTION EVENTS:")
            for event, timestamp in self.connection_events:
                print(f"  - {event} at {timestamp}")
        
        print("="*60)

async def main():
    print("🚀 Starting Socket.IO Client Test")
    print("🎯 Testing CryptoVault real-time connectivity")
    print("-" * 60)
    
    tester = CryptoVaultSocketIOTester()
    
    # Run the test
    success = await tester.connect_and_test()
    
    # Print summary
    tester.print_summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        import asyncio
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        exit(1)