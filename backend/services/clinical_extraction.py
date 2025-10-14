"""
Servizio unificato per estrazione entità cliniche
Gestisce sia l'estrazione LLM (NVIDIA NIM) che NER (Text2NER)
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

from .nvidia_nim import nvidia_nim_service
from .ner_service import ner_service

logger = logging.getLogger(__name__)


class ExtractionMethod(Enum):
    """Metodi di estrazione disponibili"""
    LLM = "llm"
    NER = "ner"


class ClinicalExtractionService:
    """
    Servizio unificato per estrazione entità cliniche
    Permette di scegliere tra LLM e NER mantenendo un'interfaccia consistente
    """
    
    def __init__(self):
        
        # Inizializza LLM service
        try:
            self.llm_service = nvidia_nim_service
        except Exception as e:
            logger.warning(f"Impossibile inizializzare servizio LLM: {e}")
            self.llm_service = None
        
        # Inizializza NER service con gestione errori
        try:
            self.ner_service = ner_service
        except Exception as e:
            logger.warning(f"Impossibile inizializzare servizio NER: {e}")
            self.ner_service = None
            
        self.default_method = ExtractionMethod.LLM
    
    def get_available_methods(self) -> Dict[str, Dict[str, Any]]:
        """
        Restituisce i metodi di estrazione disponibili con il loro stato
        
        Returns:
            Dizionario con informazioni sui metodi disponibili
        """
        llm_status = self.llm_service.test_connection()
        
        # Gestione sicura per NER
        if self.ner_service:
            try:
                ner_status = self.ner_service.test_connection()
            except Exception as e:
                logger.error(f"Errore test NER service: {e}")
                ner_status = {
                    'success': False,
                    'error': f'Errore inizializzazione: {str(e)}',
                    'config': {'model_loaded': False}
                }
        else:
            ner_status = {
                'success': False,
                'error': 'Servizio NER non inizializzato',
                'config': {'model_loaded': False}
            }
        
        return {
            "llm": {
                "name": "Large Language Model (NVIDIA NIM)",
                "available": llm_status['success'],
                "model": getattr(self.llm_service, 'model', 'N/A'),
                "description": "Estrazione basata su modello linguistico avanzato",
                "status": llm_status
            },
            "ner": {
                "name": "Named Entity Recognition (Text2NER)",
                "available": ner_status['success'],
                "model": getattr(self.ner_service, 'model_path', 'pacovalentino/Text2NER') if self.ner_service else 'N/A',
                "description": "Estrazione basata su riconoscimento entità nominate",
                "status": ner_status
            }
        }
    
    def extract_clinical_entities(
        self, 
        transcript_text: str, 
        method: str = None,
        usage_mode: str = ""
    ) -> Dict[str, Any]:
        """
        Estrae entità cliniche dal testo usando il metodo specificato
        
        Args:
            transcript_text: Testo della trascrizione medica
            method: Metodo di estrazione ("llm" o "ner")
            usage_mode: Modalità d'uso (es. "Checkup", "Emergency")
            
        Returns:
            Dizionario con entità cliniche estratte
        """
        # Determina il metodo da usare
        if method is None:
            method = self.default_method.value
        
        # Valida il metodo
        if method not in ["llm", "ner"]:
            logger.error(f"Metodo di estrazione non valido: {method}")
            return self._error_response(f"Metodo non supportato: {method}")
        
        # Log del metodo scelto
        logger.info(f"Estrazione entità cliniche con metodo: {method.upper()}")
        print(f"\n=== ESTRAZIONE ENTITÀ CLINICHE ===")
        print(f"Metodo: {method.upper()}")
        print(f"Modalità: {usage_mode}")
        print(f"Lunghezza testo: {len(transcript_text)} caratteri")
        
        try:
            if method == ExtractionMethod.LLM.value:
                result = self._extract_with_llm(transcript_text, usage_mode)
            elif method == ExtractionMethod.NER.value:
                result = self._extract_with_ner(transcript_text, usage_mode)
            else:
                return self._error_response(f"Metodo non implementato: {method}")
            
            # Aggiungi metadati comuni
            result['extraction_method'] = method
            result['timestamp'] = self._get_timestamp()
            result['text_length'] = len(transcript_text)
            
            print(f"Estrazione completata con successo")
            print(f"Dati estratti: {len(result.get('extracted_data', {}))} campi")
            print(f"Errori validazione: {len(result.get('validation_errors', []))}")
            print(f"==================================\n")
            
            return result
            
        except Exception as e:
            logger.error(f"Errore durante estrazione con metodo {method}: {str(e)}")
            return self._error_response(f"Errore estrazione: {str(e)}")
    
    def _extract_with_llm(self, transcript_text: str, usage_mode: str) -> Dict[str, Any]:
        """Estrae entità usando il servizio LLM"""
        return self.llm_service.extract_clinical_entities(transcript_text, usage_mode)
    
    def _extract_with_ner(self, transcript_text: str, usage_mode: str) -> Dict[str, Any]:
        """Estrae entità usando il servizio NER"""
        if not self.ner_service:
            return self._error_response("Servizio NER non disponibile")
        
        try:
            return self.ner_service.extract_clinical_entities(transcript_text, usage_mode)
        except Exception as e:
            logger.error(f"Errore nell'estrazione NER: {e}")
            return self._error_response(f"Errore NER: {str(e)}")
    
    def set_default_method(self, method: str) -> bool:
        """
        Imposta il metodo di estrazione predefinito
        
        Args:
            method: Metodo da impostare come predefinito ("llm" o "ner")
            
        Returns:
            True se il metodo è stato impostato correttamente
        """
        if method in ["llm", "ner"]:
            self.default_method = ExtractionMethod.LLM if method == "llm" else ExtractionMethod.NER
            logger.info(f"Metodo predefinito impostato su: {method.upper()}")
            return True
        else:
            logger.error(f"Metodo non valido per default: {method}")
            return False
    
    def get_method_comparison(self, transcript_text: str, usage_mode: str = "") -> Dict[str, Any]:
        """
        Esegue l'estrazione con entrambi i metodi per confronto
        ATTENZIONE: Operazione costosa, usare solo per testing/debug
        
        Args:
            transcript_text: Testo della trascrizione medica
            usage_mode: Modalità d'uso
            
        Returns:
            Dizionario con risultati di entrambi i metodi
        """
        logger.warning("Esecuzione confronto tra metodi LLM e NER - operazione costosa")
        
        results = {
            "comparison_timestamp": self._get_timestamp(),
            "text_length": len(transcript_text),
            "usage_mode": usage_mode
        }
        
        # Estrazione con LLM
        try:
            llm_result = self._extract_with_llm(transcript_text, usage_mode)
            results["llm_result"] = llm_result
            results["llm_success"] = True
        except Exception as e:
            results["llm_result"] = self._error_response(f"Errore LLM: {str(e)}")
            results["llm_success"] = False
        
        # Estrazione con NER
        try:
            ner_result = self._extract_with_ner(transcript_text, usage_mode)
            results["ner_result"] = ner_result
            results["ner_success"] = True
        except Exception as e:
            results["ner_result"] = self._error_response(f"Errore NER: {str(e)}")
            results["ner_success"] = False
        
        # Confronto dei risultati
        if results["llm_success"] and results["ner_success"]:
            results["field_comparison"] = self._compare_extracted_fields(
                results["llm_result"].get("extracted_data", {}),
                results["ner_result"].get("extracted_data", {})
            )
        
        return results
    
    def _compare_extracted_fields(self, llm_data: Dict, ner_data: Dict) -> Dict[str, Any]:
        """Confronta i campi estratti dai due metodi"""
        comparison = {
            "matching_fields": [],
            "different_fields": [],
            "llm_only_fields": [],
            "ner_only_fields": [],
            "similarity_score": 0.0
        }
        
        all_fields = set(llm_data.keys()) | set(ner_data.keys())
        
        for field in all_fields:
            llm_value = str(llm_data.get(field, "")).strip()
            ner_value = str(ner_data.get(field, "")).strip()
            
            if field in llm_data and field in ner_data:
                if llm_value == ner_value:
                    comparison["matching_fields"].append(field)
                else:
                    comparison["different_fields"].append({
                        "field": field,
                        "llm_value": llm_value,
                        "ner_value": ner_value
                    })
            elif field in llm_data:
                comparison["llm_only_fields"].append(field)
            else:
                comparison["ner_only_fields"].append(field)
        
        # Calcola score di similarità
        total_fields = len(all_fields)
        matching_fields = len(comparison["matching_fields"])
        comparison["similarity_score"] = (matching_fields / total_fields) * 100 if total_fields > 0 else 0
        
        return comparison
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Crea una risposta di errore standardizzata"""
        return {
            'extracted_data': {},
            'validation_errors': [error_message],
            'extraction_method': 'error',
            'timestamp': self._get_timestamp(),
            'success': False,
            'error': error_message
        }
    
    def _get_timestamp(self) -> str:
        """Restituisce timestamp corrente in formato ISO"""
        from datetime import datetime
        return datetime.now().isoformat()


# Istanza singleton del servizio unificato
clinical_extraction_service = ClinicalExtractionService()