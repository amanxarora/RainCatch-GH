# RainCatch-GH

> **Global Rainfall Extraction, Volumetric Catchment & Wind-Driven Rain (WDR) Analysis for Grasshopper and Rhino 8.**

[![Grasshopper](https://img.shields.io/badge/Platform-Grasshopper%20%7C%20Rhino%207%20%26%208-green.svg)](https://www.rhino3d.com/)
[![Python](https://img.shields.io/badge/Python-3.x%20%26%20IronPython%202.7-blue.svg)](https://www.python.org/)
[![Data Source](https://img.shields.io/badge/Data-Climate.OneBuilding%20%7C%20NASA%20POWER-orange.svg)](https://climate.onebuilding.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

---

## 🌧️ The Problem: Why RainCatch-GH Exists

1. **The Defunct Legacy Provider**: The historic Ladybug Legacy rainfall component depended entirely on `gisclimatechange.ucar.edu`, which NCAR permanently decommissioned (HTTP 404).
2. **The Modern Ladybug Tools (1.x) Gap**: In modern Ladybug Tools (LBT 1.x), liquid precipitation was omitted from the native `LB Import EPW` workflow, leaving designers without an official rainfall tool.
3. **The Rhino 8 Interoperability Crash**: Passing custom Python collections into standard IronPython Ladybug chart components in Rhino 8 triggers runtime failures (`TypeError: 'PyObject' has no len()`).

**RainCatch-GH** solves this by providing a self-contained, zero-dependency Grasshopper component that pulls verified climatology datasets, computes volumetric rainwater harvesting with material runoff physics, isolates wind-driven rain attack angles, and renders a clean architectural 2-row presentation table directly in Rhino.

---

## ⚡ Key Capabilities

* **Verified Global Climatology**: Direct download and parsing of official **WMO station statistics** via [Climate.OneBuilding.org](https://climate.onebuilding.org/) or **NASA POWER MERRA-2** satellite models without requiring API tokens.
* **Material-Specific Volumetric Harvesting**: Calculates monthly and annual rainwater volume ($L$ and $m^3$) using surface geometry and realistic runoff coefficients (calibrated for **3D-printed architectural terracotta**).
* **Wind-Driven Rain (WDR) Vectors**: Correlates precipitation events with coincident wind directions to reveal dominant façade rain attack orientations (e.g. East Mediterranean storms in Barcelona).
* **Native Vector Table Generator**: Directly generates a 2-row architectural presentation drawing in the Rhino viewport using true vector curve typography (`CreateCurves`) and colored mesh gradient cells, completely immune to annotation scaling bugs.

---

## 📐 Runoff Coefficients ($\text{C}$) Reference

RainCatch-GH incorporates surface retention physics. Default is `1.0`; connect `_runoffCoeff_` to specify:

| Material Type | Runoff Coefficient ($\text{C}$) | Design Application |
| :--- | :---: | :--- |
| **Glazed Ceramic Tile / Glass / Metal** | `0.85 – 0.92` | Impermeable roofs, curtain walls |
| **Sealed / Hydrophobic Terracotta** | `0.80 – 0.85` | Silane/siloxane treated façade panels |
| **3D-Printed Unglazed Terracotta (Bisque)** | `0.70 – 0.75` | Porous ceramic façades (8–14% absorption) |
| **Heavy Fluted / Corrugated 3D-Clay** | `0.60 – 0.70` | Deep horizontal layer-line water retention |
| **Extensive Green Roof / Permeable Substrate**| `0.30 – 0.50` | Vegetated roofs, retention substrates |

---

## 🔌 Component Interface

### Inputs
| Pin | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `download` | *Boolean* | `False` | Toggle to `True` to download or parse data. |
| `_locationName` | *String* | `"Barcelona"` | City name OR direct `.zip`/`.stat` link from Climate.OneBuilding.org. |
| `_latitude` | *Float* | — | Site latitude in decimal degrees. |
| `_longitude` | *Float* | — | Site longitude in decimal degrees. |
| `_surfaceArea_m2_` | *Float / Brep* | `1.0` | Catchment area in $m^2$ or Rhino surface/mesh geometry. |
| `_runoffCoeff_` | *Float* | `1.0` | Surface runoff coefficient (`0.0`–`1.0`). |
| `_base_pt_` | *Point3d* | `(0, 0, 0)` | Optional origin point for the 2-row table. |
| `legend_par_` | *Object / Float* | `1.5` | `LB Legend Parameters` or Number Slider for text scale. |

### Outputs
| Pin | Type | Description |
| :--- | :---: | :--- |
| `readMe!` | *String* | Execution and cache status log. |
| `Header` | *List[String]* | Metadata summary (location, annual totals, source). |
| `Rainfall_mm` | *List[Float]* | 12 monthly rainfall totals in millimeters. |
| `Rainfall_inch` | *List[Float]* | 12 monthly rainfall totals in inches. |
| `RainVolume_L` | *List[Float]* | 12 monthly rainwater harvest volumes in Liters. |
| `RainVolume_m` | *List[Float]* | 12 monthly rainwater harvest volumes in $m^3$. |
| `AnnualRainfall_mm` | *Float* | Total annual precipitation in millimeters. |
| `AnnualVolume_m3` | *Float* | Total annual water harvested in cubic meters. |
| `DominantRainDirection`| *String* | Prevailing wind-driven rain orientation (e.g. `E`). |
| `BarChart_mesh` | *List[Mesh]* | Colored 2D mesh swatches showing precipitation intensity. |
| `BarChart_labels` | *List[Curve]* | Pure vector text curves for month headers and grid lines. |

---

## 🚀 Installation

### Option 1: UserObject Drag & Drop (Recommended)
1. Download `userObjects/Download rainfall data.ghuser`.
2. In Grasshopper, open **File $\rightarrow$ Special Folders $\rightarrow$ User Object Folder**.
3. Copy the `.ghuser` file into that folder.
4. Restart Grasshopper or press `F5`. The component will appear under **Ladybug $\rightarrow$ Extra**.

### Option 2: Script Component Copy
1. Place a standard **Python 3** or **IronPython 2** component in Grasshopper.
2. Copy the code from `src/DownloadRainfall.py` into the editor.
3. Configure the inputs and outputs as listed above.

---

## 📚 Acknowledgments & Data Sources
* [Climate.OneBuilding.org](https://climate.onebuilding.org/) — Maintained by Drury Crawley and Linda Lawrie for open-source building simulation climatology.
* [NASA POWER Project](https://power.larc.nasa.gov/) — Satellite and MERRA-2 meteorological data products from NASA Langley Research Center.
* [Ladybug Tools](https://www.ladybug.tools/) — Environmental analysis ecosystem started by Mostapha Sadeghipour Roudsari and Chris Mackey.

---

## 📄 License
This project is licensed under the [GNU General Public License v3.0 (GPL-3.0)](LICENSE).
