"""
Swarm Engine
Manages a collection of QuartzMarble nodes and emergent behaviors.
"""

from __future__ import annotations
import math
import random
from typing import List, Dict, Tuple, Optional
from .marble import QuartzMarble, ArgonCore


class Swarm:
    def __init__(self, n_nodes: int = 50, space_size: float = 10.0):
        self.nodes: Dict[str, QuartzMarble] = {}
        self.space_size = space_size
        self.ambient_temp = 298.15
        self.tick = 0
        self._spawn_nodes(n_nodes)

    def _spawn_nodes(self, n: int):
        for _ in range(n):
            pos = (
                random.uniform(0, self.space_size),
                random.uniform(0, self.space_size),
                random.uniform(0, self.space_size),
            )
            m = QuartzMarble(position=pos)
            self.nodes[m.id] = m
        self._update_neighbors()

    def _update_neighbors(self, radius: float = 2.5):
        ids = list(self.nodes.keys())
        for i, id_a in enumerate(ids):
            a = self.nodes[id_a]
            a.neighbors = []
            for id_b in ids[i+1:]:
                b = self.nodes[id_b]
                if a.distance_to(b) < radius:
                    a.neighbors.append(id_b)
                    b.neighbors.append(id_a)

    def stigmergic_step(self):
        """Indirect communication via environmental modification."""
        # Each node leaves a 'trace' in local field based on its state
        fields: Dict[str, float] = {}
        for nid, node in self.nodes.items():
            if node.health < 0.05:
                continue
            emission = node.emit_photon(0.3 + random.random() * 0.2)
            fields[nid] = emission * node.core.ionization

        # Nodes sense neighbors' traces
        for nid, node in self.nodes.items():
            local_field = 0.0
            for neigh_id in node.neighbors:
                local_field += fields.get(neigh_id, 0.0)
            avg_field = local_field / max(1, len(node.neighbors))
            node.sense_environment(self.ambient_temp, avg_field)

            # Simple flocking / cohesion response
            if node.neighbors and node.health > 0.3:
                cx = cy = cz = 0.0
                for neigh_id in node.neighbors:
                    n = self.nodes[neigh_id]
                    cx += n.position[0]
                    cy += n.position[1]
                    cz += n.position[2]
                n_count = len(node.neighbors)
                target = (cx / n_count, cy / n_count, cz / n_count)
                # Soft attraction
                dx = (target[0] - node.position[0]) * 0.01
                dy = (target[1] - node.position[1]) * 0.01
                dz = (target[2] - node.position[2]) * 0.01
                node.position = (
                    node.position[0] + dx,
                    node.position[1] + dy,
                    node.position[2] + dz,
                )

    def self_heal(self):
        """Detect failed nodes and reinforce neighbors."""
        for node in self.nodes.values():
            if node.health < 0.2:
                # Neighbors try to compensate / heal locally
                for neigh_id in node.neighbors:
                    neigh = self.nodes[neigh_id]
                    if neigh.health > 0.6:
                        neigh.heal(0.02)
                        # Slight energy cost
                        neigh.core.temperature += 1.5
            else:
                # Natural slow recovery if not critically damaged
                if random.random() < 0.1:
                    node.heal(0.01)

    def optical_compute_step(self) -> float:
        """Simulate a crude parallel optical multiply-accumulate across a path."""
        active = [n for n in self.nodes.values() if n.health > 0.4]
        if len(active) < 3:
            return 0.0
        # Pick a short chain
        chain = random.sample(active, min(5, len(active)))
        signal = 1.0
        for node in chain:
            signal *= (0.5 + node.core.ionization * 0.5)
            signal = node.emit_photon(signal * 0.2) + signal * 0.8
        return signal

    def step(self):
        self.tick += 1
        self.stigmergic_step()
        if self.tick % 5 == 0:
            self.self_heal()
            self._update_neighbors()
        # Occasional random stress / damage
        if random.random() < 0.05:
            victim = random.choice(list(self.nodes.values()))
            victim.degrade(random.uniform(0.05, 0.2))
            victim.apply_stress(random.uniform(1.0, 5.0))

    def status(self) -> dict:
        healths = [n.health for n in self.nodes.values()]
        ionizations = [n.core.ionization for n in self.nodes.values()]
        return {
            "tick": self.tick,
            "n_nodes": len(self.nodes),
            "avg_health": sum(healths) / len(healths),
            "avg_ionization": sum(ionizations) / len(ionizations),
            "alive": sum(1 for h in healths if h > 0.1),
            "optical_signal": self.optical_compute_step(),
        }
