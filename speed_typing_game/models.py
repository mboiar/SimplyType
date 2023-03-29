"""
Classes:

    Wordset: contains words
    TypingGame: represents typing game state

"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import time
from collections import Counter
import random


class Wordset:
    """A named set with unique words from certain language and difficulty."""
    def __init__(self, name) -> None:
        self.name = name
        self.language = language
        self.difficulty = difficulty
        self.words = words

    def __str__(self) -> str:
        return f"Wordset {self.name} - {self.language} - {self.difficulty} - {len(self.words)} words"
    
    def get_subset_with_repetitions(self, count: int, seed: int = None) -> Tuple[str]:
        """Ranomly generate a tuple of words from this wordset, with words possibly repeating themselves."""
        word_pool = tuple(self.words)
        SeededRandom = random.Random(seed)
        indices = sorted(SeededRandom.choices(range(len(word_pool)), k=count))
        return tuple(word_pool[i] for i in indices)


class TypingGame:
    def __init__(
            self,
            wordset: Wordset, 
            seed: int = time.time(),
            mode: str = "default", 
            duration: int = 30
    ) -> None:
        self.seed = seed
        self.wordset = wordset
        self.text = self.wordset.get_subset_with_repetitions(100, self.seed)
        self.pos = 0
        self.mode = 0
        self.duration = duration
        self.incorrect_chars = Counter()
        self.in_progress = False
        self.start_time = 0
        self.elapsed = 0
        self.last_paused = 0
        self.logger = logging.getLogger(__name__)

    def __str__(self) -> str:
        return f"Game: wordset {self.wordset}, seed {self.seed}, mode {self.mode}, duration {self.duration}"

    def start_or_resume(self) -> bool:
        if self.in_progress or self.is_finished():
            self.logger.warning("Unable to start: game in progress or finished")
            return False
        if not self.start_time:
            self.start_time = time.time()
        self.in_progress = True
        self.logger.info(f"Started/resumed game {self}")
        return True

    def finish_or_pause(self) -> bool:
        if not self.in_progress or self.is_finished():
            self.logger.warning("Unable to pause: game not in progress or finished")
            return False
        pause_time = time.time()
        self.elapsed += pause_time - self.last_paused
        self.last_paused = pause_time
        self.in_progress = False
        return True

    def get_word_count(self) -> int:
        return len(self.text[:self.pos].split())
    
    def get_wpm(self) -> float:
        if self.elapsed:
            return self.get_word_count()/self.elapsed
        else:
            return None
        
    def get_accuracy(self):
        return (self.pos - sum(self.incorrect_chars.values())) / self.pos
    
    def get_incorrect_char_freq(self):
        return self.incorrect_chars.items()
    
    def is_finished(self) -> bool:
        return self.elapsed > self.duration
    
    def get_stats(self) -> Dict:
        return {
            "duration": self.duration,
            "elapsed": self.elapsed, 
            "wpm": self.get_wpm(),
            "incorrect characters frequency": self.get_incorrect_char_freq(),
            "accuracy": self.get_accuracy(),
            "last character position": self.pos
        }
    
    def save(self) -> bool:
        pass
