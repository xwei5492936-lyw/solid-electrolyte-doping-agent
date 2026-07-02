# PERD: Performance-aware Electrolyte Rule Discovery

PERD stands for Performance-aware Electrolyte Rule Discovery.

Chinese title: 面向电池性能的固态电解质掺杂规律发现算法

## Core Goal

Build a new algorithm that starts from a literature-mined solid-state electrolyte database and combines composition, processing, transport, interface, and battery-performance features to discover doping rules.

The key claim to test is that PERD can predict real battery performance better than traditional composition-only or conductivity-only models.

## Motivation

Most dopant recommendation workflows focus on composition descriptors or electrolyte conductivity. Those views are useful but incomplete because practical solid-state battery performance also depends on processing history, interfacial compatibility, cycling conditions, electrode pairing, stack pressure, and cell-level metrics.

PERD treats dopant rule discovery as a performance-aware learning problem rather than a single-property optimization problem.

## Feature Families

- Composition: host chemistry, dopant identity, dopant site, dopant fraction, charge compensation, ionic radius mismatch, valence mismatch.
- Processing: synthesis route, sintering temperature and time, atmosphere, milling, pellet density, post-treatment.
- Transport: room-temperature conductivity, activation energy, grain-boundary resistance, electronic conductivity, relative density.
- Interface: Li compatibility, cathode compatibility, interphase formation, coating or buffer layers, impedance growth.
- Battery performance: cell type, electrode pairing, current density, capacity retention, Coulombic efficiency, cycle life, critical current density.

## Baselines

- Composition-only model.
- Conductivity-only model.
- Composition plus conductivity model.
- PERD full feature model.

## Evaluation Targets

- Predict whether a doped electrolyte supports strong cell performance under reported testing conditions.
- Rank dopant schemes by performance-aware utility rather than conductivity alone.
- Extract interpretable rules linking dopant chemistry, processing, interface behavior, and battery outcomes.

## Initial Implementation Plan

1. Extend the literature database schema from dopant cases to cell-performance-linked dopant cases.
2. Add feature encoders for composition, process, transport, interface, and battery metrics.
3. Build baseline models for composition-only and conductivity-only prediction.
4. Build the PERD model using the full feature set.
5. Compare predictive performance and extract interpretable rules.
