import pytest

from referral_service import ReferralService


class FakeCollection:
    def __init__(self, *, find_one_results=None):
        self.find_one_results = list(find_one_results or [])
        self.find_one_calls = []
        self.update_one_calls = []
        self.insert_one_calls = []

    async def find_one(self, query):
        self.find_one_calls.append(query)
        if self.find_one_results:
            return self.find_one_results.pop(0)
        return None

    async def update_one(self, query, update):
        self.update_one_calls.append((query, update))

    async def insert_one(self, doc):
        self.insert_one_calls.append(doc)


class FakeDB:
    def __init__(self, users_col, referrals_col):
        self._collections = {
            "users": users_col,
            "referrals": referrals_col,
        }

    def get_collection(self, name):
        return self._collections[name]


@pytest.mark.anyio
async def test_validate_referral_code_normalizes_and_validates():
    users_col = FakeCollection(find_one_results=[{"id": "ref-1", "name": "Alice"}])
    referrals_col = FakeCollection(find_one_results=[None])
    service = ReferralService(FakeDB(users_col, referrals_col))

    result = await service.validate_referral_code("new-user", "  abcd1234 ")

    assert result["success"] is True
    assert result["referral_code"] == "ABCD1234"
    assert result["referrer_id"] == "ref-1"
    assert users_col.find_one_calls[0] == {"referral_code": "ABCD1234"}


@pytest.mark.anyio
async def test_apply_referral_uses_prevalidated_data_without_requerying():
    users_col = FakeCollection()
    referrals_col = FakeCollection()
    service = ReferralService(FakeDB(users_col, referrals_col))

    validation = {
        "success": True,
        "referrer_id": "ref-9",
        "referrer_name": "Tester",
        "referral_code": "REFCODE9",
    }

    result = await service.apply_referral_code(
        "new-user",
        "ignored-input",
        validation=validation,
    )

    assert result["success"] is True
    assert result["referrer_name"] == "Tester"
    assert users_col.find_one_calls == []
    assert len(referrals_col.insert_one_calls) == 1
    assert referrals_col.insert_one_calls[0]["referral_code"] == "REFCODE9"
