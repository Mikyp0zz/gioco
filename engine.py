import pygame
import math
import random
import time

# Costanti Colore (Centralizzate)
RED    = (200, 50, 50)
ORANGE = (255, 140, 0)
CYAN   = (0, 255, 255)
GOLD   = (241, 196, 15)
PURPLE = (155, 89, 182)
WHITE  = (255, 255, 255)

class Particella:
    def __init__(self, x, y, color):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(random.uniform(-4, 4), random.uniform(-4, 4))
        self.life = 255
        self.color = color

    def update(self, dt):
        self.pos += self.vel * (dt * 60) # Scalato sul tempo
        self.life -= 720 * dt # Svanisce in circa 0.35 secondi

class ExperienceGem:
    def __init__(self, x, y, xp_val):
        self.pos = pygame.Vector2(x, y)
        self.xp_val = xp_val
        self.rect = pygame.Rect(x-5, y-5, 10, 10)
        self.magnetized = False
        self.speed = 5

    def update(self, player_pos, dt):
        dist = self.pos.distance_to(player_pos)
        if dist < 180: self.magnetized = True
        
        if self.magnetized:
            # Velocità incrementale per evitare che la gemma orbiti senza essere presa
            self.speed += 25 * dt 
            # Evita divisione per zero se la gemma è esattamente sul player
            if dist > 0:
                dir_to_p = (player_pos - self.pos).normalize()
                self.pos += dir_to_p * self.speed
            self.rect.center = self.pos

class EntityManager:
    def __init__(self, player_ref):
        self.player = player_ref
        self.enemies = []
        self.particles = []
        self.gems = []
        self.damage_numbers = []
        self.boss = None
        
        self.start_time = time.time()
        self.elapsed_time = 0
        self.difficulty = 1.0
        self.shake_amount = 0
        self.paused = False 
        
        self.last_spawn = 0
        self.spawn_delay = 1.5
        self.boss_interval = 45
        self.boss_spawn_timer = time.time()

    def create_particles(self, x, y, color, count=8):
        for _ in range(count):
            self.particles.append(Particella(x, y, color))

    def add_damage_number(self, x, y, val, is_crit=False):
        self.damage_numbers.append({
            "pos": pygame.Vector2(x, y), 
            "val": int(val),
            "life": 1.0, 
            "color": GOLD if is_crit else WHITE, 
            "crit": is_crit
        })

    def spawn_enemy(self, width, height):
        if self.boss or self.paused: return
        
        # Spawn fuori schermo
        angle = random.uniform(0, math.pi * 2)
        dist = max(width, height) * 0.7
        x = width//2 + math.cos(angle) * dist
        y = height//2 + math.sin(angle) * dist
        
        r = random.random()
        if r < 0.15 and self.difficulty > 1.3:
            etype, hp_m, spd_m, dmg_m, size = "tank", 3.0, 0.6, 2.0, 45
        elif r > 0.85 and self.difficulty > 1.2:
            etype, hp_m, spd_m, dmg_m, size = "runner", 0.7, 2.2, 0.8, 22
        else:
            etype, hp_m, spd_m, dmg_m, size = "base", 1.0, 1.0, 1.0, 32

        hp = 45 * self.difficulty * hp_m
        self.enemies.append({
            "type": etype, "pos": pygame.Vector2(x, y),
            "rect": pygame.Rect(0, 0, size, size),
            "hp": hp, "max_hp": hp,
            "speed": (1.8 + (self.difficulty * 0.15)) * spd_m,
            "damage": 15 * self.difficulty * dmg_m,
            "hit_flash": 0, "kb_vel": pygame.Vector2(0, 0)
        })

    def spawn_boss(self, width, height):
        hp = 1500 * self.difficulty
        self.boss = {
            "pos": pygame.Vector2(width//2, 50), # Spawna in alto dentro lo schermo
            "rect": pygame.Rect(0, 0, 110, 110),
            "hp": hp, "max_hp": hp,
            "speed": 1.3, "damage": 50,
            "hit_flash": 0, "kb_vel": pygame.Vector2(0, 0),
            "atk_zone_timer": 0, "phase2": False
        }

    def apply_damage(self, entity, base_dmg, crit_chance):
        is_crit = random.random() < crit_chance
        final_dmg = base_dmg * (2.5 if is_crit else 1.0)
        
        # Sottrai la vita
        entity["hp"] -= final_dmg
        entity["hit_flash"] = 0.15 
        
        # --- EFFETTO SANGUE ---
        num_particles = 12 if is_crit else 6
        self.create_particles(entity["pos"].x, entity["pos"].y, (180, 0, 0), num_particles)
        
        # Feedback numerico e scuotimento
        self.add_damage_number(entity["pos"].x, entity["pos"].y, final_dmg, is_crit)
        self.shake_amount = max(self.shake_amount, 12 if is_crit else 5)
        
        return final_dmg

    def update_logic(self, dt, width, height):
        if self.paused: return
        
        self.elapsed_time = time.time() - self.start_time
        self.difficulty = 1.0 + (self.elapsed_time / 60)
        self.spawn_delay = max(0.2, 1.6 - (self.difficulty * 0.35))

        # Smorza lo shake (Risolto il bug del tremolio infinito)
        if self.shake_amount > 0: 
            self.shake_amount = max(0, self.shake_amount - dt * 60)

        # Update Damage Numbers
        for dn in self.damage_numbers[:]:
            dn["life"] -= dt * 1.8
            dn["pos"].y -= dt * 50
            if dn["life"] <= 0: self.damage_numbers.remove(dn)
            
        # Update Particles
        for p in self.particles[:]:
            p.update(dt)
            if p.life <= 0: self.particles.remove(p)

        # Update Gems
        for gem in self.gems[:]:
            gem.update(self.player.pos, dt)
            if gem.rect.colliderect(self.player.rect):
                self.player.add_xp(gem.xp_val)
                self.gems.remove(gem)

        # --- LOGICA NEMICI COMUNI ---
        for en in self.enemies[:]:
            # Inerzia e movimento
            en["pos"] += en["kb_vel"]
            en["kb_vel"] *= 0.85
            
            dir_e = (self.player.pos - en["pos"])
            if dir_e.length() > 2:
                en["pos"] += dir_e.normalize() * en["speed"]
            
            # CLAMPING (Muri invisibili)
            en["pos"].x = max(20, min(width - 20, en["pos"].x))
            en["pos"].y = max(20, min(height - 20, en["pos"].y))

            en["rect"].center = en["pos"]
            
            if en["hit_flash"] > 0: 
                en["hit_flash"] -= dt
            
            # Collisione Player
            if en["rect"].colliderect(self.player.rect):
                self.player.take_damage(en["damage"] * dt)
                
            # Morte Nemico
            if en["hp"] <= 0:
                self.create_particles(en["pos"].x, en["pos"].y, (200, 0, 0), 12) 
                self.gems.append(ExperienceGem(en["pos"].x, en["pos"].y, 20))
                self.player.kills += 1
                self.enemies.remove(en)

        # --- LOGICA BOSS ---
        # Spawn
        if not self.boss and (time.time() - self.boss_spawn_timer > self.boss_interval):
            self.spawn_boss(width, height)
            
        # Movimento e Attacchi Boss
        if self.boss:
            b = self.boss
            b["pos"] += b["kb_vel"]
            b["kb_vel"] *= 0.85
            
            dir_b = (self.player.pos - b["pos"])
            if dir_b.length() > 5:
                b["pos"] += dir_b.normalize() * b["speed"]
            
            # CLAMPING BOSS
            b["pos"].x = max(55, min(width - 55, b["pos"].x))
            b["pos"].y = max(55, min(height - 55, b["pos"].y))
            b["rect"].center = b["pos"]

            if b["hit_flash"] > 0: b["hit_flash"] -= dt

            if b["rect"].colliderect(self.player.rect):
                self.player.take_damage(b["damage"] * dt)
            
            # Transizione Fase 2
            if b["hp"] <= b["max_hp"] * 0.5 and not b["phase2"]:
                b["phase2"] = True
                b["speed"] *= 1.5
                b["damage"] *= 1.2
                self.create_particles(b["pos"].x, b["pos"].y, ORANGE, 30)
                
            # Attacco AOE (Ad area)
            b["atk_zone_timer"] += dt * (1.6 if b["phase2"] else 1.0)
            if b["atk_zone_timer"] > 3.0:
                if b["pos"].distance_to(self.player.pos) < 230:
                    self.player.take_damage(b["damage"] * 0.8)
                    self.shake_amount = max(self.shake_amount, 20)
                b["atk_zone_timer"] = 0
            
            # Morte Boss
            if b["hp"] <= 0:
                self.create_particles(b["pos"].x, b["pos"].y, (200, 0, 0), 50)
                self.gems.append(ExperienceGem(b["pos"].x, b["pos"].y, 150))
                self.player.kills += 10
                self.boss = None
                self.boss_spawn_timer = time.time() # Resetta il timer per il prossimo boss