from typing import List, Optional

def chunk_text(text: str, size: int = 6) -> List[str]:
    words = text.split()
    return [" ".join(words[i:i+size]) for i in range(0, len(words), size)]

def generate_subtitles(user_lang: str, audio_lang: str, transcript: str) -> Optional[List[str]]:
    """
    Returns subtitle chunks if language mismatch, otherwise None.
    In real use, you’d add ASR + translation here.
    """
    if user_lang == audio_lang:
        return None
    return chunk_text(transcript, size=7)

if __name__ == "__main__":
    # Demo
    user_pref = "en"
    audio_lang = "es"
    transcript = "hola a todos bienvenidos al show espero que lo disfruten mucho"
    
    subs = generate_subtitles(user_pref, audio_lang, transcript)
    if subs:
        print("Generated subtitles:")
        for line in subs:
            print("  ", line)
    else:
        print("No subtitles needed.")
