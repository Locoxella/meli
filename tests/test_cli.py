import subprocess
import sys
import pytest


def test_cli_help():
    res = subprocess.run([sys.executable, "-m", "melikit", "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "Herramienta CLI para Mercado Libre" in res.stdout
    assert "auth" in res.stdout
    assert "category" in res.stdout
    assert "item" in res.stdout
    assert "picture" in res.stdout
    assert "image" in res.stdout


def test_cli_item_help():
    res = subprocess.run([sys.executable, "-m", "melikit", "item", "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "list" in res.stdout
    assert "description" in res.stdout


def test_cli_picture_help():
    res = subprocess.run([sys.executable, "-m", "melikit", "picture", "--help"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "upload" in res.stdout
