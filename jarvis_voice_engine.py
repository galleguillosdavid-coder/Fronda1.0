"""
J.A.R.V.I.S. Neural Voice Engine (Python + Ollama + Edge-TTS)
Permite interactuar por voz con Ollama usando voces neuronales de alta definición.
"""
import os
import sys
import json
import asyncio
import tempfile
import urllib.request

VOICE = "es-ES-AlvaroNeural"  # Voz neural masculina en español realista (o "en-GB-RyanNeural" para Jarvis inglés)
OLLAMA_API = "http://127.0.0.1:11434/api/chat"
MODEL = "jarvis"

async def speak_neural(text: str):
    """Sintetiza voz neural con edge-tts y reproduce el audio"""
    try:
        import edge_tts
        import pygame
        
        # Limpiar markdown y bloques de código
        clean_text = text.replace("```", "").replace("*", "").replace("#", "").strip()
        if not clean_text:
            return
            
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name
            
        communicate = edge_tts.Communicate(clean_text, VOICE, rate="+5%", pitch="-2Hz")
        await communicate.save(temp_path)
        
        pygame.mixer.init()
        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
        
        try:
            os.remove(temp_path)
        except:
            pass
    except Exception as e:
        print(f"[Aviso Audio]: {e}")

def query_ollama(prompt: str) -> str:
    """Envía la directiva a Ollama local y retorna la respuesta"""
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }).encode("utf-8")
    
    req = urllib.request.Request(
        OLLAMA_API,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
            return data.get("message", {}).get("content", "")
    except Exception as e:
        return f"Error de comunicación con el núcleo de Ollama: {e}"

def listen_microphone() -> str:
    """Captura audio del micrófono y lo convierte a texto"""
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("\n🎙️ [ESCUCHANDO...] Habla ahora, señor:")
            r.adjust_for_ambient_noise(source, duration=0.8)
            audio = r.listen(source, timeout=8, phrase_time_limit=12)
            print("⚡ [PROCESANDO VOZ...]")
            text = r.recognize_google(audio, language="es-ES")
            print(f"👤 Tú: {text}")
            return text
    except Exception as e:
        return ""

async def main():
    print("=" * 60)
    print("       J.A.R.V.I.S. MOTOR DE VOZ NEURAL EN LÍNEA")
    print("=" * 60)
    print(f"Modelo Ollama: {MODEL} | Voz Neural: {VOICE}")
    print("Di 'salir' o 'apagar' para terminar.\n")
    
    await speak_neural("Sistemas de voz neural activos. Estoy listo para escucharle, señor.")
    
    while True:
        try:
            text = listen_microphone()
            if not text:
                continue
                
            if text.lower() in ["salir", "apagar", "cerrar", "adios jarvis"]:
                await speak_neural("Desconectando sistemas. Hasta luego, señor.")
                break
                
            print(f"⚡ Consultando a Ollama ({MODEL})...")
            response = query_ollama(text)
            print(f"\n🤖 JARVIS:\n{response}\n")
            
            await speak_neural(response)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    asyncio.run(main())
