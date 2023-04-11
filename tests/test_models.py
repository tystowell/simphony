import pytest

from simphony.models import Model, OPort, EPort
from simphony.exceptions import ModelValidationError


class TestModelDeclaration:
    def test_missing_sparams(self):
        with pytest.raises(ModelValidationError):

            class BadModel(Model):
                pass

            BadModel()

    def test_missing_onames(self):
        with pytest.raises(ModelValidationError):

            class BadModel(Model):
                def s_params(self, wl):
                    pass

            BadModel()

    def test_missing_ocount(self):
        with pytest.raises(ModelValidationError):

            class BadModel(Model):
                def s_params(self, wl):
                    pass

            BadModel()

    def test_ocount_and_onames_mismatch(self):
        with pytest.raises(ModelValidationError):

            class BadModel(Model):
                ocount = 3
                onames = ["o0", "o1"]

                def s_params(self, wl):
                    pass

            BadModel()

    def test_good_model_onames_and_ocount(self):
        class GoodModel(Model):
            ocount = 3
            onames = ["o0", "o1", "o2"]

            def s_params(self, wl):
                pass

        GoodModel()

    def test_good_model_onames(self):
        class GoodModel(Model):
            onames = ["o0", "o1", "o2"]

            def s_params(self, wl):
                pass

        GoodModel()

    def test_good_model_ocount(self):
        class GoodModel(Model):
            ocount = 3

            def s_params(self, wl):
                pass

        GoodModel()


class TestModelContextAccessibility:
    def test_model(self):
        pass


@pytest.fixture
def test_model():
    class TestModel(Model):
        onames = ["o0", "o1"]

        def s_params(self, wl):
            pass

    return TestModel()


@pytest.fixture
def test_model_with_eports():
    class TestModel(Model):
        onames = ["o0", "o1"]
        enames = ["e0", "e1"]

        def s_params(self, wl):
            pass

    return TestModel()


@pytest.fixture
def test_model_three_ports():
    class TestModel(Model):
        onames = ["o0", "o1", "o2"]
        enames = ["e0", "e1", "e2"]

        def s_params(self, wl):
            pass

    return TestModel()


@pytest.fixture
def oport():
    return OPort(name="test_port", instance=None)


@pytest.fixture
def eport():
    return EPort(name="test_port", instance=None)


class TestModelPorts:
    def test_model_str(self, test_model, test_model_with_eports):
        modelstr = test_model.__str__()
        assert "o: [o0, o1]" in modelstr
        assert "TestModel" in modelstr
        assert "e: [None]" in modelstr
        modelstr = test_model_with_eports.__str__()
        assert "o: [o0, o1]" in modelstr
        assert "TestModel" in modelstr
        assert "e: [e0, e1]" in modelstr

    def test_oport_by_name_and_index(self, test_model):
        assert test_model.o("o0") == test_model.o(0)
        assert test_model.o("o1") == test_model.o(1)

    def test_eport_by_name_and_index(self, test_model_with_eports):
        assert test_model_with_eports.e("e0") == test_model_with_eports.e(0)
        assert test_model_with_eports.e("e1") == test_model_with_eports.e(1)

    def test_next_unconnected_oport(self, test_model, oport):
        assert test_model.o(0).connected is False
        assert test_model.o(1).connected is False
        assert test_model.next_unconnected_oport() == test_model.o(0)
        test_model.o(0).connect_to(oport)
        assert test_model.next_unconnected_oport() == test_model.o(1)

    def test_next_unconnected_eport(self, test_model_with_eports, eport):
        assert test_model_with_eports.e(0).connected is False
        assert test_model_with_eports.e(1).connected is False
        assert (
            test_model_with_eports.next_unconnected_eport()
            == test_model_with_eports.e(0)
        )
        test_model_with_eports.e(0).connect_to(eport)
        assert (
            test_model_with_eports.next_unconnected_eport()
            == test_model_with_eports.e(1)
        )

    def test_next_unconnected_oport_all_taken(
        self, test_model, test_model_three_ports, oport
    ):
        test_model.o(0).connect_to(test_model_three_ports.o(0))
        test_model.o(1).connect_to(oport)
        assert test_model.next_unconnected_oport() is None

    def test_next_unconnected_eport_all_taken(
        self, test_model_with_eports, test_model_three_ports, eport
    ):
        test_model_with_eports.e(0).connect_to(test_model_three_ports.e(0))
        test_model_with_eports.e(1).connect_to(eport)
        assert test_model_with_eports.next_unconnected_eport() is None

    def test_duplicate_oport_name(self):
        pass

    def test_duplicate_eport_name(self):
        pass


class TestModelCaching:
    def test_model_instance_attributes_constant(self):
        pass

    def test_model_instance_attributes_variable(self):
        pass
