import pytest

from app.adapters.sql.models import (
    ExperienceModel,
    ExperiencePhotoModel,
    ServiceModel,
    ServicePhotoModel,
)

API = "/api/v1"


@pytest.fixture
def catalogue(app, make_user):
    host, _ = make_user(is_host=True)
    with app.state.session_factory() as s:
        experiences = [
            ExperienceModel(
                host_id=host.id,
                title="Heritage walk",
                description="d",
                category="heritage",
                city="Jaipur",
                state="Rajasthan",
                latitude=26.9,
                longitude=75.8,
                start_time="08:30",
                duration_minutes=150,
                price_per_guest=1000,
                max_guests=8,
                rating_avg=4.9,
                review_count=40,
            ),
            ExperienceModel(
                host_id=host.id,
                title="Thali night",
                description="d",
                category="food",
                city="Jaipur",
                state="Rajasthan",
                latitude=26.9,
                longitude=75.8,
                start_time="19:00",
                duration_minutes=120,
                price_per_guest=2000,
                max_guests=6,
                rating_avg=None,
                review_count=0,
            ),
            ExperienceModel(
                host_id=host.id,
                title="Canoe ride",
                description="d",
                category="nature",
                city="Alleppey",
                state="Kerala",
                latitude=9.5,
                longitude=76.3,
                start_time="08:00",
                duration_minutes=150,
                price_per_guest=900,
                max_guests=4,
                rating_avg=4.8,
                review_count=12,
            ),
        ]
        services = [
            ServiceModel(
                host_id=host.id,
                title="Portraits at Amber Fort",
                description="d",
                service_type="photography",
                city="Jaipur",
                state="Rajasthan",
                price_from=6500,
                price_unit="session",
                is_popular=True,
                rating_avg=4.9,
                review_count=30,
            ),
            ServiceModel(
                host_id=host.id,
                title="Home chef",
                description="d",
                service_type="chefs",
                city="Jaipur",
                state="Rajasthan",
                price_from=2200,
                price_unit="guest",
                rating_avg=4.7,
                review_count=9,
            ),
            ServiceModel(
                host_id=host.id,
                title="Beach portraits",
                description="d",
                service_type="photography",
                city="Goa",
                state="Goa",
                price_from=5500,
                price_unit="session",
                rating_avg=4.8,
                review_count=5,
            ),
        ]
        s.add_all([*experiences, *services])
        s.flush()
        for row in experiences:
            s.add(
                ExperiencePhotoModel(
                    experience_id=row.id,
                    url="/media/a.webp",
                    card_url="/media/a_card.webp",
                    position=0,
                )
            )
        for row in services:
            s.add(
                ServicePhotoModel(
                    service_id=row.id,
                    url="/media/a.webp",
                    card_url="/media/a_card.webp",
                    position=0,
                )
            )
        s.commit()
        return {"experience": experiences[0].id, "service": services[0].id}


def test_experiences_can_be_searched_by_place_and_category(client, catalogue):
    jaipur = client.get(f"{API}/experiences", params={"location": "jaipur"}).json()
    assert jaipur["total"] == 2
    assert [e["title"] for e in jaipur["items"]][0] == "Heritage walk"  # best rated first
    assert jaipur["items"][0]["photos"][0]["card_url"].endswith("_card.webp")

    food = client.get(f"{API}/experiences", params={"category": "food"}).json()
    assert [e["title"] for e in food["items"]] == ["Thali night"]
    cheapest = client.get(f"{API}/experiences", params={"sort": "price_asc"}).json()
    assert cheapest["items"][0]["title"] == "Canoe ride"
    assert client.get(f"{API}/experiences", params={"category": "bogus"}).status_code == 422


def test_experience_and_service_detail_pages(client, catalogue):
    experience = client.get(f"{API}/experiences/{catalogue['experience']}").json()
    assert experience["host"]["first_name"] == "Test" and "email" not in experience["host"]
    assert (experience["start_time"], experience["max_guests"]) == ("08:30", 8)
    service = client.get(f"{API}/services/{catalogue['service']}").json()
    assert service["price_unit"] == "session" and len(service["all_photos"]) == 1
    assert client.get(f"{API}/experiences/9999").json()["code"] == "EXPERIENCE_NOT_FOUND"
    assert client.get(f"{API}/services/9999").json()["code"] == "SERVICE_NOT_FOUND"


def test_services_are_grouped_into_types_and_filtered(client, catalogue):
    types = client.get(f"{API}/services/types").json()
    assert [(t["key"], t["count"]) for t in types] == [("photography", 2), ("chefs", 1)]
    assert types[0]["label"] == "Photography"
    in_jaipur = client.get(f"{API}/services/types", params={"location": "jaipur"}).json()
    assert [(t["key"], t["count"]) for t in in_jaipur] == [("photography", 1), ("chefs", 1)]

    photography = client.get(f"{API}/services", params={"service_type": "photography"}).json()
    assert photography["total"] == 2 and photography["items"][0]["is_popular"] is True
