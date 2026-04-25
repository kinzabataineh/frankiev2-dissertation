import sys
from speech import speak

if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) or "Hi! I am Frankie."
    speak(text, voice="Samantha", rate=170)

