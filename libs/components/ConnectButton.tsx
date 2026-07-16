'use client'
import { useConnect, useAccount, useDisconnect } from 'wagmi'

export default function ConnectButton() {
  const { connect, connectors } = useConnect()
  const { address, isConnected } = useAccount()
  const { disconnect } = useDisconnect()

  if (isConnected)
    return (
      <button onClick={() => disconnect()}>
        Disconnect {address.slice(0, 6)}…
      </button>
    )

  return (
    <button onClick={() => connect({ connector: connectors[0] })}>
      Connect Wallet
    </button>
  )
}
