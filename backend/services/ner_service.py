"""
Service for extracting clinical entities with NER model
Manages extraction using the Text2NER model from pacovalentino/Text2NER
"""

import torch
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class NERService:
    """
    Service for extracting clinical entities with NER model pacovalentino/Text2NER
    """
    
    def __init__(self):
        """Initialize the NER service"""
        self.model_path = "pacovalentino/Text2NER"
        self.ner_pipeline = None
        self.available = False
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the NER model"""
        try:
            from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
            
            logger.info(f"Caricamento modello NER: {self.model_path}")
            
            # Prova a caricare con impostazioni più conservative
            tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                trust_remote_code=False,
                local_files_only=False
            )
            model = AutoModelForTokenClassification.from_pretrained(
                self.model_path,
                trust_remote_code=False,
                local_files_only=False,
                torch_dtype="auto"
            )
            model.eval()
            
            # Usa CPU se CUDA non è disponibile o causa problemi
            device = 0 if torch.cuda.is_available() else -1
            
            self.ner_pipeline = pipeline(
                "ner",
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="simple",
                device=device
            )
            
            self.available = True
            logger.info("Modello NER caricato con successo")
            
        except ImportError as e:
            logger.error(f"Dipendenze mancanti per NER: {str(e)}")
            self.available = False
        except Exception as e:
            logger.error(f"Errore durante il caricamento del modello NER: {str(e)}")
            logger.info("NER non disponibile - verrà usato fallback")
            self.available = False
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the availability of the NER model

        :returns: Dictionary with model information
        :rtype: Dict[str, Any]
        """
        if not self.available:
            return {
                'success': False,
                'error': 'Modello NER non disponibile - utilizzare metodo LLM',
                'config': {
                    'model_path': self.model_path,
                    'cuda_available': torch.cuda.is_available(),
                    'model_loaded': False,
                    'device': 'none'
                }
            }
        
        try:
            # Test semplice con testo di esempio
            test_text = "Il paziente Mario Rossi, maschio, 58 anni, presentava SpO₂ 91%."
            results = self.ner_pipeline(test_text)
            
            # Determina il device in modo sicuro
            device_info = 'unknown'
            try:
                if hasattr(self.ner_pipeline, 'device'):
                    device_info = str(self.ner_pipeline.device)
                elif hasattr(self.ner_pipeline, 'model') and hasattr(self.ner_pipeline.model, 'device'):
                    device_info = str(self.ner_pipeline.model.device)
            except:
                device_info = 'cpu' if not torch.cuda.is_available() else 'auto'
            
            return {
                'success': True,
                'test_entities_found': len(results),
                'config': {
                    'model_path': self.model_path,
                    'cuda_available': torch.cuda.is_available(),
                    'model_loaded': True,
                    'device': device_info
                }
            }
        except Exception as e:
            logger.error(f"Errore test modello NER: {str(e)}")
            return {
                'success': False,
                'error': f"Test fallito: {str(e)}",
                'config': {
                    'model_path': self.model_path,
                    'cuda_available': torch.cuda.is_available(),
                    'model_loaded': self.available,
                    'device': 'error'
                }
            }
    
    def extract_clinical_entities(self, transcript_text: str, usage_mode: str = "") -> Dict[str, Any]:
        """
        Extract clinical entities from the transcribed text using the NER model
        
        :param str transcript_text: Transcribed medical text
        :type transcript_text: str
        :param str usage_mode: Usage mode (e.g. "Checkup", "Emergency")
        :type usage_mode: str
        :returns: Dictionary with extracted clinical entities
        :rtype: Dict[str, Any]
        """
        if not self.available or not self.ner_pipeline:
            logger.warning("Modello NER non disponibile: utilizzo fallback")
            return self._fallback_response("Modello NER non caricato")
        
        try:
            logger.debug(f"Avvio estrazione NER con modalità: {usage_mode}")
            
            # Splitta il testo in frasi per analisi più accurata
            sentences = self._split_text_into_sentences(transcript_text)
            
            # Estrai entità da ogni frase e accumula i risultati
            all_ner_results = []
            for i, sentence in enumerate(sentences):
                if sentence.strip():  # Salta frasi vuote
                    sentence = sentence + "." if not sentence.endswith(('.', '!', '?')) else sentence
                    
                    sentence_results = self.ner_pipeline(sentence)
                    all_ner_results.extend(sentence_results)
            
            logger.debug(f"Totale entità trovate: {len(all_ner_results)}")
            if logger.isEnabledFor(logging.DEBUG):
                for result in all_ner_results:
                    logger.debug(f"  {result['word']:<30} | {result['entity_group']}")
            
            # Mappa le entità NER ai campi standard con aggregazione
            extracted_data = self._map_ner_to_clinical_fields_aggregated(all_ner_results, transcript_text)
            
            # Normalizza i campi mantenendo le unità di misura
            normalized_data = self._normalize_fields_with_units(extracted_data, usage_mode)
            
            # Valida i campi estratti
            validation_errors = self._validate_fields(normalized_data, transcript_text)
            
            logger.debug(f"Dati estratti e normalizzati: {len(normalized_data)} campi")
            
            return {
                'extracted_data': normalized_data,
                'validation_errors': validation_errors,
                'extraction_method': 'ner',
                'model': self.model_path,
                'entities_found': len(all_ner_results),
                'raw_ner_results': all_ner_results,
                'sentences_processed': len(sentences)
            }
            
        except Exception as e:
            logger.error(f"Errore durante estrazione entità NER: {str(e)}")
            return self._fallback_response(f"Errore estrazione NER: {str(e)}")
    
    def _split_text_into_sentences(self, text: str) -> List[str]:
        """
        Split the text into sentences using appropriate delimiters for the medical context

        :param str text: Text to split
        :type text: str
        :return: List of sentences
        :rtype: List[str]
        """
        import re
        
        # Pattern per identificare fine frase nel contesto medico
        # Considera punti, punti esclamativi, punti interrogativi e due punti seguiti da spazio/newline
        sentence_delimiters = r'[.!?:]\s+|[.!?:]$'
        
        # Splitta il testo mantenendo i delimitatori
        sentences = re.split(sentence_delimiters, text.strip())
        
        # Filtra frasi vuote o troppo corte
        filtered_sentences = []
        for sentence in sentences:
            cleaned = sentence.strip()
            if cleaned and len(cleaned) > 3:  # Frasi di almeno 4 caratteri
                filtered_sentences.append(cleaned)
        
        logger.debug(f"Frasi estratte: {len(filtered_sentences)} frasi")
        return filtered_sentences
    
    def _map_ner_to_clinical_fields_aggregated(self, ner_results: List[Dict], transcript_text: str) -> Dict[str, Any]:
        """
        Map the NER entities to standard clinical fields with aggregation by type
        Entities of the same type are joined with a comma

        :param ner_results: NER model results from all sentences
        :type ner_results: List[Dict]
        :param transcript_text: Original text for context
        :type transcript_text: str
        :return: Dictionary with mapped and aggregated clinical fields
        :rtype: Dict[str, Any]
        """
        from collections import defaultdict
        
        # Raggruppa entità per tipo
        entities_by_type = defaultdict(list)
        
        for entity in ner_results:
            entity_text = entity['word'].strip()
            label = entity['entity_group']
            entities_by_type[label].append(entity_text)
        
        logger.debug(f"Entità raggruppate per tipo: {len(entities_by_type)} tipi")
        
        # Inizializza tutti i campi vuoti
        clinical_data = {
            'first_name': '',
            'last_name': '',
            'access_mode': '',
            'birth_date': '',
            'birth_place': '',
            'age': '',
            'gender': '',
            'residence_city': '',
            'residence_address': '',
            'phone': '',
            'skin_state': '',
            'consciousness_state': '',
            'pupils_state': '',
            'respiratory_state': '',
            'history': '',
            'medications_taken': '',
            'symptoms': '',
            'heart_rate': '',
            'oxygenation': '',
            'blood_pressure': '',
            'temperature': '',
            'blood_glucose': '',
            'medical_actions': '',
            'assessment': '',
            'plan': '',
            'triage_code': ''
        }
        
        # Mappa le entità aggregate ai campi
        for label, entity_texts in entities_by_type.items():
            # Rimuovi duplicati mantenendo l'ordine
            unique_texts = []
            for text in entity_texts:
                if text not in unique_texts:
                    unique_texts.append(text)
            
            # Mapping delle entità NER ai campi clinici con aggregazione
            if label == 'NOME_COGNOME':
                # Per nome e cognome, prova a separare il primo elemento
                if unique_texts:
                    parts = unique_texts[0].split()
                    if len(parts) >= 2:
                        clinical_data['first_name'] = parts[0]
                        clinical_data['last_name'] = ' '.join(parts[1:])
                    else:
                        clinical_data['first_name'] = unique_texts[0]
                        
            elif label == 'SESSO':
                # Per il sesso, prendi il primo valore
                if unique_texts:
                    clinical_data['gender'] = self._normalize_gender(unique_texts[0])
                    
            elif label == 'DATA_NASCITA':
                # Per la data di nascita, prendi il primo valore
                if unique_texts:
                    clinical_data['birth_date'] = self._normalize_date(unique_texts[0])
                    
            elif label == 'LUOGO_NASCITA':
                # Unisci tutti i luoghi di nascita
                clinical_data['birth_place'] = ', '.join(unique_texts)
                    
            elif label == 'COMUNE_RESIDENZA':
                # Unisci tutte le città di residenza
                clinical_data['residence_city'] = ', '.join(unique_texts)
                    
            elif label == 'VIA_RESIDENZA':
                # Unisci tutti gli indirizzi
                clinical_data['residence_address'] = ', '.join(unique_texts)
                    
            elif label in ['TELEFONO', 'NUMERO_TELEFONO']:
                # Unisci tutti i telefoni (supporta entrambe le etichette)
                clinical_data['phone'] = ', '.join(unique_texts)
                
            elif label == 'FC_BPM':
                # Per frequenza cardiaca, mantieni l'unità di misura
                if unique_texts:
                    clinical_data['heart_rate'] = self._extract_with_units(unique_texts, 'bpm')
                
            elif label == 'SpO2':
                # Per saturazione, mantieni l'unità di misura
                if unique_texts:
                    clinical_data['oxygenation'] = self._extract_with_units(unique_texts, '%')
                
            elif label == 'PA_MMHG':
                # Per pressione, mantieni l'unità di misura
                if unique_texts:
                    clinical_data['blood_pressure'] = self._extract_with_units(unique_texts, 'mmHg')
                
            elif label == 'TEMPERATURA':
                # Per temperatura, mantieni l'unità di misura
                if unique_texts:
                    clinical_data['temperature'] = self._extract_with_units(unique_texts, '°C')
                
            elif label == 'GLICEMIA':
                # Per glicemia, mantieni l'unità di misura
                if unique_texts:
                    clinical_data['blood_glucose'] = self._extract_with_units(unique_texts, 'mg/dl')
                
            elif label == 'CUTE':
                # Unisci tutti gli stati della cute
                clinical_data['skin_state'] = ', '.join(unique_texts)
                
            elif label == 'COSCIENZA':
                # Unisci tutti gli stati di coscienza
                clinical_data['consciousness_state'] = ', '.join(unique_texts)
                
            elif label in ['PUPILLE_TIPO_DX', 'PUPILLE_TIPO_SX', 'PUPILLE_REATTIVITA']:
                # Unisci tutte le informazioni sulle pupille
                if clinical_data['pupils_state']:
                    clinical_data['pupils_state'] += ', ' + ', '.join(unique_texts)
                else:
                    clinical_data['pupils_state'] = ', '.join(unique_texts)
                    
            elif label == 'RESPIRO':
                # Unisci tutti gli stati respiratori
                clinical_data['respiratory_state'] = ', '.join(unique_texts)
                
            elif label == 'MEDICINA':
                # Unisci tutti i farmaci
                clinical_data['medications_taken'] = ', '.join(unique_texts)
                    
            elif label == 'CONDIZIONE_RIFERITA':
                # Unisci tutti i sintomi
                clinical_data['symptoms'] = ', '.join(unique_texts)
                    
            elif label in ['PROVVEDIMENTI_ALTRO', 'PROVVEDIMENTI_CIRCOLO', 
                          'PROVVEDIMENTI_IMMOBILIZZAZIONE', 'PROVVEDIMENTI_RESPIRO']:
                # Unisci tutte le azioni mediche
                if clinical_data['medical_actions']:
                    clinical_data['medical_actions'] += ', ' + ', '.join(unique_texts)
                else:
                    clinical_data['medical_actions'] = ', '.join(unique_texts)
                    
            elif label == 'CODICE_USCITA':
                # Per codice triage, prendi il primo valore valido
                if unique_texts:
                    triage_mapping = {
                        'rosso': 'rosso',
                        'giallo': 'giallo', 
                        'verde': 'verde',
                        'bianco': 'bianco',
                        'nero': 'nero'
                    }
                    normalized_code = unique_texts[0].lower()
                    clinical_data['triage_code'] = triage_mapping.get(normalized_code, '')
            
            # Mapping addizionali per etichette che potrebbero essere varianti
            elif label in ['ETA', 'AGE', 'ANNI']:
                # Età del paziente
                clinical_data['age'] = ', '.join(unique_texts)
                
            elif label in ['ANAMNESI', 'STORIA_CLINICA', 'HISTORY']:
                # Storia clinica/anamnesi
                clinical_data['history'] = ', '.join(unique_texts)
                
            elif label in ['VALUTAZIONE', 'ASSESSMENT', 'DIAGNOSI']:
                # Valutazione clinica
                clinical_data['assessment'] = ', '.join(unique_texts)
                
            elif label in ['PIANO', 'PLAN', 'TERAPIA', 'TRATTAMENTO']:
                # Piano terapeutico
                clinical_data['plan'] = ', '.join(unique_texts)
                
            elif label in ['MODALITA_ACCESSO', 'ACCESS_MODE', 'ARRIVO']:
                # Modalità di accesso
                clinical_data['access_mode'] = ', '.join(unique_texts)
            
            # Caso di default per etichette non riconosciute
            else:
                logger.warning(f"Etichetta NER non mappata: '{label}' con valore: {unique_texts}")
        
        return clinical_data
    
    def _extract_with_units(self, entity_texts: List[str], default_unit: str) -> str:
        """
        Extract numeric values while keeping the unit of measurement if present.
        Correctly handles spaces in values like "120 / 70"
        
        :param entity_texts: List of entity texts to analyze
        :type entity_texts: List[str]
        :param default_unit: Default unit to use if none found
        :type default_unit: str
        :return: Extracted value with unit
        :rtype: str
        """
        import re
        
        for text in entity_texts:
            text_clean = text.strip()
            
            # Pattern speciali per temperatura con spazi e punti anomali
            if default_unit.lower() == '°c':
                temp_patterns = [
                    r'(\d+)\.\s*(\d+)\s*(gradi|°c?|celsius)',   # "36. 8 gradi"
                    r'(\d+),\s*(\d+)\s*(gradi|°c?|celsius)',    # "36, 8 gradi"
                    r'(\d+(?:[.,]\d+)?)\s*(gradi|°c?|celsius)', # "36.8 gradi" normale
                    r'(\d+(?:[.,]\d+)?)',                       # solo numero
                ]
                
                for pattern in temp_patterns:
                    match = re.search(pattern, text_clean.lower())
                    if match:
                        if len(match.groups()) >= 2 and match.group(2) and match.group(2).isdigit():
                            # Caso "36. 8" o "36, 8" - ricostruisci il numero
                            temp_value = f"{match.group(1)}.{match.group(2)}"
                        else:
                            # Caso normale "36.8"
                            temp_value = match.group(1).replace(',', '.')
                        
                        try:
                            # Valida che sia una temperatura ragionevole
                            temp_float = float(temp_value)
                            if 30 <= temp_float <= 45:  # Range temperatura corporea ragionevole
                                return f"{temp_value} {default_unit}"
                        except ValueError:
                            continue
            
            # Pattern speciali per pressione arteriosa con spazi
            if default_unit.lower() == 'mmhg':
                bp_patterns = [
                    r'(\d+)\s*/\s*(\d+)\s*([a-zA-Z]+)?',  # "120 / 70" o "120/70 mmHg"
                    r'(\d+)\s*su\s*(\d+)\s*([a-zA-Z]+)?',  # "120 su 70"
                    r'(\d+)\s*-\s*(\d+)\s*([a-zA-Z]+)?',   # "120 - 70"
                ]
                
                for pattern in bp_patterns:
                    match = re.search(pattern, text_clean)
                    if match:
                        systolic = match.group(1)
                        diastolic = match.group(2)
                        unit = match.group(3) if match.group(3) else default_unit
                        
                        # Normalizza unità pressione
                        if unit.lower() in ['mmhg', 'mm', 'hg']:
                            unit = 'mmHg'
                        else:
                            unit = default_unit
                            
                        return f"{systolic}/{diastolic} {unit}"
            
            # Pattern per valori con spazi "95 %" o "120 bpm"
            patterns = [
                r'(\d+(?:[.,]\d+)?)\s*([a-zA-Z/%°]+)',  # numero + spazio + unità
                r'(\d+(?:[.,]\d+)?)\s*([%°])',          # numero + spazio + simbolo
                r'(\d+(?:[.,]\d+)?)\s+([a-zA-Z]+)',     # numero + spazi + unità
                r'(\d+(?:[.,]\d+)?)',                   # solo numero
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text_clean)
                if match:
                    value = match.group(1).replace(',', '.')
                    unit = match.group(2) if len(match.groups()) > 1 and match.group(2) else default_unit
                    
                    # Normalizza alcune unità comuni
                    unit_mapping = {
                        'bpm': 'bpm',
                        'battiti': 'bpm',
                        'beat': 'bpm',
                        'beats': 'bpm',
                        '%': '%',
                        'percento': '%',
                        'percent': '%',
                        '°c': '°C',
                        '°': '°C',
                        'gradi': '°C',
                        'celsius': '°C',
                        'c': '°C',
                        'mmhg': 'mmHg',
                        'mm': 'mmHg',
                        'hg': 'mmHg',
                        'mg/dl': 'mg/dl',
                        'mgdl': 'mg/dl',
                        'mg': 'mg/dl'
                    }
                    
                    normalized_unit = unit_mapping.get(unit.lower(), unit)
                    return f"{value} {normalized_unit}"
        
        return ', '.join(entity_texts)  # Fallback: unisci tutto
    
    def _map_ner_to_clinical_fields(self, ner_results: List[Dict], transcript_text: str) -> Dict[str, Any]:
        """
        Map the NER entities to standard clinical fields

        :param ner_results: Risultati del modello NER
        :type ner_results: List[Dict]
        :param transcript_text: Testo originale per contesto
        :type transcript_text: str
        :return: Dizionario con campi clinici mappati
        :rtype: Dict[str, Any]
        """
        # Inizializza tutti i campi vuoti
        clinical_data = {
            'first_name': '',
            'last_name': '',
            'access_mode': '',
            'birth_date': '',
            'birth_place': '',
            'age': '',
            'gender': '',
            'residence_city': '',
            'residence_address': '',
            'phone': '',
            'skin_state': '',
            'consciousness_state': '',
            'pupils_state': '',
            'respiratory_state': '',
            'history': '',
            'medications_taken': '',
            'symptoms': '',
            'heart_rate': '',
            'oxygenation': '',
            'blood_pressure': '',
            'temperature': '',
            'blood_glucose': '',
            'medical_actions': '',
            'assessment': '',
            'plan': '',
            'triage_code': ''
        }
        
        # Mappa le entità NER ai campi
        for entity in ner_results:
            entity_text = entity['word'].strip()
            label = entity['entity_group']
            
            # Mapping delle entità NER ai campi clinici
            if label == 'NOME_COGNOME':
                # Prova a separare nome e cognome
                parts = entity_text.split()
                if len(parts) >= 2:
                    clinical_data['first_name'] = parts[0]
                    clinical_data['last_name'] = ' '.join(parts[1:])
                else:
                    clinical_data['first_name'] = entity_text
                    
            elif label == 'SESSO':
                clinical_data['gender'] = self._normalize_gender(entity_text)
                
            elif label == 'DATA_NASCITA':
                clinical_data['birth_date'] = self._normalize_date(entity_text)
                
            elif label == 'LUOGO_NASCITA':
                clinical_data['birth_place'] = entity_text
                
            elif label == 'COMUNE_RESIDENZA':
                clinical_data['residence_city'] = entity_text
                
            elif label == 'VIA_RESIDENZA':
                if clinical_data['residence_address']:
                    clinical_data['residence_address'] += f", {entity_text}"
                else:
                    clinical_data['residence_address'] = entity_text
                    
            elif label == 'NUMERO_RESIDENZA':
                if clinical_data['residence_address']:
                    clinical_data['residence_address'] += f" {entity_text}"
                else:
                    clinical_data['residence_address'] = entity_text
                    
            elif label == 'NUMERO_TELEFONO':
                clinical_data['phone'] = entity_text
                
            elif label == 'FC_BPM':
                # Usa la normalizzazione robusta per frequenza cardiaca
                hr_value, _ = self._extract_numeric_with_unit(
                    entity_text, 
                    ['bpm', 'battiti', 'beat'], 
                    (30, 250)
                )
                if hr_value:
                    clinical_data['heart_rate'] = str(int(hr_value))
                else:
                    # Fallback con estrazione semplice
                    match = re.search(r'(\d{2,3})', entity_text)
                    if match:
                        clinical_data['heart_rate'] = match.group(1)
                
            elif label == 'SpO2':
                # Usa la normalizzazione robusta per saturazione
                sat_value, _ = self._extract_numeric_with_unit(
                    entity_text,
                    ['%', 'percento', 'spo2'],
                    (50, 100)
                )
                if sat_value:
                    clinical_data['oxygenation'] = str(int(sat_value))
                else:
                    # Fallback
                    match = re.search(r'(\d{1,3})', entity_text)
                    if match and 50 <= int(match.group(1)) <= 100:
                        clinical_data['oxygenation'] = match.group(1)
                
            elif label == 'PA_MMHG':
                # Normalizzazione robusta per pressione arteriosa
                bp_text = entity_text.lower()
                bp_patterns = [
                    r'(\d{2,3})[\/\-](\d{2,3})',
                    r'(\d{2,3})\s*su\s*(\d{2,3})',
                    r'sistolica[:\s]*(\d{2,3}).*diastolica[:\s]*(\d{2,3})'
                ]
                
                for pattern in bp_patterns:
                    match = re.search(pattern, bp_text)
                    if match:
                        try:
                            systolic, diastolic = int(match.group(1)), int(match.group(2))
                            if 50 <= systolic <= 250 and 30 <= diastolic <= 150 and systolic > diastolic:
                                clinical_data['blood_pressure'] = f"{systolic}/{diastolic}"
                                break
                        except:
                            continue
                
            elif label == 'TEMPERATURA':
                # Normalizzazione robusta per temperatura
                temp_value, _ = self._extract_numeric_with_unit(
                    entity_text,
                    ['°c', '°', 'gradi', 'celsius'],
                    (30, 45)
                )
                if temp_value:
                    clinical_data['temperature'] = round(temp_value, 1)
                else:
                    # Fallback
                    match = re.search(r'(\d{1,2}[.,]\d{1,2})', entity_text.replace(',', '.'))
                    if match:
                        try:
                            temp = float(match.group(1))
                            if 30 <= temp <= 45:
                                clinical_data['temperature'] = round(temp, 1)
                        except:
                            pass
                
            elif label == 'GLICEMIA':
                # Normalizzazione robusta per glicemia
                glucose_value, unit = self._extract_numeric_with_unit(
                    entity_text,
                    ['mg/dl', 'mg', 'mmol/l', 'glicemia'],
                    (30, 600)
                )
                
                if glucose_value:
                    # Conversione da mmol/l a mg/dl se necessario
                    if unit and 'mmol' in unit:
                        glucose_value = glucose_value * 18.0
                    clinical_data['blood_glucose'] = str(int(glucose_value))
                else:
                    # Fallback
                    match = re.search(r'(\d{2,3})', entity_text)
                    if match and 30 <= int(match.group(1)) <= 600:
                        clinical_data['blood_glucose'] = match.group(1)
                
            elif label == 'CUTE':
                clinical_data['skin_state'] = entity_text
                
            elif label == 'COSCIENZA':
                clinical_data['consciousness_state'] = entity_text
                
            elif label in ['PUPILLE_TIPO_DX', 'PUPILLE_TIPO_SX', 'PUPILLE_REATTIVITA']:
                if clinical_data['pupils_state']:
                    clinical_data['pupils_state'] += f", {entity_text}"
                else:
                    clinical_data['pupils_state'] = entity_text
                    
            elif label == 'RESPIRO':
                clinical_data['respiratory_state'] = entity_text
                
            elif label == 'MEDICINA':
                if clinical_data['medications_taken']:
                    clinical_data['medications_taken'] += f", {entity_text}"
                else:
                    clinical_data['medications_taken'] = entity_text
                    
            elif label == 'CONDIZIONE_RIFERITA':
                if clinical_data['symptoms']:
                    clinical_data['symptoms'] += f", {entity_text}"
                else:
                    clinical_data['symptoms'] = entity_text
                    
            elif label in ['PROVVEDIMENTI_ALTRO', 'PROVVEDIMENTI_CIRCOLO', 
                          'PROVVEDIMENTI_IMMOBILIZZAZIONE', 'PROVVEDIMENTI_RESPIRO']:
                if clinical_data['medical_actions']:
                    clinical_data['medical_actions'] += f", {entity_text}"
                else:
                    clinical_data['medical_actions'] = entity_text
                    
            elif label == 'CODICE_USCITA':
                # Mappa i codici uscita ai codici triage
                triage_mapping = {
                    'rosso': 'rosso',
                    'giallo': 'giallo', 
                    'verde': 'verde',
                    'bianco': 'bianco',
                    'nero': 'nero'
                }
                normalized_code = entity_text.lower()
                clinical_data['triage_code'] = triage_mapping.get(normalized_code, '')
        
        return clinical_data
    
    def _normalize_gender(self, text: str) -> str:
        """Normalize the gender field with robust mapping
        
        :param str text: Input text
        :type text: str
        :return: Normalized gender
        :rtype: str
        """
        text_lower = text.lower().strip()
        
        # Mappatura completa per genere maschile
        male_variants = [
            'm', 'maschio', 'maschile', 'male', 'uomo', 'man', 'boy', 'ragazzo',
            'masculine', 'masculino', 'homme', 'hombre'
        ]
        
        # Mappatura completa per genere femminile  
        female_variants = [
            'f', 'femmina', 'femminile', 'female', 'donna', 'woman', 'girl', 'ragazza',
            'feminine', 'feminino', 'femme', 'mujer'
        ]
        
        # Controlla match esatto prima (più specifico)
        if text_lower in male_variants:
            return 'M'
        elif text_lower in female_variants:
            return 'F'
        # Poi controlla se contiene le varianti (solo per parole lunghe > 1 carattere)
        elif any(variant in text_lower for variant in male_variants if len(variant) > 1):
            return 'M'
        elif any(variant in text_lower for variant in female_variants if len(variant) > 1):
            return 'F'
        else:
            return 'O'  # Altro/Non specificato
    
    def _normalize_date(self, text: str) -> str:
        """Normalize a date into the YYYY-MM-DD format with support for Italian formats
        
        :param str text: Input date text
        :type text: str
        :return: Normalized date or original text if parsing fails
        :rtype: str
        """
        import calendar
        
        # Mappatura dei mesi italiani
        italian_months = {
            'gennaio': 1, 'gen': 1,
            'febbraio': 2, 'feb': 2, 
            'marzo': 3, 'mar': 3,
            'aprile': 4, 'apr': 4,
            'maggio': 5, 'mag': 5,
            'giugno': 6, 'giu': 6,
            'luglio': 7, 'lug': 7,
            'agosto': 8, 'ago': 8,
            'settembre': 9, 'set': 9, 'sett': 9,
            'ottobre': 10, 'ott': 10,
            'novembre': 11, 'nov': 11,
            'dicembre': 12, 'dic': 12
        }
        
        text = text.strip().lower()
        
        # Pattern per date numeriche standard
        date_patterns = [
            r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})',  # dd/mm/yyyy
            r'(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})',  # yyyy/mm/dd
            r'(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2})',  # dd/mm/yy
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                part1, part2, part3 = match.groups()
                
                # Determina il formato in base alla lunghezza del terzo gruppo
                if len(part3) == 4:  # Anno completo
                    if int(part3) > 1900:  # yyyy/mm/dd
                        year, month, day = part3, part1, part2
                    else:  # dd/mm/yyyy
                        day, month, year = part1, part2, part3
                else:  # dd/mm/yy
                    day, month, year = part1, part2, f"19{part3}" if int(part3) > 30 else f"20{part3}"
                
                try:
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except:
                    continue
        
        # Pattern per date con mesi in italiano: "23 febbraio 1990"
        month_pattern = r'(\d{1,2})\s+(\w+)\s+(\d{4})'
        match = re.search(month_pattern, text)
        if match:
            day, month_name, year = match.groups()
            
            # Cerca il mese nella mappatura italiana
            month_num = None
            for italian_month, num in italian_months.items():
                if italian_month in month_name.lower():
                    month_num = num
                    break
            
            if month_num:
                try:
                    return f"{year}-{str(month_num).zfill(2)}-{day.zfill(2)}"
                except:
                    pass
        
        # Pattern per date con mesi abbreviati: "23 feb 1990", "feb 23, 1990"
        abbrev_patterns = [
            r'(\d{1,2})\s+(\w{3,4})\s+(\d{4})',  # 23 feb 1990
            r'(\w{3,4})\s+(\d{1,2}),?\s+(\d{4})',  # feb 23, 1990
        ]
        
        for i, pattern in enumerate(abbrev_patterns):
            match = re.search(pattern, text)
            if match:
                if i == 0:  # dd mmm yyyy
                    day, month_abbr, year = match.groups()
                else:  # mmm dd, yyyy
                    month_abbr, day, year = match.groups()
                
                # Cerca il mese nella mappatura italiana
                month_num = None
                for italian_month, num in italian_months.items():
                    if month_abbr.lower() in italian_month or italian_month.startswith(month_abbr.lower()):
                        month_num = num
                        break
                
                if month_num:
                    try:
                        return f"{year}-{str(month_num).zfill(2)}-{day.zfill(2)}"
                    except:
                        continue
        
        # Se non riesce a parsare, restituisce il testo originale
        return text
    
    def _normalize_fields_with_units(self, data: Dict[str, Any], usage_mode: str = "") -> Dict[str, Any]:
        """
        Normalize the extracted fields while preserving units of measurement where appropriate

        :param dict data: Extracted data to normalize
        :type data: Dict[str, Any]
        :param str usage_mode: Usage mode
        :type usage_mode: str
        :return: Normalized data with preserved units of measurement
        :rtype: Dict[str, Any]
        """
        normalized = data.copy()
        null_values = {"unknown", "na", "n/a", "null", "none", "sconosciuto", ""}
        
        # Rimuove valori considerati nulli
        for key, value in normalized.items():
            if isinstance(value, str) and value.strip().lower() in null_values:
                normalized[key] = ""
        
        # Per i parametri vitali, mantieni le unità se già presenti o aggiungile se mancano
        vital_signs_with_units = {
            'heart_rate': 'bpm',
            'oxygenation': '%', 
            'temperature': '°C',
            'blood_glucose': 'mg/dl'
        }
        
        for field, default_unit in vital_signs_with_units.items():
            if data.get(field):
                value_str = str(data[field]).strip()
                if value_str:
                    # Se il valore ha già un'unità, mantienilo
                    if any(unit in value_str.lower() for unit in ['bpm', '%', '°c', '°', 'mg/dl', 'mmhg']):
                        normalized[field] = value_str
                    else:
                        # Se è solo un numero, aggiungi l'unità di default
                        import re
                        number_match = re.search(r'(\d+(?:[.,]\d+)?)', value_str)
                        if number_match:
                            number = number_match.group(1)
                            normalized[field] = f"{number} {default_unit}"
                        else:
                            normalized[field] = value_str
        
        # Per la pressione arteriosa, gestisci il formato speciale
        if data.get("blood_pressure"):
            bp_value = str(data["blood_pressure"]).strip()
            if bp_value:
                # Se contiene già mmHg, mantienilo
                if 'mmhg' not in bp_value.lower():
                    # Se è un formato sistolica/diastolica, aggiungi mmHg
                    import re
                    if re.search(r'\d+[/\-]\d+', bp_value):
                        normalized["blood_pressure"] = f"{bp_value} mmHg"
                    else:
                        normalized["blood_pressure"] = bp_value
                else:
                    normalized["blood_pressure"] = bp_value
        
        # Se modalità Checkup, mantieni solo campi specifici
        if usage_mode == "Checkup":
            fields_to_keep = {
                "first_name", "last_name", "medications_taken",
                "heart_rate", "oxygenation", "blood_pressure",
                "temperature", "blood_glucose", "medical_actions",
                "assessment", "plan", "symptoms"
            }
            normalized = {k: v for k, v in normalized.items() if k in fields_to_keep}
        
        return normalized
    
    def _normalize_fields(self, data: Dict[str, Any], usage_mode: str = "") -> Dict[str, Any]:
        """
        Normalize the extracted fields while preserving units of measurement where appropriate

        :param dict data: Extracted data to normalize
        :type data: Dict[str, Any]
        :param str usage_mode: Usage mode
        :type usage_mode: str
        :return: Normalized data with preserved units of measurement
        :rtype: Dict[str, Any]
        """
        normalized = data.copy()
        null_values = {"unknown", "na", "n/a", "null", "none", "sconosciuto", ""}
        
        # Rimuove valori considerati nulli
        for key, value in normalized.items():
            if isinstance(value, str) and value.strip().lower() in null_values:
                normalized[key] = ""
        
        # Normalizzazione frequenza cardiaca - supporta "bpm", "battiti", etc.
        if data.get("heart_rate"):
            hr_text = str(data["heart_rate"]).lower()
            # Pattern più robusti per FC
            hr_patterns = [
                r"(\d{2,3})\s*(?:bpm|battiti|beat|pulsazioni|bat)",
                r"fc[:\s]*(\d{2,3})",
                r"frequenza[:\s]+cardiaca[:\s]*(\d{2,3})",
                r"(\d{2,3})\s*(?:al|per)\s*minuto",
                r"\b(\d{2,3})\b"  # Fallback per solo numero
            ]
            
            hr_value = None
            for pattern in hr_patterns:
                match = re.search(pattern, hr_text)
                if match:
                    hr_value = int(match.group(1))
                    if 30 <= hr_value <= 250:  # Range fisiologico
                        break
            
            normalized["heart_rate"] = str(hr_value) if hr_value else ""
        
        # Normalizzazione saturazione ossigeno - supporta "%" e varianti
        if data.get("oxygenation"):
            sat_text = str(data["oxygenation"]).lower()
            # Pattern per saturazione
            sat_patterns = [
                r"(\d{1,3})\s*%",
                r"spo2[:\s]*(\d{1,3})",
                r"saturazione[:\s]*(\d{1,3})",
                r"ossigeno[:\s]*(\d{1,3})",
                r"\b(\d{2,3})\b"  # Fallback per solo numero
            ]
            
            sat_value = None
            for pattern in sat_patterns:
                match = re.search(pattern, sat_text)
                if match:
                    sat_value = int(match.group(1))
                    if 50 <= sat_value <= 100:  # Range fisiologico
                        break
            
            normalized["oxygenation"] = str(sat_value) if sat_value else ""
        
        # Normalizzazione temperatura - supporta "°C", "gradi", etc.
        if data.get("temperature"):
            temp_text = str(data["temperature"]).replace(",", ".").lower()
            # Pattern per temperatura
            temp_patterns = [
                r"(\d{1,2}[.,]\d{1,2})\s*(?:°c|gradi|celsius)",
                r"temperatura[:\s]*(\d{1,2}[.,]\d{1,2})",
                r"(\d{1,2}[.,]\d{1,2})\s*°",
                r"(\d{1,2}[.,]\d{1,2})\s*gradi",
                r"(\d{1,2}[.,]\d{1,2})"  # Fallback
            ]
            
            temp_value = None
            for pattern in temp_patterns:
                match = re.search(pattern, temp_text)
                if match:
                    try:
                        temp_value = float(match.group(1).replace(",", "."))
                        if 30 <= temp_value <= 45:  # Range fisiologico
                            break
                    except:
                        continue
            
            normalized["temperature"] = temp_value if temp_value else ""
        
        # Normalizzazione glicemia - supporta "mg/dl", "mmol/l", etc.
        if data.get("blood_glucose"):
            glucose_text = str(data["blood_glucose"]).lower()
            # Pattern per glicemia
            glucose_patterns = [
                r"(\d{2,3})\s*mg/dl",
                r"(\d{2,3})\s*mg",
                r"glicemia[:\s]*(\d{2,3})",
                r"glucosio[:\s]*(\d{2,3})",
                r"(\d{1,2}[.,]\d{1,2})\s*mmol/l",  # Conversione da mmol/l
                r"\b(\d{2,3})\b"  # Fallback
            ]
            
            glucose_value = None
            for i, pattern in enumerate(glucose_patterns):
                match = re.search(pattern, glucose_text)
                if match:
                    try:
                        value = float(match.group(1).replace(",", "."))
                        
                        # Se è in mmol/l, converti in mg/dl
                        if i == 4:  # Pattern mmol/l
                            value = value * 18.0  # Conversione mmol/l -> mg/dl
                        
                        if 30 <= value <= 600:  # Range fisiologico esteso
                            glucose_value = int(value)
                            break
                    except:
                        continue
            
            normalized["blood_glucose"] = str(glucose_value) if glucose_value else ""
        
        # Normalizzazione pressione arteriosa - supporta vari formati
        if data.get("blood_pressure"):
            bp_text = str(data["blood_pressure"]).lower()
            # Pattern per pressione arteriosa
            bp_patterns = [
                r"(\d{2,3})[\/\-](\d{2,3})\s*mmhg",
                r"(\d{2,3})[\/\-](\d{2,3})",
                r"pa[:\s]*(\d{2,3})[\/\-](\d{2,3})",
                r"pressione[:\s]*(\d{2,3})[\/\-](\d{2,3})",
                r"sistolica[:\s]*(\d{2,3}).*diastolica[:\s]*(\d{2,3})",
                r"(\d{2,3})\s*su\s*(\d{2,3})",
                r"(\d{2,3})\s*mmhg.*(\d{2,3})\s*mmhg"
            ]
            
            bp_value = None
            for pattern in bp_patterns:
                match = re.search(pattern, bp_text)
                if match:
                    try:
                        systolic = int(match.group(1))
                        diastolic = int(match.group(2))
                        
                        # Verifica range fisiologici
                        if 50 <= systolic <= 250 and 30 <= diastolic <= 150 and systolic > diastolic:
                            bp_value = f"{systolic}/{diastolic}"
                            break
                    except:
                        continue
            
            normalized["blood_pressure"] = bp_value if bp_value else ""
        
        # Normalizzazione età - estrae numero dagli anni
        if data.get("age"):
            age_text = str(data["age"]).lower()
            age_patterns = [
                r"(\d{1,3})\s*anni",
                r"(\d{1,3})\s*years",
                r"età[:\s]*(\d{1,3})",
                r"\b(\d{1,3})\b"
            ]
            
            age_value = None
            for pattern in age_patterns:
                match = re.search(pattern, age_text)
                if match:
                    age_val = int(match.group(1))
                    if 0 <= age_val <= 120:  # Range ragionevole
                        age_value = age_val
                        break
            
            normalized["age"] = age_value if age_value else ""
        
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
    
    def _extract_numeric_with_unit(self, text: str, expected_units: list, value_range: tuple = None) -> tuple:
        """
        Extract a numeric value with unit of measurement from a text

        :param str text: Text to analyze
        :type text: str
        :param list expected_units: List of expected units (e.g. ['bpm', 'battiti'])
        :type expected_units: list
        :param tuple value_range: Tuple (min, max) for range validation
        :type value_range: tuple
        :return: Tuple (value, unit) or (None, None) if not found
        :rtype: tuple
        """
        text_lower = text.lower().strip()
        
        for unit in expected_units:
            # Pattern per trovare numero + unità
            patterns = [
                rf"(\d+(?:[.,]\d+)?)\s*{re.escape(unit)}",
                rf"{re.escape(unit)}[:\s]*(\d+(?:[.,]\d+)?)",
                rf"(\d+(?:[.,]\d+)?)\s*{re.escape(unit[:3])}"  # Abbreviazione
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    try:
                        value = float(match.group(1).replace(",", "."))
                        
                        # Verifica range se specificato
                        if value_range and not (value_range[0] <= value <= value_range[1]):
                            continue
                            
                        return value, unit
                    except ValueError:
                        continue
        
        return None, None
    
    def _parse_vital_signs_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze a text to extract all present vital signs

        :param str  text: Text containing vital parameters
        :type text: str
        :return: Dictionary with found parameters
        :rtype: Dict[str, Any]
        """
        vitals = {}
        text_lower = text.lower()
        
        # Pattern per riconoscere gruppi di parametri vitali
        vital_patterns = {
            'heart_rate': {
                'patterns': [r'fc[:\s]*(\d{2,3})', r'(\d{2,3})\s*bpm', r'battiti[:\s]*(\d{2,3})'],
                'range': (30, 250)
            },
            'blood_pressure': {
                'patterns': [r'pa[:\s]*(\d{2,3})[\/\-](\d{2,3})', r'(\d{2,3})[\/\-](\d{2,3})\s*mmhg'],
                'validator': lambda m: 50 <= int(m[0]) <= 250 and 30 <= int(m[1]) <= 150
            },
            'oxygenation': {
                'patterns': [r'spo2[:\s]*(\d{1,3})', r'(\d{1,3})\s*%', r'saturazione[:\s]*(\d{1,3})'],
                'range': (50, 100)
            },
            'temperature': {
                'patterns': [r'(\d{1,2}[.,]\d{1,2})\s*°c?', r'temperatura[:\s]*(\d{1,2}[.,]\d{1,2})'],
                'range': (30, 45)
            }
        }
        
        for vital_name, config in vital_patterns.items():
            for pattern in config['patterns']:
                match = re.search(pattern, text_lower)
                if match:
                    try:
                        if vital_name == 'blood_pressure':
                            if len(match.groups()) == 2 and config['validator'](match.groups()):
                                vitals[vital_name] = f"{match.group(1)}/{match.group(2)}"
                        else:
                            value = float(match.group(1).replace(",", "."))
                            if 'range' in config and config['range'][0] <= value <= config['range'][1]:
                                vitals[vital_name] = int(value) if value.is_integer() else value
                        break
                    except (ValueError, AttributeError):
                        continue
        
        return vitals
    
    def _validate_fields(self, data: Dict[str, Any], original_text: str) -> List[str]:
        """
        Validate extracted fields against the original text
        
        :param dict data: Extracted data to validate
        :type data: Dict[str, Any]
        :param str original_text: Original text for context
        :type original_text: str
        :return: List of validation error messages
        :rtype: List[str]
        """
        error_fields = []
        original_text_lower = original_text.lower()
        
        # Validazione nome
        if data.get("first_name") and str(data["first_name"]).strip():
            name_value = str(data["first_name"]).strip()
            if len(name_value) < 2:
                error_fields.append("first_name: nome troppo corto")
        
        # Validazione cognome
        if data.get("last_name") and str(data["last_name"]).strip():
            surname_value = str(data["last_name"]).strip()
            if len(surname_value) < 2:
                error_fields.append("last_name: cognome troppo corto")
        
        # Validazione temperatura
        if data.get("temperature") and str(data["temperature"]).strip():
            try:
                temp_value = data["temperature"].split("°C")[0]
                temp_value = float(temp_value)
                if temp_value < 30 or temp_value > 45:
                    error_fields.append("temperature: valore fuori range normale (30-45°C)")
            except:
                error_fields.append("temperature: formato non valido")
        
        return list(set(error_fields))

    def _fallback_response(self, warning: Optional[str] = None) -> Dict[str, Any]:
        """Response fallback when the NER model is not available
        
        :param str warning: Optional warning message
        :type warning: str
        :return: Fallback response payload
        :rtype: Dict[str, Any]
        """
        payload = {
            'extracted_data': {},
            'validation_errors': [],
            'extraction_method': 'ner-fallback',
            'model': self.model_path,
            'entities_found': 0,
            'raw_ner_results': []
        }

        if warning:
            payload['warnings'] = [warning]

        return payload


# Istanza singleton del servizio NER
ner_service = NERService()