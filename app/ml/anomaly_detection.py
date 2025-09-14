"""Machine Learning anomaly detection service using TensorFlow."""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import structlog
from datetime import datetime, timedelta

from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class AnomalyDetectionModel:
    """TensorFlow-based anomaly detection model for sensor data."""
    
    def __init__(self):
        self.model: Optional[keras.Model] = None
        self.scaler: Optional[StandardScaler] = None
        self.label_encoder: Optional[LabelEncoder] = None
        self.settings = get_settings()
        self.feature_columns = [
            'value', 'hour', 'day_of_week', 'rolling_mean_24h',
            'rolling_std_24h', 'value_diff', 'value_change_rate'
        ]
        self.sequence_length = 24  # Use 24 hours of data for prediction
        
    def _create_model(self, input_shape: Tuple[int, int]) -> keras.Model:
        """Create the neural network model architecture."""
        model = keras.Sequential([
            # LSTM layers for time series analysis
            keras.layers.LSTM(64, return_sequences=True, input_shape=input_shape),
            keras.layers.Dropout(0.2),
            keras.layers.LSTM(32, return_sequences=False),
            keras.layers.Dropout(0.2),
            
            # Dense layers for classification
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dropout(0.1),
            keras.layers.Dense(16, activation='relu'),
            keras.layers.Dense(1, activation='sigmoid')  # Binary classification
        ])
        
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy', 'precision', 'recall']
        )
        
        return model
    
    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features from raw sensor data."""
        # Time-based features
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        
        # Rolling statistics (24-hour window)
        df = df.sort_values('timestamp')
        df['rolling_mean_24h'] = df['value'].rolling(window=24, min_periods=1).mean()
        df['rolling_std_24h'] = df['value'].rolling(window=24, min_periods=1).std()
        
        # Value differences and change rates
        df['value_diff'] = df['value'].diff().fillna(0)
        df['value_change_rate'] = df['value'].pct_change().fillna(0)
        
        # Fill NaN values
        df = df.fillna(0)
        
        return df
    
    def _create_sequences(self, data: np.ndarray, labels: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM input."""
        X, y = [], []
        
        for i in range(len(data) - self.sequence_length + 1):
            X.append(data[i:(i + self.sequence_length)])
            y.append(labels[i + self.sequence_length - 1])
        
        return np.array(X), np.array(y)
    
    async def train_model(self, training_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Train the anomaly detection model."""
        logger.info("Starting model training")
        
        # Convert to DataFrame
        df = pd.DataFrame(training_data)
        
        # Engineer features
        df = self._engineer_features(df)
        
        # Prepare features and labels
        X = df[self.feature_columns].values
        y = df['is_anomaly'].values.astype(int)
        
        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Create sequences for LSTM
        X_seq, y_seq = self._create_sequences(X_scaled, y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_seq, y_seq, test_size=0.2, random_state=42, stratify=y_seq
        )
        
        # Create and train model
        self.model = self._create_model((self.sequence_length, len(self.feature_columns)))
        
        # Train with early stopping
        early_stopping = keras.callbacks.EarlyStopping(
            monitor='val_loss', patience=10, restore_best_weights=True
        )
        
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=100,
            batch_size=32,
            callbacks=[early_stopping],
            verbose=1
        )
        
        # Evaluate model
        y_pred = (self.model.predict(X_test) > 0.5).astype(int)
        
        metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred)),
            'recall': float(recall_score(y_test, y_pred)),
            'f1_score': float(f1_score(y_test, y_pred))
        }
        
        logger.info(f"Model training completed. Metrics: {metrics}")
        
        # Save model and scaler
        await self._save_model()
        
        return metrics
    
    async def predict_anomaly(self, sensor_data: List[Dict[str, Any]]) -> Tuple[bool, float]:
        """Predict if the latest sensor data is anomalous."""
        if not self.model or not self.scaler:
            await self.load_model()
        
        # Convert to DataFrame
        df = pd.DataFrame(sensor_data)
        
        # Engineer features
        df = self._engineer_features(df)
        
        # Prepare features
        X = df[self.feature_columns].values
        X_scaled = self.scaler.transform(X)
        
        # We need at least sequence_length data points
        if len(X_scaled) < self.sequence_length:
            # Pad with zeros or return default prediction
            logger.warning(f"Insufficient data for prediction: {len(X_scaled)} < {self.sequence_length}")
            return False, 0.0
        
        # Use the latest sequence
        X_seq = X_scaled[-self.sequence_length:].reshape(1, self.sequence_length, len(self.feature_columns))
        
        # Predict
        prediction = self.model.predict(X_seq)[0][0]
        is_anomaly = prediction > 0.5
        
        logger.debug(f"Anomaly prediction: {prediction:.4f}, is_anomaly: {is_anomaly}")
        
        return bool(is_anomaly), float(prediction)
    
    async def _save_model(self) -> None:
        """Save the trained model and scaler."""
        if self.model:
            self.model.save(self.settings.MODEL_PATH)
            logger.info(f"Model saved to {self.settings.MODEL_PATH}")
        
        if self.scaler:
            scaler_path = self.settings.MODEL_PATH.replace('.h5', '_scaler.pkl')
            joblib.dump(self.scaler, scaler_path)
            logger.info(f"Scaler saved to {scaler_path}")
    
    async def load_model(self) -> None:
        """Load the trained model and scaler."""
        try:
            self.model = keras.models.load_model(self.settings.MODEL_PATH)
            logger.info(f"Model loaded from {self.settings.MODEL_PATH}")
            
            scaler_path = self.settings.MODEL_PATH.replace('.h5', '_scaler.pkl')
            self.scaler = joblib.load(scaler_path)
            logger.info(f"Scaler loaded from {scaler_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise


class AnomalyDetectionService:
    """Service for anomaly detection operations."""
    
    def __init__(self):
        self.model = AnomalyDetectionModel()
        self.settings = get_settings()
    
    async def detect_anomaly(self, current_data: Dict[str, Any], 
                           historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect anomaly in current sensor data using historical context."""
        try:
            # Combine current data with historical data
            all_data = historical_data + [current_data]
            
            # Predict anomaly
            is_anomaly, anomaly_score = await self.model.predict_anomaly(all_data)
            
            # Create alert if anomaly detected and score is above threshold
            if is_anomaly and anomaly_score >= self.settings.MODEL_ACCURACY_THRESHOLD:
                severity = self._determine_severity(anomaly_score)
                
                return {
                    'is_anomaly': True,
                    'anomaly_score': anomaly_score,
                    'severity': severity,
                    'message': f"Anomaly detected with score {anomaly_score:.4f}",
                    'timestamp': current_data.get('timestamp', datetime.utcnow().isoformat()),
                    'sensor_id': current_data.get('sensor_id'),
                    'sensor_value': current_data.get('value')
                }
            
            return {
                'is_anomaly': False,
                'anomaly_score': anomaly_score,
                'severity': 'normal',
                'message': 'No anomaly detected'
            }
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'severity': 'error',
                'message': f"Detection error: {str(e)}"
            }
    
    def _determine_severity(self, anomaly_score: float) -> str:
        """Determine alert severity based on anomaly score."""
        if anomaly_score >= 0.9:
            return 'critical'
        elif anomaly_score >= 0.8:
            return 'high'
        elif anomaly_score >= 0.6:
            return 'medium'
        else:
            return 'low'


# Global anomaly detection service instance
anomaly_detection_service = AnomalyDetectionService()