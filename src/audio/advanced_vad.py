import asyncio
import collections
import webrtcvad
import numpy as np
import time
import configparser
from pathlib import Path


class AdvancedVADSegmenter:
    """VAD avanzado con supresión de ruido y detección de bucles."""

    def __init__(self, sample_rate=16000, frame_ms=20, config_file="config.ini"):
        assert frame_ms in (10, 20, 30)
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.bytes_per_frame = int(sample_rate * frame_ms / 1000) * 2
        
        # Cargar configuración
        self.config = configparser.ConfigParser()
        config_path = Path(config_file)
        if config_path.exists():
            self.config.read(config_path)
        else:
            # Valores por defecto
            self.config.read_dict({
                'vad': {
                    'aggressiveness': '3',
                    'padding_ms': '600',
                    'voice_ratio_threshold': '0.8'
                },
                'audio': {
                    'min_speech_duration_ms': '300',
                    'max_silence_duration_ms': '800',
                    'voice_threshold_db': '-30',
                    'noise_gate_db': '-45'
                },
                'feedback_prevention': {
                    'enable_feedback_detection': 'true',
                    'max_consecutive_translations': '3',
                    'cooldown_after_translation_ms': '500',
                    'similarity_threshold': '0.8'
                }
            })
        
        # Configuración VAD
        aggressiveness = int(self.config.get('vad', 'aggressiveness', fallback=3))
        padding_ms = int(self.config.get('vad', 'padding_ms', fallback=600))
        self.voice_ratio_threshold = float(self.config.get('vad', 'voice_ratio_threshold', fallback=0.8))
        
        self.vad = webrtcvad.Vad(aggressiveness)
        self.num_pad = max(1, padding_ms // frame_ms)
        
        # Configuración de audio
        self.min_speech_duration_ms = int(self.config.get('audio', 'min_speech_duration_ms', fallback=300))
        self.max_silence_duration_ms = int(self.config.get('audio', 'max_silence_duration_ms', fallback=800))
        self.voice_threshold_db = float(self.config.get('audio', 'voice_threshold_db', fallback=-30))
        self.noise_gate_db = float(self.config.get('audio', 'noise_gate_db', fallback=-45))
        
        # Prevención de bucles
        self.enable_feedback_detection = self.config.getboolean('feedback_prevention', 'enable_feedback_detection', fallback=True)
        self.max_consecutive = int(self.config.get('feedback_prevention', 'max_consecutive_translations', fallback=3))
        self.cooldown_ms = int(self.config.get('feedback_prevention', 'cooldown_after_translation_ms', fallback=500))
        
        # Estado interno
        self.consecutive_count = 0
        self.last_translation_time = 0
        self.recent_utterances = collections.deque(maxlen=5)
        
        print(f"[VAD] Configuración cargada: aggressiveness={aggressiveness}, padding={padding_ms}ms")
        print(f"[VAD] Umbral de voz: {self.voice_threshold_db}dB, puerta de ruido: {self.noise_gate_db}dB")

    def reload_config(self):
        """Recarga la configuración desde el archivo config.ini en tiempo real."""
        try:
            # Recargar el archivo de configuración
            self.config.read(self.config_file)
            
            # Actualizar parámetros de VAD
            aggressiveness = int(self.config.get('vad', 'aggressiveness', fallback=3))
            self.vad.set_mode(aggressiveness)
            
            padding_ms = int(self.config.get('vad', 'padding_ms', fallback=600))
            self.num_pad = max(1, padding_ms // self.frame_ms)
            
            # Actualizar configuración de audio
            self.min_speech_duration_ms = int(self.config.get('audio', 'min_speech_duration_ms', fallback=300))
            self.max_silence_duration_ms = int(self.config.get('audio', 'max_silence_duration_ms', fallback=800))
            self.voice_threshold_db = float(self.config.get('audio', 'voice_threshold_db', fallback=-30))
            self.noise_gate_db = float(self.config.get('audio', 'noise_gate_db', fallback=-45))
            
            # Actualizar prevención de bucles
            self.enable_feedback_detection = self.config.getboolean('feedback_prevention', 'enable_feedback_detection', fallback=True)
            self.max_consecutive = int(self.config.get('feedback_prevention', 'max_consecutive_translations', fallback=3))
            self.cooldown_ms = int(self.config.get('feedback_prevention', 'cooldown_after_translation_ms', fallback=500))
            
            print(f"[VAD] ✅ Configuración recargada: aggressiveness={aggressiveness}, padding={padding_ms}ms")
            print(f"[VAD] ✅ Niveles actualizados: voz={self.voice_threshold_db}dB, ruido={self.noise_gate_db}dB")
            
        except Exception as e:
            print(f"[VAD] ❌ Error recargando configuración: {e}")

    def calculate_rms_db(self, audio_bytes):
        """Calcula el RMS en decibelios del audio."""
        if len(audio_bytes) == 0:
            return -100
        
        # Convertir bytes a int16
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        
        # Calcular RMS
        rms = np.sqrt(np.mean(audio_int16.astype(np.float32) ** 2))
        
        # Convertir a dB (referencia: 32767 = 0dB)
        if rms > 0:
            db = 20 * np.log10(rms / 32767.0)
        else:
            db = -100
            
        return db

    def is_noise_gate_open(self, audio_bytes):
        """Verifica si el audio supera la puerta de ruido."""
        db_level = self.calculate_rms_db(audio_bytes)
        return db_level > self.noise_gate_db

    def is_voice_level_sufficient(self, audio_bytes):
        """Verifica si el nivel de audio es suficiente para voz."""
        db_level = self.calculate_rms_db(audio_bytes)
        return db_level > self.voice_threshold_db

    def should_process_utterance(self, utterance_bytes):
        """Determina si el utterance debe procesarse (anti-bucle)."""
        current_time = time.time() * 1000  # en ms
        
        # Verificar cooldown después de traducción
        if current_time - self.last_translation_time < self.cooldown_ms:
            print(f"[VAD] Utterance ignorado por cooldown ({current_time - self.last_translation_time:.0f}ms)")
            return False
        
        # Verificar duración mínima
        duration_ms = len(utterance_bytes) * 1000 // (self.sample_rate * 2)
        if duration_ms < self.min_speech_duration_ms:
            print(f"[VAD] Utterance muy corto ignorado ({duration_ms}ms)")
            return False
        
        # Verificar nivel de voz suficiente
        if not self.is_voice_level_sufficient(utterance_bytes):
            print(f"[VAD] Utterance ignorado por nivel insuficiente ({self.calculate_rms_db(utterance_bytes):.1f}dB)")
            return False
        
        # Verificar máximo de traducciones consecutivas
        if self.consecutive_count >= self.max_consecutive:
            print(f"[VAD] Máximo de traducciones consecutivas alcanzado ({self.consecutive_count})")
            self.consecutive_count = 0
            return False
        
        return True

    def mark_translation_completed(self):
        """Marca que se completó una traducción."""
        self.last_translation_time = time.time() * 1000
        self.consecutive_count += 1

    async def segments(self, frames_q: asyncio.Queue):
        ring = collections.deque(maxlen=self.num_pad)
        voiced_frames = bytearray()
        triggered = False
        silence_count = 0
        
        while True:
            frame: bytes = await frames_q.get()
            
            # Normalizar tamaño exacto de frame
            if len(frame) != self.bytes_per_frame:
                if len(frame) < self.bytes_per_frame:
                    frame = frame + b"\x00" * (self.bytes_per_frame - len(frame))
                else:
                    frame = frame[: self.bytes_per_frame]

            # Aplicar puerta de ruido
            if not self.is_noise_gate_open(frame):
                # Frame demasiado silencioso, tratarlo como silencio
                is_speech = False
            else:
                # Frame suficientemente fuerte, verificar con VAD
                is_speech = self.vad.is_speech(frame, self.sample_rate)

            if not triggered:
                ring.append((frame, is_speech))
                num_voiced = sum(1 for _, s in ring if s)
                # Usar umbral más estricto
                if num_voiced > self.voice_ratio_threshold * ring.maxlen:
                    triggered = True
                    for f, _ in ring:
                        voiced_frames.extend(f)
                    ring.clear()
                    print(f"[VAD] Inicio de utterance detectado")
            else:
                voiced_frames.extend(frame)
                ring.append((frame, is_speech))
                if not is_speech:
                    silence_count += 1
                else:
                    silence_count = 0

                # Usar configuración dinámica para el final
                max_silence_frames = self.max_silence_duration_ms // self.frame_ms
                if silence_count >= min(self.num_pad, max_silence_frames):
                    # Fin de utterance
                    utterance = bytes(voiced_frames)
                    
                    # Verificar si debe procesarse
                    if self.should_process_utterance(utterance):
                        duration_ms = len(utterance) * 1000 // (self.sample_rate * 2)
                        db_level = self.calculate_rms_db(utterance)
                        print(f"[VAD] Utterance válido: {duration_ms}ms, {db_level:.1f}dB")
                        yield utterance
                        # Resetear contador solo si fue procesado exitosamente
                        # self.mark_translation_completed() se llamará externamente
                    
                    voiced_frames = bytearray()
                    ring.clear()
                    triggered = False
                    silence_count = 0


# Compatibilidad con el VAD original
VADSegmenter = AdvancedVADSegmenter
