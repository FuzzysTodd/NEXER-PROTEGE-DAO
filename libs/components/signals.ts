export function subscribeToSignals(callback) {
  const ws = new WebSocket('wss://your-nppi-event-spine')

  ws.onmessage = (msg) => {
    const evt = JSON.parse(msg.data)
    callback(evt)
  }

  return () => ws.close()
}
