# AsyncIO Event Loop Error Fix

## Issue
On application startup, the following errors appeared:
```
Failed to get models: <asyncio.locks.Event object at 0x000002161FC82210 [unset]> is bound to a different event loop
```

## Root Cause
There were two issues causing event loop conflicts:

1. **Multiple Event Loops**: The application was using `asyncio.run(main())` which creates its own event loop, but then inside main() it was creating a QEventLoop. This resulted in multiple event loops competing.

2. **HTTP Client Binding**: The httpx.AsyncClient and its internal event objects were being bound to one event loop but used in another.

## Solution
Implemented a two-part fix:

### 1. Fixed Event Loop Creation in main.py
Changed from:
```python
async def main():
    # ... setup code ...
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    # ...

# This creates an extra event loop!
asyncio.run(main())
```

To:
```python
def main():  # Not async anymore
    # ... setup code ...
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Schedule async initialization
    asyncio.ensure_future(init_app())
    
    with loop:
        loop.run_forever()

# No asyncio.run() - just call main()
main()
```

### 2. Enhanced HTTP Client Management in comfyui_client.py
- **Lazy initialization**: Set `self.http_client = None` in `__init__`
- **Event loop tracking**: Track which event loop the client was created in
- **Smart recreation**: If event loop changes, close old client and create new one

### Key Changes in comfyui_client.py:

```python
async def _ensure_http_client(self):
    """Ensure HTTP client exists in the current event loop"""
    try:
        current_loop = asyncio.get_running_loop()
        if not hasattr(self, '_last_loop') or self._last_loop != current_loop:
            if self.http_client:
                await self.http_client.aclose()
            self.http_client = httpx.AsyncClient(timeout=60.0)
            self._last_loop = current_loop
        elif self.http_client is None or self.http_client.is_closed:
            self.http_client = httpx.AsyncClient(timeout=60.0)
    except Exception as e:
        self.logger.error(f"Error ensuring HTTP client: {e}")
        self.http_client = httpx.AsyncClient(timeout=60.0)
```

## Result
- No more event loop binding errors on startup
- Single QEventLoop managed by qasync
- HTTP client is created in the correct event loop context
- All async operations work properly without conflicts

## Lessons Learned
1. Don't mix `asyncio.run()` with manual event loop creation
2. When using qasync, let it manage the event loop entirely
3. Always track which event loop async resources are created in
4. Recreate resources if the event loop changes