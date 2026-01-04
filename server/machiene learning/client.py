import os
import pandas as pd
import numpy as np
import xgboost as xgb

# Paths
possible_models = [
    "client_updated_model.json",
    "Central_model.json",
]
model_path = None
for fname in possible_models:
    p = os.path.join("model", fname)
    if os.path.exists(p):
        model_path = p
        break
if model_path is None:
    # default path (will raise if missing)
    model_path = os.path.join("Central_model.json")
updated_model_path = os.path.join("model", "client_updated_model2.json")

if not os.path.exists(model_path):
    raise FileNotFoundError(
        f"Model file not found: {model_path}.\nRun `python3 main.py` to train and save the central model into the `model/` folder."
    )
client_data_path = os.path.join(os.path.dirname(__file__), "client_data", "client_data.csv")

print(f"📂 Loading central model from {model_path}...")
xgb_model = xgb.XGBClassifier()
xgb_model.load_model(model_path)
print("✅ Central model loaded successfully!")

if not os.path.exists(client_data_path):
    raise FileNotFoundError(f"Client data not found: {client_data_path}")

print(f"📂 Loading client data from {client_data_path}...")
df = pd.read_csv(client_data_path)

if 'label' in df.columns:
    X = df.drop('label', axis=1)
    y = df['label']
    print(f"🔖 Found labels in client data. Continuing supervised training on {len(X)} rows...")
    try:
        # Use warm-start by passing the existing booster
        booster = xgb_model.get_booster()
        xgb_model.fit(X, y, xgb_model=booster)
    except (TypeError, AttributeError):
        # Fallback if xgb_model param not accepted by installed xgboost version
        xgb_model.fit(X, y)
    print("✅ Supervised fine-tuning complete.")
else:
    # Use pseudo-labeling for unlabeled client data
    X = df
    print(f"🛈 No label column found — using pseudo-labeling on {len(X)} rows.")
    probs = xgb_model.predict_proba(X)
    max_probs = probs.max(axis=1)
    pseudo_labels = probs.argmax(axis=1)

    # Diagnostics to help debug unexpected class indices
    print(f"🔎 predict_proba output shape: {probs.shape}")
    print(f"🔎 max predicted probability: {float(max_probs.max()):.4f}")
    print(f"🔎 predicted label range: {pseudo_labels.min()} .. {pseudo_labels.max()}")
    print(f"🔎 unique predicted labels (sample): {np.unique(pseudo_labels)[:10]}")

    # Keep only high-confidence predictions
    threshold = 0.95
    mask = max_probs >= threshold
    num_confident = int(mask.sum())
    if num_confident == 0:
        print(f"⚠️  No confident pseudo-labels found (threshold={threshold}). Nothing to train on.")
    else:
        X_confident = X.iloc[mask]
        y_pseudo = pseudo_labels[mask]
        
        # Get the number of classes the model expects
        n_classes_pred = probs.shape[1]
        
        # Get unique classes from the original model's training
        # XGBoost stores this information in the booster
        try:
            booster = xgb_model.get_booster()
            # Get the number of classes from the model configuration
            model_num_classes = int(booster.attributes().get('num_class', n_classes_pred))
        except:
            model_num_classes = n_classes_pred
        
        print(f"🔎 Model was trained on {model_num_classes} classes")
        print(f"🔎 Unique pseudo labels before filtering: {np.unique(y_pseudo)}")
        
        # Filter pseudo labels to only include valid classes for the original model
        # Keep only samples where pseudo label is in the valid range [0, model_num_classes)
        valid_class_mask = (y_pseudo >= 0) & (y_pseudo < model_num_classes)
        X_confident = X_confident[valid_class_mask]
        y_pseudo = y_pseudo[valid_class_mask]
        
        num_valid = len(y_pseudo)
        if num_valid == 0:
            print(f"⚠️  No valid pseudo-labels found after filtering. Nothing to train on.")
        else:
            print(f"✳️  Using {num_valid} high-confidence pseudo-labeled rows (filtered from {num_confident}) to continue training...")
            print(f"🔎 Unique pseudo labels after filtering: {np.unique(y_pseudo)}")
            
            # CRITICAL FIX: Remap pseudo labels to consecutive integers [0, 1, 2, ...]
            # XGBoost requires consecutive class labels starting from 0
            unique_labels = np.unique(y_pseudo)
            label_mapping = {old_label: new_label for new_label, old_label in enumerate(unique_labels)}
            y_pseudo_remapped = np.array([label_mapping[label] for label in y_pseudo])
            
            print(f"🔎 Remapped pseudo labels to consecutive integers: {np.unique(y_pseudo_remapped)}")
            print(f"🔎 Number of unique classes: {len(unique_labels)}")
            
            try:
                # Use warm-start by passing the existing booster
                booster = xgb_model.get_booster()
                xgb_model.fit(X_confident, y_pseudo_remapped, xgb_model=booster)
                print("✅ Pseudo-label fine-tuning complete (with warm-start).")
            except (TypeError, AttributeError):
                # Fallback if xgb_model param not accepted
                xgb_model.fit(X_confident, y_pseudo_remapped)
                print("✅ Pseudo-label fine-tuning complete.")
            except ValueError as ve:
                # Class mismatch - need to create a new model
                print(f"⚠️  Warm-start failed: {ve}")
                print(f"🔎 unique pseudo labels: {np.unique(y_pseudo_remapped)}")
                print("ℹ️  Creating a new model instance to handle class mismatch...")
                
                # Create a new XGBoost model with the correct number of classes
                new_model = xgb.XGBClassifier(
                    n_estimators=50,
                    learning_rate=0.2,
                    max_depth=4,
                    objective='multi:softprob',
                    num_class=len(unique_labels),
                    tree_method='hist',
                    random_state=42
                )
                new_model.fit(X_confident, y_pseudo_remapped)
                xgb_model = new_model
                print("✅ Pseudo-label fine-tuning complete (with new model).")

# Save the updated model
xgb_model.save_model(updated_model_path)
print(f"💾 Updated model saved to {updated_model_path}")