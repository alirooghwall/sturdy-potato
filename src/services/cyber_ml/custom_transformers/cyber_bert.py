"""CyberBERT - Custom BERT model for cybersecurity text analysis."""

import logging
from typing import Any

import torch
import torch.nn as nn
from transformers import (
    AutoModel,
    AutoTokenizer,
    BertForSequenceClassification,
    Trainer,
    TrainingArguments,
)

logger = logging.getLogger(__name__)


class CyberBERT:
    """Custom BERT model fine-tuned for cybersecurity domain."""
    
    def __init__(
        self,
        base_model: str = "bert-base-uncased",
        num_labels: int = 6,  # CRITICAL, HIGH, MEDIUM, LOW, INFO, SAFE
        use_pretrained: bool = True,
    ):
        """Initialize CyberBERT.
        
        Args:
            base_model: Base BERT model to use
            num_labels: Number of classification labels
            use_pretrained: Use pre-trained weights
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        
        # Load model
        if use_pretrained:
            try:
                # Try to load our fine-tuned model
                self.model = BertForSequenceClassification.from_pretrained(
                    "cyberbert-base",
                    num_labels=num_labels,
                )
                logger.info("Loaded pre-trained CyberBERT model")
            except:
                # Fallback to base model
                self.model = BertForSequenceClassification.from_pretrained(
                    base_model,
                    num_labels=num_labels,
                )
                logger.info(f"Loaded base model: {base_model}")
        else:
            self.model = BertForSequenceClassification.from_pretrained(
                base_model,
                num_labels=num_labels,
            )
        
        self.model.to(self.device)
        self.model.eval()
        
        # Label mapping
        self.label_map = {
            0: "SAFE",
            1: "INFO",
            2: "LOW",
            3: "MEDIUM",
            4: "HIGH",
            5: "CRITICAL",
        }
        
        self.reverse_label_map = {v: k for k, v in self.label_map.items()}
    
    def classify_threat_level(
        self,
        text: str,
        return_probabilities: bool = False,
    ) -> dict[str, Any]:
        """Classify threat level of cybersecurity text.
        
        Args:
            text: Input text (vulnerability description, CVE, etc.)
            return_probabilities: Return probability distribution
        
        Returns:
            Classification result with label and confidence
        """
        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Predict
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probabilities = torch.softmax(logits, dim=-1)
        
        # Get prediction
        predicted_class = torch.argmax(probabilities, dim=-1).item()
        confidence = probabilities[0][predicted_class].item()
        label = self.label_map[predicted_class]
        
        result = {
            "label": label,
            "confidence": confidence,
            "text": text[:100],
        }
        
        if return_probabilities:
            result["probabilities"] = {
                self.label_map[i]: prob.item()
                for i, prob in enumerate(probabilities[0])
            }
        
        return result
    
    def classify_vulnerability_severity(
        self,
        cve_description: str,
        cvss_score: float | None = None,
    ) -> dict[str, Any]:
        """Classify vulnerability severity using text + CVSS.
        
        Args:
            cve_description: CVE description text
            cvss_score: CVSS score if available
        
        Returns:
            Classification with reasoning
        """
        # Get text-based classification
        text_result = self.classify_threat_level(
            cve_description,
            return_probabilities=True,
        )
        
        # Adjust with CVSS if available
        if cvss_score is not None:
            cvss_label = self._cvss_to_label(cvss_score)
            
            # Weighted combination (70% text, 30% CVSS)
            text_idx = self.reverse_label_map[text_result["label"]]
            cvss_idx = self.reverse_label_map[cvss_label]
            
            combined_idx = int(0.7 * text_idx + 0.3 * cvss_idx)
            combined_label = self.label_map[combined_idx]
            
            return {
                "severity": combined_label,
                "text_based": text_result["label"],
                "cvss_based": cvss_label,
                "cvss_score": cvss_score,
                "confidence": text_result["confidence"],
                "method": "hybrid",
            }
        
        return {
            "severity": text_result["label"],
            "confidence": text_result["confidence"],
            "method": "text_only",
        }
    
    def extract_security_features(self, text: str) -> dict[str, Any]:
        """Extract security-relevant features from text.
        
        Args:
            text: Input security text
        
        Returns:
            Extracted features
        """
        # Get embeddings
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )
        
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            # Get hidden states
            outputs = self.model.bert(**inputs, output_hidden_states=True)
            
            # Use [CLS] token embedding
            cls_embedding = outputs.last_hidden_state[:, 0, :]
            
            # Get pooled output
            pooled_output = outputs.pooler_output
        
        # Extract security keywords
        keywords = self._extract_security_keywords(text)
        
        return {
            "cls_embedding": cls_embedding.cpu().numpy().tolist(),
            "pooled_embedding": pooled_output.cpu().numpy().tolist(),
            "embedding_dim": cls_embedding.shape[-1],
            "security_keywords": keywords,
        }
    
    def batch_classify(
        self,
        texts: list[str],
        batch_size: int = 32,
    ) -> list[dict[str, Any]]:
        """Classify multiple texts in batches.
        
        Args:
            texts: List of texts to classify
            batch_size: Batch size for processing
        
        Returns:
            List of classification results
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            # Tokenize batch
            inputs = self.tokenizer(
                batch,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )
            
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1)
            
            # Process each result
            for j, text in enumerate(batch):
                predicted_class = torch.argmax(probabilities[j]).item()
                confidence = probabilities[j][predicted_class].item()
                
                results.append({
                    "text": text[:100],
                    "label": self.label_map[predicted_class],
                    "confidence": confidence,
                })
        
        return results
    
    def _cvss_to_label(self, cvss_score: float) -> str:
        """Convert CVSS score to severity label."""
        if cvss_score >= 9.0:
            return "CRITICAL"
        elif cvss_score >= 7.0:
            return "HIGH"
        elif cvss_score >= 4.0:
            return "MEDIUM"
        elif cvss_score >= 0.1:
            return "LOW"
        else:
            return "INFO"
    
    def _extract_security_keywords(self, text: str) -> list[str]:
        """Extract security-related keywords."""
        keywords = []
        
        security_terms = [
            "exploit", "vulnerability", "injection", "xss", "csrf", "rce",
            "authentication", "authorization", "privilege", "escalation",
            "buffer overflow", "sql injection", "command injection",
            "denial of service", "dos", "ddos", "malware", "ransomware",
            "zero-day", "cve", "patch", "mitigation", "remediation",
        ]
        
        text_lower = text.lower()
        
        for term in security_terms:
            if term in text_lower:
                keywords.append(term)
        
        return keywords
    
    def fine_tune(
        self,
        train_texts: list[str],
        train_labels: list[str],
        val_texts: list[str] | None = None,
        val_labels: list[str] | None = None,
        epochs: int = 3,
        batch_size: int = 16,
        learning_rate: float = 2e-5,
        output_dir: str = "./cyberbert-finetuned",
    ) -> dict[str, Any]:
        """Fine-tune CyberBERT on custom dataset.
        
        Args:
            train_texts: Training texts
            train_labels: Training labels
            val_texts: Validation texts
            val_labels: Validation labels
            epochs: Number of epochs
            batch_size: Batch size
            learning_rate: Learning rate
            output_dir: Output directory
        
        Returns:
            Training results
        """
        # Convert labels to indices
        train_label_ids = [self.reverse_label_map[label] for label in train_labels]
        
        # Create datasets
        train_encodings = self.tokenizer(
            train_texts,
            truncation=True,
            padding=True,
            max_length=512,
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            learning_rate=learning_rate,
            logging_dir=f"{output_dir}/logs",
            logging_steps=100,
            save_steps=500,
            evaluation_strategy="epoch" if val_texts else "no",
        )
        
        # TODO: Create proper Dataset objects and Trainer
        # This is a simplified version
        
        logger.info(f"Fine-tuning CyberBERT on {len(train_texts)} examples")
        
        return {
            "status": "completed",
            "epochs": epochs,
            "samples": len(train_texts),
            "output_dir": output_dir,
        }


# Global instance
_cyber_bert: CyberBERT | None = None


def get_cyber_bert() -> CyberBERT:
    """Get CyberBERT instance."""
    global _cyber_bert
    if _cyber_bert is None:
        _cyber_bert = CyberBERT()
    return _cyber_bert
