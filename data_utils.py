"""
data_utils.py

Utility functions for accessing molecule, clinical trial, and market data
from CSV and JSON files used in the drug repurposing project.

Files expected in ./data/:
- molecules.csv
- clinical_trials.json
- market_data.json
"""

import os
import csv
import json

# Base directory for data
BASE_DIR = os.path.join(os.path.dirname(__file__), "data")


def _load_csv(filename):
    """Helper function to load a CSV file and return a list of dicts."""
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV file not found: {path}")

    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _load_json(filename):
    """Helper function to load a JSON file and return parsed data."""
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"JSON file not found: {path}")

    with open(path, mode="r", encoding="utf-8") as f:
        return json.load(f)


def get_molecule_info(molecule_name):
    """
    Retrieve information about a molecule from molecules.csv.

    Args:
        molecule_name (str): Name of the molecule to look up.

    Returns:
        dict: A dictionary containing molecule details.

    Raises:
        ValueError: If the molecule is not found.
        FileNotFoundError: If the CSV file is missing.
    """
    molecules = _load_csv("molecules.csv")
    for row in molecules:
        if row["molecule_name"].strip().lower() == molecule_name.strip().lower():
            return row

    raise ValueError(f"Molecule '{molecule_name}' not found in molecules.csv")


def get_clinical_trials(molecule_name):
    """
    Retrieve all clinical trials for a given molecule.

    Args:
        molecule_name (str): Name of the molecule to search for.

    Returns:
        list: List of trial dicts (empty if none found).

    Raises:
        FileNotFoundError: If the JSON file is missing.
    """
    trials = _load_json("clinical_trials.json")
    result = [
        t for t in trials
        if t["molecule_name"].strip().lower() == molecule_name.strip().lower()
    ]

    return result


def get_market_data(disease_name):
    """
    Retrieve market statistics for a given disease.

    Args:
        disease_name (str): Disease name to look up.

    Returns:
        dict: Market data for the disease.

    Raises:
        ValueError: If the disease is not found.
        FileNotFoundError: If the JSON file is missing.
    """
    market_data = _load_json("market_data.json")
    for entry in market_data:
        if entry["disease_name"].strip().lower() == disease_name.strip().lower():
            return entry

    raise ValueError(f"Disease '{disease_name}' not found in market_data.json")
