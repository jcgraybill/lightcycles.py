# TODO: single player is a time trial
# TODO: Derez edge case - also erases opponent's trail
# TODO: engine sounds like it's one channel in multiplayer
# TODO: make the explosion much less of a hack
# TODO: make the menu much less of a hack

import pygame
import asyncio
from catppuccin import Flavour
from collections import deque

# constants
STARTINGFPS         = 60
MAXFPS              = 170
WIDTH, HEIGHT       = 1440,744
STATUSBAR           = 24
COLORS              = Flavour.macchiato()
WHITE               = [255,255,255]
SPEED               = 4
STILL               = 0
XPOS, YVAL          = 0, 1
COLORPOS, RECTPOS   = 0,1
PLAYERSIZE          = 4
HAZARD              = 1
TEXTSIZE            = 32
TURNBUFFER          = 2 * STARTINGFPS
ESSPLOSIONROWS      = 6
ESSPLOSIONCOLS      = 8
ESSPLOSION_IMAGE    = "img/boom.png"
ESSPLOSION_SOUND    = "sfx/mixkit-car-explosion-debris-1562.wav"
ENGINE_SOUND        = "sfx/jetcar_start01-32544.wav"
MUSIC               = "sfx/Powerful-Trap-.wav"
MENUSIZE            = 72
SUBMENUSIZE         = 24
MENUBUFFER          = 30

# globals
framespersecond     = STARTINGFPS
numplayers          = 0
grid                = []
essplode            = (0,0)
essplosion_step     = 0
esssprites          = pygame.image.load(ESSPLOSION_IMAGE)
ewidth, eheight     = esssprites.get_width() / ESSPLOSIONCOLS, esssprites.get_height() / ESSPLOSIONROWS
esssound            = None
enginesound         = None
turnbuffer          = 0
reset               = True
isMenu              = True
menuCountdown       = int(6.2 * framespersecond)
MENUCOUNTDOWNMAX    = menuCountdown

class player:
    traildata = []
    x,y = 0,0
    bearing = (SPEED,STILL)
    alive = True
    derez = int(framespersecond/4)
    clearkeys = True
    score = 0
    channel = None

    UP, DOWN, LEFT, RIGHT = pygame.K_UP,pygame.K_DOWN,pygame.K_LEFT,pygame.K_RIGHT
    COLOR = COLORS.yellow.rgb
    DEREZMAX = derez

    def __init__(self):
       self.channel = pygame.mixer.find_channel()
       self.reset()

    def reset(self):
         self.traildata = deque()
         self.derez = self.DEREZMAX
         self.clearkeys = True
         self.alive = True

    def go(self):
        self.channel.set_volume(0.5)
        self.channel.play(enginesound)

    def shaddup(self):
        self.channel.stop()

    def turn(self,keys):
        if keys[self.UP] and self.clearkeys:
            if self.bearing[YVAL] == STILL: 
                self.bearing = (STILL, -SPEED)
                self.channel.play(enginesound)
                self.clearkeys = False
        elif keys[self.DOWN] and self.clearkeys:
            if self.bearing[YVAL] == STILL: 
                self.bearing = (STILL, SPEED)
                self.channel.play(enginesound)
                self.clearkeys = False
        elif keys[self.LEFT] and self.clearkeys:
            if self.bearing[XPOS] == STILL: 
                self.bearing = (-SPEED, STILL)
                self.channel.play(enginesound)
                self.clearkeys = False
        elif keys[self.RIGHT] and self.clearkeys:
            if self.bearing[XPOS] == STILL: 
                self.bearing = (SPEED, STILL)
                self.channel.play(enginesound)
                self.clearkeys = False
        else:
            self.clearkeys = True

    def move(self):
        if not self.alive: return
        self.x += self.bearing[XPOS]
        self.y += self.bearing[YVAL]

    def draw(self):
        return pygame.Rect(self.x, self.y, PLAYERSIZE, PLAYERSIZE)
    
    def trail(self):
        if self.alive:
            if len(self.traildata) < 5: return []
            trail = list()
            trail.append([COLORS.base.rgb, self.traildata[1]])
            trail.append([WHITE, self.traildata[2]])
            trail.append([[int((self.COLOR[0] + WHITE[0]) / 2), int((self.COLOR[1] + WHITE[1])/2), int((self.COLOR[1] + WHITE[1])/2)] ,self.traildata[3]])
            trail.append([self.COLOR, self.traildata[4]])
            return trail
        elif self.derez > 0:
            self.derez -= 1
            trail = list()
            color = [
                int((self.COLOR[0] * self.derez + COLORS.base.rgb[0] * (self.DEREZMAX-self.derez))/ self.DEREZMAX ),
                int((self.COLOR[1] * self.derez + COLORS.base.rgb[1] * (self.DEREZMAX-self.derez))/ self.DEREZMAX ),
                int((self.COLOR[2] * self.derez + COLORS.base.rgb[2] * (self.DEREZMAX-self.derez))/ self.DEREZMAX )
            ]
            for i in self.traildata:
                trail.append([color,i])
            return trail
        else: return []
            
    def collide(self):
        global essplode
        if grid[int(self.y/PLAYERSIZE)][int(self.x/PLAYERSIZE)] == None:
            grid[int(self.y/PLAYERSIZE)][int(self.x/PLAYERSIZE)] = HAZARD
            self.traildata.appendleft(pygame.Rect(self.x, self.y, PLAYERSIZE, PLAYERSIZE))
        else:
            self.alive = False
            self.channel.stop()
            essplode = (self.x, self.y)
            self.channel.set_volume(1)
            self.channel.play(esssound)
            for i in self.traildata:
                grid[int(i.y/PLAYERSIZE)][int(i.x/PLAYERSIZE)] = None

def update(players):
    keys = pygame.key.get_pressed()
    for player in players:
        if player.alive:
            player.turn(keys)
            player.move()
            player.collide()

def essplosion(screen):
    global essplosion_step, essplode
    if essplode == (0,0): return
    row = essplosion_step % ESSPLOSIONCOLS
    col = essplosion_step // ESSPLOSIONCOLS
    show = pygame.Rect(row * ewidth, col * eheight, ewidth, eheight)
    screen.blit(esssprites, (essplode[0] - int(ewidth/2), essplode[1] - int(eheight/2)), show)
    essplosion_step += 1
    if essplosion_step >= ESSPLOSIONCOLS * ESSPLOSIONROWS:
        essplosion_step = 0
        essplode = (0,0)

def statusbar(players):
    status = pygame.Surface((WIDTH,STATUSBAR))
    status.fill(COLORS.mantle.rgb)
    basicFont = pygame.font.SysFont(None, TEXTSIZE)
    spacing = len(players) + 1
    for i, player in enumerate(players):
        text = basicFont.render(str(player.score), True, player.COLOR)
        textRect = text.get_rect()
        textRect.centerx = int((i+1) * status.get_rect().width / spacing)
        textRect.centery = status.get_rect().centery
        status.blit(text, textRect)    
    return status

def draw(players, field, screen):
    for player in players:
        if player.alive: pygame.draw.rect(field,player.COLOR,player.draw())
        for t in player.trail(): 
            pygame.draw.rect(field, t[COLORPOS], t[RECTPOS])
    screen.blit(field, (0,STATUSBAR)) 
    essplosion(screen)
    screen.blit(statusbar(players),(0,0))

def play(players,field, screen):
    global turnbuffer, reset
    update(players)
    if turnbuffer == 0:
        alive = 0
        for player in players:
            if player.alive: 
                alive += 1
        if (numplayers > 1 and alive == 1) or (numplayers == 1 and alive == 0):
            for player in players:
                if player.alive: player.score += 1
                if numplayers == 1: player.score += 1
            turnbuffer += 1
    elif turnbuffer >= TURNBUFFER:
        reset = True
    else:
        turnbuffer += 1
    draw(players,field, screen)

def initialize_players(players):
    players[0].reset()
    players[0].x, players[0].y = WIDTH/4,HEIGHT/2
    players[0].bearing = (SPEED,STILL)
    players[0].UP = pygame.K_w
    players[0].DOWN = pygame.K_s
    players[0].LEFT = pygame.K_a
    players[0].RIGHT = pygame.K_d
    players[0].go()

    if len(players) == 2:
        players[1].reset()
        players[1].x, players[1].y = 3*WIDTH/4, HEIGHT/2
        players[1].COLOR = COLORS.red.rgb
        players[1].bearing = (-SPEED,STILL)
        players[1].go()
    elif len(players) == 3:
        players[1].reset()
        players[1].COLOR = COLORS.blue.rgb
        players[1].x, players[1].y = WIDTH/2,HEIGHT/4
        players[1].bearing = (STILL,SPEED)
        players[1].UP = pygame.K_i
        players[1].DOWN = pygame.K_k
        players[1].LEFT = pygame.K_j
        players[1].RIGHT = pygame.K_l
        players[1].go()

        players[2].reset()
        players[2].x, players[2].y = 3*WIDTH/4, HEIGHT/2
        players[2].COLOR = COLORS.red.rgb
        players[2].bearing = (-SPEED,STILL)
        players[2].go()

def initialize_grid():
    global grid
    grid = [ [None] * int(WIDTH/PLAYERSIZE) for _ in range(int(HEIGHT/PLAYERSIZE))]
    for gy in range(len(grid)):
        for gx in range(len(grid[gy])):
            if gx == 0 or gy == 0: grid[gy][gx] = HAZARD
            if gx == len(grid[gy]) - 1: grid[gy][gx] = HAZARD
            if gy == len(grid) - 1: grid[gy][gx] = HAZARD

def initialize_round(field, players):
    global turnbuffer
    field.fill(COLORS.base.rgb)
    initialize_players(players)
    initialize_grid()
    turnbuffer = 0

def menu(field, screen):
    global isMenu, menuCountdown,numplayers

    menufont = pygame.font.SysFont(None, MENUSIZE)
    submenufont = pygame.font.SysFont(None, SUBMENUSIZE)

    if menuCountdown == MENUCOUNTDOWNMAX:
        field.fill(COLORS.base.rgb)

        menu = [("lightcycles.py", ""), 
                ("one player", "just drive around with no particular goal"),
                ("two players", "classic head to head action"),
                ("three players", "single keyboard mayhem")
                ]
        for i, t in enumerate(menu):
            text = menufont.render(t[0], True, COLORS.text.rgb )
            subtext = submenufont.render(t[1], True, COLORS.subtext0.rgb)
            textrect = text.get_rect()
            subtextrect = subtext.get_rect()
            textrect.x = (field.get_rect().width / 4)
            textrect.centery = int(field.get_rect().height / 5) * ( i + 1 )
            subtextrect.x = (field.get_rect().width / 4)
            subtextrect.centery = textrect.centery + textrect.height
            field.blit(text, textrect)
            field.blit(subtext, subtextrect)
            if i > 0:
                press = submenufont.render("PRESS " + str(i) + ":", True, COLORS.subtext1.rgb)
                pressrect = press.get_rect()
                pressrect.x = textrect.x - pressrect.width - MENUBUFFER
                pressrect.centery = textrect.centery
                field.blit(press,pressrect)
        
        screen.blit(field, (0,STATUSBAR))

        keys = pygame.key.get_pressed()
        if keys[pygame.K_1]:
            numplayers = 1
            menuCountdown -= 1
            pygame.mixer.music.play()
        elif keys[pygame.K_2]:
            numplayers = 2
            menuCountdown -= 1
            pygame.mixer.music.play()
        elif keys[pygame.K_3]:
            numplayers = 3
            menuCountdown -= 1
            pygame.mixer.music.play()
    else:
        field.fill(COLORS.base.rgb)
        menu = []
        if numplayers == 1:
            menu = [
                ("drive around until you hit 21 walls", COLORS.text.rgb),
                ("WASD", COLORS.yellow.rgb)
                ]
        elif numplayers == 2:
            menu = [
                ("play 21 rounds", COLORS.text.rgb),
                ("WASD", COLORS.yellow.rgb),
                ("ARROW KEYS", COLORS.red.rgb)
            ]
        elif numplayers == 3:
            menu = [
                ("play 21 rounds", COLORS.text.rgb),
                ("WASD", COLORS.yellow.rgb),
                ("IJKL", COLORS.blue.rgb),
                ("ARROW KEYS", COLORS.red.rgb)
            ]

        for i, t in enumerate(menu):
            text = menufont.render(t[0], True, t[1] )
            textrect = text.get_rect()
            textrect.x = (field.get_rect().width / 4)
            textrect.centery = int(field.get_rect().height / 5) * ( i + 1 )
            field.blit(text, textrect)
            if i > 0:
                press = submenufont.render("PLAYER " + str(i) + " CONTROLS:", True, COLORS.subtext1.rgb)
                pressrect = press.get_rect()
                pressrect.x = textrect.x - pressrect.width - MENUBUFFER
                pressrect.centery = textrect.centery
                field.blit(press,pressrect)
        screen.blit(statusbar([]),(0,0))
        screen.blit(field, (0,STATUSBAR)) 

        menuCountdown -= 1
        if menuCountdown == 0:
            isMenu = False
            menuCountdown = MENUCOUNTDOWNMAX
            players = []
            for _ in range(numplayers):
                players.append(player())
            return players

async def main():
    global reset, framespersecond, esssound, enginesound, isMenu
    if SPEED < PLAYERSIZE: return # Players will collide with their own lightcycle
    screen = pygame.display.set_mode((WIDTH, HEIGHT + STATUSBAR))
    pygame.display.set_caption("lightcycles.py")

    field = pygame.Surface((WIDTH,HEIGHT))
    esssound = pygame.mixer.Sound(ESSPLOSION_SOUND)
    enginesound = pygame.mixer.Sound(ENGINE_SOUND)
    pygame.mixer.music.load(MUSIC)
    fps =  pygame.time.Clock()
    players = None
    
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        if isMenu: # TODO: second game immediately crashes
            players = menu(field, screen)
            pygame.display.update()
            await asyncio.sleep(0)
        else:
            if reset:
                initialize_round(field, players)
                framespersecond *= 1.05
                reset = False
            else:
                if framespersecond <= MAXFPS:
                    play(players, field, screen)
                    pygame.display.update()
                    await asyncio.sleep(0)
                else:
                    for p in players:
                        p.shaddup()
                    isMenu = True
                    framespersecond = STARTINGFPS
                    reset = True

        fps.tick(framespersecond)

    pygame.mixer.music.stop()

pygame.init()
asyncio.run(main())
pygame.quit()