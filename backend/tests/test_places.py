"""Place API integration tests."""

from __future__ import annotations

import uuid


async def _create_place(client, api_headers, **overrides):
    payload = {"canonical_name": f"test-place-{uuid.uuid4()}"}
    payload.update(overrides)
    response = await client.post("/api/v1/places", json=payload, headers=api_headers)
    assert response.status_code == 201, response.text
    return response.json()["place"]


async def test_create_place(client, api_headers):
    place = await _create_place(client, api_headers)

    assert place["canonical_name"].startswith("test-place-")
    assert place["normalized_name"]

    delete_res = await client.delete(f"/api/v1/places/{place['id']}", headers=api_headers)
    assert delete_res.status_code == 204


async def test_create_place_with_tags(client, api_headers):
    place = await _create_place(client, api_headers, tags=["pytest-tag"], notes=["pytest-note"])

    detail_res = await client.get(f"/api/v1/places/{place['id']}", headers=api_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()

    assert any(tag["name"] == "pytest-tag" for tag in detail["tags"])
    assert any(note["content"] == "pytest-note" for note in detail["notes"])

    delete_res = await client.delete(f"/api/v1/places/{place['id']}", headers=api_headers)
    assert delete_res.status_code == 204


async def test_get_place(client, api_headers):
    place = await _create_place(client, api_headers)

    response = await client.get(f"/api/v1/places/{place['id']}", headers=api_headers)
    assert response.status_code == 200
    assert response.json()["id"] == place["id"]

    await client.delete(f"/api/v1/places/{place['id']}", headers=api_headers)


async def test_list_places(client, api_headers):
    p1 = await _create_place(client, api_headers)
    p2 = await _create_place(client, api_headers)

    response = await client.get("/api/v1/places", params={"limit": 2}, headers=api_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) >= 2
    assert "next_cursor" in body

    await client.delete(f"/api/v1/places/{p1['id']}", headers=api_headers)
    await client.delete(f"/api/v1/places/{p2['id']}", headers=api_headers)


async def test_update_place(client, api_headers):
    place = await _create_place(client, api_headers)

    response = await client.patch(
        f"/api/v1/places/{place['id']}",
        json={"is_favorite": True, "user_rating": 5},
        headers=api_headers,
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["is_favorite"] is True
    assert updated["user_rating"] == 5

    await client.delete(f"/api/v1/places/{place['id']}", headers=api_headers)


async def test_delete_place(client, api_headers):
    place = await _create_place(client, api_headers)

    delete_res = await client.delete(f"/api/v1/places/{place['id']}", headers=api_headers)
    assert delete_res.status_code == 204

    get_res = await client.get(f"/api/v1/places/{place['id']}", headers=api_headers)
    assert get_res.status_code == 404
