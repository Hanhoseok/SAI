from gtts import gTTS
import os
import time
import pyglet
def speak(S_text,S_lang):
    name = S_text + ".mp3"
    tts = gTTS(text=S_text, lang=S_lang)
    tts.save(name)
    music = pyglet.media.load(name, streaming=False)
    music.play()
    time.sleep(music.duration)
    os.remove(name)


