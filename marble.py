"""
Quartz Marble Node
Represents a single argon-trapped quartz sphere in the swarm.
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import uuid


@dataclass
class ArgonCore:
    """Sealed argon micro-plasma / dielectric core."""
    pressure: float = 1.0          # relative units
    ionization: float = 0.0        # 0.0 – 1.0
    temperature: float = 300.0     # Kelvin
    refractive_index: float = 1.0003

    def excite(self, energy: float) -> float:
        """Apply electromagnetic/thermal excitation. Returns emitted photon intensity."""
        self.ionization = min(1.0, self.ionization + energy * 0.3)
        self.temperature += energy * 5.0
        emission = self.ionization * (self.temperature / 400.0)
        # Natural decay
        self.ionization *= 0.92
        self.temperature = 300.0 + (self.temperature - 300.0) * 0.85
        return max(0.0, emission)

    def thermal_gradient_effect(self, ambient: float) -> float:
        delta = self.temperature - ambient
        self.temperature += (ambient - self.temperature) * 0.05
        return delta


@dataclass
class QuartzMarble:
    """A single node in the swarm."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    core: ArgonCore = field(default_factory=ArgonCore)
    resonance_freq: float = 1.0e6   # Hz baseline
    piezoelectric_charge: float = 0.0
    neighbors: List[str] = field(default_factory=list)
    local_memory: dict = field(default_factory=dict)
    health: float = 1.0             # 0.0 = failed, 1.0 = perfect

    def distance_to(self, other: "QuartzMarble") -> float:
        dx = self.position[0] - other.position[0]
        dy = self.position[1] - other.position[1]
        dz = self.position[2] - other.position[2]
        return math.sqrt(dx*dx + dy*dy + dz*dz)

    def apply_stress(self, force: float) -> float:
        """Piezoelectric response: stress generates charge."""
        self.piezoelectric_charge += force * 0.1 * self.health
        self.resonance_freq += force * 100.0
        return self.piezoelectric_charge

    def emit_photon(self, energy: float = 0.5) -> float:
        if self.health < 0.1:
            return 0.0
        return self.core.excite(energy * self.health)

    def sense_environment(self, ambient_temp: float, local_field: float) -> dict:
        thermal = self.core.thermal_gradient_effect(ambient_temp)
        self.local_memory["last_thermal"] = thermal
        self.local_memory["local_field"] = local_field
        return {
            "thermal_delta": thermal,
            "ionization": self.core.ionization,
            "charge": self.piezoelectric_charge,
            "health": self.health,
        }

    def degrade(self, amount: float = 0.01):
        """Simulate wear or damage."""
        self.health = max(0.0, self.health - amount)

    def heal(self, amount: float = 0.05):
        self.health = min(1.0, self.health + amount)
