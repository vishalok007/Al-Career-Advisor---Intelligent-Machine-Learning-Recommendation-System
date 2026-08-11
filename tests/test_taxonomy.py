"""Unit tests for 3-tier career taxonomy engine."""
from __future__ import annotations
import pytest
from utils.taxonomy import resolve_hierarchical_role, get_taxonomy_breadcrumbs

def test_resolve_hierarchical_role_ml():
    node = resolve_hierarchical_role("Senior Machine Learning Engineer")
    assert node["domain"] == "AI & Data Science"
    assert node["family"] == "Machine Learning Engineering"
    assert node["level"] == "Senior Level"
    assert node["onet_code"] == "15-1252.00"

def test_resolve_hierarchical_role_devops():
    node = resolve_hierarchical_role("Cloud DevOps Engineer")
    assert node["domain"] == "Cloud & DevOps"
    assert node["family"] == "Infrastructure & Cloud"
    assert node["onet_code"] == "15-1244.00"

def test_get_taxonomy_breadcrumbs():
    breadcrumbs = get_taxonomy_breadcrumbs("Data Scientist")
    assert "AI & Data Science" in breadcrumbs
    assert "Data Engineering & Analytics" in breadcrumbs
    assert "15-2051.00" in breadcrumbs
