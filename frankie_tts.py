import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 160)
engine.setProperty('volume', 1.0)
engine.say("Hi! I'm Frankie. Nice to see you again.")
engine.runAndWait()


