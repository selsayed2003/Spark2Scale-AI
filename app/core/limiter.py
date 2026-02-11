import asyncio

# Allow only 2 concurrent LLM calls to stay safe under the 10 RPM limit
# If you upgrade your plan, you can increase this to 5 or 10.
concurrency_limiter = asyncio.Semaphore(1)