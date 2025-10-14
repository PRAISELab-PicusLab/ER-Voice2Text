"""
Servizio per integrazione con NVIDIA NIM API
Gestisce le chiamate LLM per l'estrazione di entità cliniche
"""

from openai import OpenAI
from django.conf import settings
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class NVIDIANIMService:
    """
    Servizio per chiamate LLM via NVIDIA NIM
    """
    
    def __init__(self):
        self.model = getattr(settings, 'NVIDIA_MODEL', "openai/gpt-oss-20b")
        self.available = bool(settings.NVIDIA_API_KEY)

        if self.available:
            self.client = OpenAI(
                base_url=settings.NVIDIA_BASE_URL,
                api_key=settings.NVIDIA_API_KEY
            )
        else:
            self.client = None
            logger.warning("NVIDIA_API_KEY non configurata - servizio LLM non disponibile (fallback abilitato)")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testa la connessione con NVIDIA NIM API
        
        Returns:
            Dizionario con informazioni sulla connessione
        """
        if not self.available:
            return {
                'success': False,
                'error': 'NVIDIA_API_KEY non configurata',
                'config': {
                    'base_url': settings.NVIDIA_BASE_URL,
                    'model': self.model,
                    'api_key_configured': False
                }
            }
        
        try:
            # Test semplice con una richiesta minimale
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test connection. Rispondi semplicemente 'OK'."}],
                temperature=0.1,
                max_tokens=10
            )
            
            response_text = completion.choices[0].message.content
            
            return {
                'success': True,
                'response': response_text,
                'config': {
                    'base_url': settings.NVIDIA_BASE_URL,
                    'model': self.model,
                    'api_key_configured': True
                }
            }
        except Exception as e:
            logger.error(f"Errore test connessione NVIDIA NIM: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'config': {
                    'base_url': settings.NVIDIA_BASE_URL,
                    'model': self.model,
                    'api_key_configured': bool(settings.NVIDIA_API_KEY)
                }
            }
    
    def extract_clinical_entities(self, transcript_text: str, usage_mode: str = "") -> Dict[str, Any]:
        """
        Estrae entità cliniche dal testo trascritto usando NVIDIA NIM
        
        Args:
            transcript_text: Testo della trascrizione medica
            usage_mode: Modalità d'uso (es. "Checkup", "Emergency")
            
        Returns:
            Dizionario con entità cliniche estratte
        """
        if not self.available or not self.client:
            logger.warning("NVIDIA NIM non disponibile: utilizzo fallback locale per estrazione entità")
            return self._fallback_response("NVIDIA_API_KEY non configurata")
        
        prompt = self._create_extraction_prompt(transcript_text, usage_mode)
        print(f"\n=== PROMPT NVIDIA NIM ===")
        print(f"{prompt}")
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Bassa temperatura per output più deterministico
                top_p=0.9,
                max_tokens=2048,
                stream=True  # Usa streaming come suggerito dalla documentazione
            )
            
            # Raccoglie la risposta dallo stream
            response_text = ""
            reasoning_text = ""
            
            print(f"\n=== RISPOSTA NVIDIA NIM (STREAMING) ===")
            for chunk in completion:
                # Gestisce reasoning content se presente
                reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
                if reasoning:
                    reasoning_text += reasoning
                    print(f"[REASONING] {reasoning}", end="")
                
                # Gestisce il contenuto normale
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    response_text += content
                    print(content, end="")
            
            print(f"\n=== FINE STREAMING ===")
            print(f"Testo completo: {response_text}")
            print(f"Lunghezza: {len(response_text)} caratteri")
            if reasoning_text:
                print(f"Reasoning: {reasoning_text}")
            print(f"===========================\n")
            
            # Estrai e parsa il JSON dalla risposta
            extracted_data = self._parse_json_response(response_text)
            
            print(f"\n=== PARSING JSON ===")
            print(f"Extracted data: {extracted_data}")
            print(f"Tipo: {type(extracted_data)}")
            if extracted_data is None:
                print("ERRORE: extracted_data è None - parsing fallito")
            print(f"====================\n")
            
            if extracted_data:
                # Normalizza i campi seguendo la logica del Project 2
                normalized_data = self._normalize_fields(extracted_data, usage_mode)
                
                # Valida i campi estratti
                validation_errors = self._validate_fields(normalized_data, transcript_text)
                
                return {
                    'extracted_data': normalized_data,
                    'validation_errors': validation_errors,
                    'llm_model': self.model,
                    'extraction_timestamp': datetime.utcnow().isoformat(),
                    'raw_response': response_text
                }
            else:
                logger.error("Impossibile parsare la risposta JSON")
                return {}
                
        except Exception as e:
            warning = f"Errore durante estrazione entità via NIM: {str(e)}"
            logger.error(warning)
            return self._fallback_response(warning)
    
    def _create_extraction_prompt(self, text: str, usage_mode: str) -> str:
        """Crea il prompt per l'estrazione entità"""
        prompt = f"""Estrai le informazioni richieste in formato JSON dal seguente testo clinico in italiano:

{text}

----

Requisiti:
- Traduci campi e valori nella stessa lingua del testo di input (italiano).
- Mantieni il JSON compatto e ben formattato.
- Per i campi non esplicitamente menzionati nel testo, restituisci una stringa vuota "".
- Estrai solo informazioni effettivamente presenti nel testo.
- IMPORTANTE: Per i parametri vitali, INCLUDI SEMPRE le unità di misura quando disponibili.

Informazioni richieste:
- first_name: nome del paziente
- last_name: cognome del paziente  
- access_mode: modalità di arrivo del paziente
- birth_date: data di nascita (YYYY-MM-DD)
- birth_place: luogo di nascita
- age: età
- gender: sesso (M/F/O)
- residence_city: città di residenza
- residence_address: indirizzo di residenza
- phone: numero di telefono
- skin_state: stato della cute
- consciousness_state: stato di coscienza
- pupils_state: stato delle pupille
- respiratory_state: stato respiratorio
- history: anamnesi
- medications_taken: farmaci assunti
- symptoms: sintomi riferiti
- heart_rate: frequenza cardiaca (INCLUDI unità: es. "120 bpm")
- oxygenation: saturazione ossigeno (INCLUDI unità: es. "95%")
- blood_pressure: pressione arteriosa (INCLUDI unità: es. "120/80 mmHg")
- temperature: temperatura corporea (INCLUDI unità: es. "37.2°C")
- blood_glucose: glicemia (INCLUDI unità: es. "110 mg/dl")
- medical_actions: azioni mediche effettuate
- assessment: valutazione clinica
- plan: piano terapeutico
- triage_code: codice triage (bianco/verde/giallo/rosso/nero)

JSON:
"""
        return prompt
    
    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Estrae e parsa il JSON dalla risposta del modello"""
        print(f"\n=== DEBUG PARSING ===")
        print(f"Testo da parsare: '{response_text[:500]}...'")
        
        try:
            # Trova il primo blocco JSON nella risposta
            start = response_text.find('{')
            print(f"Posizione primo '{{': {start}")
            if start == -1:
                print("ERRORE: Nessun '{' trovato nella risposta")
                return None
            
            depth = 0
            for i in range(start, len(response_text)):
                if response_text[i] == '{':
                    depth += 1
                elif response_text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        json_str = response_text[start:i+1]
                        print(f"JSON estratto: '{json_str}'")
                        result = json.loads(json_str)
                        print(f"JSON parsato con successo: {result}")
                        return result
            
            print("ERRORE: Blocco JSON non chiuso correttamente")
            return None
            
        except json.JSONDecodeError as e:
            print(f"ERRORE parsing JSON: {e}")
            print(f"Testo che ha causato l'errore: '{response_text}'")
            return None
    
    def _normalize_fields(self, data: Dict[str, Any], usage_mode: str = "") -> Dict[str, Any]:
        """
        Normalizza i campi estratti mantenendo le unità di misura quando appropriate
        """
        import re
        
        normalized = data.copy()
        null_values = {"unknown", "na", "n/a", "null", "none", "sconosciuto"}
        
        # Rimuove valori considerati nulli
        for key, value in normalized.items():
            if isinstance(value, str) and value.strip().lower() in null_values:
                normalized[key] = ""
        
        # Normalizzazione frequenza cardiaca - mantieni unità
        if data.get("heart_rate"):
            value_str = str(data["heart_rate"])
            # Se ha già bpm, mantienilo
            if 'bpm' in value_str.lower() or 'battiti' in value_str.lower():
                normalized["heart_rate"] = value_str
            else:
                # Pattern migliorati per gestire spazi
                hr_patterns = [
                    r'(\d{2,3})\s*(bpm|battiti)',  # "120 bpm" con spazi
                    r'(\d{2,3})',                  # solo numero
                ]
                
                for pattern in hr_patterns:
                    match = re.search(pattern, value_str.lower())
                    if match:
                        number = match.group(1)
                        normalized["heart_rate"] = f"{number} bpm"
                        break
                else:
                    normalized["heart_rate"] = ""
        
        # Normalizzazione saturazione ossigeno - mantieni %
        if data.get("oxygenation"):
            value_str = str(data["oxygenation"])
            # Se ha già %, mantienilo
            if '%' in value_str or 'percento' in value_str.lower():
                normalized["oxygenation"] = value_str
            else:
                # Pattern migliorati per gestire spazi
                oxy_patterns = [
                    r'(\d{1,3})\s*(%|percento)',  # "95 %" con spazi
                    r'(\d{1,3})',                 # solo numero
                ]
                
                for pattern in oxy_patterns:
                    match = re.search(pattern, value_str.lower())
                    if match:
                        number = match.group(1)
                        normalized["oxygenation"] = f"{number}%"
                        break
                else:
                    normalized["oxygenation"] = ""
        
        # Normalizzazione temperatura - mantieni °C
        if data.get("temperature"):
            value_str = str(data["temperature"]).replace(",", ".")
            # Se ha già °C o °, mantienilo
            if '°' in value_str or 'gradi' in value_str.lower() or 'celsius' in value_str.lower():
                normalized["temperature"] = value_str
            else:
                # Pattern migliorati per temperatura con spazi
                temp_patterns = [
                    r'([-+]?\d+(?:\.\d+)?)\s*(°c?|gradi|celsius)',  # "37.5 °C" con spazi
                    r'([-+]?\d+(?:\.\d+)?)',                       # solo numero
                ]
                
                for pattern in temp_patterns:
                    match = re.search(pattern, value_str.lower())
                    if match:
                        number = match.group(1)
                        normalized["temperature"] = f"{number}°C"
                        break
                else:
                    normalized["temperature"] = ""
        
        # Normalizzazione glicemia - mantieni mg/dl
        if data.get("blood_glucose"):
            value_str = str(data["blood_glucose"])
            # Se ha già mg/dl, mantienilo
            if 'mg' in value_str.lower() or 'mmol' in value_str.lower():
                normalized["blood_glucose"] = value_str
            else:
                # Pattern migliorati per glicemia con spazi
                glucose_patterns = [
                    r'(\d{2,3})\s*(mg/dl|mg|mmol/l)',  # "110 mg/dl" con spazi
                    r'(\d{2,3})',                      # solo numero
                ]
                
                for pattern in glucose_patterns:
                    match = re.search(pattern, value_str.lower())
                    if match:
                        number = match.group(1)
                        normalized["blood_glucose"] = f"{number} mg/dl"
                        break
                else:
                    normalized["blood_glucose"] = ""
        
        # Normalizzazione pressione arteriosa - mantieni mmHg
        if data.get("blood_pressure"):
            value_str = str(data["blood_pressure"])
            # Se ha già mmHg, mantienilo
            if 'mmhg' in value_str.lower():
                normalized["blood_pressure"] = value_str
            else:
                # Pattern migliorati per gestire spazi in pressione arteriosa
                bp_patterns = [
                    r'(\d{2,3})\s*/\s*(\d{2,3})',  # "120 / 70" con spazi
                    r'(\d{2,3})/(\d{2,3})',        # "120/70" senza spazi  
                    r'(\d{2,3})\s+su\s+(\d{2,3})', # "120 su 70"
                    r'(\d{2,3})\s*-\s*(\d{2,3})',  # "120 - 70"
                ]
                
                for pattern in bp_patterns:
                    match = re.search(pattern, value_str)
                    if match:
                        normalized["blood_pressure"] = f"{match.group(1)}/{match.group(2)} mmHg"
                        break
                else:
                    # Fallback: cerca due numeri separati
                    match = re.findall(r"\b(\d{2,3})\b", value_str)
                    if len(match) == 2:
                        normalized["blood_pressure"] = f"{match[0]}/{match[1]} mmHg"
                    else:
                        normalized["blood_pressure"] = ""
        
        # Se modalità Checkup, mantieni solo campi specifici
        if usage_mode == "Checkup":
            fields_to_keep = {
                "first_name", "last_name", "medications_taken",
                "heart_rate", "oxygenation", "blood_pressure",
                "temperature", "blood_glucose", "medical_actions",
                "assessment", "plan", "symptoms"
            }
            for key in list(normalized.keys()):
                if key not in fields_to_keep:
                    normalized[key] = ""
        
        return normalized
    
    def _validate_fields(self, data: Dict[str, Any], original_text: str) -> list:
        """
        Valida i campi estratti contro il testo originale
        """
        import re
        from dateutil.parser import parse
        from datetime import datetime
        
        error_fields = []
        original_text_lower = original_text.lower()
        
        # Validazione nome
        if data.get("first_name") and str(data["first_name"]).strip():
            name_value = str(data["first_name"]).strip()
            if len(name_value) < 2 or name_value.lower() not in original_text_lower:
                error_fields.append("first_name")
        
        # Validazione cognome
        if data.get("last_name") and str(data["last_name"]).strip():
            surname_value = str(data["last_name"]).strip()
            if len(surname_value) < 2 or surname_value.lower() not in original_text_lower:
                error_fields.append("last_name")
        
        # Validazione età e anno nascita
        age_value = None
        if data.get("age") and str(data["age"]).strip():
            try:
                age_str = str(data["age"]).strip()
                match = re.search(r"\d+", age_str)
                if match:
                    age_value = int(match.group())
                    if not (0 <= age_value <= 130) or str(age_value) not in original_text:
                        error_fields.append("age")
                else:
                    error_fields.append("age")
            except:
                error_fields.append("age")
        
        # Validazione temperatura
        if data.get("temperature") and str(data["temperature"]).strip():
            try:
                temp_value = data["temperature"].split("°C")[0]
                temp_value = float(temp_value)
                if not (0 <= temp_value <= 50) or str(int(temp_value)) not in original_text:
                    error_fields.append("temperature")
            except:
                error_fields.append("temperature")
        
        return list(set(error_fields))

    def _fallback_response(self, warning: Optional[str] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            'extracted_data': {},
            'validation_errors': [],
            'llm_model': 'nvidia-fallback',
            'fallback': True,
            'raw_response': ''
        }

        if warning:
            payload['warnings'] = [warning]

        return payload


# Istanza singleton del servizio - solo se necessario
nvidia_nim_service = NVIDIANIMService()