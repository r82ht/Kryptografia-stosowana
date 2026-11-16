import pytest

from common import crypto
from common.blockchain import Blockchain, block_hash, create_block, make_genesis, verify_block

PRIV = crypto.generate_private_key()
PUB = crypto.public_key_to_hex(PRIV.public_key())


@pytest.fixture
def genesis():
    return make_genesis()


@pytest.fixture
def block(genesis):
    return create_block(genesis, [], PUB, PRIV)


def test_hash_changes_with_content(block):
    zmieniony = dict(block, transactions=[{"x": 1}])
    assert block_hash(block) != block_hash(zmieniony)


def test_genesis_is_always_the_same():
    assert make_genesis() == make_genesis()


def test_valid_block_passes(block, genesis):
    assert verify_block(block, genesis, PUB)[0]


def test_changed_content_rejected(block, genesis):
    block["transactions"] = [{"hack": 1}]
    assert not verify_block(block, genesis, PUB)[0]


def test_rehashed_block_has_bad_signature(block, genesis):
    block["transactions"] = [{"hack": 1}]
    block["hash"] = block_hash(block)
    assert not verify_block(block, genesis, PUB)[0]


def test_wrong_prev_hash_rejected(block, genesis):
    block["prev_hash"] = "0" * 64
    assert not verify_block(block, genesis, PUB)[0]


def test_longer_chain_replaces_shorter():
    a = Blockchain(PUB)
    a.mine_block([], PRIV)
    a.mine_block([], PRIV)
    b = Blockchain(PUB)
    assert b.replace_chain(a.snapshot())
    assert len(b.chain) == 3


def test_same_length_not_replaced():
    a = Blockchain(PUB)
    a.mine_block([], PRIV)
    assert not Blockchain(PUB).replace_chain([make_genesis()])
    b = Blockchain(PUB)
    b.mine_block([], PRIV)
    assert not b.replace_chain(a.snapshot())


def test_tampered_chain_rejected():
    a = Blockchain(PUB)
    a.mine_block([], PRIV)
    zly = a.snapshot()
    zly[1] = dict(zly[1], transactions=[{"hack": 1}])
    assert not Blockchain(PUB).replace_chain(zly)