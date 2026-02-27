import os
import sys
import tempfile
import pandas as pd
import numpy as np
import xgboost as xgb
import json
import hashlib
import argparse
from datetime import datetime

try:
    import requests
    from dotenv import load_dotenv

    # Load .env from the server directory (one level up from this script)
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    requests = None
    load_dotenv = None


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


# ── IPFS Gateways (tried in order) ──────────────────────────────────────────
IPFS_GATEWAYS = [
    "https://gateway.pinata.cloud/ipfs/{cid}",
    "https://ipfs.io/ipfs/{cid}",
    "https://cloudflare-ipfs.com/ipfs/{cid}",
]


def read_ipfs_hash_from_blockchain(blockchain_path=None):
    """
    Read the IPFS CID of the global model from blockchain.txt.

    blockchain.txt is expected to contain a line like:
        Global mode=<CID>
    Returns the CID string, or None if not found / file missing.
    """
    if blockchain_path is None:
        blockchain_path = os.path.join(os.path.dirname(__file__), "blockchain.txt")

    if not os.path.exists(blockchain_path):
        print(f"⚠️  blockchain.txt not found at {blockchain_path}")
        return None, blockchain_path

    with open(blockchain_path, "r") as f:
        content = f.read().strip()

    # Support two formats:
    #  1.  "Global mode=<CID>"  (written by main.py / server)
    #  2.  Bare CID on its own line
    cid = None
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("Global mode="):
            cid = line.split("=", 1)[1].strip()
            break
        # Also accept a bare 46-char CIDv0 (Qm…) or CIDv1
        if line.startswith("Qm") or line.startswith("bafy"):
            cid = line
            break

    if cid:
        print(f"\n🔗 Found IPFS CID in blockchain.txt: {cid}")
    else:
        print("⚠️  Could not parse an IPFS CID from blockchain.txt")

    return cid, blockchain_path


def download_model_from_ipfs(cid, save_path):
    """
    Download the model JSON identified by *cid* from IPFS and save it to
    *save_path*.  Tries multiple public gateways in sequence.

    Returns True on success, False on failure.
    """
    if requests is None:
        print("⚠️  'requests' package not installed – cannot download from IPFS.")
        return False

    for gateway_tpl in IPFS_GATEWAYS:
        url = gateway_tpl.format(cid=cid)
        print(f"   Trying gateway: {url}")
        try:
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "wb") as fh:
                    fh.write(resp.content)
                print(f"✅ Model downloaded from IPFS → {save_path}")
                return True
            else:
                print(f"   ✗ HTTP {resp.status_code}")
        except Exception as exc:
            print(f"   ✗ Error: {exc}")

    print("❌ All IPFS gateways failed.")
    return False


def load_global_model(model_folder="model"):
    """
    Load the global model.

    Strategy (in order):
      1. Read the IPFS CID from blockchain.txt and download the model.
      2. Fall back to locally cached model files.
    """
    print("=" * 70)
    print("🔐 FEDERATED LEARNING CLIENT")
    print("=" * 70)

    # ── Step 1: try to get the model from IPFS via blockchain.txt ─────────────
    cid, blockchain_path = read_ipfs_hash_from_blockchain()
    ipfs_model_path = os.path.join(model_folder, "global_model_ipfs.json")

    if cid:
        print("\n📡 Downloading global model from IPFS...")
        success = download_model_from_ipfs(cid, ipfs_model_path)
        if success:
            print(f"\n📂 Loading model from IPFS download: {ipfs_model_path}")
            model = xgb.XGBClassifier()
            model.load_model(ipfs_model_path)
            print("✅ Global model loaded successfully from IPFS!")
            return model, ipfs_model_path
        else:
            print("⚠️  IPFS download failed – falling back to local model files.")

    # ── Step 2: fall back to local files ──────────────────────────────────────
    possible_models = [
        "global_model.json",
        "Central_model.json",
        "client_updated_model.json",
    ]

    model_path = None
    for fname in possible_models:
        p = os.path.join(model_folder, fname)
        if os.path.exists(p):
            model_path = p
            break

    if model_path is None:
        raise FileNotFoundError(
            f"No global model found in '{model_folder}' folder and IPFS download failed.\n"
            "Ensure blockchain.txt contains a valid IPFS CID or provide a local model."
        )

    print(f"\n📂 Loading global model from local file: {model_path}")
    model = xgb.XGBClassifier()
    model.load_model(model_path)
    print("✅ Global model loaded successfully from local file!")

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


def upload_to_ipfs_and_log_blockchain(
    histogram_data,
    client_id,
    accuracy=None,
    blockchain_path=None,
):
    """
    Upload client training details (histogram metadata) to IPFS via Pinata
    and append the CID to blockchain.txt.

    Returns:
        str | None: The IPFS CID on success, or None on failure.
    """
    if requests is None:
        print("⚠️  'requests' package not installed – skipping IPFS upload.")
        return None

    if blockchain_path is None:
        blockchain_path = os.path.join(os.path.dirname(__file__), "blockchain.txt")

    PINATA_API_KEY = os.getenv("PINATA_API_KEY")
    PINATA_SECRET_API_KEY = os.getenv("PINATA_SECRET_API_KEY")

    if not PINATA_API_KEY or not PINATA_SECRET_API_KEY:
        print(
            "⚠️  PINATA_API_KEY / PINATA_SECRET_API_KEY not set in .env – "
            "skipping histogram IPFS upload."
        )
        return None

    training_record = {
        "client_id": client_id,
        "round_id": histogram_data.get("round_id", 1),
        "timestamp": datetime.now().isoformat(),
        "num_samples": histogram_data.get("num_samples", 0),
        "num_features": histogram_data.get("num_features", 0),
        "num_classes": histogram_data.get("num_classes", 0),
        "label_distribution": histogram_data.get("label_distribution", {}),
        "histogram_hash": histogram_data.get("histogram_hash", ""),
        "local_accuracy": accuracy,
        "framework": "XGBoost-FedAvg",
    }

    print("\n" + "=" * 70)
    print("🔗 IPFS UPLOAD – CLIENT TRAINING RECORD")
    print("=" * 70)
    print(f"   Client      : {client_id}")
    print(f"   Samples     : {training_record['num_samples']}")
    print(f"   Hist hash   : {training_record['histogram_hash']}")
    if accuracy is not None:
        print(f"   Accuracy    : {accuracy:.4f}")

    ipfs_hash = None
    temp_file_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, prefix=f"{client_id}_training_"
        ) as tmp:
            json.dump(training_record, tmp, indent=2)
            temp_file_path = tmp.name

        url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
        headers = {
            "pinata_api_key": PINATA_API_KEY,
            "pinata_secret_api_key": PINATA_SECRET_API_KEY,
        }
        pinata_metadata = {
            "name": f"{client_id}_round{training_record['round_id']}_training_record"
        }

        print("\n📤 Uploading training record to IPFS via Pinata...")
        with open(temp_file_path, "rb") as fh:
            response = requests.post(
                url,
                files={"file": fh},
                data={"pinataMetadata": json.dumps(pinata_metadata)},
                headers=headers,
                timeout=60,
            )

        if response.status_code == 200:
            ipfs_hash = response.json()["IpfsHash"]
            print(f"✅ Uploaded to IPFS – CID: {ipfs_hash}")
            print(f"   🌐 https://gateway.pinata.cloud/ipfs/{ipfs_hash}")
        else:
            print(f"❌ Pinata upload failed: {response.status_code} – {response.text}")
            return None

    except Exception as exc:
        print(f"❌ Error during IPFS upload: {exc}")
        return None

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

    # Append entry to blockchain.txt
    try:
        entry = (
            f"{training_record['timestamp']} | "
            f"client={client_id} | "
            f"round={training_record['round_id']} | "
            f"samples={training_record['num_samples']} | "
            f"hist_hash={training_record['histogram_hash']} | "
            f"accuracy={accuracy if accuracy is not None else 'N/A'} | "
            f"ipfs_cid={ipfs_hash}\n"
        )
        with open(blockchain_path, "a") as bf:
            bf.write(entry)
        print(f"📝 Entry appended to blockchain.txt: {blockchain_path}")
        print(f"   {entry.strip()}")
    except Exception as exc:
        print(f"⚠️  Could not write to blockchain.txt: {exc}")

    print("=" * 70)
    return ipfs_hash


def upload_updated_model_to_ipfs(
    model, client_id, model_folder="model", blockchain_path=None
):
    """
    Save the locally-trained model to a file, upload it to IPFS via Pinata,
    and OVERWRITE blockchain.txt with the new CID in the same format as main.py:

        Global mode=<new_CID>

    This makes the updated model available for the next federated round.

    Args:
        model: Trained XGBClassifier instance.
        client_id (str): Client identifier (used for the Pinata pin name).
        model_folder (str): Folder to temporarily save the model JSON.
        blockchain_path (str | None): Path to blockchain.txt.

    Returns:
        str | None: The new IPFS CID on success, or None on failure.
    """
    if requests is None:
        print("⚠️  'requests' package not installed – skipping updated-model upload.")
        return None

    if blockchain_path is None:
        blockchain_path = os.path.join(os.path.dirname(__file__), "blockchain.txt")

    PINATA_API_KEY = os.getenv("PINATA_API_KEY")
    PINATA_SECRET_API_KEY = os.getenv("PINATA_SECRET_API_KEY")

    if not PINATA_API_KEY or not PINATA_SECRET_API_KEY:
        print(
            "⚠️  PINATA_API_KEY / PINATA_SECRET_API_KEY not set in .env – "
            "skipping updated-model upload."
        )
        return None

    print("\n" + "=" * 70)
    print("🚀 UPLOADING UPDATED MODEL TO IPFS")
    print("=" * 70)

    # Save model to a temporary file
    os.makedirs(model_folder, exist_ok=True)
    temp_model_path = os.path.join(model_folder, f"{client_id}_updated_model_tmp.json")
    try:
        model.save_model(temp_model_path)
        print(f"💾 Model saved temporarily to: {temp_model_path}")
    except Exception as exc:
        print(f"❌ Could not save model: {exc}")
        return None

    new_cid = None
    try:
        url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
        headers = {
            "pinata_api_key": PINATA_API_KEY,
            "pinata_secret_api_key": PINATA_SECRET_API_KEY,
        }
        pinata_metadata = {
            "name": f"{client_id}_updated_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }

        print("📤 Uploading updated model to IPFS via Pinata...")
        with open(temp_model_path, "rb") as fh:
            response = requests.post(
                url,
                files={"file": fh},
                data={"pinataMetadata": json.dumps(pinata_metadata)},
                headers=headers,
                timeout=120,
            )

        if response.status_code == 200:
            new_cid = response.json()["IpfsHash"]
            print(f"✅ Updated model uploaded to IPFS – CID: {new_cid}")
            print(f"   🌐 https://gateway.pinata.cloud/ipfs/{new_cid}")
        else:
            print(f"❌ Pinata upload failed: {response.status_code} – {response.text}")
            return None

    except Exception as exc:
        print(f"❌ Error uploading updated model: {exc}")
        return None

    finally:
        # Clean up temporary model file
        if os.path.exists(temp_model_path):
            os.unlink(temp_model_path)

    # ── Overwrite blockchain.txt with the new global model CID ────────────────
    try:
        new_entry = f"Global mode={new_cid}"
        with open(blockchain_path, "w") as bf:
            bf.write(new_entry)
        print("\n📝 blockchain.txt updated with new model CID:")
        print(f"   {new_entry}")
        print(f"   Path: {blockchain_path}")
    except Exception as exc:
        print(f"⚠️  Could not update blockchain.txt: {exc}")

    print("=" * 70)
    return new_cid


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

    # Save outputs (histograms sent to server)
    hist_path, local_model_path = save_client_outputs(
        model, histogram_data, client_id, output_folder="model"
    )

    # Upload training details (histogram metadata) to IPFS and log to blockchain.txt
    hist_ipfs_cid = upload_to_ipfs_and_log_blockchain(
        histogram_data=histogram_data,
        client_id=client_id,
        accuracy=None,  # Pass a float here if you compute local accuracy
    )

    # ── KEY STEP: Upload the updated (locally-trained) model to IPFS ──────────
    # After uploading, blockchain.txt is overwritten with the new model CID so
    # that the next federated round starts from this updated model.
    new_model_cid = upload_updated_model_to_ipfs(
        model=model,
        client_id=client_id,
        model_folder="model",
    )

    # Summary
    print("\n" + "=" * 70)
    print("✅ FEDERATED LEARNING CLIENT COMPLETE")
    print("=" * 70)
    print(f"Client          : {client_id}")
    print(f"Samples trained : {histogram_data['num_samples']}")
    print(f"Histograms file : {hist_path}")
    if hist_ipfs_cid:
        print(f"Histogram CID   : {hist_ipfs_cid}")
    if new_model_cid:
        print(f"Updated model CID: {new_model_cid}")
        print("blockchain.txt  : updated with new model CID ✅")
    print("\nNext steps:")
    print("1. Send histograms to aggregation server")
    print("2. Server will aggregate from all clients")
    print(
        "3. Next client run will fetch the updated model from IPFS via blockchain.txt"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()
