import joblib
import os
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

def train_dummy_model():
    # Dummy training data
    X = [[0, 0], [1, 1]]
    y = [0, 1]
    
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(random_state=42))
    ])
    
    pipeline.fit(X, y)
    
    return pipeline

def store_ml_model(node_id, model):
    model_filename = f"../ml-models/{node_id}_model.pkl"
    joblib.dump(model, model_filename)
    print(f"Model stored successfully for node_id {node_id} at {model_filename}")

def load_ml_model(node_id):
    model_filename = f"../ml-models/{node_id}_model.pkl"
    if os.path.exists(model_filename):
        file_size = os.path.getsize(model_filename)
        print(f"Loading model for node_id {node_id} from {model_filename} (size: {file_size} bytes)")
        
        try:
            model = joblib.load(model_filename)
            print(f"Loaded model type: {type(model)}")  # Debugging line to check the type
            return model
        except Exception as e:
            print(f"Error loading model for node_id {node_id}: {e}")
            return None
    else:
        print(f"No model found for node_id {node_id}")
        return None

# Test the save and load functionality
node_id = "test_node"
dummy_model = train_dummy_model()
store_ml_model(node_id, dummy_model)

loaded_model = load_ml_model(node_id)
if loaded_model:
    print(f"Model loaded successfully: {type(loaded_model)}")
else:
    print("Failed to load model")
