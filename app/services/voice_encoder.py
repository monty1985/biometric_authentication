def compute_similarity(self, voice_print1: np.ndarray, voice_print2: np.ndarray) -> float:
        """
        Compute similarity between two voice prints using cosine similarity with preprocessing
        
        Args:
            voice_print1: First voice print
            voice_print2: Second voice print
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Ensure inputs are 2D arrays
            if voice_print1.ndim == 1:
                voice_print1 = voice_print1.reshape(1, -1)
            if voice_print2.ndim == 1:
                voice_print2 = voice_print2.reshape(1, -1)
            
            # Remove any NaN or inf values
            voice_print1 = np.nan_to_num(voice_print1, nan=0.0, posinf=1.0, neginf=-1.0)
            voice_print2 = np.nan_to_num(voice_print2, nan=0.0, posinf=1.0, neginf=-1.0)
            
            # Normalize the embeddings
            norm1 = np.linalg.norm(voice_print1, axis=1, keepdims=True)
            norm2 = np.linalg.norm(voice_print2, axis=1, keepdims=True)
            
            # Avoid division by zero
            norm1 = np.where(norm1 == 0, 1, norm1)
            norm2 = np.where(norm2 == 0, 1, norm2)
            
            voice_print1 = voice_print1 / norm1
            voice_print2 = voice_print2 / norm2
            
            # Compute cosine similarity
            similarity = np.dot(voice_print1, voice_print2.T)
            logger.info(f"Raw similarity score: {similarity}")
            
            # Apply sigmoid function to make the scores more discriminative
            similarity = 1 / (1 + np.exp(-5 * (similarity - 0.5)))
            logger.info(f"After sigmoid: {similarity}")
            
            # Ensure the score is between 0 and 1
            similarity = np.clip(similarity, 0, 1)
            logger.info(f"Final similarity score: {similarity}")
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}", exc_info=True)
            return 0.0 