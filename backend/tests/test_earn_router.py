import asyncio
from datetime import datetime, timedelta
import sys
import types

import pytest

try:
    import fastapi  # noqa: F401
except ModuleNotFoundError:
    fastapi_stub = types.ModuleType("fastapi")

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)

    class APIRouter:
        def __init__(self, *args, **kwargs):
            pass

        def get(self, *args, **kwargs):
            def deco(fn):
                return fn

            return deco

        def post(self, *args, **kwargs):
            def deco(fn):
                return fn

            return deco

    def Depends(dep):
        return dep

    fastapi_stub.APIRouter = APIRouter
    fastapi_stub.Depends = Depends
    fastapi_stub.HTTPException = HTTPException
    sys.modules["fastapi"] = fastapi_stub

try:
    import pydantic  # noqa: F401
except ModuleNotFoundError:
    pydantic_stub = types.ModuleType("pydantic")

    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    def Field(default=..., **kwargs):
        return default

    pydantic_stub.BaseModel = BaseModel
    pydantic_stub.Field = Field
    sys.modules["pydantic"] = pydantic_stub

deps_stub = types.ModuleType("dependencies")


def _noop_dep(*args, **kwargs):
    return None


deps_stub.get_current_user_id = _noop_dep
deps_stub.get_db = _noop_dep
sys.modules["dependencies"] = deps_stub

config_stub = types.ModuleType("config")


class _Settings:
    feature_staking_enabled = True


config_stub.settings = _Settings()
sys.modules["config"] = config_stub

coincap_stub = types.ModuleType("coincap_service")


class _CoincapService:
    async def get_prices(self, *_args, **_kwargs):
        return []


coincap_stub.coincap_service = _CoincapService()
sys.modules["coincap_service"] = coincap_stub

from fastapi import HTTPException
from routers import earn


async def _fake_token_price(_token: str) -> float:
    return 3500.0


class FakeCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, *args, **kwargs):
        return self

    async def to_list(self, _limit):
        return list(self.docs)


class FakeCollection:
    def __init__(self, *, docs=None):
        self.docs = list(docs or [])
        self.inserted = []

    async def find_one(self, query):
        for d in self.docs:
            if all(d.get(k) == v for k, v in query.items()):
                return d
        return None

    async def insert_one(self, doc):
        self.inserted.append(doc)
        self.docs.append(doc)

    async def update_one(self, query, update, upsert=False):
        target = None
        for d in self.docs:
            if all(d.get(k) == v for k, v in query.items()):
                target = d
                break

        if target is None and upsert:
            target = {**query}
            self.docs.append(target)

        if target is None:
            return

        for key, value in update.get("$set", {}).items():
            _assign_nested(target, key, value)

        for key, value in update.get("$inc", {}).items():
            current = _get_nested(target, key) or 0
            _assign_nested(target, key, current + value)

    def find(self, query):
        matches = [d for d in self.docs if all(d.get(k) == v for k, v in query.items())]
        return FakeCursor(matches)


def _assign_nested(data, dotted_key, value):
    keys = dotted_key.split(".")
    cur = data
    for key in keys[:-1]:
        cur.setdefault(key, {})
        cur = cur[key]
    cur[keys[-1]] = value


def _get_nested(data, dotted_key):
    cur = data
    for key in dotted_key.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


class FakeDB:
    def __init__(self, collections):
        self.collections = collections

    def get_collection(self, name):
        return self.collections[name]


def test_earn_endpoints_blocked_when_feature_disabled(monkeypatch):
    monkeypatch.setattr(earn.settings, "feature_staking_enabled", False)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(earn.get_earn_products())

    assert exc.value.status_code == 503


def test_create_stake_uses_usd_fallback_when_token_balance_missing(monkeypatch):
    monkeypatch.setattr(earn.settings, "feature_staking_enabled", True)
    monkeypatch.setattr(earn, "_token_usd_price", _fake_token_price)

    wallets = FakeCollection(docs=[{"user_id": "u1", "balances": {"USD": 1000.0}}])
    stakes = FakeCollection()
    transactions = FakeCollection()

    db = FakeDB({"wallets": wallets, "stakes": stakes, "transactions": transactions})

    payload = earn.CreateStakeRequest(product_id="eth-30d", amount=0.1)
    result = asyncio.run(earn.create_stake(payload=payload, user_id="u1", db=db))

    assert result["success"] is True
    wallet = asyncio.run(wallets.find_one({"user_id": "u1"}))
    assert wallet["balances"]["USD"] == pytest.approx(650.0)
    assert stakes.docs[0]["funding_currency"] == "USD"


def test_redeem_stake_blocks_locked_position_until_mature(monkeypatch):
    monkeypatch.setattr(earn.settings, "feature_staking_enabled", True)

    created = datetime.utcnow() - timedelta(days=5)
    stake_doc = {
        "id": "s1",
        "user_id": "u1",
        "status": "active",
        "token": "ETH",
        "amount": 0.1,
        "apy": 8.5,
        "created_at": created,
        "lock_days": 30,
        "funding_currency": "ETH",
    }

    wallets = FakeCollection(docs=[{"user_id": "u1", "balances": {"ETH": 0.0}}])
    stakes = FakeCollection(docs=[stake_doc])
    transactions = FakeCollection()
    db = FakeDB({"wallets": wallets, "stakes": stakes, "transactions": transactions})

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            earn.redeem_stake(payload=earn.CloseStakeRequest(stake_id="s1"), user_id="u1", db=db)
        )

    assert exc.value.status_code == 400
    assert "not yet redeemable" in exc.value.detail


def test_redeem_stake_credits_usd_for_usd_funded_stake(monkeypatch):
    monkeypatch.setattr(earn.settings, "feature_staking_enabled", True)
    monkeypatch.setattr(earn, "_token_usd_price", _fake_token_price)

    created = datetime.utcnow() - timedelta(days=40)
    stake_doc = {
        "id": "s1",
        "user_id": "u1",
        "status": "active",
        "token": "ETH",
        "amount": 0.1,
        "apy": 8.5,
        "created_at": created,
        "lock_days": 30,
        "funding_currency": "USD",
    }

    wallets = FakeCollection(docs=[{"user_id": "u1", "balances": {"USD": 0.0}}])
    stakes = FakeCollection(docs=[stake_doc])
    transactions = FakeCollection()
    db = FakeDB({"wallets": wallets, "stakes": stakes, "transactions": transactions})

    result = asyncio.run(earn.redeem_stake(payload=earn.CloseStakeRequest(stake_id="s1"), user_id="u1", db=db))

    assert result["success"] is True
    assert result["redeemed"]["token"] == "USD"
    wallet = asyncio.run(wallets.find_one({"user_id": "u1"}))
    assert wallet["balances"]["USD"] > 350


def test_positions_returns_dynamic_days_remaining(monkeypatch):
    monkeypatch.setattr(earn.settings, "feature_staking_enabled", True)

    created = datetime.utcnow() - timedelta(days=10)
    stakes = FakeCollection(
        docs=[
            {
                "id": "s1",
                "user_id": "u1",
                "status": "active",
                "product": "Ethereum 30-Day",
                "token": "ETH",
                "amount": 1,
                "apy": 8,
                "created_at": created,
                "lock_period": "30 days",
                "lock_days": 30,
            }
        ]
    )

    db = FakeDB({"stakes": stakes})
    data = asyncio.run(earn.get_earn_positions(user_id="u1", db=db))

    assert data["positions"][0]["daysRemaining"] == 20
