'use client'
import { useReadContract, useWriteContract } from 'wagmi'
import { DAO_CONTRACT } from '../lib/contracts'

export default function GovernancePanel() {
  const { data: proposals } = useReadContract({
    ...DAO_CONTRACT,
    functionName: 'getProposals',
  })

  const { writeContract } = useWriteContract()

  return (
    <div>
      <h2>Governance</h2>

      {proposals?.map((p, i) => (
        <div key={i}>
          <p>{p.description}</p>
          <button onClick={() =>
            writeContract({
              ...DAO_CONTRACT,
              functionName: 'vote',
              args: [p.id, true],
            })
          }>
            Vote YES
          </button>
        </div>
      ))}
    </div>
  )
}
