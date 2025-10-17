"""
Unified service for extracting clinical entities
Handles both LLM (NVIDIA NIM) and NER (Text2NER) extraction
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

from .nvidia_nim import nvidia_nim_service, get_nvidia_nim_service
from .ner_service import ner_service

logger = logging.getLogger(__name__)


class ExtractionMethod(Enum):
    """
    Listing of available clinical entity extraction methods.
    
    :cvar LLM: Extraction using Large Language Model (NVIDIA NIM)
    :cvar NER: Extraction using Named Entity Recognition
    """
    LLM = "llm"
    NER = "ner"


class ClinicalExtractionService:
    """
    Unified service for extracting clinical entities from medical transcriptions.

    Allows selection between different extraction methods (LLM and NER)
    while maintaining a consistent interface for usage.

    :ivar llm_service: Service for extraction using LLM
    :type llm_service: Optional[NVIDIANIMService]
    :ivar ner_service: Service for extraction using NER
    :type ner_service: Optional[NERService]
    :ivar default_method: Default extraction method
    :type default_method: ExtractionMethod
    """
    
    def __init__(self):
        """
        Initializes the clinical extraction service.

        Configures the available LLM and NER services, handling any initialization errors
        and setting the default method.
        """
        # Inizializza LLM service
        try:
            self.llm_service = nvidia_nim_service or get_nvidia_nim_service()
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
        Returns the available extraction methods with their operational status.

        :returns: Dictionary containing information about available methods and their status
        :rtype: Dict[str, Dict[str, Any]]
        """
        llm_status = self.llm_service.test_connection()

        # Safe handling for NER
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
        Extract clinical entities from a medical transcription using the specified method.

        :param transcript_text: Text of the medical transcription to analyze
        :type transcript_text: str
        :param method: Extraction method ("llm" or "ner"), if None uses the default
        :type method: str
        :param usage_mode: Usage mode to customize extraction (e.g. "Checkup", "Emergency")
        :type usage_mode: str
        :returns: Dictionary containing the extracted clinical entities and metadata
        :rtype: Dict[str, Any]
        :raises ValueError: If the specified method is invalid
        """
        # Determines the method to use
        if method is None:
            method = self.default_method.value

        # Validates the method
        if method not in ["llm", "ner"]:
            logger.error(f"Invalid extraction method: {method}")
            return self._error_response(f"Unsupported method: {method}")

        # Log of the chosen method
        logger.info(f"Extracting clinical entities with method: {method.upper()}")
        logger.debug(f"Usage mode: {usage_mode}, text length: {len(transcript_text)} characters")

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
            
            logger.info(f"Extraction completed: {len(result.get('extracted_data', {}))} fields extracted, "
                        f"{len(result.get('validation_errors', []))} validation errors")

            return result
            
        except Exception as e:
            logger.error(f"Error during extraction with method {method}: {str(e)}")
            return self._error_response(f"Extraction error: {str(e)}")
    
    def _extract_with_llm(self, transcript_text: str, usage_mode: str) -> Dict[str, Any]:
        """Extract entities using the LLM service
        
        :param transcript_text: Text of the medical transcription to analyze
        :type transcript_text: str
        :param usage_mode: Usage mode to customize extraction
        :type usage_mode: str
        :returns: Extracted clinical entities and metadata
        :rtype: Dict[str, Any]
        """
        return self.llm_service.extract_clinical_entities(transcript_text, usage_mode)
    
    def _extract_with_ner(self, transcript_text: str, usage_mode: str) -> Dict[str, Any]:
        """Extract entities using the NER service
        
        :param transcript_text: Text of the medical transcription to analyze
        :type transcript_text: str
        :param usage_mode: Usage mode to customize extraction
        :type usage_mode: str
        :returns: Extracted clinical entities and metadata
        :rtype: Dict[str, Any]
        """
        if not self.ner_service:
            return self._error_response("Servizio NER non disponibile")
        
        try:
            return self.ner_service.extract_clinical_entities(transcript_text, usage_mode)
        except Exception as e:
            logger.error(f"Errore nell'estrazione NER: {e}")
            return self._error_response(f"Errore NER: {str(e)}")
    
    def set_default_method(self, method: str) -> bool:
        """
        Setting of default extraction method

        :param method: Method to set as default ("llm" or "ner")
        :type method: str
        :returns: True if the method was set successfully
        :rtype: bool
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
        Execute extraction with both methods for comparison
        WARNING: This is a costly operation, use only for testing/debugging

        :param transcript_text: Text of the medical transcription
        :type transcript_text: str
        :param usage_mode: Usage mode
        :type usage_mode: str
        :returns: Dictionary with results from both methods
        :rtype: Dict[str, Any]
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
        """Compare extracted fields from both methods
        
        :param llm_data: Extracted data from LLM
        :type llm_data: Dict
        :param ner_data: Extracted data from NER
        :type ner_data: Dict
        :returns: Comparison results including matching and differing fields
        :rtype: Dict[str, Any]
        """
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
        """Create a standardized error response
        
        :param error_message: Description of the error
        :type error_message: str
        :returns: Standardized error response dictionary
        :rtype: Dict[str, Any]
        """
        return {
            'extracted_data': {},
            'validation_errors': [error_message],
            'extraction_method': 'error',
            'timestamp': self._get_timestamp(),
            'success': False,
            'error': error_message
        }
    
    def _get_timestamp(self) -> str:
        """Returns the current timestamp in ISO format

        :returns: Current timestamp in ISO format
        :rtype: str
        """
        from datetime import datetime
        return datetime.now().isoformat()


# Istanza singleton del servizio unificato
clinical_extraction_service = ClinicalExtractionService()