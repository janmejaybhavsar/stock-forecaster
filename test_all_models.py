import sys
sys.path.insert(0, ".")
import time
from datetime import date
from src.data_layer.provider_factory import get_provider
from src.features.pipeline import FeaturePipeline
from src.models.model_registry import list_models, get_model

provider = get_provider()
df = provider.get_historical("AAPL", date(2023, 1, 1), date(2025, 5, 1))
pipeline = FeaturePipeline()
features = pipeline.build("AAPL", df, include_sentiment=False)
print(f"Features shape: {features.shape}\n")

for name in list_models():
    print(f"--- {name.upper()} ---")
    start = time.time()
    try:
        model = get_model(name)
        model.fit(features, target_col="Close")
        preds = model.predict(5)
        elapsed = time.time() - start
        print(f"  Time: {elapsed:.1f}s")
        print(f"  Predictions: {preds['predicted_close'].tolist()}")
        print(f"  Bounds: [{preds['lower_bound'].iloc[0]:.2f}, {preds['upper_bound'].iloc[0]:.2f}]")
        print(f"  OK")
    except Exception as e:
        elapsed = time.time() - start
        print(f"  FAILED ({elapsed:.1f}s): {e}")
    print()
