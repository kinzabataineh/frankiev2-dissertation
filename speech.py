import subprocess

def speak(text, voice=None, rate=None):
    cmd = ["say", text]
    if voice:
        cmd += ["-v", voice]       
    if rate:
        cmd += ["-r", str(rate)]   
    subprocess.run(cmd)


