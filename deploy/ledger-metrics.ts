import { createServer } from 'node:http';

export const statuses = [
  'waiting',
  'starting',
  'playing',
  'paused',
  'finished',
  'closed',
] as const;
export type RoomMetrics = {
  rooms: Record<string, number>;
  connections: number;
};

export function aggregateRoomMetrics(
  rooms: Iterable<{ status: string }>,
  connections: Iterable<Set<{ readyState: number }>>,
): RoomMetrics {
  const counts: Record<string, number> = Object.fromEntries(
    statuses.map((status) => [status, 0]),
  );
  for (const room of rooms)
    if (Object.hasOwn(counts, room.status)) counts[room.status]++;
  let total = 0;
  for (const group of connections)
    for (const conn of group) if (conn.readyState === 1) total++;
  return { rooms: counts, connections: total };
}

export function startRoomMetrics(snapshot: () => RoomMetrics) {
  const server = createServer((req, res) => {
    if (req.method !== 'GET' || req.url !== '/metrics') {
      res.writeHead(404).end();
      return;
    }
    res.writeHead(200, {
      'Content-Type': 'application/json',
      'Cache-Control': 'no-store',
    });
    res.end(JSON.stringify(snapshot()));
  });
  server.on('error', () =>
    console.error('[roomsrv] internal metrics listener unavailable'),
  );
  server.listen(Number(process.env.ROOM_METRICS_PORT ?? 8788), '127.0.0.1');
  return server;
}
