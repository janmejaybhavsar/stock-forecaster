from datetime import timedelta

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

from src.models.base_model import ForecastModel

SEQUENCE_LENGTH = 60


class _LSTMNet(nn.Module):
    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Linear(hidden_size, 1)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        out = self.dropout(out[:, -1, :])
        return self.fc(out)


class LSTMModel(ForecastModel):
    name = "lstm"

    def __init__(self, epochs: int = 50, batch_size: int = 32):
        self._epochs = epochs
        self._batch_size = batch_size
        self._model: _LSTMNet | None = None
        self._scaler_X = MinMaxScaler()
        self._scaler_y = MinMaxScaler()
        self._last_sequence = None
        self._last_date = None

    def fit(self, train_df: pd.DataFrame, target_col: str = "Close") -> None:
        feature_cols = [c for c in train_df.columns if c not in ["Open", "High", "Low", "Volume"]]
        target_idx = feature_cols.index(target_col) if target_col in feature_cols else 0

        data = train_df[feature_cols].values.astype(np.float32)
        targets = train_df[[target_col]].values.astype(np.float32)

        X_scaled = self._scaler_X.fit_transform(data)
        y_scaled = self._scaler_y.fit_transform(targets)

        X_seq, y_seq = [], []
        for i in range(SEQUENCE_LENGTH, len(X_scaled)):
            X_seq.append(X_scaled[i - SEQUENCE_LENGTH:i])
            y_seq.append(y_scaled[i])

        X_tensor = torch.tensor(np.array(X_seq), dtype=torch.float32)
        y_tensor = torch.tensor(np.array(y_seq), dtype=torch.float32)

        split = int(len(X_tensor) * 0.85)
        X_train, X_val = X_tensor[:split], X_tensor[split:]
        y_train, y_val = y_tensor[:split], y_tensor[split:]

        input_size = X_tensor.shape[2]
        self._model = _LSTMNet(input_size)
        optimizer = torch.optim.Adam(self._model.parameters(), lr=0.001)
        criterion = nn.MSELoss()

        best_val_loss = float("inf")
        patience_counter = 0

        for epoch in range(self._epochs):
            self._model.train()
            dataset = torch.utils.data.TensorDataset(X_train, y_train)
            loader = torch.utils.data.DataLoader(dataset, batch_size=self._batch_size, shuffle=True)

            for batch_X, batch_y in loader:
                optimizer.zero_grad()
                pred = self._model(batch_X)
                loss = criterion(pred, batch_y)
                loss.backward()
                optimizer.step()

            self._model.eval()
            with torch.no_grad():
                val_pred = self._model(X_val)
                val_loss = criterion(val_pred, y_val).item()

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= 5:
                    break

        self._last_sequence = X_scaled[-SEQUENCE_LENGTH:]
        self._last_date = train_df.index[-1]

    def predict(self, horizon: int) -> pd.DataFrame:
        self._model.eval()
        predictions, lowers, uppers = [], [], []

        n_mc = 30

        def enable_dropout(model):
            for m in model.modules():
                if isinstance(m, nn.Dropout):
                    m.train()

        for step in range(horizon):
            seq = torch.tensor(self._last_sequence[np.newaxis, :], dtype=torch.float32)

            mc_preds = []
            enable_dropout(self._model)
            for _ in range(n_mc):
                with torch.no_grad():
                    pred = self._model(seq).item()
                mc_preds.append(pred)

            mean_pred = np.mean(mc_preds)
            std_pred = np.std(mc_preds)

            pred_unscaled = self._scaler_y.inverse_transform([[mean_pred]])[0][0]
            lower = self._scaler_y.inverse_transform([[mean_pred - 1.96 * std_pred]])[0][0]
            upper = self._scaler_y.inverse_transform([[mean_pred + 1.96 * std_pred]])[0][0]

            predictions.append(pred_unscaled)
            lowers.append(lower)
            uppers.append(upper)

            new_row = self._last_sequence[-1].copy()
            self._last_sequence = np.vstack([self._last_sequence[1:], new_row])

        dates = pd.bdate_range(start=self._last_date + timedelta(days=1), periods=horizon)

        return pd.DataFrame({
            "date": dates,
            "predicted_close": predictions,
            "lower_bound": lowers,
            "upper_bound": uppers,
        })
