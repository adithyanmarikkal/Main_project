# True Federated Learning Implementation

This implementation provides **true federated learning** for XGBoost models using the **FedAvg (Federated Averaging)** algorithm with histogram-based aggregation.

## 🔐 What is True Federated Learning?

In true federated learning:
- **Clients keep their data private** - data never leaves the client
- **Only aggregated statistics are shared** - not raw data or full models
- **Server aggregates gradients/hessians** - using weighted averaging (FedAvg)
- **Privacy is preserved** - server never sees individual client data

## 📁 Files

### Client Side
- **`client.py`** - Federated learning client implementation
  - Loads global model from server
  - Trains on local private data
  - Computes gradients and hessians
  - Sends only histogram statistics to server

### Server Side
- **`aggregation.py`** - Federated aggregation server
  - Collects histograms from all clients
  - Performs weighted averaging (FedAvg)
  - Builds global model from aggregated statistics
  - Distributes updated global model to clients

## 🚀 Usage

### Step 1: Run Clients

Each client trains on their private data and computes histograms:

```bash
# Client 1
python client.py --client-id client_1

# Client 2 (if you have multiple clients)
CLIENT_ID=client_2 python client.py

# Client 3
python client.py --client-id client_3
```

**Output**: Each client generates a `{client_id}_histograms.json` file in the `model/` folder.

### Step 2: Run Server Aggregation

The server aggregates histograms from all clients:

```bash
python aggregation.py
```

**Output**: 
- `model/aggregated_histograms.json` - Aggregated statistics
- `model/global_model.json` - Updated global model

### Step 3: Distribute Global Model

In the next round, clients load the `global_model.json` and repeat the process.

## 🔄 Federated Learning Workflow

```
Round 1:
┌─────────────┐
│   Server    │
│  (Initial   │
│   Model)    │
└──────┬──────┘
       │ Distribute
       ▼
┌──────────────────────────────────┐
│  Client 1  │  Client 2  │ Client 3 │
│  (Private  │  (Private  │ (Private │
│   Data)    │   Data)    │  Data)   │
└─────┬──────┴─────┬──────┴────┬─────┘
      │            │           │
      │ Train      │ Train     │ Train
      │ Locally    │ Locally   │ Locally
      ▼            ▼           ▼
┌─────────────────────────────────┐
│  Compute Gradients & Histograms │
└─────┬──────┬─────┬──────────────┘
      │      │     │
      │ Send │     │ Send
      │ Stats│     │ Stats
      ▼      ▼     ▼
┌─────────────────────┐
│   Server Aggregates │
│   (FedAvg)          │
└──────┬──────────────┘
       │
       ▼
┌──────────────┐
│ Global Model │
│  (Updated)   │
└──────────────┘

Repeat for Round 2, 3, ...
```

## 📊 What Gets Shared?

### ✅ Shared with Server (Privacy-Preserving)
- **Histograms**: Aggregated gradients and hessians per feature bin
- **Metadata**: Number of samples, label distribution
- **Statistics**: Feature-level aggregated statistics

### ❌ NOT Shared with Server
- **Raw data**: Client data stays on client
- **Individual predictions**: Only aggregated statistics
- **Full model weights**: Only histograms are sent

## 🔑 Key Features

### 1. **FedAvg Algorithm**
Implements the standard Federated Averaging algorithm:
- Weighted averaging based on client sample counts
- Proper gradient and hessian aggregation
- Supports multiple clients with different data sizes

### 2. **Histogram-Based Aggregation**
For XGBoost models, we use histogram-based aggregation:
- Computes gradients (G) and hessians (H) for each feature
- Bins features into histograms
- Aggregates statistics per bin across clients

### 3. **Privacy Preservation**
- Data never leaves the client device
- Only aggregated statistics are transmitted
- Server cannot reconstruct individual data points

### 4. **Multi-Client Support**
- Supports any number of clients
- Each client identified by unique ID
- Automatic weight calculation based on data size

## 📝 Client Data Format

Place your client data in `client_data/`:

```
client_data/
├── client_1_data.csv  # Client 1's private data
├── client_2_data.csv  # Client 2's private data
└── client_3_data.csv  # Client 3's private data
```

Or use a generic `client_data.csv` for all clients.

### Data Format
- **With labels**: CSV with features and a `label` column
- **Without labels**: CSV with features only (uses pseudo-labeling)

## 🛠️ Advanced Configuration

### Client Configuration
```python
# In client.py, you can modify:
- threshold: Confidence threshold for pseudo-labeling (default: 0.95)
- num_bins: Number of histogram bins (default: 10)
- round_id: Current training round
```

### Server Configuration
```python
# In aggregation.py, you can modify:
- use_histograms: Enable/disable histogram aggregation (default: True)
- weights: Custom client weights (default: auto-calculated)
```

## 📈 Monitoring

Each client outputs:
- Number of samples trained
- Label distribution
- Histogram hash (for verification)
- Training status

Server outputs:
- Number of clients aggregated
- Total samples across all clients
- Client weights
- Aggregation method used

## 🔒 Security Considerations

This implementation provides:
- **Data privacy**: Raw data never shared
- **Aggregated statistics**: Only histograms transmitted
- **Weighted aggregation**: Fair contribution from all clients

For production use, consider adding:
- **Secure aggregation**: Encrypted histogram transmission
- **Differential privacy**: Add noise to histograms
- **Authentication**: Verify client identities
- **Secure channels**: Use TLS/SSL for communication

## 🎯 Next Steps

1. **Multiple Rounds**: Implement iterative training over multiple rounds
2. **Client Selection**: Randomly select subset of clients per round
3. **Differential Privacy**: Add noise to gradients for stronger privacy
4. **Secure Aggregation**: Encrypt histograms during transmission
5. **Model Compression**: Reduce communication overhead

## 📚 References

- **FedAvg Paper**: [Communication-Efficient Learning of Deep Networks from Decentralized Data](https://arxiv.org/abs/1602.05629)
- **XGBoost**: [XGBoost Documentation](https://xgboost.readthedocs.io/)
- **Federated Learning**: [Google AI Blog on Federated Learning](https://ai.googleblog.com/2017/04/federated-learning-collaborative.html)
