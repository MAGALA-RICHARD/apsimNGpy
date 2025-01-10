"""This module is for organizing the soil path parameters"""
from dataclasses import dataclass


def _physical(node):
    return f'Physical.{node}'


def _organic(node):
    return f'Organic.{node}'


def _chemical(node):
    return f'Chemical.{node}'


@dataclass
class Soil:
    @dataclass
    class Physical:
        BD = _physical('BD')
        DUL = _physical('DUL')

    @dataclass
    class Organic:
        Carbon = _organic('Carbon')
        FBiom = _organic('FBiom')

    @dataclass
    class Chemical:
        NH3 = _chemical('NH3')


