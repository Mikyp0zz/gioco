import pygame
import time
import math
import random
from engine import EntityManager
from ui import UIManager

# CONFIGURAZIONE
WIDTH, HEIGHT = 800, 600
FPS = 60
# Colori
GREEN = (46, 77, 35)
WHITE = (255, 255, 255)
RED = (200, 50, 50)
BLUE = (52, 152, 219)
BLACK = (10, 10, 10)
GOLD = (241, 196, 15)
PURPLE = (155, 89, 182)
ORANGE = (255, 140, 0)
CYAN = (0, 255, 255)
GRAY = (60, 60, 60)

class Player:
    def __init__(self):
        self.pos = pygame.Vector2(WIDTH//2, HEIGHT//2)
        self.rect = pygame.Rect(0, 0, 40, 40)
        self.stats = {
            "hp": 100, "max_hp": 100, "atk": 50, "speed": 5, 
            "regen": 0.5, "crit_chance": 0.1, "lifesteal": 0, "orbs": 0
        }
        self.xp, self.level, self.xp_next = 0, 1, 100
        self.kills = 0
        self.facing_dir = pygame.Vector2(1, 0)
        self.ult_charge, self.ult_ready = 0, False
        self.last_regen_time = time.time()
        
        # Variabili Dash
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_max_timer = 0.15
        self.dash_cd = 0
        self.dash_speed = 18

    def add_xp(self, amount):
        self.xp += amount
        return self.xp >= self.xp_next

    def level_up(self):
        self.level += 1
        self.xp -= self.xp_next
        self.xp_next = int(self.xp_next * 1.3)
        self.stats["hp"] = self.stats["max_hp"] # Cura completa
        self.stats["crit_chance"] += 0.02 # +2% Critico automatico ad ogni livello

    def take_damage(self, amount):
        if not self.is_dashing:
            self.stats["hp"] -= amount

    def update(self, keys, dt):
        if self.dash_cd > 0: self.dash_cd -= dt
        
        if self.dash_timer > 0:
            self.dash_timer -= dt
            self.pos += self.facing_dir * self.dash_speed
        else:
            self.is_dashing = False
            move = pygame.Vector2(0, 0)
            if keys[pygame.K_w]: move.y -= 1
            if keys[pygame.K_s]: move.y += 1
            if keys[pygame.K_a]: move.x -= 1
            if keys[pygame.K_d]: move.x += 1
            
            if move.length() > 0:
                self.facing_dir = move.normalize()
                self.pos += self.facing_dir * self.stats["speed"]

        # Clamp bordi
        self.pos.x = max(20, min(WIDTH - 20, self.pos.x))
        self.pos.y = max(20, min(HEIGHT - 20, self.pos.y))
        self.rect.center = self.pos

        # Rigenerazione passiva
        self.stats["hp"] = min(self.stats["max_hp"], self.stats["hp"] + self.stats["regen"] * dt)


def run_game():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    display_surf = pygame.Surface((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 16, bold=True)
    
    p = Player()
    em = EntityManager(p)
    ui = UIManager(screen, p, WIDTH, HEIGHT)
    
    game_state = "MENU"
    is_attacking, atk_timer = False, 0
    current_atk_rect = None

    while True:
        dt = clock.tick(FPS) / 1000
        keys = pygame.key.get_pressed()

        # --- CICLO EVENTI ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return
            
            if game_state == "MENU":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    game_state = "PLAYING"
            
            elif game_state == "PLAYING":
                if event.type == pygame.KEYDOWN:
                    # Attacco Spada
                    if event.key == pygame.K_SPACE and not is_attacking:
                        is_attacking, atk_timer = True, 0.15
                        ar = pygame.Rect(0,0,120,90) if abs(p.facing_dir.x) > abs(p.facing_dir.y) else pygame.Rect(0,0,90,120)
                        ar.center = p.pos + p.facing_dir * 50
                        current_atk_rect = ar
                        
                        targets = em.enemies + ([em.boss] if em.boss else [])
                        for t in targets:
                            if ar.colliderect(t["rect"]):
                                dmg = em.apply_damage(t, p.stats["atk"], p.stats["crit_chance"])
                                if p.stats["lifesteal"] > 0:
                                    p.stats["hp"] = min(p.stats["max_hp"], p.stats["hp"] + dmg * p.stats["lifesteal"])
                                t["kb_vel"] = (t["pos"] - p.pos).normalize() * 20
                                p.ult_charge = min(100, p.ult_charge + 5)
                                if p.ult_charge >= 100: p.ult_ready = True
                    # Nel ciclo eventi di main.py, dentro: elif game_state == "PLAYING":
                    if event.key == pygame.K_RETURN:  # Tasto INVIO
                        game_state = "DEBUG"
                        em.paused = True

                    # Dash
                    if event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT] and p.dash_cd <= 0:
                        p.is_dashing = True
                        p.dash_timer = p.dash_max_timer
                        p.dash_cd = 0.8
                        em.create_particles(p.pos.x, p.pos.y, WHITE, 10)

                    # Ultimate (Q)
                    if event.key == pygame.K_q and p.ult_ready:
                        p.ult_ready, p.ult_charge = False, 0
                        em.shake_amount = 25
                        ult_r = pygame.Rect(p.pos.x-180, p.pos.y-180, 360, 360)
                        em.create_particles(p.pos.x, p.pos.y, PURPLE, 50)
                        for t in (em.enemies + ([em.boss] if em.boss else [])):
                            if ult_r.colliderect(t["rect"]):
                                dmg = em.apply_damage(t, p.stats["atk"] * 3.5, 0.5)
                                t["kb_vel"] = (t["pos"] - p.pos).normalize() * 35

            elif game_state == "LEVEL_UP":
                if event.type == pygame.KEYDOWN:
                    keys_map = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3}
                    if event.key in keys_map:
                        ui.apply_upgrade(keys_map[event.key])
                        p.level_up()
                        em.paused = False
                        game_state = "PLAYING"

            elif game_state == "GAMEOVER":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r: run_game(); return
                    if event.key == pygame.K_ESCAPE: pygame.quit(); return
             # Poi aggiungi un nuovo blocco elif per lo stato DEBUG
            elif game_state == "DEBUG":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        game_state = "PLAYING"
                        em.paused = False
                    
                    # Gestione Cheat Numerici
                    if event.key == pygame.K_1: # Cura
                        p.stats["hp"] = p.stats["max_hp"]
                    if event.key == pygame.K_2: # Max HP
                        p.stats["max_hp"] += 50
                        p.stats["hp"] += 50 # Aumenta anche la salute attuale
                    if event.key == pygame.K_3: # Attacco
                        p.stats["atk"] += 50
                    if event.key == pygame.K_4: # Velocità
                        p.stats["speed"] += 2
                    if event.key == pygame.K_5: # Orbe
                        p.stats["orbs"] = p.stats.get("orbs", 0) + 1
                    if event.key == pygame.K_6: # Critico
                        p.stats["crit_chance"] = min(1.0, p.stats["crit_chance"] + 0.1)
                    if event.key == pygame.K_7: # Rigenerazione
                        p.stats["regen"] += 1.0
                    if event.key == pygame.K_8: # XP / Level Up rapido
                        p.xp += 100
                    if event.key == pygame.K_9: # Ultimate
                        p.ult_ready = True
                        p.ult_charge = 100
                    if event.key == pygame.K_0:
                        # Aumentiamo la base del cheat
                        em.bonus_difficulty += 0.5 
                        # Aggiorniamo il riferimento per la UI (legge il valore totale calcolato)
                        p.debug_diff_ref = em.difficulty 
                        print(f"CHEAT: Difficoltà Bonus aumentata! Totale: {em.difficulty:.2f}")
                                    
                        if event.key == pygame.K_RETURN:
                            game_state = "PLAYING"
                            em.paused = False

        # --- LOGICA DI GIOCO ---
        if game_state == "PLAYING":
            p.update(keys, dt)
            em.update_logic(dt, WIDTH, HEIGHT)
            
            # Spawn Timer ripristinato
            if not em.boss and (time.time() - em.last_spawn > em.spawn_delay):
                em.spawn_enemy(WIDTH, HEIGHT)
                em.last_spawn = time.time()
            
            if is_attacking:
                atk_timer -= dt
                if atk_timer <= 0: is_attacking, current_atk_rect = False, None

            if p.xp >= p.xp_next:
                game_state = "LEVEL_UP"
                em.paused = True
                ui.generate_upgrades()
                
            if p.stats["hp"] <= 0:
                game_state = "GAMEOVER"

        # --- RENDERING MONDO (display_surf) ---
        display_surf.fill(GREEN)
        
        # Gemme e Particelle
        for gem in em.gems: pygame.draw.rect(display_surf, CYAN, gem.rect)
        for part in em.particles:
            s = pygame.Surface((4,4)); s.set_alpha(int(max(0, part.life))); s.fill(part.color)
            display_surf.blit(s, part.pos)

        # Orbe Orbitali
        num_orbs = p.stats.get("orbs", 0)
        if num_orbs > 0:
            for i in range(num_orbs):
                angle = time.time() * 3 + (i * (math.pi * 2 / num_orbs))
                orb_pos = pygame.Vector2(p.pos.x + math.cos(angle) * 110, p.pos.y + math.sin(angle) * 110)
                pygame.draw.circle(display_surf, GOLD, (int(orb_pos.x), int(orb_pos.y)), 10)
                pygame.draw.circle(display_surf, WHITE, (int(orb_pos.x), int(orb_pos.y)), 11, 2)
                
                if game_state == "PLAYING":
                    orb_r = pygame.Rect(orb_pos.x-10, orb_pos.y-10, 20, 20)
                    for t in (em.enemies + ([em.boss] if em.boss else [])):
                        if orb_r.colliderect(t["rect"]):
                            em.apply_damage(t, max(2, p.stats["atk"] * 0.05), 0)

        # Rendering Fendente Spada (disegnato PRIMA delle entità o DIETRO di esse se preferisci)
        if is_attacking and current_atk_rect:
            atk_s = pygame.Surface((current_atk_rect.width, current_atk_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(atk_s, (255, 255, 255, 120), (0, 0, current_atk_rect.width, current_atk_rect.height), border_radius=15)
            display_surf.blit(atk_s, current_atk_rect.topleft)

        # Entità ordinate per Y-Sort
        entities = [{"t":"p", "y":p.pos.y, "obj":p}]
        if em.boss: entities.append({"t":"b", "y":em.boss["pos"].y, "obj":em.boss})
        for en in em.enemies: entities.append({"t":"e", "y":en["pos"].y, "obj":en})
        entities.sort(key=lambda x: x["y"])

        for e in entities:
            if e["t"] == "p":
                col = CYAN if p.is_dashing else BLUE
                pygame.draw.circle(display_surf, col, p.pos, 20)
            
            elif e["t"] == "e":
                en = e["obj"]
                col = WHITE if en["hit_flash"] > 0 else (RED if en["type"]=="base" else (100,50,0) if en["type"]=="tank" else (200,200,0))
                pygame.draw.rect(display_surf, col, en["rect"])
                # Barre vita nemici comuni
                if en["hp"] < en["max_hp"]:
                    pygame.draw.rect(display_surf, BLACK, (en["pos"].x-15, en["pos"].y-25, 30, 4))
                    pygame.draw.rect(display_surf, (50, 255, 50), (en["pos"].x-15, en["pos"].y-25, int(30 * (max(0, en["hp"])/en["max_hp"])), 4))
            
            elif e["t"] == "b":
                b = e["obj"]
                col = WHITE if b["hit_flash"] > 0 else (120,0,0) if not b["phase2"] else (180,0,180)
                pygame.draw.rect(display_surf, col, b["rect"])
                if b["atk_zone_timer"] > 2.0: 
                    pygame.draw.circle(display_surf, ORANGE, b["pos"], 230, 2)

        # Numeri di Danno
        for dn in em.damage_numbers:
            try:
                txt_surf = font.render(str(dn["val"]), True, dn["color"])
                txt_surf.set_alpha(int(max(0, dn["life"]) * 255))
                display_surf.blit(txt_surf, dn["pos"])
            except:
                pass # Previene crash se l'alpha va fuori range

        # Applica SHAKE
        shake_x = random.uniform(-1, 1) * em.shake_amount
        shake_y = random.uniform(-1, 1) * em.shake_amount
        screen.blit(display_surf, (shake_x, shake_y))

        # --- UI STATICA (Fuori dallo shake) ---
        pygame.draw.rect(screen, BLACK, (0, 0, WIDTH, 75))
        pygame.draw.rect(screen, GRAY, (0, 75, WIDTH, 5))
        pygame.draw.rect(screen, CYAN, (0, 75, int(WIDTH * (p.xp/max(1, p.xp_next))), 5))
        
        # Barre Player (HP e Ult)
        pygame.draw.rect(screen, (60,0,0), (20, 15, 200, 20))
        pygame.draw.rect(screen, (0,200,80), (20, 15, int(200 * (max(0, p.stats['hp'])/p.stats['max_hp'])), 20))
        screen.blit(font.render(f"HP: {int(max(0, p.stats['hp']))} / {p.stats['max_hp']}", True, WHITE), (20, 38))
        
        pygame.draw.rect(screen, (30,30,30), (240, 15, 150, 20))
        u_col = PURPLE if p.ult_ready else (100,100,100)
        pygame.draw.rect(screen, u_col, (240, 15, int(150 * (p.ult_charge/100)), 20))
        screen.blit(font.render("ULTIMATE (Q)" if p.ult_ready else "CHARGING", True, u_col), (240, 38))

        # Stats e Timer
        m, s = divmod(int(em.elapsed_time), 60)
        screen.blit(font.render(f"LVL: {p.level} | KILLS: {p.kills}", True, GOLD), (WIDTH-180, 15))
        screen.blit(font.render(f"TIME: {m:02d}:{s:02d}", True, WHITE), (WIDTH-180, 38))

        # Boss Bar
        if em.boss:
            pygame.draw.rect(screen, BLACK, (WIDTH//2-152, 90, 304, 20))
            pygame.draw.rect(screen, RED, (WIDTH//2-150, 92, int(300 * (max(0, em.boss['hp'])/em.boss['max_hp'])), 16))
            screen.blit(font.render("BOSS", True, WHITE), (WIDTH//2-20, 92))

        # Menu Overlays
        # Alla fine di main.py, dove disegni gli overlay:
        if game_state == "MENU": 
            ui.draw_main_menu()
        elif game_state == "LEVEL_UP": 
            ui.draw_level_up_menu()
        elif game_state == "DEBUG": 
            ui.draw_debug_menu() # <-- Aggiungi questo
        elif game_state == "GAMEOVER": 
            ui.draw_game_over(p.kills, f"{m:02d}:{s:02d}")

        pygame.display.flip()

if __name__ == "__main__":
    run_game()