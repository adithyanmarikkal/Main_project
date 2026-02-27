/**
 * routes/blockchain.js
 * ─────────────────────
 * Contract interaction routes (read + write).
 *
 *  POST /api/submit-client-update   – submitLocalUpdate(cid, metadata)
 *  POST /api/authorize-node         – addNode(address)   [owner only]
 *  GET  /api/latest-model           – getLatestModelCID()
 *  GET  /api/model-versions         – getAllModelVersions()
 *  GET  /api/client-updates/:round  – getClientUpdatesForRound(round)
 *  GET  /api/current-round          – currentRound()
 *  GET  /api/owner                  – Returns the server signer address (contract owner)
 */

const express = require("express");
const { ethers } = require("ethers");
const {
    updateGlobalModel,
    submitClientUpdate,
    authorizeNode,
    getLatestModelCID,
    getAllModelVersions,
    getClientUpdatesForRound,
    getCurrentRound,
    getSigner,
} = require("../lib/contract");

const router = express.Router();

// ── GET /api/owner ────────────────────────────────────────────────────────────
/**
 * Returns the Ethereum address of the server's signer (contract owner).
 * The frontend compares this against the connected MetaMask address to
 * decide whether to grant admin access.
 */
router.get("/owner", (req, res) => {
    try {
        const signer = getSigner();
        res.json({ owner: signer.address.toLowerCase() });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ── POST /api/submit-client-update ────────────────────────────────────────────
/**
 * Body (JSON): { cid: string, metadata?: string }
 * Returns:     { txHash, blockNumber, cid }
 */
router.post("/submit-client-update", async (req, res) => {
    const { cid, metadata = "" } = req.body;

    if (!cid) {
        return res.status(400).json({ error: "'cid' is required in the request body." });
    }

    try {
        console.log(`\n📨 submitClientUpdate  CID=${cid}  metadata="${metadata}"`);
        const receipt = await submitClientUpdate(cid, metadata);
        console.log(`✅ Tx: ${receipt.hash}  block #${receipt.blockNumber}`);

        res.json({
            success: true,
            cid,
            txHash: receipt.hash,
            blockNumber: receipt.blockNumber,
            explorer: `https://www.oklink.com/amoy/tx/${receipt.hash}`,
        });
    } catch (err) {
        console.error("❌ submit-client-update error:", err.message);
        res.status(500).json({ error: err.message });
    }
});

// ── POST /api/authorize-node ──────────────────────────────────────────────────
/**
 * Body (JSON): { address: string }   (owner only)
 * Returns:     { txHash, blockNumber, address }
 */
router.post("/authorize-node", async (req, res) => {
    const { address } = req.body;

    if (!address) {
        return res.status(400).json({ error: "'address' is required in the request body." });
    }

    try {
        console.log(`\n🔐 authorizeNode  address=${address}`);
        const receipt = await authorizeNode(address);
        console.log(`✅ Tx: ${receipt.hash}  block #${receipt.blockNumber}`);

        res.json({
            success: true,
            address,
            txHash: receipt.hash,
            blockNumber: receipt.blockNumber,
            explorer: `https://www.oklink.com/amoy/tx/${receipt.hash}`,
        });
    } catch (err) {
        console.error("❌ authorize-node error:", err.message);
        res.status(500).json({ error: err.message });
    }
});

// ── GET /api/latest-model ─────────────────────────────────────────────────────
router.get("/latest-model", async (_req, res) => {
    try {
        const cid = await getLatestModelCID();
        res.json({
            cid,
            gateway: `https://gateway.pinata.cloud/ipfs/${cid}`,
        });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ── GET /api/model-versions ───────────────────────────────────────────────────
router.get("/model-versions", async (_req, res) => {
    try {
        const versions = await getAllModelVersions();

        // Serialise BigInt → Number for JSON
        const parsed = versions.map((v) => ({
            version: Number(v.version),
            round: Number(v.round),
            ipfsCID: v.ipfsCID,
            timestamp: Number(v.timestamp),
            recordedAt: new Date(Number(v.timestamp) * 1000).toISOString(),
            recordedBy: v.recordedBy,
            gateway: `https://gateway.pinata.cloud/ipfs/${v.ipfsCID}`,
        }));

        res.json({ total: parsed.length, versions: parsed });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ── GET /api/client-updates/:round ────────────────────────────────────────────
router.get("/client-updates/:round", async (req, res) => {
    const round = parseInt(req.params.round, 10);

    if (isNaN(round) || round < 1) {
        return res.status(400).json({ error: "':round' must be a positive integer." });
    }

    try {
        const updates = await getClientUpdatesForRound(round);

        const parsed = updates.map((u) => ({
            nodeAddress: u.nodeAddress,
            ipfsCID: u.ipfsCID,
            timestamp: Number(u.timestamp),
            submittedAt: new Date(Number(u.timestamp) * 1000).toISOString(),
            metadata: u.metadata,
            gateway: `https://gateway.pinata.cloud/ipfs/${u.ipfsCID}`,
        }));

        res.json({ round, total: parsed.length, updates: parsed });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ── GET /api/current-round ────────────────────────────────────────────────────
router.get("/current-round", async (_req, res) => {
    try {
        const round = await getCurrentRound();
        res.json({ currentRound: Number(round) });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

module.exports = router;
