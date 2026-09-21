import time
import asyncio
from typing import Optional, Dict, Any
from ces import MissionState
from drivers.input_driver import input_driver

class ExecutorAgent:
    def __init__(self, kernel):
        self.kernel = kernel
        self.agent_id = "agent_executor"
        self.role = "Physical Input Simulation & HUD Projection"
        self.state = "IDLE"

    async def execute_autotype(self, custom_text: Optional[str] = None):
        """
        Dispatches keystrokes with biological cadence into active window.
        """
        text_to_type = custom_text
        if not text_to_type and self.kernel.ces.current_suggestion:
            # Prefer code snippet if present, otherwise summary or first bullet
            sug = self.kernel.ces.current_suggestion
            if sug.code_snippet:
                text_to_type = sug.code_snippet
            elif sug.summary:
                text_to_type = sug.summary
            elif sug.bullet_points:
                text_to_type = " ".join(sug.bullet_points)

        if not text_to_type:
            self.kernel.broadcast_ws({
                "type": "AUTOTYPE_STATUS",
                "status": "ERROR",
                "message": "No text available to autotype."
            })
            return

        self.state = "INJECTING"
        self.kernel.ces.state = MissionState.INJECTING
        self.kernel.broadcast_ws({
            "type": "MISSION_STATE",
            "state": MissionState.INJECTING
        })
        self.kernel.broadcast_ws({
            "type": "AUTOTYPE_STATUS",
            "status": "IN_PROGRESS",
            "character_count": len(text_to_type)
        })

        # Small 1-second delay so operator can focus the target code/chat window if needed
        await asyncio.sleep(0.8)

        receipt = await input_driver.inject_keystrokes(
            text=text_to_type,
            wpm_target=self.kernel.config.TYPING_WPM
        )

        self.state = "IDLE"
        self.kernel.ces.state = MissionState.LISTENING
        self.kernel.broadcast_ws({
            "type": "MISSION_STATE",
            "state": MissionState.LISTENING
        })
        self.kernel.broadcast_ws({
            "type": "AUTOTYPE_STATUS",
            "status": "COMPLETED",
            "receipt": receipt
        })

    def abort(self):
        input_driver.emergency_abort()
        self.state = "IDLE"
        self.kernel.ces.state = MissionState.LISTENING
        self.kernel.broadcast_ws({
            "type": "AUTOTYPE_STATUS",
            "status": "ABORTED"
        })
