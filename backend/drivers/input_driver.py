import asyncio
import random
import time
import sys
from typing import Optional, Dict, Any
from drivers.base import BaseInputDriver

# Adjacent QWERTY keys for realistic typo simulation
QWERTY_NEIGHBORS = {
    'a': 'qwsz', 'b': 'vghn', 'c': 'xdfv', 'd': 'serfcx', 'e': 'wsdr',
    'f': 'drtgvc', 'g': 'ftyhbv', 'h': 'gyujnb', 'i': 'ujko', 'j': 'huknmi',
    'k': 'jilmo', 'l': 'kop', 'm': 'njk', 'n': 'bhjm', 'o': 'iklp',
    'p': 'ol', 'q': 'wa', 'r': 'edft', 's': 'awedxz', 't': 'rfgy',
    'u': 'yhij', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc', 'y': 'tghu',
    'z': 'asx'
}

class HumanizedInputDriver(BaseInputDriver):
    def __init__(self, target_wpm: int = 85, typo_rate: float = 0.015):
        self.target_wpm = target_wpm
        self.typo_rate = typo_rate
        self.abort_requested = False
        self.is_windows = sys.platform.startswith("win")
        self._init_os_handles()

    def _init_os_handles(self):
        self.keyboard_controller = None
        try:
            from pynput.keyboard import Controller
            self.keyboard_controller = Controller()
        except Exception:
            pass

    def emergency_abort(self):
        self.abort_requested = True

    def _get_gaussian_delay(self) -> float:
        """Calculate biological keystroke delay based on target WPM (5 chars = 1 word)."""
        # avg characters per second = (target_wpm * 5) / 60
        # mean delay = 1.0 / cps
        mean_delay = 60.0 / (self.target_wpm * 5.0)
        std_dev = mean_delay * 0.25
        delay = random.gauss(mean_delay, std_dev)
        return max(0.035, min(0.300, delay))

    async def inject_keystrokes(
        self, 
        text: str, 
        target_hwnd: Optional[int] = None,
        wpm_target: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes biological keystroke cadence injection.
        Simulates natural human typing with variable micro-pauses, digraph fluency,
        and occasional self-correcting typos.
        """
        self.abort_requested = False
        if wpm_target:
            self.target_wpm = wpm_target

        start_time = time.time()
        typed_count = 0
        typos_corrected = 0

        for char in text:
            if self.abort_requested:
                break

            # 1. Stochastic typo injection
            if char.isalpha() and random.random() < self.typo_rate:
                lower = char.lower()
                neighbors = QWERTY_NEIGHBORS.get(lower, "")
                if neighbors:
                    typo_char = random.choice(neighbors)
                    if char.isupper():
                        typo_char = typo_char.upper()
                    
                    # Type erroneous character
                    self._press_key(typo_char)
                    typed_count += 1
                    
                    # Human cognitive reaction latency before realizing mistake (180ms - 320ms)
                    await asyncio.sleep(random.uniform(0.18, 0.32))
                    
                    # Backspace to erase mistake
                    self._send_backspace()
                    await asyncio.sleep(self._get_gaussian_delay())
                    typos_corrected += 1

            # 2. Type intended character
            self._press_key(char)
            typed_count += 1

            # 3. Micro-pause after punctuation or words
            delay = self._get_gaussian_delay()
            if char in ".?!":
                delay += random.uniform(0.20, 0.45)
            elif char in ",;":
                delay += random.uniform(0.10, 0.22)
            elif char == " ":
                delay += random.uniform(0.04, 0.09)

            await asyncio.sleep(delay)

        elapsed = time.time() - start_time
        effective_wpm = (typed_count / 5.0) / (elapsed / 60.0) if elapsed > 0 else 0

        return {
            "characters_typed": typed_count,
            "typos_corrected": typos_corrected,
            "elapsed_seconds": round(elapsed, 2),
            "effective_wpm": round(effective_wpm, 1),
            "aborted": self.abort_requested
        }

    def _press_key(self, char: str):
        if self.keyboard_controller:
            try:
                self.keyboard_controller.type(char)
            except Exception:
                pass

    def _send_backspace(self):
        if self.keyboard_controller:
            try:
                from pynput.keyboard import Key
                self.keyboard_controller.press(Key.backspace)
                self.keyboard_controller.release(Key.backspace)
            except Exception:
                pass

input_driver = HumanizedInputDriver()
