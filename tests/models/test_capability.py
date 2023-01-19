import pytest


from mamoge.models.capabilities import (
    Capabilities,
    Capability,
    CapabilityBag,
    Requirement,
    Requirements,
)


class TestCapability:
    @classmethod
    def setup_class(cls):
        cls.req = Requirement("water", 10)
        cls.cap = Capability("water", 10)

    def test_int_capability_sufficient_water(self):

        assert self.req.meet(self.cap)
        assert self.cap.satisfy(self.req)

    def test_int_capability_insufficient_water(self):

        cap = Capability("water", 9)
        assert self.req.meet(cap) is False
        assert cap.satisfy(self.req) is False

    def test_int_capability_more_than_sufficient_water(self):
        cap = Capability("water", 20)
        assert self.req.meet(cap)
        assert cap.satisfy(self.req)


class TestCapabilities:
    @classmethod
    def setup_class(cls):
        cls.r_water = Requirement("water", 10)
        cls.r_energy = Requirement("energy", 15)
        cls.cap_water = Capability("water", 10)
        cls.cap_energy = Capability("energy", 15)

        cls.req_single = Requirements(cls.r_water)
        cls.req_multiple = Requirements(cls.r_water, cls.r_energy)
        cls.cap_single = Capabilities(cls.cap_water)
        cls.cap_multiple = Capabilities(cls.cap_water, cls.cap_energy)

    def test_int_capabilities_single(self):

        assert self.req_single.meet(self.cap_single)
        assert self.cap_single.satisfy(self.req_single)

    def test_int_capabilities_multiple(self):

        assert self.req_multiple.meet(self.cap_multiple)
        assert self.cap_multiple.satisfy(self.req_multiple)

        assert self.req_multiple.meet(self.cap_single) is False

        # "I have multiple capabilities (can do more) and the requirements are less"
        assert self.cap_multiple.satisfy(self.req_single)

        # "I can do just one thing while two are required"
        assert self.cap_single.satisfy(self.req_multiple) is False

        # "I have ONE JOB but can do multiple things"
        assert self.req_single.meet(self.cap_multiple)

    def test_int_capabilities_multiple_capabilities_not_fitting(self):
        cap_energy = Capability("energy", 15)
        cap_carry = Capability("carry", 20)
        cap_multiple = Capabilities(cap_energy, cap_carry)

        assert self.req_multiple.meet(cap_multiple) is False

    def test_int_capabilities_single_diverging_capability(self):
        self.cap_water.value = 5

        assert self.r_water.meet(self.cap_water) is False
        assert self.cap_water.satisfy(self.r_water) is False

        self.cap_water.value = 20

        assert self.r_water.meet(self.cap_water)
        assert self.cap_water.satisfy(self.r_water)


def test_multi_int_capabilities():

    r_water = Requirement("water", 10)
    r_temp = Requirement("temp", 50)

    req = Requirements(r_water, r_temp)

    cap_water = Capability("water", 10)

    cap = Capabilities(cap_water)

    assert req.meet(cap) is False
    assert cap.satisfy(req) is False

    cap_temp = Capability("temp", 20)
    cap += cap_temp

    assert req.meet(cap) is False
    assert cap.satisfy(req) is False

    cap_temp.value = 50
    assert req.meet(cap)
    assert cap.satisfy(req)


def test_capabilitybag_basics():

    cap = Capabilities(Capability("water", 20))

    caps = CapabilityBag(cap)

    rc = caps.remaining_capabilities()
    print(rc)
