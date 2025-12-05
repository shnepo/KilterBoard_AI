import random
import math
import parsing # Need this import for _mutate
from typing import List, Dict
from route_representation import Route, Hold

class GeneticRouteGenerator:
    def __init__(self, hold_dataset: Dict[int, Hold]):
        self.holds = hold_dataset
        self.population_size = 24  
        self.mutation_rate = 0.2
        self.holds_map = self.holds # Alias for clarity
        
    def init_population(self, difficulty: float, style: dict) -> List[Route]:
        """
        Creates the first generation. Each route's length is randomized 
        around a target based on the input difficulty.
        """
        pop = []
        for _ in range(self.population_size):
            
            target_base_len = self._get_target_length(difficulty)
            
            # Introduce +/- 2 moves variation to ensure different starting lengths
            route_len = max(4, target_base_len + random.randint(-2, 2)) 
            
            route_ids = self._create_random_route_ids(route_len, style)
            r = Route(holds=route_ids, hold_objects=self.holds_map)
            pop.append(r)
        return pop
    
    def _get_target_length(self, difficulty: float) -> int:
        """
        Maps normalized difficulty (0.0 to 1.0) to a target route length.
        Harder routes (higher difficulty) require more moves.
        """
        # V0 (0.0) -> Base 5 moves
        # V15 (1.0) -> Max 15 moves
        base_length = 5
        max_increase = 10
        return base_length + int(difficulty * max_increase)

    # ... (evolve method remains largely the same) ...
    def evolve(self, current_pop: List[Route], favorites_indices: List[int], difficulty: float, style: dict) -> List[Route]:
        """
        The main GA evolution step: Selection -> Crossover -> Mutation.
        """
        # 1. Calculate Hybrid Fitness (Machine + Human)
        scored_pop = []
        for i, route in enumerate(current_pop):
            m_fitness = self._machine_fitness(route, style, difficulty)
            human_boost = 1.0 if i in favorites_indices else 0.0
            A = 0.7 
            C = 0.3 
            total_score = (A * human_boost) + (C * m_fitness)
            scored_pop.append((route, total_score))
            
        scored_pop.sort(key=lambda x: x[1], reverse=True)
        
        # 2. Selection (Elitism)
        next_gen = []
        elite_size = 4
        
        for i in range(min(elite_size, len(scored_pop))):
            next_gen.append(scored_pop[i][0])
        
        # 3. Crossover and Mutation
        pool = [x[0] for x in scored_pop[:12]]
        
        while len(next_gen) < self.population_size:
            p1 = random.choice(pool)
            p2 = random.choice(pool)
            
            child_ids = self._crossover(p1.holds, p2.holds)
            
            if random.random() < self.mutation_rate:
                child_ids = self._mutate(child_ids, style)
                
            child = Route(holds=child_ids, hold_objects=self.holds_map)
            next_gen.append(child)
            
        return next_gen


    def _machine_fitness(self, route: Route, style: dict, difficulty: float) -> float:
        # ... (fitness logic remains the same) ...
        if len(route.holds) < 3: return 0.0
        
        score = 0.5
        dists = []
        vertical_gain = route.hold_objects[route.holds[-1]].y - route.hold_objects[route.holds[0]].y
        
        # 1. Analyze Move Distances and Vertical Progress
        for i in range(len(route.holds) - 1):
            h1 = self.holds[route.holds[i]]
            h2 = self.holds[route.holds[i+1]]
            d = math.sqrt((h1.x - h2.x)**2 + (h1.y - h2.y)**2)
            dists.append(d)
            
            if h2.y < h1.y - 0.05: score -= 0.1
            if d < style["reach_min"] or d > style["reach_max"]: score -= 0.05
                
        # 2. Style Consistency (Variance)
        if dists:
            avg_dist = sum(dists) / len(dists)
            target = style.get("avg_move_dist", 0.18)
            score -= abs(avg_dist - target) * style["variance_penalty"] * 0.1
        
        # 3. Reward Total Vertical Gain
        score += vertical_gain * 0.1 

        # 4. Penalty for being too short/long relative to target difficulty
        target_len = self._get_target_length(difficulty)
        length_deviation = abs(len(route.holds) - target_len)
        score -= length_deviation * 0.05 

        return max(0.0, min(1.0, score))

    def _create_random_route_ids(self, length: int, style: dict) -> List[int]:
        # Start at bottom quarter of the board
        start_holds = [h for h, obj in self.holds_map.items() if obj.y < 0.25]
        if not start_holds: return []
        
        current = random.choice(start_holds)
        route = [current]
        
        for _ in range(length - 1):
            possible = self._get_reachable_holds(current, style)
            
            if not possible: break
            
            # --- START OF FIX: STOCHASTIC SELECTION ---
            
            # 1. Calculate weights: Higher Y-value = higher weight
            hold_weights = []
            current_y = self.holds_map[current].y
            
            for hid in possible:
                h = self.holds_map[hid]
                
                # Progress is difference in Y. Max progress is 1.0 (normalized)
                progress = h.y - current_y 
                
                # Weight = Base (0.5) + Progress bonus (0 to 0.5). Ensures variety but rewards upward movement.
                weight = 0.5 + max(0, progress * 2.0)
                hold_weights.append(weight)

            # 2. Select next hold using calculated weights
            nxt = random.choices(possible, weights=hold_weights, k=1)[0]
            # --- END OF FIX ---

            route.append(nxt)
            current = nxt
            
        return route

    def _get_reachable_holds(self, current_id: int, style: dict) -> List[int]:
        curr = self.holds_map[current_id]
        candidates = []
        
        min_dist = style["reach_min"]
        max_dist = style["reach_max"]
        
        for hid, h in self.holds_map.items():
            if hid == current_id: continue
            
            dx = h.x - curr.x
            dy = h.y - curr.y
            dist = math.sqrt(dx*dx + dy*dy)
            
            # Distance and Vertical Progress Check
            # Allow small downward moves (-0.05 normalized)
            if min_dist < dist < max_dist and dy > -0.05: 
                candidates.append(hid)
                    
        return candidates

    def _mutate(self, route_ids: List[int], style: dict) -> List[int]:
        """Performs a random mutation: nudge, add, or remove a hold."""
        if len(route_ids) < 3: return route_ids
        
        mutation_type = random.choice(['nudge', 'nudge', 'add', 'remove'])
        
        if mutation_type == 'nudge':
            idx = random.randint(1, len(route_ids)-2) 
            prev_id = route_ids[idx-1]
            neighbors = self._get_reachable_holds(prev_id, style)
            if neighbors:
                route_ids[idx] = random.choice(neighbors)
                
        elif mutation_type == 'add':
            if len(route_ids) < 16:
                idx = random.randint(1, len(route_ids)-1)
                h1_id = route_ids[idx-1]
                
                possible_inserts = self._get_reachable_holds(h1_id, style)
                
                if possible_inserts:
                    new_hold = random.choice(possible_inserts)
                    route_ids.insert(idx, new_hold)
                
        elif mutation_type == 'remove':
            if len(route_ids) > 4: 
                idx = random.randint(1, len(route_ids)-2)
                route_ids.pop(idx)
            
        return route_ids

    def _crossover(self, p1: List[int], p2: List[int]) -> List[int]:
        if len(p1) < 2 or len(p2) < 2: return p1 
        min_len = min(len(p1), len(p2))
        cut_point = random.randint(1, min_len - 1) 
        child = p1[:cut_point] + p2[cut_point:]
        return child