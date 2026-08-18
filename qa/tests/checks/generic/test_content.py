"""Tests for generic content checks."""

import pytest

from qa.checks.base import EmptyFieldError, MissingDataError
from qa.checks.models import QaDataRegistry, Metadata, OnFailurePolicy
from qa.checks.generic.content import IsEnglish


def inputs(abstract: str | None) -> QaDataRegistry:
    return QaDataRegistry(metadata=Metadata(abstract=abstract))


def make(cls, **kwargs):
    return cls(on_failure_policy=OnFailurePolicy.WARN, data="metadata", field="abstract", **kwargs)


class TestIsEnglish:
    check = make(IsEnglish)

    def test_missing_data_raises(self):
        with pytest.raises(MissingDataError):
            self.check.run(QaDataRegistry())

    def test_none_field_raises(self):
        with pytest.raises(EmptyFieldError):
            self.check.run(inputs(None))

    def test_empty_field_raises(self):
        with pytest.raises(EmptyFieldError):
            self.check.run(inputs(""))

    def test_too_short_passes(self):
        assert self.check.run(inputs("1234")).passed

    def test_short_passes(self):
        assert self.check.run(inputs("This is a test.")).passed

    def test_fail_on_french(self):
        french_text = "Nous analysons le routage UAS réfléchi pour des files d'attente hétérogènes à serveurs multiples, avec des paramètres fixes et sous charge sous-critique. Le modèle déterministe utilisé est une équation différentielle ordinaire (EDO) réfléchie sur l'orthant non négatif, et non l'équation de dérive non contrainte."
        result = self.check.run(inputs(french_text))
        assert not result.passed

    def test_fail_on_russian(self):
        russian_text = "Мы анализируем маршрутизацию с использованием отраженного БПЛА для гетерогенных многосерверных очередей при фиксированных параметрах в условиях субкритической нагрузки. Детерминированным заменителем является отраженное ОДУ на неотрицательном ортанте, а не уравнение дрейфа без ограничений. Это отраженное ОДУ имеет единственное граничное равновесие, характеризуемое скалярным уравнением согласованности и представлением выпуклого потенциала; все траектории сходятся к нему."
        result = self.check.run(inputs(russian_text))
        assert not result.passed

    def test_fail_on_chinese(self):
        chinese_text = "我們在亞臨界負載及固定參數條件下，分析了異質多伺服器排隊系統中的「反射式 UAS」（Reflected UAS）路由策略。此系統的確定性替代模型並非無約束漂移方程，而是定義在非負象限上的反射型常微分方程（ODE）。"
        result = self.check.run(inputs(chinese_text))
        assert not result.passed
