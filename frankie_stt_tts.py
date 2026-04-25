import speech_recognition as sr
import subprocess
import re
import time

# this is basically frankies brain
# each topic has a keyword that triggers a response 

TOPICS = [
    {
        "name": "greeting",
        "keywords": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"],
        "response": "Hi! I'm Frankie. Nice to talk to you."
    },
    {
        "name": "how_are_you",
        "keywords": ["how are you", "how you doing", "are you okay", "how is it going"],
        "response": "I'm running perfectly, thank you!"
    },
    {
        "name": "identity",
        "keywords": ["your name", "what is your name", "who are you", "what are you", "frankie"],
        "response": "I'm Frankie. I'm here to help people dispose of medicines safely."
    },
    {
        "name": "purpose",
        "keywords": ["what do you do", "what is this", "why are you here", "what is this for", "what can you do"],
        "response": "I help people understand how to safely return unused medicines to a pharmacy."
    },
    {
        "name": "disposal_how",
        "keywords": [
            "unused", "leftover", "old", "expired", "out of date", "dispose", "disposal",
            "throw", "bin", "trash", "garbage", "flush", "sink", "toilet", "drain"
        ],
        "response": "Please return unused medicines to a pharmacy. Do not throw them in the bin or flush them."
    },
    {
        "name": "where_return",
        "keywords": ["where do i", "where can i", "where should i", "return", "take back", "drop off",
                     "pharmacy", "chemist", "boots", "superdrug"],
        "response": "You can return unused medicines to any pharmacy for safe disposal."
    },
    {
        "name": "why_pollution",
        "keywords": [
            "why", "why not", "why should i", "why do i", "why would i", "how come", "what for",
            "pollution", "river", "rivers", "water", "environment", "fish", "wildlife",
            "harm", "damage", "antibiotic", "resistance", "amr"
        ],
        "response": (
            "Because medicines can pollute rivers and harm wildlife if they’re flushed or thrown away. "
            "Returning them to a pharmacy means safe disposal, protecting water and the environment."
        )
    },
    {
        "name": "reuse_sensors",
        "keywords": ["reuse", "re-use", "recycle", "recycling", "sensor", "temperature", "humidity",
                     "quality", "safe", "checked", "check"],
        "response": (
            "Medicine reuse is not allowed in UK community pharmacies because storage conditions at home are unknown. "
            "Sensor-based packaging could help show if storage conditions stayed safe."
        )
    },
    {
        "name": "thanks",
        "keywords": ["thank you", "thanks", "appreciate", "cheers"],
        "response": "You're welcome!"
    },
    {
        "name": "favourite_colour",
        "keywords": ["favourite colour", "favorite color", "favourite color", "favorite colour"],
        "response": "Blue, obviously!"
    },
    {
        "name": "bye",
        "keywords": ["bye", "goodbye", "see you", "see ya", "later"],
        "response": "Goodbye! Take care."
    },
]


VOICE = "Samantha" #change voice (female/male)
RATE = "170"

#for prototyping on my macbook before using raspberry pi
def speak(text: str):
    """macOS text-to-speech using 'say'."""
    if not text:
        return
    print("Frankie:", text)
    subprocess.run(["say", "-v", VOICE, "-r", RATE, text], check=False)

#cleans up the input from users and turns everything lowercase
def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text

# this decides how frankie responds 
# checks input for keywords to match a response to
def get_reply(user_text: str) -> str:
    if not user_text:
        return "I didn’t catch that. Could you say it again?"

    t = normalize(user_text)

    
    if t in ["why", "why though", "how come", "what for"]:
        for topic in TOPICS:
            if topic["name"] == "why_pollution":
                return topic["response"]

# go through each topic and count keyword matches
# topic with the highest score is chosen as the response

    best_topic = None
    best_score = 0

    for topic in TOPICS:
        score = 0
        for kw in topic["keywords"]:
            if kw in t:
                score += 1
        if score > best_score:
            best_score = score
            best_topic = topic

    if best_topic and best_score > 0:
        return best_topic["response"]

    return (
        "I can help with unused medicines. You can ask: "
        "how to dispose of them, where to return them, or why it matters for rivers."
    )


# listens to user through microphone and converts speech to text
# uses Google speech recognition API

def listen_once(timeout: int = 5) -> str | None:
    r = sr.Recognizer()
    r.energy_threshold = 300
    r.pause_threshold = 0.8
    r.non_speaking_duration = 0.4

    with sr.Microphone() as source:
        print("Calibrating noise…")
        r.adjust_for_ambient_noise(source, duration=0.5) # adjusts for background noise

        print("Listening…")
        audio = r.listen(source, timeout=timeout)

    print("Recognising…")
    try:
        text = r.recognize_google(audio)
        print(f"\nUser: {text}\n")
        return text
    except sr.UnknownValueError:
        print("Sorry, I couldn't understand that.")
        return None
    except sr.RequestError as e:
        print("API error:", e)
        return None

# main interaction loop
# starts convo immediately when triggered
def run_conversation_session(
    idle_timeout_seconds: int = 10,   # end if nobody speaks for 10s
    max_total_seconds: int = 60,      # cap to limit convo
    max_turns: int = 6               
):
    """
    Starts speaking immediately.
    Continues while user engages.
    Ends when no speech for idle_timeout_seconds OR caps reached.
    Drops a couple of facts during the interaction.
    """

    FACTS = [
        "Quick fact: The NHS estimates around three hundred million pounds worth of prescribed medicines are wasted in England each year.",
        "Quick fact: In England, community pharmacies are required to accept unwanted medicines for safe disposal.",
        "Quick fact: Even very low levels of some medicines in water can affect wildlife.",
        "Quick fact: Antibiotic residues in the environment can add pressure that contributes to antimicrobial resistance over time."
    ]

    speak(
        "Hello! I'm Frankie. Please return unused medicines to a pharmacy for safe disposal. "
        "Don't put them in the bin or flush them."
    )

    start_time = time.time()
    last_engaged_time = start_time
    turns = 0

    # Speak facts after these successful user turns (not by time)
    fact_after_turns = [1, 3]
    fact_index = 0

    while True:
        now = time.time()

        # limits the conversation timing
        if now - start_time > max_total_seconds:
            break
        if turns >= max_turns:
            break

        # End interaction if user stops engaging
        if now - last_engaged_time > idle_timeout_seconds:
            break

        
        try:
            user_text = listen_once(timeout=4)
        except sr.WaitTimeoutError:
            continue

        if not user_text:
            continue

        last_engaged_time = time.time()
        turns += 1

        reply = get_reply(user_text)
        speak(reply)

        # Drop a fact naturally in convo after certain turns
        if fact_index < len(fact_after_turns) and turns >= fact_after_turns[fact_index]:
            speak(FACTS[fact_index % len(FACTS)])
            fact_index += 1

    speak(
        "Thank you for taking your time to talk to me. Please remember to return unused medicines to a pharmacy instead of putting them in a bin. Thank you!"
    )

def main():

    run_conversation_session(idle_timeout_seconds=10, max_total_seconds=60, max_turns=6)

if __name__ == "__main__":
    main()