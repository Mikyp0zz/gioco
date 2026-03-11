import pygame
import random

# Colori UI (Centralizzati)
WHITE = (255, 255, 255)
GOLD  = (241, 196, 15)
GRAY  = (150, 150, 150) # Reso un po' più chiaro per leggibilità
DARK_GRAY = (30, 30, 30)
RED   = (255, 50, 50)

class UIManager:
    def __init__(self, screen, player, width, height):
        self.screen = screen
        self.player = player
        self.w = width
        self.h = height
        
        # Font
        self.font_main = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_button = pygame.font.SysFont("Arial", 18, bold=True)
        
        # Pool dei potenziamenti
        self.upgrade_pool = [
            {"id": "hp", "text": "MAX HP +20", "desc": "Aumenta salute e ti cura al massimo"},
            {"id": "atk", "text": "ATTACK +10", "desc": "Aumenta il danno di spada e orbe"},
            {"id": "spd", "text": "SPEED +0.5", "desc": "Ti muovi più velocemente"},
            {"id": "regen", "text": "SUPER REGEN", "desc": "Rigenerazione salute +1.0 HP/s"},
            {"id": "lifesteal", "text": "LIFESTEAL +2%", "desc": "Cura una parte del danno inflitto"},
            {"id": "orb", "text": "ORBITAL ORB", "desc": "Aggiunge una sfera rotante letale"},
            {"id": "dash", "text": "LONG DASH", "desc": "Aumenta potenza e durata dello scatto"}
        ]
        self.current_options = []

    def generate_upgrades(self):
        """Seleziona 4 opzioni casuali e uniche dal pool."""
        self.current_options = random.sample(self.upgrade_pool, 4)

    def draw_level_up_menu(self):
        """Disegna il menu di selezione upgrade."""
        # Overlay oscurante
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))
        
        # Titolo
        title = self.font_big.render("LEVEL UP! CHOOSE YOUR POWER", True, GOLD)
        self.screen.blit(title, (self.w // 2 - title.get_width() // 2, 60))

        # Box degli upgrade
        for i, opt in enumerate(self.current_options):
            rect = pygame.Rect(self.w // 2 - 220, 140 + i * 100, 440, 85)
            
            # Effetto hover (opzionale: potremmo aggiungere un colore diverso se il mouse è sopra)
            pygame.draw.rect(self.screen, DARK_GRAY, rect, border_radius=12)
            pygame.draw.rect(self.screen, GOLD, rect, 2, border_radius=12)
            
            # Testi
            num_txt = self.font_main.render(f"{i+1}.", True, GOLD)
            name_txt = self.font_main.render(opt["text"], True, WHITE)
            desc_txt = self.font_button.render(opt["desc"], True, GRAY)
            
            self.screen.blit(num_txt, (rect.x + 15, rect.y + 15))
            self.screen.blit(name_txt, (rect.x + 45, rect.y + 15))
            self.screen.blit(desc_txt, (rect.x + 45, rect.y + 48))

    def apply_upgrade(self, index):
        """Applica l'effetto dell'upgrade selezionato."""
        if index >= len(self.current_options): return
        
        opt = self.current_options[index]
        p = self.player
        
        if opt["id"] == "hp":
            p.stats["max_hp"] += 20
            p.stats["hp"] = p.stats["max_hp"] # Cura completa
        elif opt["id"] == "atk":
            p.stats["atk"] += 10
        elif opt["id"] == "spd":
            p.stats["speed"] += 0.5
        elif opt["id"] == "regen":
            p.stats["regen"] += 1.0
        elif opt["id"] == "lifesteal":
            p.stats["lifesteal"] += 0.02
        elif opt["id"] == "orb":
            p.stats["orbs"] += 1
        elif opt["id"] == "dash":
            p.dash_speed += 4
            p.dash_max_timer += 0.04

    def draw_game_over(self, kills, time_str):
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((40, 0, 0, 230))
        self.screen.blit(overlay, (0, 0))
        
        t1 = self.font_big.render("DEFEATED", True, RED)
        t2 = self.font_main.render(f"Kills: {kills}  |  Survival Time: {time_str}", True, WHITE)
        t3 = self.font_button.render("Press 'R' to Revive or 'ESC' to Exit", True, GOLD)
        
        self.screen.blit(t1, (self.w//2 - t1.get_width()//2, self.h//2 - 100))
        self.screen.blit(t2, (self.w//2 - t2.get_width()//2, self.h//2 - 20))
        self.screen.blit(t3, (self.w//2 - t3.get_width()//2, self.h//2 + 80))

    def draw_main_menu(self):
        self.screen.fill((15, 25, 15)) # Verde molto scuro
        t = self.font_big.render("SWORD SURVIVOR", True, WHITE)
        s = self.font_main.render("Press SPACE to Start", True, GOLD)
        
        # Disegna un cerchio decorativo dietro il titolo
        pygame.draw.circle(self.screen, (30, 60, 30), (self.w//2, self.h//2 - 100), 100)
        
        self.screen.blit(t, (self.w//2 - t.get_width()//2, self.h//2 - 120))
        self.screen.blit(s, (self.w//2 - s.get_width()//2, self.h//2 + 50))