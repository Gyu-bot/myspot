"""Deduplication integration tests."""

from __future__ import annotations

import uuid


async def _create_place(client, api_headers, **overrides):
    payload = {"canonical_name": f"dedup-place-{uuid.uuid4()}"}
    payload.update(overrides)
    response = await client.post("/api/v1/places", json=payload, headers=api_headers)
    assert response.status_code == 201, response.text
    return response.json()["place"]


async def test_duplicate_by_name(client, api_headers):
    place = await _create_place(client, api_headers, canonical_name="중복테스트카페")

    dup_res = await client.post(
        "/api/v1/places/check-duplicates",
        json={"canonical_name": "중복 테스트 카페"},
        headers=api_headers,
    )
    assert dup_res.status_code == 200
    candidates = dup_res.json()
    assert any(c["place_id"] == place["id"] for c in candidates)

    await client.delete(f"/api/v1/places/{place['id']}", headers=api_headers)


async def test_duplicate_by_phone(client, api_headers):
    place = await _create_place(client, api_headers, phone="010-9999-0000", canonical_name="전화중복테스트")

    dup_res = await client.post(
        "/api/v1/places/check-duplicates",
        json={"canonical_name": "다른이름", "phone": "01099990000"},
        headers=api_headers,
    )
    assert dup_res.status_code == 200
    candidates = dup_res.json()
    assert any(c["place_id"] == place["id"] for c in candidates)

    await client.delete(f"/api/v1/places/{place['id']}", headers=api_headers)


async def test_merge_places(client, api_headers):
    keep = await _create_place(client, api_headers, canonical_name=f"merge-keep-{uuid.uuid4()}")
    merge = await _create_place(client, api_headers, canonical_name=f"merge-src-{uuid.uuid4()}")

    note_res = await client.post(
        "/api/v1/notes",
        json={"place_id": merge["id"], "content": "merge-note"},
        headers=api_headers,
    )
    assert note_res.status_code == 201

    merge_res = await client.post(
        f"/api/v1/places/{keep['id']}/merge",
        json={"merge_with": merge["id"]},
        headers=api_headers,
    )
    assert merge_res.status_code == 200
    merged = merge_res.json()
    assert any(note["content"] == "merge-note" for note in merged["notes"])

    missing_res = await client.get(f"/api/v1/places/{merge['id']}", headers=api_headers)
    assert missing_res.status_code == 404

    await client.delete(f"/api/v1/places/{keep['id']}", headers=api_headers)
