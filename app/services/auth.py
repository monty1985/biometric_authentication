import numpy as np
import faiss
import json
import os
from pathlib import Path
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

from .embedding import VoiceEmbeddingService
from .anti_spoof import AntiSpoofService
from ..core.config import settings

logger = logging.getLogger(__name__)

class AuthenticationService:
    def __init__(self):
        self.embedding_service = VoiceEmbeddingService()
        self.anti_spoof_service = AntiSpoofService()
        self.index = None
        self.user_map = {}
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize FAISS index and load existing embeddings"""
        try:
            # Create storage directory if it doesn't exist
            os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)
            
            # Initialize FAISS index
            self.index = faiss.IndexFlatL2(192)  # ECAPA-TDNN produces 192-dim vectors
            
            # Load existing embeddings if any
            self._load_embeddings()
            
        except Exception as e:
            logger.error(f"Failed to initialize storage: {str(e)}")
            raise
    
    def _load_embeddings(self):
        """Load existing embeddings from disk"""
        try:
            index_path = Path(settings.VECTOR_DB_PATH) / "index.faiss"
            user_map_path = Path(settings.VECTOR_DB_PATH) / "user_map.json"
            
            if index_path.exists() and user_map_path.exists():
                self.index = faiss.read_index(str(index_path))
                with open(user_map_path, 'r') as f:
                    self.user_map = json.load(f)
                logger.info(f"Loaded {len(self.user_map)} user embeddings")
        except Exception as e:
            logger.error(f"Failed to load embeddings: {str(e)}")
    
    def _save_embeddings(self):
        """Save embeddings to disk"""
        try:
            index_path = Path(settings.VECTOR_DB_PATH) / "index.faiss"
            user_map_path = Path(settings.VECTOR_DB_PATH) / "user_map.json"
            
            faiss.write_index(self.index, str(index_path))
            with open(user_map_path, 'w') as f:
                json.dump(self.user_map, f)
        except Exception as e:
            logger.error(f"Failed to save embeddings: {str(e)}")
    
    async def enroll_user(self, user_id: str, audio_path: str) -> Tuple[bool, str]:
        """
        Enroll a new user with their voice sample
        
        Args:
            user_id: Unique identifier for the user
            audio_path: Path to the voice sample
            
        Returns:
            Tuple of (success, message)
        """
        try:
            logger.info(f"Starting enrollment process for user {user_id}")
            
            # Check if user already exists
            if user_id in self.user_map:
                logger.warning(f"User {user_id} already enrolled")
                return False, "User already enrolled"
            
            logger.info("Checking audio quality and liveness")
            # Check audio quality and liveness
            quality_metrics = self.anti_spoof_service.analyze_audio_quality(audio_path)
            logger.info(f"Audio quality metrics: {quality_metrics}")
            
            is_genuine, confidence, error = self.anti_spoof_service.check_liveness(audio_path)
            logger.info(f"Liveness check - is_genuine: {is_genuine}, confidence: {confidence}")
            
            if not is_genuine:
                logger.warning(f"Voice sample appears to be spoofed (confidence: {confidence:.2f})")
                return False, f"Voice sample appears to be spoofed (confidence: {confidence:.2f})"
            
            logger.info("Generating voice embedding")
            # Generate embedding
            embedding, error = self.embedding_service.generate_embedding(audio_path)
            if error:
                logger.error(f"Failed to generate embedding: {error}")
                return False, f"Failed to generate embedding: {error}"
            
            logger.info("Adding embedding to FAISS index")
            # Add to FAISS index
            self.index.add(np.array([embedding]))
            
            # Update user map
            self.user_map[user_id] = {
                "index": self.index.ntotal - 1,
                "enrolled_at": datetime.utcnow().isoformat(),
                "quality_metrics": quality_metrics
            }
            
            logger.info("Saving embeddings to disk")
            # Save to disk
            self._save_embeddings()
            
            logger.info(f"Successfully enrolled user {user_id}")
            return True, "User enrolled successfully"
            
        except Exception as e:
            logger.error(f"Error enrolling user: {str(e)}", exc_info=True)
            return False, f"Enrollment failed: {str(e)}"
    
    async def verify_user(self, user_id: str, audio_path: str) -> Tuple[bool, float, str]:
        """
        Verify a user's voice sample
        
        Args:
            user_id: User identifier
            audio_path: Path to the verification voice sample
            
        Returns:
            Tuple of (is_verified, confidence, message)
        """
        try:
            # Check if user exists
            if user_id not in self.user_map:
                return False, 0.0, "User not found"
            
            # Check liveness
            is_genuine, confidence, error = self.anti_spoof_service.check_liveness(audio_path)
            logger.info(f"Liveness check - is_genuine: {is_genuine}, confidence: {confidence}")
            
            if not is_genuine:
                return False, 0.0, f"Voice sample appears to be spoofed (confidence: {confidence:.2f})"
            
            # Generate embedding
            embedding, error = self.embedding_service.generate_embedding(audio_path)
            if error:
                return False, 0.0, f"Failed to generate embedding: {error}"
            
            # Get stored embedding
            stored_idx = self.user_map[user_id]["index"]
            stored_embedding = self.index.reconstruct(stored_idx)
            
            # Compute similarity
            similarity = self.embedding_service.compute_similarity(embedding, stored_embedding)
            logger.info(f"Voice similarity score: {similarity:.2%}")
            
            # Use 65% threshold for verification
            threshold = 0.65
            is_verified = similarity >= threshold
            
            logger.info(f"Verification - similarity: {similarity:.2%}, threshold: {threshold:.2%}, is_verified: {is_verified}")
            
            if not is_verified:
                return False, similarity, f"Verification failed. Similarity {similarity:.2%} below threshold {threshold:.2%}"
            
            return is_verified, similarity, "Verification successful"
            
        except Exception as e:
            logger.error(f"Error verifying user: {str(e)}")
            return False, 0.0, f"Verification failed: {str(e)}"
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """Get user enrollment information"""
        return self.user_map.get(user_id)

    def verify_voice(self, user_id: str, voice_sample_path: str) -> Tuple[bool, float, Optional[str]]:
        """
        Verify a voice sample against the stored voice print
        
        Args:
            user_id: User ID to verify against
            voice_sample_path: Path to the voice sample file
            
        Returns:
            Tuple of (is_verified, confidence_score, error_message)
        """
        try:
            # Check if user exists
            if not self.user_map:
                return False, 0.0, "User not found"
            
            # Check audio quality and liveness
            quality_metrics = self.anti_spoof_service.analyze_audio_quality(voice_sample_path)
            logger.info(f"Audio quality metrics: {quality_metrics}")
            
            is_genuine, confidence, error = self.anti_spoof_service.check_liveness(voice_sample_path)
            logger.info(f"Liveness check - is_genuine: {is_genuine}, confidence: {confidence}")
            
            if not is_genuine:
                return False, confidence, "Voice sample appears to be spoofed"
            
            # Generate voice print
            voice_print, error = self.embedding_service.generate_embedding(voice_sample_path)
            if voice_print is None:
                return False, 0.0, "Failed to generate voice print"
            
            # Get stored voice print
            stored_print = self.index.reconstruct(self.user_map[user_id]["index"])
            if stored_print is None:
                return False, 0.0, "No stored voice print found"
            
            # Calculate similarity
            similarity = self.embedding_service.compute_similarity(voice_print, stored_print)
            logger.info(f"Voice similarity score: {similarity}")
            
            # More lenient threshold for testing
            threshold = 0.5  # Lower threshold for testing
            is_verified = similarity > threshold
            
            logger.info(f"Verification - similarity: {similarity}, threshold: {threshold}, is_verified: {is_verified}")
            
            return is_verified, similarity, None
            
        except Exception as e:
            error_msg = f"Error in voice verification: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, 0.0, error_msg 