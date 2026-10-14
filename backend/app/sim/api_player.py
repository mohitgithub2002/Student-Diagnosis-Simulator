"""Drive the real HTTP API with a simulated student (used by integration tests and the demo seed)."""

import dataclasses
from typing import Any

from app.sim.simulator import Persona, Player


def play_cycle_via_api(client: Any, token: str, persona: Persona, band: str, lookup=None) -> list[dict]:
    headers = {"Authorization": f"Bearer {token}"}
    player = Player(persona, band, lookup or (lambda *_: []), start=None)  # type: ignore[arg-type]
    results = []
    client.post(
        "/api/student/warmup",
        json={"language": persona.language, "mic_ok": persona.voice, "audio_ok": True},
        headers=headers,
    ).raise_for_status()
    for number in range(1, 8):
        r = client.post(f"/api/student/sessions/{number}/start", json={"device_type": "sim"}, headers=headers)
        r.raise_for_status()
        bundle = r.json()["bundle"]
        if not r.json()["voice_allowed"] and player.p.voice:
            player.p = dataclasses.replace(player.p, voice=False)  # the app falls back to typing
        events, feats = player.play_bundle(bundle)
        for i in range(0, len(events), 100):
            client.post(
                f"/api/student/sessions/{number}/events", json={"events": events[i : i + 100]}, headers=headers
            ).raise_for_status()
        if feats:
            client.post(
                f"/api/student/sessions/{number}/features", json={"features": feats}, headers=headers
            ).raise_for_status()
        done = client.post(f"/api/student/sessions/{number}/complete", headers=headers)
        done.raise_for_status()
        results.append({"number": number, "events": len(events), "features": len(feats), **done.json()})
    return results
