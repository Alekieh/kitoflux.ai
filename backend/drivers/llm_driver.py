import json
import asyncio
import os
import aiohttp
from typing import AsyncIterator, List
from config import config
from drivers.base import BaseLLMDriver

class LLMDriver(BaseLLMDriver):
    def __init__(self):
        self.provider = config.LLM_PROVIDER
        self.groq_key = config.GROQ_API_KEY
        self.openai_key = config.OPENAI_API_KEY
        self.groq_model = config.GROQ_MODEL
        self.openai_model = config.OPENAI_MODEL

    async def stream_reasoning(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        context_chunks: List[str]
    ) -> AsyncIterator[str]:
        """
        Streams reasoning tokens using Groq (primary low-latency) or OpenAI.
        Falls back to local mock streaming if no API keys are present, enabling instant testing.
        """
        context_block = "\n\n".join([f"[RELEVANT CONTEXT CHUNK {i+1}]:\n{c}" for i, c in enumerate(context_chunks)])
        full_system = f"{system_prompt}\n\n{context_block}" if context_chunks else system_prompt

        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": user_prompt}
        ]

        if self.groq_key and (self.provider == "groq" or not self.openai_key):
            async for chunk in self._stream_groq(messages):
                yield chunk
        elif self.openai_key:
            async for chunk in self._stream_openai(messages):
                yield chunk
        else:
            # Fallback mock engine for out-of-the-box local verification
            async for chunk in self._stream_fallback(user_prompt, context_chunks):
                yield chunk

    async def _stream_groq(self, messages: list) -> AsyncIterator[str]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.groq_model,
            "messages": messages,
            "stream": True,
            "temperature": 0.2,
            "max_tokens": 1024
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    err_text = await resp.text()
                    yield f"[Groq Error {resp.status}]: {err_text}"
                    return
                
                async for line in resp.content:
                    line_str = line.decode("utf-8").strip()
                    if line_str.startswith("data: ") and line_str != "data: [DONE]":
                        try:
                            data = json.loads(line_str[6:])
                            delta = data["choices"][0]["delta"]
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue

    async def _stream_openai(self, messages: list) -> AsyncIterator[str]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.openai_model,
            "messages": messages,
            "stream": True,
            "temperature": 0.2,
            "max_tokens": 1024
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    err_text = await resp.text()
                    yield f"[OpenAI Error {resp.status}]: {err_text}"
                    return

                async for line in resp.content:
                    line_str = line.decode("utf-8").strip()
                    if line_str.startswith("data: ") and line_str != "data: [DONE]":
                        try:
                            data = json.loads(line_str[6:])
                            delta = data["choices"][0]["delta"]
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue

    async def _stream_fallback(self, query: str, context_chunks: List[str]) -> AsyncIterator[str]:
        """Provides simulated tactical response tokens when API key is not yet configured."""
        yield "**Strategic Takeaway:** Structured architectural response ready.\n\n"
        await asyncio.sleep(0.05)
        yield "* **Core Technical Concept:** Address the trade-off directly (consistency vs. latency).\n"
        await asyncio.sleep(0.04)
        yield "* **Real-World Reference:** Cite production experience with horizontal partitioning and replication.\n"
        await asyncio.sleep(0.04)
        if context_chunks:
            yield f"* **Resume Grounding:** Drawing from pre-loaded context ({len(context_chunks)} matching nodes).\n"
        await asyncio.sleep(0.04)
        yield "\n```python\n# Suggested algorithm outline\ndef handle_consensus(quorum, state):\n    return state.commit() if quorum.majority_ack() else state.rollback()\n```\n"

llm_driver = LLMDriver()
