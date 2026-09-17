import ConnectButton from '../components/ConnectButton'
import GovernancePanel from '../components/GovernancePanel'
import SignalsFeed from '../components/SignalsFeed'

export default function Home() {
  return (
    <main>
      <ConnectButton />
      <GovernancePanel />
      <SignalsFeed />
    </main>
  )
}
