
import time
import numpy as np
import pygame
import sys, os
import keyboard


pygame.init()
pygame.joystick.init()


import datetime

# coding: utf-8

import ctypes.wintypes
import ctypes
import time
import sys

SendInput = ctypes.windll.user32.SendInput

# C struct redefinitions
PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time",ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                 ("mi", MouseInput),
                 ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]


def PressKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput( 0, hexKeyCode, 0x0008, 0, ctypes.pointer(extra) )
    x = Input( ctypes.c_ulong(1), ii_ )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
def ReleaseKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput( 0, hexKeyCode, 0x0008 | 0x0002, 0, ctypes.pointer(extra) )
    x = Input( ctypes.c_ulong(1), ii_ )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


class GamePadConverter:

    def parseKeys(self,key):
        if key is None:
            return []
        if not isinstance(key, (list, tuple)):
            return [key]
        return key

    def pressButton(self, button, amount):
        if amount==0:
            return
        #print( button, amount)
        for i in range(amount):
            PressKey(button)
            time.sleep(0.001)
            ReleaseKey(button)


class ButtonsToKeys(GamePadConverter):
    def __init__(self, keyMapping, device=0):
        self.keyMapping = keyMapping
        self.device = device
        self.keyStates = {key:False for key in self.keyMapping}

    def read( self, joysticks ):
        joystick = joysticks[self.device]

        for key in self.keyStates:
            state = joystick.get_button(key)
            if state!=self.keyStates[key]:
                #Act
                if state:
                    PressKey(self.keyMapping[key])
                else:
                    ReleaseKey(self.keyMapping[key])

                self.keyStates[key] = state
                print(key)

    def tick(self, t, dt):
        pass
        #self.pressButton(k, int(bPress))
class AxisToKeys(GamePadConverter):
    def __init__(self, key, axis, device=0, negative=False):
        self.key = key
        self.deadZone=0.3
        self.device = device
        self.keyState = False
        self.axis = axis
        self.negative=negative
    def read( self, joysticks ):
        joystick = joysticks[self.device]

        if self.negative:
            state = joystick.get_axis(self.axis)<=-self.deadZone
        else:
            state = joystick.get_axis(self.axis)>=self.deadZone
        if state!=self.keyState:
            #Act
            if state:
                PressKey(self.key)
            else:
                ReleaseKey(self.key)

            self.keyState = state

    def tick(self, t, dt):
        pass
        #self.pressButton(k, int(bPress))

class HatReader():
    def __init__(self,device=0, xOnchange=None, yOnchange=None):
        self.device=device
        self.status = [0,0]
        self.xOnchange = xOnchange
        self.yOnchange = yOnchange

    def read(self, joysticks ):
        joystick = joysticks[self.device]

        stateX, stateY = joystick.get_hat(0)
        if stateX!=self.status[0] and self.xOnchange is not None:
            self.xOnchange(stateX)
            self.status[0] = stateX

        if stateY!=self.status[1] and self.yOnchange is not None:
            self.yOnchange(stateY)
            self.status[1] = stateY


import pickle
import os
class RelativeAxisToPresses(GamePadConverter):

    def __init__(self,
        keyA=None, # Can be one or more
        keyB=None,
        axis=0, # Axis 0 is up/down, 1-left right
        device=0,
        deadZoneRatio=0.25, # This part is ignored as speed
        vMax=25.0  # In keypresses per second, None to hold
        ):
        self.deadZoneRatio = deadZoneRatio
        self.vMax = vMax
        self.device=device
        self.axis = axis
        self.configPath = './%s_%s.pickle' % (self.device, self.axis )
        self.loadConfig()

        self.aKeys = self.parseKeys(keyA)
        self.bKeys = self.parseKeys(keyB)

        self.speed = [0,0]
        self.lastPresses =[None,None]
        self.cumPresses= np.array([0.0,0.0])
        self.hat = HatReader(self.device, self.changeMapper ,self.changeSensitivity)

    def loadConfig(self):
        if os.path.exists(self.configPath):
            with open(self.configPath,'rb') as f:
                d = pickle.load(f)
                if 'deadZone' in d:
                    self.deadZoneRatio = d['deadZone']
                    print('Set deadzone to %s' % self.deadZoneRatio )
                if 'vMax' in d:
                    self.vMax = d['vMax']
                    print('Set vmax to %s' % self.vMax )


    def writeConfig(self):

        with open(self.configPath,'wb') as f:
            pickle.dump({'deadZone':self.deadZoneRatio, 'vMax':self.vMax},f)


    def changeSensitivity(self, state):
        if state==1:
            self.vMax += 1
            print('Sensitivity %s is now %s' % (self.device, self.vMax))
        if state==-1:
            self.vMax -= 1
            print('Sensitivity %s is now %s' % (self.device, self.vMax))

        self.writeConfig()
    def changeMapper(self, state):
        if state==1:
            self.deadZoneRatio += 0.01
            print('deadzone %s is now %s' % (self.device, self.deadZoneRatio))
        if state==-1:
            self.deadZoneRatio -= 0.01
            print('deadzone %s is now %s' % (self.device, self.deadZoneRatio))
        self.writeConfig()
    def read( self, joysticks ):
        self.hat.read(joysticks)
        joystick = joysticks[self.device]

        ratio =  joystick.get_axis(self.axis)
        #ratio = (val)/(32768.0)
        #scale:


        if ratio>self.deadZoneRatio:
            sratio = ratio #-self.deadZoneRatio
            aRatio = 0.0
            bRatio = sratio
            self.cumPresses[1] = 0.0
        elif ratio<-self.deadZoneRatio:
            sratio = abs(ratio) #+self.deadZoneRatio
            aRatio = sratio
            bRatio = 0.0
            self.cumPresses[0] = 0.0
        else:
            bRatio=0.0
            aRatio=0.0
            self.cumPresses[0] = 0.0
            self.cumPresses[1] = 0.0


        self.speed = np.array([ self.ratToSpeed(bRatio), self.ratToSpeed(aRatio)])


        #print("##:")
        #print(self.speed,self.cumPresses)
        #print(ratio,self.speed)

    def ratToSpeed(self, ratio):
        if self.vMax is None:
            return (ratio>0)*1
        return  self.vMax*ratio #(self.vMax*ratio)*(self.vMax*ratio)

    def tick(self, t, dt):
        # Per delta time we need to press the knobs
        self.cumPresses += self.speed*dt

        #pop:
        (aKeep,bKeep), (aPress,bPress) = np.modf( self.cumPresses )
        self.cumPresses = np.array( (aKeep, bKeep))
        #print( (aKeep,aPress), (bKeep,bPress) )

        for k in self.aKeys:
            self.pressButton(k, int(aPress))
        for k in self.bKeys:
            self.pressButton(k, int(bPress))
        #timeSpan = t - np.array(self.lastPresses)


listeners = [
    RelativeAxisToPresses(0xCD,0xCB,0,0),
    #RelativeAxisToPresses(0xD0,0xC8,axis=1,device=0),

    AxisToKeys(0xD0, axis=1, device=0),
    AxisToKeys(0xC8, axis=1, device=0, negative=True),

    AxisToKeys(0x21, axis=2, device=0),
    AxisToKeys(0x22, axis=2, device=0, negative=True),
    #6 start
    ButtonsToKeys({0:0x14, 1:0x15, 2:0x16, 3:0x17, 4:0x18, 5:0x19, 6:0x01, 7:0x1C}, device=0),

    RelativeAxisToPresses(0x2C,0x2D,axis=0,device=1),
    #RelativeAxisToPresses(0x2E,0x2F,axis=1,device=1),
    AxisToKeys(0x2E, axis=1, device=1),
    AxisToKeys(0x2F, axis=1, device=1, negative=True),

    AxisToKeys(0x23, axis=2, device=1),
    AxisToKeys(0x24, axis=2, device=1, negative=True),
    ButtonsToKeys({0:0x25, 1:0x26, 2:0x27, 3:0x28, 4:0x29, 5:0x2A, 6:0x01, 7:0x1C}, device=1),

]


def utcnow_microseconds():
    system_time = ctypes.wintypes.FILETIME()
    ctypes.windll.kernel32.GetSystemTimeAsFileTime(ctypes.byref(system_time))
    large = (system_time.dwHighDateTime << 32) + system_time.dwLowDateTime
    return large // 10 - 11644473600000000

prev = 0
lastTime = utcnow_microseconds()

joystick_count = pygame.joystick.get_count()

joysticks = {}
for i in range(joystick_count) :
    j = pygame.joystick.Joystick(i)
    joysticks[i] = j

    j.init()
    print(j.get_name())
    print(j.get_numaxes())

done=False
updateTime=0.001
while done==False:
    #events = get_gamepad()
    pygame.event.pump()
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT: # If user clicked close
            done=True # Flag that we are done so we exit this loop

    for listener in listeners:
        listener.read(joysticks)

    now = utcnow_microseconds()
    dt = float( now-lastTime)
    dt*= 0.001 * 0.001
    if dt>=updateTime:
        #print('update:',dt)

        for listener in listeners:
            listener.tick(now, dt)

        #Recalculate because we took some time processing
        lastTime= utcnow_microseconds()
