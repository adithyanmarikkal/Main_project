import xgboost as xgb
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import glob
import tempfile
import requests
from dotenv import load_dotenv

# Load environment variables from .env file in server directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# 0. Load data from folder
print("📂 Loading data from folder...")
data_folder = os.path.join(os.path.dirname(__file__), 'data')
csv_files = sorted(glob.glob(os.path.join(data_folder, 'part-*.csv')))

# Read and concatenate all CSV files
dataframes = []
for csv_file in csv_files:
    df = pd.read_csv(csv_file)
    dataframes.append(df)

# Combine all dataframes
data = pd.concat(dataframes, ignore_index=True)

# Display first few rows


# 1. Separate features and labels
X = data.drop('label', axis=1)
y = data['label']

# 2. Encode labels
le = LabelEncoder()
y_encoded = le.fit_transform(y)
num_classes = len(le.classes_)


# 3. Split data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
# 5. Initialize XGBoost Classifier
# use 'multi:softprob' for multi-class classification
# tree_method='hist' and device='cuda' makes it much faster if you have a GPU
xgb_model = xgb.XGBClassifier(
    n_estimators=50,
    learning_rate=0.2,
    max_depth=4,
    objective='multi:softprob',
    num_class=num_classes,
    tree_method='hist', # Fast histogram optimized method
    random_state=42
)

# 6. Train the model
xgb_model.fit(X_train, y_train)

# 7. Predict
y_pred_xgb = xgb_model.predict(X_test)

# 8. Evaluate
print(f"\n✅ XGBoost Accuracy: {accuracy_score(y_test, y_pred_xgb):.4f}")

# 9. Detailed Report
used_labels = np.unique(y_encoded)
used_names = le.inverse_transform(used_labels)

# 10. Upload the XGBoost model to IPFS using Pinata
print("📤 Uploading model to IPFS...")

# Get Pinata API credentials
PINATA_API_KEY = os.getenv('PINATA_API_KEY')
PINATA_SECRET_API_KEY = os.getenv('PINATA_SECRET_API_KEY')

if not PINATA_API_KEY or not PINATA_SECRET_API_KEY:
    raise ValueError("PINATA_API_KEY and PINATA_SECRET_API_KEY must be set in .env file")

# Save model to temporary file
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
    xgb_model.save_model(temp_file.name)
    temp_file_path = temp_file.name

# Upload to Pinata
url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
headers = {
    'pinata_api_key': PINATA_API_KEY,
    'pinata_secret_api_key': PINATA_SECRET_API_KEY
}

try:
    with open(temp_file_path, 'rb') as file:
        files = {'file': file}
        response = requests.post(url, files=files, headers=headers)
        
    if response.status_code == 200:
        ipfs_hash = "Global mode=" + response.json()['IpfsHash']
        print(f"✅ Model uploaded to IPFS with hash: {ipfs_hash}")
        
        # Store hash in blockchain.txt
        with open('blockchain.txt', 'w') as f:
            f.write(ipfs_hash)
        print("📝 IPFS hash saved to blockchain.txt")
    else:
        print(f"❌ Error uploading to IPFS: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"❌ Error during upload: {str(e)}")
    
finally:
    # Clean up temporary file
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)