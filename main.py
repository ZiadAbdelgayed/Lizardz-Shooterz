#--------------------- Imports ---------------------#
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader
from ursina.prefabs.health_bar import HealthBar
import random, threading, time
from ursina.lights import DirectionalLight
from WaveData import Waves
#--------------------- Imports ---------------------#



#--------------------- App ---------------------#
window.vsync = False
Text.default_resolution = 1080 * Text.size
app = Ursina(title="shooter")
#--------------------- App ---------------------#



#--------------------- Variables ---------------------#
# scene.fog_density = (1,100)
# for z in range(-100, 100, 20):
#     for x in range(-100, 100, 20):
#         ground = Entity(model="plane", scale=(20,1,20), color=color.dark_gray, position=(x,0,z), shader=lit_with_shadows_shader)
#         ground.collider = "box"
# ground = Entity(model="ForestModel", texture="ForestTexture", scale=(5,5,5), position=(0,0,0), shader=lit_with_shadows_shader, collider="sphere")
ground = Entity(model="plane", scale=(100,1,100), color=color.dark_gray, position=(0,0,0), shader=lit_with_shadows_shader, collider="box")
player = FirstPersonController(model='cube', collider="box")
player.cursor =  Entity(parent=camera.ui, model='circle', color=color.pink, scale=.008)
# player.cursor.color= color.white
Sky(texture="sky_default")
walking = held_keys['a'] or held_keys['w'] or held_keys['s'] or held_keys['d']
inStartMenu = True
inSettingsMenu = False
gameStarted = False
gameVolume = 1
playerHasWeapon, playerHasSword, playerHasSniper, playerHasGun = False, False, False, False
sprinting = False
bullet = Entity()
spawnNumOfEnemies = 10
wave = 1
playerScore, damageTime, shootTime = 0, 0, 0
ammo, totalAmmo = 0, 100
ammoBoxs = []
backgroundMusic = Audio("backgroundMusic.mp3", loop=True, volume=gameVolume)
walk = Audio("walkingSFX.mp3", loop=True, volume=gameVolume)
PistolTooltip = Tooltip(
    '<scale:1.5><pink>' + 'PISTOL' + '<scale:1> \n \n' + "Fire-rate: 100 \n" + "Max Ammo: 30\n " + "Distance: 10",
        background_color=color.violet,
        font='VeraMono.ttf',
        wordwrap=50,
)
sniperTooltip = Tooltip(
    '<scale:1.5><pink>' + 'SNIPER' + '<scale:1> \n \n' + "Fire-rate: 10 \n" + "Max Ammo: 10\n" + "Distance: 100",
        background_color=color.violet,
        font='VeraMono.ttf',
        wordwrap=50,
)
swordTooltip = Tooltip(
    '<scale:2><pink>' + 'SWORD    ',
        background_color=color.violet,
        font='VeraMono.ttf',
        wordwrap=50,
)
#--------------------- Variables ---------------------#


#--------------------- Classes ---------------------#
class Enemy:
    enemies = []
    MAX_HP = 5
    numOfEnemies = 0

    def __init__(self, entity):
        self.hp = Enemy.MAX_HP
        self.entity = entity

    @classmethod
    def createEnemies(cls):
        Enemy.numOfEnemies += spawnNumOfEnemies
        for i in range(spawnNumOfEnemies):
            newEntity = Entity(parent=scene,
                               model="enemyModel",
                               position=((i*random.randint(-15,15))+10, 0, (i*random.randint(-15,15))+10),
                               scale=(.3, .3, .3),
                               collider="box",
                               shader=lit_with_shadows_shader)
            newEnemy = Enemy(newEntity)
            Enemy.enemies.append(newEnemy)


    def removeEnemy(cls):
        Enemy.enemies.remove(cls)
        Enemy.numOfEnemies -= 1


    def move(cls):
        cls.rotation_y = 0
        cls.rotation_z = 0
        cls.look_at(player.position)
        cls.animate_position(cls.position+(cls.forward*0))


    def checkDeath(cls):
        global playerScore
        if cls.hp == 0:
            playerScore += 10
            playerScoreLbl.text = f"score: {playerScore}"
            if random.randint(0, 100) <= 30:
                ammoBox = Entity(parent=scene,
                                   model="ammoBoxModel",
                                   texture="ammobox_texture",
                                   position=cls.entity.position,
                                   scale=(.5, .5, .5),
                                   collider="box",
                                   shader=lit_with_shadows_shader)
                ammoBoxs.append(ammoBox)
            destroy(cls.entity)
            Enemy.removeEnemy(cls)
#--------------------- Classes ---------------------#


#--------------------- Functions ---------------------#
def startWave():
    global spawnNumOfEnemies, wave
    spawnNumOfEnemies = Waves[wave]
    Enemy.createEnemies()
    wave += 1
def getGun():
    global playerHasGun, playerHasWeapon
    if not playerHasSword:
        gun.parent = player
        gun.rotation_x = 0
        gun.position = Vec3(.5,1.2,.5)
        gun.collider = None
        playerHasGun = True
        playerHasWeapon = True

def getSniper():
    global playerHasSniper, playerHasWeapon
    if not playerHasWeapon:
        sniper.parent = player
        sniper.rotation_z = 90
        sniper.position = Vec3(.5,1.5,.5)
        sniper.collider = None
        playerHasSniper = True
        playerHasWeapon = True

def getSword():
    global playerHasSword, playerHasWeapon
    if not playerHasWeapon:
        sword.parent = player
        sword.rotation_x = 0
        sword.rotation_z = 1
        sword.position = Vec3(.5, 0, .5)
        sword.collider = None
        playerHasSword = True
        playerHasWeapon = True
def resetSword():
    sword.rotation_x = 0
    sword.rotation_z = 1
    sword.collider = None
    # sword.position = Vec3(.5, 0, .5)

def spawnBullet(speed,distance):
    global bullet
    Audio("gunShot.mp3", loop=False)
    bullet = Entity(parent=player, model='circle', scale=.1, color=color.black, position=(.2, 2, 0), collider="box",
                    shader=lit_with_shadows_shader)
    bullet.rotation_x = player.camera_pivot.rotation_x
    bullet.world_parent = scene
    bullet.animate_position(bullet.position + (bullet.forward * speed), curve=curve.linear, duration=distance)
    destroy(bullet, delay=distance)

def reload():
    global ammo, totalAmmo
    ammoLeft = totalAmmo
    totalAmmo -= (((30 if playerHasGun else 10) - ammo) if (totalAmmo > (30 if playerHasGun else 10)) else (30 - ammo)) if totalAmmo > (30-ammo) else totalAmmo
    if playerHasGun:
        ammo = 30 if ammoLeft > 30 else ((ammo + ammoLeft) if ammoLeft < (30-ammo) else 30)
    if playerHasSniper:
        ammo = 10 if ammoLeft > 10 else ((ammo + ammoLeft) if ammoLeft < (10-ammo) else 10)
def startGameFunc():
    global gameStarted, inStartMenu
    gameStarted = True
    inStartMenu = False
    updateScreen()
    player.on_enable()
    application.paused = not application.paused

def updateScreen():
    startButton.enabled = True if inStartMenu else False
    title.enabled = True if inStartMenu else False
    settingsButton.enabled = True if inStartMenu else False
    volume.enabled = True if inSettingsMenu else False
    backButton.enabled = True if inSettingsMenu else False
    menuBackground.enabled = True if inStartMenu or inSettingsMenu else False

def openSettingsMenu():
    global inSettingsMenu, inStartMenu
    inSettingsMenu = True
    inStartMenu = False
    updateScreen()

def backToMenu():
    global inSettingsMenu, inStartMenu
    inSettingsMenu = False
    inStartMenu = True
    updateScreen()

def updateVolume():
    global gameVolume
    gameVolume = volume.value/100
    backgroundMusic.volume = gameVolume

def gunToolTipsOn():
    PistolTooltip.enabled = True
def gunToolTipsOff():
    PistolTooltip.enabled = False
def sniperToolTipsOn():
    sniperTooltip.enabled = True
def sniperToolTipsOff():
    sniperTooltip.enabled = False
def swordToolTipsOn():
    swordTooltip.enabled = True
def swordToolTipsOff():
    swordTooltip.enabled = False




def nothing():
    pass
#--------------------- Functions ---------------------#



#--------------------- Shadows ---------------------#
sun = DirectionalLight(shadow_map_resolution=(2048,2048))
sun.look_at(Vec3(-1,-1,20))
#--------------------- Shadows ---------------------#




#--------------------- Cooldowns ---------------------#
def sniperTimer():
    global shootTime
    while True:
        shootTime += 1
        time.sleep(1)
timerThread = threading.Thread(target=sniperTimer)
timerThread.start()
def damageTimer():
    global damageTime
    while True:
        damageTime += 1
        time.sleep(0.2)
timerThread = threading.Thread(target=damageTimer)
timerThread.start()
def staminaDrain():
    global sprinting
    while True:
        while sprinting:
            staminaBar.value -= 1
            time.sleep(.05)
        time.sleep(.2)
        if 0 <= staminaBar.value < 100 and not walking and player.grounded:
            staminaBar.value += 1
staminaDrainThread = threading.Thread(target=staminaDrain)
staminaDrainThread.start()
#--------------------- Cooldowns ---------------------#



#--------------------- Entities ---------------------#
staminaBar = HealthBar(bar_color=color.yellow.tint(-.25),scale =(.5, .03),origin=(-.5, 30, 0) )

playerScoreBox = Entity(parent=scene, position=(0, 100, 0), scale=(20, 10, 20), billboard=True, shader=lit_with_shadows_shader)

health = HealthBar(bar_color=color.lime.tint(-.25), scale=(.5,.03),origin=(-.5, 28.5, 0))

sword = Button(parent=scene, model='swordModel.fbx', texture="swordTexture1.png", position=(-5,.1,3), scale=(.1,.1,.1), rotation_y = -90,
             rotation_x = -90, collider="box", shader=lit_with_shadows_shader)

gun = Button(parent=scene, model='gunModel.dae', texture="bois_albedo.jpeg", position=(3,.1,3), scale=(.004,.004,.004), rotation_y = -90,
             rotation_x = -90, collider="box", shader=lit_with_shadows_shader)

sniper = Button(parent=scene, model='cube', position=(3,.1,-2), scale=(.25,3,.25), rotation_y = -90,
                rotation_x = -90, collider="box", shader=lit_with_shadows_shader)
#--------------------- Entities ---------------------#




#--------------------- Labels ---------------------#
pause_text = Text('PAUSED', origin=(0,-7), scale=2, enabled=False)
numberOfEnemiesLbl = Text(parent=camera.ui, text=f'Number Of Enemies: {Enemy.numOfEnemies}', origin=(2.5,-18), color=color.black)
numOfAmmoLbl = Text(text=f'Ammo: {ammo}/{totalAmmo}', origin=(4.7,-15.5), color=color.black)
playerScoreLbl = Text(parent=playerScoreBox, text = f"score: {playerScore}", color=color.black, scale=15, font="VeraMono.ttf")

menuBackground = Text("", scale=50, background=True)
title = Text("Lizardz Shooterz", scale=4, font="VeraMono.ttf", origin=(0,-3.5))
startButton = Button("Start Game", highlight_color=color.green.tint(.4), scale =(.5, .05), font="VeraMono.ttf", color=color.green, origin=(0, -3), ignore_paused=True)
settingsButton = Button("Settings", highlight_color=color.dark_gray, scale =(.5, .05), font="VeraMono.ttf", color=color.gray, origin=(0, -1.5), ignore_paused=True)
volume = Slider(0, 100, default=100, text="Volume", step=1, y=.1, x=-.2, on_value_changed=updateVolume, enabled=False, ignore_paused=True, dynamic=True)

# volumeBar = Slider(0, 20, default=10, height=Text.size*3, y=-.4, step=1, on_value_changed=updateVolume, vertical=True)

backButton = Button("Back", highlight_color=color.dark_gray, scale =(.5, .05), font="VeraMono.ttf", color=color.gray, origin=(0, 0), enabled=False, ignore_paused=True)
#--------------------- Labels ---------------------#





#--------------------- Ursina Functions ---------------------#
def update():
    global bullet, totalAmmo, damageTime, gameStarted, sprinting, walking
    walking = held_keys['a'] or held_keys['w'] or held_keys['s'] or held_keys['d']
    numberOfEnemiesLbl.text = f'Number Of Enemies: {Enemy.numOfEnemies}'
    numOfAmmoLbl.text = f'Ammo: {ammo}/{totalAmmo}'
    if not gameStarted:
        application.pause()
        player.on_disable()
    if held_keys["shift"] and walking and staminaBar.value > 0:
        player.speed = 20
        camera.fov = 110
        sprinting = True
    else:
        player.speed = 10
        camera.fov = 100
        sprinting = False
    if staminaBar.value == 0 or staminaBar.value < 5:
        player.jump_height = 0
    else:
        player.jump_height = 4
    if health.value == 0:
        pause_handler_input("escape")
        menuBackground.enabled = True
        pause_text.text = "YOU DIED"
        pause_text.color = color.black
    for enemy in Enemy.enemies:
        Enemy.move(enemy.entity)
        if bullet.intersects(enemy.entity).hit:
            enemy.hp -= 5
            Enemy.checkDeath(enemy)
        elif sword.intersects(enemy.entity).hit:
            enemy.hp -= 0.5
            Enemy.checkDeath(enemy)
        # elif raycast(player.position, direction=player.position, traverse_target=enemy.entity, distance=inf).hit:
        elif player.intersects(enemy.entity).hit and damageTime > 0:
            damageTime = 0
            health.value -= 1
    for ammoLoot in ammoBoxs:
        if player.intersects(ammoLoot).hit:
            totalAmmo += 10
            ammoBoxs.remove(ammoLoot)
            destroy(ammoLoot)
    if playerHasGun:
        gun.rotation_z = player.camera_pivot.rotation_x
    if walking and walk.playing == 0:
        walk.play()
    elif not walking and walk.playing == 1:
        walk.stop()
    if Enemy.numOfEnemies == 0 and gameStarted:
        health.value += 20
        startWave()


    # if raycast(player.position, playerDirection, traverse_target=gun, distance=20, debug=False).hit:
        gun.on_click = getGun
        gun.on_mouse_enter = gunToolTipsOn
        gun.on_mouse_exit = gunToolTipsOff
    # else:
    #     gun.on_click = nothing
    #     gun.on_mouse_enter = nothing

    # if raycast(player.position, direction=player.position, traverse_target=sniper, distance=20, debug=False).hit:
        sniper.on_click = getSniper
        sniper.on_mouse_enter = sniperToolTipsOn
        sniper.on_mouse_exit = sniperToolTipsOff
    # else:
    #     sniper.on_click = nothing
    #     sniper.on_mouse_enter = nothing

    sword.on_click = getSword
    sword.on_mouse_enter = swordToolTipsOn
    sword.on_mouse_exit = swordToolTipsOff


    startButton.on_click = startGameFunc
    settingsButton.on_click = openSettingsMenu
    backButton.on_click = backToMenu

def input(key):
    global playerHasGun, playerHasSword, playerHasSniper, bullet, playerHasWeapon, shootTime, ammo, totalAmmo
    if key == 'left mouse down' and playerHasGun and ammo > 0:
        ammo -= 1
        spawnBullet(1000,1)
    elif key == 'left mouse down' and playerHasGun and ammo == 0:
        Audio("emptyGunShot.mp3", loop=False)
    if key == 'left mouse down' and playerHasSniper and shootTime > 0 and ammo > 0:
        spawnBullet(5000, 3)
        shootTime = 0
        ammo -= 1
    elif key == 'left mouse down' and playerHasSniper and shootTime > 0 and ammo == 0:
        Audio("emptyGunShot.mp3", loop=False)
    if key == 'left mouse down' and playerHasSword:
        Audio("swordSwing.mp3", loop=False)
        # if sword.rotation_z < 90:
        sword.animate_rotation(sword.rotation + (sword.rotation * 2), curve=curve.linear, duration=.19)
        # sword.position = Vec3(.5, 1, .5)
        sword.collider = "box"
        invoke(resetSword, delay=.2)
    if key == "m":
        player.position = (0,2,0)
        # player.gravity = 0
    if key == "f" and playerHasGun:
        totalAmmo += ammo
        ammo = 0
        playerHasGun = False
        playerHasWeapon = False
        gun.position = (player.x,0.1,player.z)
        gun.rotation_x = -90
        gun.collider = "box"
        gun.parent = scene
    if key == "f" and playerHasSniper:
        totalAmmo += ammo
        ammo = 0
        playerHasSniper = False
        playerHasWeapon = False
        sniper.position = (player.x,0.1,player.z)
        sniper.rotation_x = -90
        sniper.collider = "box"
        sniper.parent = scene
    if key == "f" and playerHasSword:
        playerHasSword = False
        playerHasWeapon = False
        sword.position = (player.x,0.1,player.z)
        sword.rotation_x = -90
        sword.collider = "box"
        sword.parent = scene
    if key == "p":
        bullet = Entity()
        startWave()
    if key == "space" and staminaBar.value > 5 and player.grounded:
        staminaBar.value -= 5
    if key == "r" and playerHasWeapon and totalAmmo > 0:
        if playerHasGun and ammo < 30:
            Audio("gunReloads.mp3", loop=False)
            invoke(reload, delay = .3)
        elif playerHasSniper and ammo < 10:
            Audio("gunReloads.mp3", loop=False)
            invoke(reload, delay=.3)
def pause_handler_input(key):
    global player
    if key == 'escape':
        application.paused = not application.paused
        pause_text.enabled = application.paused
        menuBackground.enabled = True if application.paused else False
        player.on_disable() if application.paused else player.on_enable()
#--------------------- Ursina Functions ---------------------#

pause_handler = Entity(ignore_paused=True)
pause_handler.input = pause_handler_input


app.run()