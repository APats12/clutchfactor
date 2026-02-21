import client from './client'

export async function startReplay(
  gameId: string,
  csvFilename: string,
  nflfastrGameId: string,
  speed = 1.0,
): Promise<void> {
  await client.post(`/replay/${gameId}/start`, null, {
    params: { csv_filename: csvFilename, nflfastr_game_id: nflfastrGameId, speed },
  })
}

export async function stopReplay(gameId: string): Promise<void> {
  await client.post(`/replay/${gameId}/stop`)
}
