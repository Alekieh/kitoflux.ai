from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional, Callable, Coroutine, Dict, Any

class BaseLLMDriver(ABC):
    @abstractmethod
    async def stream_reasoning(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        context_chunks: List[str]
    ) -> AsyncIterator[str]:
        pass

class BaseInputDriver(ABC):
    @abstractmethod
    async def inject_keystrokes(
        self, 
        text: str, 
        target_hwnd: Optional[int] = None,
        wpm_target: int = 85
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def emergency_abort(self) -> None:
        pass
