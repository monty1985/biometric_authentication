import torch
import torchaudio
import numpy as np
from speechbrain.inference import EncoderClassifier
from pathlib import Path
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class VoiceEmbeddingService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the ECAPA-TDNN model"""
        try:
            self.model = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="pretrained_models/spkrec-ecapa-voxceleb",
                run_opts={"device": self.device}
            )
            logger.info("ECAPA-TDNN model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ECAPA-TDNN model: {str(e)}")
            raise
    
    def generate_embedding(self, audio_path: str) -> Tuple[np.ndarray, Optional[str]]:
        """
        Generate voice embedding from audio file
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Tuple of (embedding vector, error message if any)
        """
        try:
            # Load and preprocess audio
            signal, fs = torchaudio.load(audio_path)
            
            # Ensure audio is mono
            if signal.shape[0] > 1:
                signal = torch.mean(signal, dim=0, keepdim=True)
            
            # Generate embedding
            embedding = self.model.encode_batch(signal)
            embedding = embedding.squeeze().cpu().numpy()
            
            return embedding, None
            
        except Exception as e:
            error_msg = f"Error generating embedding: {str(e)}"
            logger.error(error_msg)
            return np.array([]), error_msg
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Normalize embeddings
            embedding1 = embedding1 / np.linalg.norm(embedding1)
            embedding2 = embedding2 / np.linalg.norm(embedding2)
            
            # Compute cosine similarity
            similarity = np.dot(embedding1, embedding2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}")
            return 0.0 