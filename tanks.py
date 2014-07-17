#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
from pygame import *
from math import *
import libs.tmx as tmx

WINDOW_WIDTH = 1280   
WINDOW_HEIGHT = 624

DISPLAY = (WINDOW_WIDTH, WINDOW_HEIGHT)
GRAY_COLOR = (200, 200, 200)
GRAVITY = 40

class SmallTank(pygame.sprite.Sprite):
    """Основной класс объекта игрока"""
    def __init__(self, location, name_str, isFirstPlayer, *groups):
        super(SmallTank, self).__init__(*groups)

        self.imageLeft = pygame.image.load('graphics/emptyTank.gif') 
        self.imageLeft.blit(pygame.image.load('graphics/gunLeft.gif'), (1,6))
        self.imageLeft.blit(pygame.image.load('graphics/smallTankLeft.gif'), (0,0))

        self.imageRight = pygame.image.load('graphics/emptyTank.gif') 
        self.imageRight.blit(pygame.image.load('graphics/gunRight.gif'), (19,6))
        self.imageRight.blit(pygame.image.load('graphics/smallTankRight.gif'), (0,0))

        self.image = self.imageLeft
        self.rect = pygame.rect.Rect(location, self.image.get_size())


        self.boom_images = []

        for nbr in xrange(1,9,1):
            self.boom_images.append(pygame.image.load('graphics/explosion.png').subsurface((64*(nbr-1),0,64,64)))
        for nbr in xrange(1,9,1):
            self.boom_images.append(pygame.image.load('graphics/explosion.png').subsurface((64*(nbr-1),64,64,64)))
        for nbr in xrange(1,8,1):
            self.boom_images.append(pygame.image.load('graphics/explosion.png').subsurface((64*(nbr-1),128,64,64)))

        self.name_str = name_str
        self.faced = 'left'
        self.firstPlayer = isFirstPlayer
        self.dy = 0
        self.health = 100
        self.gunAngle = 45
        self.time_of_death = 0
        self.shellType = 'genericShell'

    def shoot(self, *groups):
        if self.shellType == 'genericShell':
            GenericShell(self.rect.center, self.gunAngle, 12, self.faced, *groups)
        elif self.shellType == 'rocketShell':
            RocketShell(self.rect.center, self.gunAngle, 12, self.faced, *groups)

    def updateHealthBy(self, hits):
        self.health += hits

    def setShellType(self, shellType):
        self.shellType = shellType
        
    def update(self, dt, game):
        # При здоровье меньше 0 запускается анимация взрыва 
        if self.health <= 0:
            self.time_of_death += dt
            try:
                self.image = self.boom_images[int(self.time_of_death/0.033)]
            except IndexError:
                self.rect.y = 0
                self.rect.x = 0
                self.kill()

        last = self.rect.copy()
        key = pygame.key.get_pressed()

        if self.firstPlayer:
            if key[pygame.K_LEFT]:
                self.rect.x -= 300 * dt
                self.image = self.imageLeft
                self.faced = 'left'
            elif key[pygame.K_RIGHT]:
                self.rect.x += 300 * dt
                self.image = self.imageRight
                self.faced = 'right'
            elif key[pygame.K_UP]:
                if self.gunAngle < 90:self.gunAngle += 3
            elif key[pygame.K_DOWN]:
                if self.gunAngle > 0: self.gunAngle -= 3
        else:
            if key[pygame.K_a]:
                self.rect.x -= 300 * dt
                self.image = self.imageLeft
                self.faced = 'left'
            elif key[pygame.K_d]:
                self.rect.x += 300 * dt
                self.image = self.imageRight
                self.faced = 'right'
            elif key[pygame.K_w]:
                if self.gunAngle < 90:self.gunAngle += 3
            elif key[pygame.K_s]:
                if self.gunAngle > 0: self.gunAngle -= 3

        self.dy = min(400, self.dy + GRAVITY)

        self.rect.y += self.dy * dt

        new = self.rect
        for cell in game.tilemap.layers['triggers'].collide(new, 'blockers'):
            if last.right <= cell.left and new.right > cell.left:
                new.right = cell.left
            if last.left >= cell.right and new.left < cell.right:
                new.left = cell.right
            if last.bottom <= cell.top and new.bottom > cell.top:
                new.bottom = cell.top
                self.dy = 0
            if last.top >= cell.bottom and new.top < cell.bottom:
                new.top = cell.bottom
                self.dy = 0

        # Обработка коллизий
        for layer in game.tilemap.layers:
            if layer.name == 'bonusItems':
                for item in layer:
                    if (abs(item.rect.x - self.rect.x) < 30) and (abs(item.rect.y - self.rect.y) < 10):
                        item.actionOn(self)

        game.tilemap.set_focus(new.x, new.y)

class Shell(pygame.sprite.Sprite):
    pass

class GenericShell(Shell):
    """Класс основного снаряда"""
    def __init__(self, start_point, angle, speed, direction, *groups):
        super(GenericShell, self).__init__(*groups)

        self.image = pygame.image.load('graphics/genericShell.png')
        self.boom_images = []
        for nbr in xrange(1,8,1):
            self.boom_images.append(pygame.image.load('graphics/explosedSprite.png').subsurface((20*(nbr-1),0,20,20)))
        self.explosed = False

        self.direction = direction
        self.rect = pygame.rect.Rect(start_point, self.image.get_size())
        self.start_point = start_point
        self.speed_constant = speed
        self.start_angle = angle
        self.time_of_birth = 0.0
        self.damage_rate = -9
        self.direction = direction # 'left', 'right'
        
    def update(self, dt, game):
        self.time_of_birth += dt
        if not self.explosed:
            if self.direction == 'right':
                self.rect.x += self.speed_constant* cos(radians(self.start_angle)) * 1
                self.rect.y += sin(radians(-self.start_angle))*self.speed_constant + 0.5*10*(self.time_of_birth**2)
            else:
                self.rect.x -= self.speed_constant* cos(radians(self.start_angle)) * 1
                self.rect.y += sin(radians(-self.start_angle))*self.speed_constant + 0.5*10*(self.time_of_birth**2)

            for cell in game.tilemap.layers['triggers'].collide(self.rect, 'blockers'):
                self.time_of_birth = 0
                self.explosed = True

            if self.time_of_birth > 0.9:
                for sp in game.tilemap.layers:
                    if sp.name == 'players':
                        for player in sp:
                            if (type(player) == SmallTank) and (abs(player.rect.x - self.rect.x) < 30) and (abs(player.rect.y - self.rect.y) < 10):
                                player.updateHealthBy(self.damage_rate)
                                self.time_of_birth = 0
                                self.explosed = True

        else:
            try:
                self.image = self.boom_images[int(self.time_of_birth/0.033)]
            except IndexError:
                self.kill()

class RocketShell(Shell):
    """Класс снаряда типа ракета"""
    def __init__(self, start_point, angle, speed, direction, *groups):
        super(RocketShell, self).__init__(*groups)
        
        if direction == 'right':
            self.image = pygame.image.load('graphics/shellRight.gif')
        else:
            self.image = pygame.image.load('graphics/shellLeft.gif')

        self.boom_images = []
        for nbr in xrange(1,8,1):
            self.boom_images.append(pygame.image.load('graphics/explosedSprite.png').subsurface((20*(nbr-1),0,20,20)))
        self.explosed = False

        self.screen = pygame.display.get_surface()
        self.rect = pygame.rect.Rect(start_point, self.image.get_size())
        self.start_point = start_point
        self.speed_constant = speed
        self.start_angle = angle
        self.time_of_birth = 0.0
        self.damage_rate = -17
        self.direction = direction # 'left', 'right'
        
    def update(self, dt, game):
        self.time_of_birth += dt
        x_acc = 1.8
        if not self.explosed:
            if self.direction == 'right':
                self.rect.x += self.speed_constant* cos(radians(self.start_angle)) + 0.5*x_acc*(self.time_of_birth**2)
                self.rect.y += sin(radians(-self.start_angle))*self.speed_constant + 0.5*10*(self.time_of_birth**2)
            else:
                self.rect.x -= self.speed_constant* cos(radians(self.start_angle)) * 0.5*x_acc*(self.time_of_birth**2)
                self.rect.y += sin(radians(-self.start_angle))*self.speed_constant + 0.5*10*(self.time_of_birth**2)

            for cell in game.tilemap.layers['triggers'].collide(self.rect, 'blockers'):
                self.time_of_birth = 0
                self.explosed = True

            if self.time_of_birth > 0.9:
                for sp in game.tilemap.layers:
                    if type(sp) == tmx.SpriteLayer and sp.name == "players":
                        for player in sp:
                            if self.rect.top > player.rect.top and self.rect.bottom < player.rect.bottom and self.rect.left > player.rect.left and self.rect.right < player.rect.right:
                                player.updateHealthBy(self.damage_rate)
                                self.time_of_birth = 0
                                self.explosed = True                      
        else:
            try:
                self.image = self.boom_images[int(self.time_of_birth/0.033)]
            except IndexError:
                self.kill()

class GenericBonusItem(pygame.sprite.Sprite):
    """Класс бонусных объектов"""
    def __init__(self, start_point, itemType, *groups):
        super(GenericBonusItem, self).__init__(*groups)
        if itemType == 'healthBox':
            self.image = pygame.image.load('graphics/healthBox.png')
        elif itemType == 'rocketShellBox':
            self.image = pygame.image.load('graphics/rocketShellBox.png')
        elif itemType == 'genericShellBox':
            self.image = pygame.image.load('graphics/genericShellBox.png')
        self.itemType = itemType
        self.rect = pygame.rect.Rect(start_point, self.image.get_size())
        self.dy = 0

    def actionOn(self, player):
        if self.itemType == 'healthBox':
            player.updateHealthBy(25)
        else:
            player.shellType = self.itemType[:-3]
      
        self.kill()

    def update(self, dt, game):
        last = self.rect.copy()
        self.dy = min(WINDOW_HEIGHT, self.dy + 40) #40 is a Gravity constant
        new = self.rect
        self.rect.y += self.dy * dt

        for cell in game.tilemap.layers['triggers'].collide(new, 'blockers'):
            if last.right <= cell.left and new.right > cell.left:
                new.right = cell.left
            if last.left >= cell.right and new.left < cell.right:
                new.left = cell.right
            if last.bottom <= cell.top and new.bottom > cell.top:
                new.bottom = cell.top
                self.dy = 0
            if last.top >= cell.bottom and new.top < cell.bottom:
                new.top = cell.bottom
                self.dy = 0

class HUD(pygame.Surface):
    """Класс боковых меню"""
    def __init__(self, position, player):
        super(HUD, self).__init__((250, 250))
        self.position = position
        self.player = player
        self.font = pygame.font.SysFont("arial", 14)
        self.font_color = (100,100,100)

    def draw(self, screen):
        lineHeight = 17
        self.fill(GRAY_COLOR)
        self.blit(self.font.render((self.player.name_str),  True, self.font_color), (0,0))
        self.blit(self.font.render("Health:", True, self.font_color), (0,lineHeight))
        health = self.font.render(str(self.player.health), True, self.font_color)
        self.blit(health, (50,lineHeight))

        self.blit(self.font.render("Gun Angle:", True, self.font_color), (0,lineHeight*2))
        gunAngle = self.font.render(str(self.player.gunAngle), True, self.font_color)
        self.blit(gunAngle, (82,lineHeight*2))

        screen.blit(self, self.position)

class MenuItem (pygame.font.Font):
    """ MenuItem должно быть наследовано от класса Font"""
    def __init__(self,text, position,fontSize=36, antialias = True, color = (255, 255, 255), background=None):
        pygame.font.Font.__init__(self,None, fontSize)
        self.text = text
        if background == None:
            self.textSurface = self.render(self.text, antialias,(255,255,255))
        else:
            self.textSurface = self.render(self.text, antialias,(255,255,255),background)
        self.position=self.textSurface.get_rect(centerx=position[0],centery=position[1])
    def getPos(self):
        return self.position
    def getText(self):
        return self.text
    def getSurface(self):
        return self.textSurface

class Menu(pygame.Surface):
    """Класс начального меню"""
    def __init__(self,menuEntries, screen,  menuCenter = None):
        super(Menu, self).__init__(screen.get_size())
        self.area = screen.get_rect()
        self.fill((0,0,0))
        self.active=False

        if pygame.font:
            fontSize = 36
            fontSpace= 4

            # calculate the height and startpoint of the menu
            # leave a space between each menu entry
            menuHeight = (fontSize+fontSpace)*len(menuEntries)
            startY = self.get_height()/2 - menuHeight/2  

            self.menuEntries = list()
            for menuEntry in menuEntries:
                centerX=self.get_width()/2
                centerY = startY+fontSize+fontSpace
                newEnty = MenuItem(menuEntry,(centerX,centerY))
                self.menuEntries.append(newEnty)
                self.blit(newEnty.getSurface(), newEnty.getPos())
                startY=startY+fontSize+fontSpace

    def drawMenu(self, screen):
        self.active=True            
        screen.blit(self, (0, 0))

    def isActive(self):
        return self.active
    def activate(self):
        self.active = True
    def deactivate(self):
        self.active = False
    def handleEvent(self,event):
        if self.isActive():
            eventX = event.pos[0]
            eventY = event.pos[1]
            for menuItem in self.menuEntries:
                textPos = menuItem.getPos()
                #check if current event is in the text area 
                if eventX > textPos.left and eventX < textPos.right and eventY > textPos.top and eventY < textPos.bottom:
                    return menuItem.getText()


class GameOverMenu(Menu):
    def __init__(self,menuEntries, screen,  menuCenter = None):
        super(Menu, self).__init__(screen.get_size())
        self.area = screen.get_rect()
        self.fill((0,0,0))
        self.active=False

        if pygame.font:
            fontSize = 72
            fontSpace= 4

            # calculate the height and startpoint of the menu
            # leave a space between each menu entry
            menuHeight = (fontSize+fontSpace)*len(menuEntries)
            startY = self.get_height()/1.5 - menuHeight/2  

            self.menuEntries = list()
            for menuEntry in menuEntries:
                centerX=self.get_width()/2
                centerY = startY+fontSize+fontSpace
                newEnty = MenuItem(menuEntry,(centerX,centerY))
                self.menuEntries.append(newEnty)
                self.blit(newEnty.getSurface(), newEnty.getPos())
                startY=startY+fontSize+fontSpace

        self.set_alpha(5)

class Game():
    def main(self, screen):
        import random
        random.seed()
        clock = pygame.time.Clock()

        self.tilemap = tmx.load('maps/map1.tmx', screen.get_size())

        self.players = tmx.SpriteLayer('players')
        self.player = SmallTank((800, 400),'First Player', True, self.players)
        self.secondPlayer = SmallTank((400, 400),'Second Player', False, self.players)
       
        self.shells = tmx.SpriteLayer('shell')
        self.bonusItems = tmx.SpriteLayer('bonusItems')

        self.tilemap.layers.append(self.players)
        self.tilemap.layers.append(self.shells)
        self.tilemap.layers.append(self.bonusItems)

        firstPlayerHUD = HUD((1175,0), self.player)
        secondPlayerHUD = HUD((0,0), self.secondPlayer)

        textForMainMenu = ("Start Game","Quit")
        mainMenu = Menu(textForMainMenu, screen)
        mainMenu.drawMenu(screen)

        textForLastMenu = ("Game Over" ," ")
        lastMenu = GameOverMenu(textForLastMenu, screen)

        gameIsRunning = True
        interval = 0

        while gameIsRunning:
            dt = clock.tick(30)
            interval += dt

            if interval > 10000 and not mainMenu.isActive(): # interval in milliseconds
                interval = 0
                item_type = random.choice(['healthBox','rocketShellBox', 'genericShellBox'])
                item_x_coord = random.randint(0, self.tilemap.px_width-20)
                item_y_coord = random.randint(0, 200)
                item =  GenericBonusItem((item_x_coord,item_y_coord), item_type, self.bonusItems)

            for e in pygame.event.get():
                if e.type == pygame.MOUSEBUTTONDOWN:
                    text = mainMenu.handleEvent(e)
                    if text == "Quit":
                        gameIsRunning = False
                    else:
                        mainMenu.deactivate()
                if self.player.alive() and e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                    self.player.shoot(self.shells)
                if self.secondPlayer.alive() and e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
                    self.secondPlayer.shoot(self.shells)
                if e.type == pygame.QUIT:
                    gameIsRunning = False
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    mainMenu.activate()

            if not self.player.alive() or not self.secondPlayer.alive():
                lastMenu.drawMenu(screen)
            elif mainMenu.isActive():
                mainMenu.drawMenu(screen)
            else:
                self.tilemap.update(dt / 1000., self)
                screen.fill(GRAY_COLOR)
                firstPlayerHUD.draw(screen)
                secondPlayerHUD.draw(screen)
                self.tilemap.draw(screen)
            
            pygame.display.flip()


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode(DISPLAY)
    pygame.display.set_caption("Tanks")
    Game().main(screen)