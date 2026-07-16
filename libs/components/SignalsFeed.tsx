'use client'
import { useEffect, useState } from 'react'
import { subscribeToSignals } from '../lib/signals'

export default function SignalsFeed() {
  const [events, setEvents] = useState([])

  useEffect(() => {
    const unsub = subscribeToSignals((evt) =>
      setEvents((prev) => [evt, ...prev])
    )
    return () => unsub()
  }, [])

  return (
    <div>
      <h2>NPPI Signals</h2>
      {events.map((e, i) => (
        <pre key={i}>{JSON.stringify(e, null, 2)}</pre>
      ))}
    </div>
  )
}
