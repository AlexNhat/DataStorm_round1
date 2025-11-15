"""
Incremental Fine-tuning: Fine-tune model với data mới mà không quên kiến thức cũ.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import warnings
warnings.filterwarnings('ignore')


class IncrementalFineTuning:
    """
    Incremental Fine-tuning: Fine-tune model với data mới.
    
    Kết hợp với Rehearsal Buffer và EWC để tránh catastrophic forgetting.
    """
    
    def __init__(
        self,
        learning_rate: float = 0.001,
        use_rehearsal: bool = True,
        use_ewc: bool = True
    ):
        """
        Args:
            learning_rate: Learning rate cho fine-tuning
            use_rehearsal: Có dùng Rehearsal Buffer không
            use_ewc: Có dùng EWC không
        """
        self.learning_rate = learning_rate
        self.use_rehearsal = use_rehearsal
        self.use_ewc = use_ewc
        
        # Sẽ được inject từ bên ngoài
        self.rehearsal_buffer = None
        self.ewc = None
    
    def fine_tune(
        self,
        model: Any,
        X_new: np.ndarray,
        y_new: np.ndarray,
        epochs: int = 5,
        batch_size: int = 32
    ) -> Dict[str, Any]:
        """
        Fine-tune model với data mới.
        
        Args:
            model: Model cần fine-tune (scikit-learn hoặc PyTorch)
            X_new: New features
            y_new: New labels
            epochs: Số epochs
            batch_size: Batch size
            
        Returns:
            Training history
        """
        history = {
            'loss': [],
            'accuracy': []
        }
        
        # Combine với rehearsal buffer nếu có
        if self.use_rehearsal and self.rehearsal_buffer:
            X_combined, y_combined = self.rehearsal_buffer.get_samples(
                n=len(X_new),
                include_new=(X_new, y_new)
            )
        else:
            X_combined, y_combined = X_new, y_new
        
        # Fine-tune
        if hasattr(model, 'partial_fit'):
            # Incremental model (scikit-learn)
            for epoch in range(epochs):
                # Shuffle
                indices = np.random.permutation(len(X_combined))
                X_shuffled = X_combined[indices]
                y_shuffled = y_combined[indices]
                
                # Batch training
                for i in range(0, len(X_shuffled), batch_size):
                    X_batch = X_shuffled[i:i+batch_size]
                    y_batch = y_shuffled[i:i+batch_size]
                    
                    model.partial_fit(X_batch, y_batch)
        
        elif hasattr(model, 'train'):
            # PyTorch model
            import torch
            import torch.optim as optim
            
            optimizer = optim.Adam(model.parameters(), lr=self.learning_rate)
            criterion = torch.nn.CrossEntropyLoss() if len(np.unique(y_combined)) > 2 else torch.nn.MSELoss()
            
            for epoch in range(epochs):
                # Shuffle
                indices = np.random.permutation(len(X_combined))
                X_shuffled = X_combined[indices]
                y_shuffled = y_combined[indices]
                
                epoch_loss = 0.0
                
                # Batch training
                for i in range(0, len(X_shuffled), batch_size):
                    X_batch = torch.FloatTensor(X_shuffled[i:i+batch_size])
                    y_batch = torch.LongTensor(y_shuffled[i:i+batch_size]) if len(np.unique(y_combined)) > 2 else torch.FloatTensor(y_shuffled[i:i+batch_size])
                    
                    optimizer.zero_grad()
                    output = model(X_batch)
                    loss = criterion(output, y_batch)
                    
                    # Add EWC penalty
                    if self.use_ewc and self.ewc:
                        ewc_loss = self.ewc.get_total_ewc_loss(model)
                        loss += ewc_loss
                    
                    loss.backward()
                    optimizer.step()
                    
                    epoch_loss += loss.item()
                
                history['loss'].append(epoch_loss / (len(X_combined) // batch_size))
        
        # Update rehearsal buffer
        if self.use_rehearsal and self.rehearsal_buffer:
            self.rehearsal_buffer.add_samples(X_new, y_new)
        
        return history

