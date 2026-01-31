import os
import sys
import pandas as pd
import numpy as np
import xgboost as xgb
import json
import hashlib
import argparse
from datetime import datetime


def get_client_id():
    """
    Get client ID from environment variable or command line argument.
    """
    # Try environment variable first
    client_id = os.environ.get("CLIENT_ID")

    # Try command line argument
    if client_id is None and len(sys.argv) > 1:
        parser = argparse.ArgumentParser()
        parser.add_argument("--client-id", type=str, help="Client identifier")
        args, _ = parser.parse_known_args()
        client_id = args.client_id

    # Default to client_1
    if client_id is None:
        client_id = "client_1"

    return client_id


def load_global_model(model_folder="model"):
    """
    Load the global model from the server.

    In true federated learning, clients receive the global model from the server
    at the beginning of each round.
    """
    print("=" * 70)
    print("🔐 FEDERATED LEARNING CLIENT")
    print("=" * 70)

    # Priority order for model loading
    possible_models = [
        "global_model.json",  # Latest global model from server
        "Central_model.json",  # Initial central model
        "client_updated_model.json",  # Previous client model
    ]

    model_path = None
    for fname in possible_models:
        p = os.path.join(model_folder, fname)
        if os.path.exists(p):
            model_path = p
            break

    if model_path is None:
        raise FileNotFoundError(
            f"No global model found in '{model_folder}' folder.\n"
            "Run the server aggregation first or train a central model."
        )

    print(f"\n📂 Loading global model from {model_path}...")
    model = xgb.XGBClassifier()
    model.load_model(model_path)
    print("✅ Global model loaded successfully!")

    return model, model_path


def load_client_data(client_id, data_folder="client_data"):
    """
    Load client-specific data.

    In federated learning, each client has its own private dataset.
    """
    # Try client-specific data file first
    client_data_path = os.path.join(data_folder, f"{client_id}_data.csv")

    # Fallback to generic client_data.csv
    if not os.path.exists(client_data_path):
        client_data_path = os.path.join(data_folder, "client_data.csv")

    if not os.path.exists(client_data_path):
        raise FileNotFoundError(
            f"Client data not found: {client_data_path}\n"
            f"Expected either '{client_id}_data.csv' or 'client_data.csv' in '{data_folder}'"
        )

    print(f"\n📂 Loading client data from {client_data_path}...")
    df = pd.read_csv(client_data_path)
    print(f"✅ Loaded {len(df)} samples")

    return df, client_data_path


def train_local_model(model, df, client_id):
    """
    Train the model on local client data.

    This is the core of federated learning - each client trains on their private data.
    """
    print(f"\n🔄 Training local model for {client_id}...")

    has_labels = "label" in df.columns

    if has_labels:
        # Supervised training
        X = df.drop("label", axis=1)
        y = df["label"]
        X_train = X
        y_train = y

        print(f"🔖 Supervised training on {len(X)} labeled samples...")

        try:
            # Use warm-start by passing the existing booster
            booster = model.get_booster()
            model.fit(X, y, xgb_model=booster)
        except (TypeError, AttributeError):
            # Fallback if xgb_model param not accepted
            model.fit(X, y)

        print("✅ Supervised training complete")

    else:
        # Semi-supervised training with pseudo-labeling
        X = df
        y_train = None

        print(f"🛈 No labels found - using pseudo-labeling on {len(X)} samples...")

        # IMPORTANT: Store original predictions BEFORE training
        # We'll use these for gradient computation to avoid class mismatch
        probs_original = model.predict_proba(X)
        max_probs = probs_original.max(axis=1)
        pseudo_labels = probs_original.argmax(axis=1)

        # Keep only high-confidence predictions
        threshold = 0.95
        mask = max_probs >= threshold
        num_confident = int(mask.sum())

        print(
            f"🔎 High-confidence samples (threshold={threshold}): {num_confident}/{len(X)}"
        )

        if num_confident == 0:
            print("⚠️  No confident pseudo-labels found. Skipping training.")
            return None, None, None, None

        X_confident = X.iloc[mask]
        y_pseudo = pseudo_labels[mask]
        probs_confident = probs_original[mask]  # Store original predictions

        # Get model's expected number of classes
        n_classes_pred = probs_original.shape[1]

        # Filter to valid class range
        valid_class_mask = (y_pseudo >= 0) & (y_pseudo < n_classes_pred)
        X_confident = X_confident[valid_class_mask]
        y_pseudo = y_pseudo[valid_class_mask]
        probs_confident = probs_confident[valid_class_mask]

        if len(y_pseudo) == 0:
            print("⚠️  No valid pseudo-labels after filtering. Skipping training.")
            return None, None, None, None

        # Remap to consecutive integers
        unique_labels = np.unique(y_pseudo)
        label_mapping = {
            old_label: new_label for new_label, old_label in enumerate(unique_labels)
        }
        y_pseudo_remapped = np.array([label_mapping[label] for label in y_pseudo])

        print(f"✳️  Training on {len(y_pseudo_remapped)} pseudo-labeled samples...")

        try:
            booster = model.get_booster()
            model.fit(X_confident, y_pseudo_remapped, xgb_model=booster)
            print("✅ Pseudo-label training complete")
        except (TypeError, AttributeError, ValueError) as e:
            # If warm-start fails due to class mismatch, train without it
            print(f"⚠️  Warm-start failed ({e}), training new model...")
            model.fit(X_confident, y_pseudo_remapped)
            print("✅ Pseudo-label training complete")

        X_train = X_confident
        y_train = y_pseudo  # Use ORIGINAL labels, not remapped

        # Return original predictions to avoid re-prediction issues
        return model, X_train, y_train, probs_confident

    return model, X_train, y_train, None


def compute_gradients_and_histograms(
    model, X_train, y_train, client_id, round_id=1, probs_precomputed=None
):
    """
    Compute gradients, hessians, and histograms for federated aggregation.

    This is the key component for true federated learning with XGBoost.
    Instead of sharing the model or raw data, clients share aggregated statistics.

    Args:
        probs_precomputed: Optional pre-computed predictions to avoid class mismatch issues
    """
    print("\n📊 Computing gradients and histograms for federated aggregation...")

    # Get predictions (use pre-computed if available to avoid class mismatch)
    if probs_precomputed is not None:
        probs = probs_precomputed
        print("   Using pre-computed predictions (avoiding class mismatch)")
    else:
        probs = model.predict_proba(X_train)
    num_classes = probs.shape[1]

    # Compute gradients and hessians
    one_hot = np.zeros((len(y_train), num_classes))
    one_hot[np.arange(len(y_train)), y_train] = 1

    # Gradient: prediction - true label (for softmax)
    grad = probs - one_hot

    # Hessian: p(1-p) for each class
    hess = probs * (1 - probs)

    print(f"   Gradient shape: {grad.shape}")
    print(f"   Hessian shape: {hess.shape}")

    # Build histograms for each feature
    histograms = {}
    num_bins = 10

    for feature_idx, feature_name in enumerate(X_train.columns):
        feature_values = X_train[feature_name].values

        # Create bins
        try:
            bins = pd.qcut(feature_values, q=num_bins, duplicates="drop", retbins=True)[
                1
            ]
            bin_ids = pd.cut(
                feature_values, bins=bins, labels=False, include_lowest=True
            )
        except ValueError:
            # Fallback for features with few unique values
            unique_vals = np.unique(feature_values)
            if len(unique_vals) <= num_bins:
                bins = np.concatenate(
                    [[-np.inf], unique_vals[:-1] + np.diff(unique_vals) / 2, [np.inf]]
                )
            else:
                bins = pd.qcut(
                    feature_values, q=num_bins, duplicates="drop", retbins=True
                )[1]
            bin_ids = pd.cut(
                feature_values, bins=bins, labels=False, include_lowest=True
            )

        # Aggregate gradients and hessians per bin
        feature_hist = {}
        for bin_id in np.unique(bin_ids):
            if np.isnan(bin_id):
                continue

            mask = bin_ids == bin_id
            if mask.sum() > 0:
                sum_grad = grad[mask].sum(axis=0).tolist()
                sum_hess = hess[mask].sum(axis=0).tolist()
                feature_hist[f"bin_{int(bin_id)}"] = {"G": sum_grad, "H": sum_hess}

        histograms[f"feature_{feature_idx}"] = feature_hist

    # Compute data distribution statistics
    label_distribution = {}
    unique, counts = np.unique(y_train, return_counts=True)
    for label, count in zip(unique, counts):
        label_distribution[int(label)] = int(count)

    # Prepare metadata
    histogram_hash = hashlib.md5(
        json.dumps(histograms, sort_keys=True).encode()
    ).hexdigest()[:8]

    data = {
        "client_id": client_id,
        "round_id": round_id,
        "timestamp": datetime.now().isoformat(),
        "num_samples": int(len(y_train)),
        "num_features": len(X_train.columns),
        "num_classes": num_classes,
        "label_distribution": label_distribution,
        "histogram_hash": histogram_hash,
        "histograms": histograms,
    }

    print(f"✅ Computed histograms for {len(histograms)} features")
    print(f"   Total samples: {len(y_train)}")
    print(f"   Label distribution: {label_distribution}")

    return data


def save_client_outputs(model, histogram_data, client_id, output_folder="model"):
    """
    Save client outputs for federated aggregation.

    In true federated learning, clients send only the histograms (aggregated statistics)
    to the server, not the full model or raw data.
    """
    os.makedirs(output_folder, exist_ok=True)

    # Save histograms (THIS IS WHAT GETS SENT TO SERVER)
    histograms_path = os.path.join(output_folder, f"{client_id}_histograms.json")
    with open(histograms_path, "w") as f:
        json.dump(histogram_data, f, indent=2)
    print(f"\n💾 Histograms saved to: {histograms_path}")
    print("   ⚡ This file will be sent to the aggregation server")

    # Optionally save the local model (for debugging/comparison)
    # In true FL, this would NOT be sent to the server
    local_model_path = os.path.join(output_folder, f"{client_id}_local_model.json")
    try:
        model.save_model(local_model_path)
        print(f"💾 Local model saved to: {local_model_path}")
        print("   ℹ️  (Local only - not sent to server)")
    except Exception as e:
        print(f"⚠️  Could not save local model: {e}")
        print("   ℹ️  This is OK - histograms are what matter for federated learning")
        local_model_path = None

    return histograms_path, local_model_path


def main():
    """
    Main federated learning client workflow.
    """
    # Get client ID
    client_id = get_client_id()
    print(f"\n🆔 Client ID: {client_id}")

    # Load global model from server
    model, model_path = load_global_model(model_folder="model")

    # Load client's private data
    df, data_path = load_client_data(client_id, data_folder="client_data")

    # Train on local data
    model, X_train, y_train, probs_precomputed = train_local_model(model, df, client_id)

    if y_train is None:
        print("\n⚠️  No training performed. Exiting.")
        return

    # Compute gradients and histograms
    histogram_data = compute_gradients_and_histograms(
        model,
        X_train,
        y_train,
        client_id,
        round_id=1,
        probs_precomputed=probs_precomputed,
    )

    # Save outputs
    hist_path, model_path = save_client_outputs(
        model, histogram_data, client_id, output_folder="model"
    )

    # Summary
    print("\n" + "=" * 70)
    print("✅ FEDERATED LEARNING CLIENT COMPLETE")
    print("=" * 70)
    print(f"Client: {client_id}")
    print(f"Samples trained: {histogram_data['num_samples']}")
    print(f"Histograms: {hist_path}")
    print("\nNext steps:")
    print("1. Send histograms to aggregation server")
    print("2. Server will aggregate from all clients")
    print("3. Receive updated global model for next round")
    print("=" * 70)


if __name__ == "__main__":
    main()
