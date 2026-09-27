import { test } from 'node:test';
import assert from 'node:assert/strict';
import { aggregateRoomMetrics } from '../deploy/ledger-metrics.ts';

test('room aggregate changes with states and connections without identities', () => {
  const rooms = [
    { status: 'waiting', code: 'private-room', nickname: 'private-player' },
    { status: 'playing' },
  ];
  const conn = { readyState: 1, token: 'secret-token' };
  const conns = [new Set([conn])];
  const first = aggregateRoomMetrics(rooms, conns);
  assert.equal(first.rooms.waiting, 1);
  assert.equal(first.rooms.playing, 1);
  assert.equal(first.connections, 1);
  rooms[0].status = 'paused';
  conn.readyState = 2;
  const next = aggregateRoomMetrics(rooms, conns);
  assert.equal(next.rooms.waiting, 0);
  assert.equal(next.rooms.paused, 1);
  assert.equal(next.connections, 0);
  assert.deepEqual(Object.keys(next).sort(), ['connections', 'rooms']);
  assert.doesNotMatch(JSON.stringify(next), /private|secret/);
});
