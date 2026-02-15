import pytest
from datetime import datetime, timedelta

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

        for key, value in update.get('$set', {}).items():
            _assign_nested(target, key, value)

        for key, value in update.get('$inc', {}).items():
            current = _get_nested(target, key) or 0
            _assign_nested(target, key, current + value)

    def find(self, query):
        matches = [d for d in self.docs if all(d.get(k) == v for k, v in query.items())]
        return FakeCursor(matches)


def _assign_nested(data, dotted_key, value):
    keys = dotted_key.split('.')
    cur = data
    for key in keys[:-1]:
        cur.setdefault(key, {})
        cur = cur[key]
    cur[keys[-1]] = value


def _get_nested(data, dotted_key):
    cur = data
    for key in dotted_key.split('.'):
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


class FakeDB:
    def __init__(self, collections):
        self.collections = collections

    def get_collection(self, name):
        return self.collections[name]


@pytest.mark.anyio
async def test_create_stake_uses_usd_fallback_when_token_balance_missing(monkeypatch):
    monkeypatch.setattr(earn.settings, 'feature_staking_enabled', True)
    monkeypatch.setattr(earn, '_token_usd_price', _fake_token_price)

    wallets = FakeCollection(docs=[{'user_id': 'u1', 'balances': {'USD': 1000.0}}])
    stakes = FakeCollection()
    transactions = FakeCollection()

    db = FakeDB({'wallets': wallets, 'stakes': stakes, 'transactions': transactions})

    payload = earn.CreateStakeRequest(product_id='eth-30d', amount=0.1)
    result = await earn.create_stake(payload=payload, user_id='u1', db=db)

    assert result['success'] is True
    wallet = await wallets.find_one({'user_id': 'u1'})
    assert wallet['balances']['USD'] == pytest.approx(650.0)
    assert stakes.docs[0]['funding_currency'] == 'USD'


@pytest.mark.anyio
async def test_redeem_stake_credits_usd_for_usd_funded_stake(monkeypatch):
    monkeypatch.setattr(earn.settings, 'feature_staking_enabled', True)
    monkeypatch.setattr(earn, '_token_usd_price', _fake_token_price)

    created = datetime.utcnow() - timedelta(days=40)
    stake_doc = {
        'id': 's1',
        'user_id': 'u1',
        'status': 'active',
        'token': 'ETH',
        'amount': 0.1,
        'apy': 8.5,
        'created_at': created,
        'lock_days': 30,
        'funding_currency': 'USD',
    }

    wallets = FakeCollection(docs=[{'user_id': 'u1', 'balances': {'USD': 0.0}}])
    stakes = FakeCollection(docs=[stake_doc])
    transactions = FakeCollection()
    db = FakeDB({'wallets': wallets, 'stakes': stakes, 'transactions': transactions})

    result = await earn.redeem_stake(payload=earn.CloseStakeRequest(stake_id='s1'), user_id='u1', db=db)

    assert result['success'] is True
    assert result['redeemed']['token'] == 'USD'
    wallet = await wallets.find_one({'user_id': 'u1'})
    assert wallet['balances']['USD'] > 350


@pytest.mark.anyio
async def test_positions_returns_dynamic_days_remaining(monkeypatch):
    monkeypatch.setattr(earn.settings, 'feature_staking_enabled', True)

    created = datetime.utcnow() - timedelta(days=10)
    stakes = FakeCollection(docs=[{
        'id': 's1',
        'user_id': 'u1',
        'status': 'active',
        'product': 'Ethereum 30-Day',
        'token': 'ETH',
        'amount': 1,
        'apy': 8,
        'created_at': created,
        'lock_period': '30 days',
        'lock_days': 30,
    }])

    db = FakeDB({'stakes': stakes})
    data = await earn.get_earn_positions(user_id='u1', db=db)

    assert data['positions'][0]['daysRemaining'] == 20
