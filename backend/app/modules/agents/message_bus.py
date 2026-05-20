"""
NOVA AI — Agent Message Bus & Shared State Manager
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
High-performance asynchronous coordination bus enabling Priority Queuing,
Event Broadcasting, Request-Response mapping, and version-controlled Shared State.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Set

logger = logging.getLogger("nova.agents.bus")


class AgentMessage:
    """Standardized message model for inter-agent communication."""

    def __init__(self, sender: str, receiver: str, topic: str,
                 payload: Dict[str, Any], priority: int = 1,
                 correlation_id: Optional[str] = None):
        self.sender = sender
        self.receiver = receiver
        self.topic = topic
        self.payload = payload
        self.priority = priority  # Higher priority messages processed first (e.g., 5 = Critical, 1 = Routine)
        self.correlation_id = correlation_id or f"corr_{sender}_{datetime.now().timestamp()}"
        self.timestamp = datetime.now()

    def __lt__(self, other: "AgentMessage"):
        # Enables priority queuing
        return self.priority > other.priority

    def __repr__(self):
        return f"<AgentMessage sender={self.sender} receiver={self.receiver} topic={self.topic} priority={self.priority}>"


class AgentMessageBus:
    """
    Publish-Subscribe & Request-Response Event Broker for specialized agents.
    Provides priority queues, asynchronous message loops, and timeout-based requests.
    """

    def __init__(self):
        self._subscriptions: Dict[str, Set[Callable]] = {}
        self._pending_responses: Dict[str, asyncio.Future] = {}
        self._queue = asyncio.PriorityQueue()
        self._running = False
        self._dispatch_task: Optional[asyncio.Task] = None

    async def start(self):
        """Starts the background message dispatch loop."""
        if not self._running:
            self._running = True
            self._dispatch_task = asyncio.create_task(self._dispatch_loop())
            logger.info("Agent Message Bus: Dispatched async event loop started")

    async def stop(self):
        """Stops the message dispatch loop cleanly."""
        self._running = False
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
            logger.info("Agent Message Bus: Dispatched async event loop stopped")

    def subscribe(self, topic: str, callback: Callable):
        """Subscribes an agent callback handler to an event topic."""
        if topic not in self._subscriptions:
            self._subscriptions[topic] = set()
        self._subscriptions[topic].add(callback)
        logger.debug(f"Message Bus: Registered subscription for topic '{topic}'")

    def unsubscribe(self, topic: str, callback: Callable):
        """Unsubscribes a callback handler from a topic."""
        if topic in self._subscriptions:
            self._subscriptions[topic].discard(callback)

    async def publish(self, message: AgentMessage):
        """Publishes a message to the priority queue for asynchronous delivery."""
        await self._queue.put(message)
        logger.debug(f"Message Bus: Queued message topic '{message.topic}' from '{message.sender}'")

    async def send_request(self, message: AgentMessage, timeout: float = 15.0) -> AgentMessage:
        """
        Sends a request to another agent and suspends execution until a matching response
        is returned or the operation times out.
        """
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_responses[message.correlation_id] = future
        
        await self.publish(message)
        
        try:
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
        except asyncio.TimeoutError:
            logger.error(f"Message Bus: Request '{message.topic}' from '{message.sender}' timed out after {timeout}s")
            raise TimeoutError(f"Agent Request timeout for correlation ID: {message.correlation_id}")
        finally:
            self._pending_responses.pop(message.correlation_id, None)

    async def send_response(self, request_msg: AgentMessage, payload: Dict[str, Any], sender: str):
        """Dispatches a response back to the waiting sender of a request."""
        response_msg = AgentMessage(
            sender=sender,
            receiver=request_msg.sender,
            topic=f"{request_msg.topic}.response",
            payload=payload,
            priority=request_msg.priority,
            correlation_id=request_msg.correlation_id
        )
        # Bypasses queue for direct high-speed request resolution
        future = self._pending_responses.get(request_msg.correlation_id)
        if future and not future.done():
            future.set_result(response_msg)
            logger.debug(f"Message Bus: Resolved request correlation ID: {request_msg.correlation_id}")
        else:
            await self.publish(response_msg)

    async def _dispatch_loop(self):
        """Background dispatcher extracting prioritized messages and routing to subscribers."""
        while self._running:
            try:
                message = await self._queue.get()
                topic = message.topic
                
                # Deliver to registered topic subscribers
                callbacks = list(self._subscriptions.get(topic, []))
                # Also deliver to wildcard topic subscribers if applicable
                wildcard_callbacks = list(self._subscriptions.get("*", []))
                
                for cb in callbacks + wildcard_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(cb):
                            asyncio.create_task(cb(message))
                        else:
                            cb(message)
                    except Exception as e:
                        logger.error(f"Message Bus subscription callback failed: {e}")
                        
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message Bus dispatcher encountered error: {e}")
                await asyncio.sleep(0.1)


class SharedStateManager:
    """
    Version-controlled, thread-safe Shared Working Memory for dynamic agent collaboration.
    Ensures conflict-safe state modifications across concurrent agent executions.
    """

    def __init__(self):
        self._lock = asyncio.Lock()
        self._state: Dict[str, Any] = {}
        self._version = 0
        self._change_listeners: Set[Callable] = set()

    async def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a state variable from shared memory."""
        async with self._lock:
            return self._state.get(key, default)

    async def get_all(self) -> Dict[str, Any]:
        """Returns a snapshot of the entire active state."""
        async with self._lock:
            return dict(self._state)

    async def set(self, key: str, value: Any, author: str = "system"):
        """Sets a state variable, increments versioning, and notifies active observers."""
        async with self._lock:
            self._state[key] = value
            self._version += 1
            logger.debug(f"Shared State [v{self._version}]: '{key}' updated to {value} by author '{author}'")
            
        # Trigger event listeners
        for listener in self._change_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    asyncio.create_task(listener(key, value, author, self._version))
                else:
                    listener(key, value, author, self._version)
            except Exception as e:
                logger.error(f"Shared State change listener notification failed: {e}")

    def register_change_listener(self, callback: Callable):
        """Subscribes a listener to receive state mutation notifications."""
        self._change_listeners.add(callback)

    def unregister_change_listener(self, callback: Callable):
        """Unsubscribes a state mutation listener."""
        self._change_listeners.discard(callback)

    @property
    def version(self) -> int:
        return self._version
