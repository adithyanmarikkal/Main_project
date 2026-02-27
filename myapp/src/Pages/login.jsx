import { useState } from "react"
import { ethers } from "ethers"

function Login() {
  const [account, setAccount] = useState(null)
  const [error, setError] = useState("")

  const connectWallet = async () => {
    try {
      if (!window.ethereum) {
        setError("MetaMask not installed")
        return
      }

      const provider = new ethers.BrowserProvider(window.ethereum)
      const accounts = await provider.send("eth_requestAccounts", [])

      setAccount(accounts[0])
    } catch (err) {
      setError("User rejected connection")
    }
  }

  return (
    <div style={{ textAlign: "center", marginTop: "80px" }}>
      <h1>Login with MetaMask</h1>

      {!account ? (
        <button onClick={connectWallet}>
          Connect MetaMask
        </button>
      ) : (
        <>
          <p>Connected as:</p>
          <strong>{account}</strong>
        </>
      )}

      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  )
}

export default Login