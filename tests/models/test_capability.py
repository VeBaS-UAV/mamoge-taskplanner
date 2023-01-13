#!/usr/bin/env python3


from mamoge.models.capabilities import (
    Capabilities,
    Capability,
    CapabilityBag,
    Requirement,
    Requirements,
)


def test_int_capability():

    req = Requirement("water", 10)

    cap = Capability("water", 10)
    assert req.meet(cap)
    assert cap.satisfy(req)

    cap = Capability("water", 9)
    assert req.meet(cap) == False
    assert cap.satisfy(req) == False

    cap = Capability("water", 20)
    assert req.meet(cap)
    assert cap.satisfy(req)


def test_int_capabilities():

    r_water = Requirement("water", 10)

    req = Requirements(r_water)

    cap_water = Capability("water", 10)

    cap = Capabilities(cap_water)

    assert req.meet(cap)
    assert cap.satisfy(req)

    cap_water.value = 5

    assert req.meet(cap) == False
    assert cap.satisfy(req) == False

    cap_water.value = 20

    assert req.meet(cap)
    assert cap.satisfy(req)


def test_multi_int_capabilities():

    r_water = Requirement("water", 10)
    r_temp = Requirement("temp", 50)

    req = Requirements(r_water, r_temp)

    cap_water = Capability("water", 10)

    cap = Capabilities(cap_water)

    assert req.meet(cap) == False
    assert cap.satisfy(req) == False

    cap_temp = Capability("temp", 20)
    cap += cap_temp

    assert req.meet(cap) == False
    assert cap.satisfy(req) == False

    cap_temp.value = 50
    assert req.meet(cap)
    assert cap.satisfy(req)


def test_capabilitybag_basics():

    cap = Capabilities(Capability("water", 20))

    caps = CapabilityBag(cap)

    rc = caps.remaining_capabilities()
    print(rc)
