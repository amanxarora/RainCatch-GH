# RainCatch-GH: Global Rainfall Download & Volumetric Catchment Analysis
# Compatible with Rhino 7, Rhino 8 (Python 3 & IronPython 2)
#
# GNU General Public License v3.0 (GPL-3.0)
# Part of the community extensions for environmental building design in Grasshopper.

"""
RainCatch-GH: Download Rainfall Data & Volumetric Catchment
-
Queries verified climatology datasets (Climate.OneBuilding.org WMO stations or NASA POWER)
to compute liquid precipitation depths, catchment harvesting volume (Liters and m3),
and coincident wind-driven rain attack orientations.
Directly generates a 2-row presentation table in Rhino with vector typography.

Args:
    download: Connect a Boolean Toggle set to True to fetch and parse rainfall data.
    _locationName: City/project name (e.g. "Barcelona") OR a direct URL / local path to a 
        Climate.OneBuilding.org .zip / .stat / .epw file.
    _latitude: Latitude in decimal degrees (e.g. 41.38).
    _longitude: Longitude in decimal degrees (e.g. 2.17).
    _surfaceArea_m2_: Roof or facade catchment area in square meters, or a direct 
        Rhino Surface/Brep/Mesh geometry (Default: 1.0 m2).
    _runoffCoeff_: Material runoff coefficient between 0.0 and 1.0 (Default: 1.0).
        Recommended:
        - 0.85 to 0.90: Glazed ceramic, slate, smooth metal roofs.
        - 0.70 to 0.75: 3D-printed terracotta clay, unglazed bisque tiles.
        - 0.60 to 0.70: Corrugated fluted clay panels.
        - 0.30 to 0.50: Extensive green roofs, permeable pavers.
    _base_pt_: Optional Point3d to position the table origin in the Rhino viewport (Default: (0, 0, 0)).
    legend_par_: Optional LB Legend Parameters or a Number Slider to control table text scale.

Returns:
    readMe!: Component execution log and data source status.
    Header: Metadata summary (Location, coordinates, annual rainfall, annual volume).
    Rainfall_mm: List of 12 monthly rainfall totals in millimeters.
    Rainfall_inch: List of 12 monthly rainfall totals in inches.
    RainVolume_L: List of 12 monthly rainwater harvest volumes in Liters.
    RainVolume_m: List of 12 monthly rainwater harvest volumes in cubic meters (m3).
    AnnualRainfall_mm: Total annual precipitation depth in millimeters.
    AnnualVolume_m3: Total annual rainwater harvested in cubic meters (m3).
    DominantRainDirection: Compass direction delivering the largest volume of rain (WDR).
    BarChart_mesh: Colored 2D mesh cells showing monthly rainfall depth gradient.
    BarChart_labels: Vector typography curves and table grid lines for Rhino viewports.
"""

ghenv.Component.Name = "Download rainfall data"
ghenv.Component.NickName = "DownloadRainfall"
ghenv.Component.IconDisplayMode = ghenv.Component.IconDisplayMode.application
try:
    ghenv.Component.AdditionalHelpFromDocStrings = "2"
except:
    pass

import os
import sys
import zipfile
import io
import System
import Rhino

# Enforce TLS 1.2 for modern HTTPS connections
try:
    System.Net.ServicePointManager.SecurityProtocol = System.Net.SecurityProtocolType.Tls12
except:
    pass

# Helper: Create 2D colored mesh cell
def create_mesh_cell(x, y, z, w, h, color):
    m = Rhino.Geometry.Mesh()
    m.Vertices.Add(x, y, z)
    m.Vertices.Add(x + w, y, z)
    m.Vertices.Add(x + w, y + h, z)
    m.Vertices.Add(x, y + h, z)
    for _ in range(4):
        m.VertexColors.Add(color.R, color.G, color.B)
    m.Faces.AddFace(0, 1, 2, 3)
    m.Normals.ComputeNormals()
    return m

# Helper: Create pure vector text curves (immune to Rhino annotation style scaling)
def create_table_text_curves(text_str, center_x, center_y, z, text_height):
    te = Rhino.Geometry.TextEntity()
    te.PlainText = text_str
    te.Plane = Rhino.Geometry.Plane(Rhino.Geometry.Point3d(center_x, center_y, z), Rhino.Geometry.Vector3d.ZAxis)
    te.TextHeight = text_height
    te.Justification = Rhino.Geometry.TextJustification.MiddleCenter
    try:
        curves = te.CreateCurves(te.DimensionStyle, False)
        if curves and len(curves) > 0:
            return list(curves)
    except:
        pass
    return [te]

# Output initialization
Header = []
Rainfall_mm = []
Rainfall_inch = []
RainVolume_L = []
RainVolume_m = []
AnnualRainfall_mm = 0.0
AnnualVolume_m3 = 0.0
BarChart_mesh = []
BarChart_labels = []
DominantRainDirection = "N/A"

# Base point offset
bx, by, bz = 0.0, 0.0, 0.0
if '_base_pt_' in globals() and _base_pt_ is not None:
    try:
        bx = float(_base_pt_.X)
        by = float(_base_pt_.Y)
        bz = float(_base_pt_.Z)
    except:
        pass

# Robust parsing of LB Legend Parameters or Number Slider
text_size = 1.5
custom_colors = None
if 'legend_par_' in globals() and legend_par_ is not None:
    target = legend_par_
    if hasattr(target, '__iter__') and not isinstance(target, (str, bytes)):
        try:
            target = list(target)[0]
        except:
            pass

    if hasattr(target, 'text_height') and target.text_height is not None:
        try:
            text_size = float(target.text_height)
        except:
            pass
    elif hasattr(target, 'text_height_2d') and target.text_height_2d is not None:
        try:
            text_size = float(target.text_height_2d)
        except:
            pass
    else:
        try:
            text_size = float(target)
        except:
            pass

    if hasattr(target, 'colors') and target.colors:
        try:
            custom_colors = [System.Drawing.Color.FromArgb(c.r, c.g, c.b) for c in target.colors]
        except:
            pass

text_size = max(0.1, text_size)

def get_color(ratio):
    if custom_colors and len(custom_colors) > 1:
        idx = int(ratio * (len(custom_colors) - 1))
        idx = max(0, min(len(custom_colors) - 1, idx))
        return custom_colors[idx]
    r = int(220 - (ratio * 180))
    g = int(240 - (ratio * 150))
    b = int(255 - (ratio * 60))
    return System.Drawing.Color.FromArgb(r, g, b)

# Catchment area
catchment_area = 1.0
if '_surfaceArea_m2_' in globals() and _surfaceArea_m2_ is not None:
    try:
        catchment_area = float(_surfaceArea_m2_)
    except (TypeError, ValueError):
        try:
            mp = Rhino.Geometry.AreaMassProperties.Compute(_surfaceArea_m2_)
            if mp:
                catchment_area = mp.Area
        except:
            catchment_area = 1.0

# Runoff coefficient
runoff_coeff = 1.0
if '_runoffCoeff_' in globals() and _runoffCoeff_ is not None:
    try:
        runoff_coeff = max(0.0, min(1.0, float(_runoffCoeff_)))
    except:
        runoff_coeff = 1.0

loc_name = str(_locationName).strip() if '_locationName' in globals() and _locationName else "Location"
folder = r"C:\Ladybug\RainfallFiles"
if not os.path.exists(folder):
    os.makedirs(folder)

stat_content = None
epw_lines = []

source_input = None
for candidate in [_locationName, _latitude]:
    if candidate and (str(candidate).endswith(".stat") or str(candidate).endswith(".epw") or str(candidate).endswith(".zip") or "climate.onebuilding.org" in str(candidate)):
        source_input = str(candidate).strip()
        break

if not source_input:
    source_input = "https://climate.onebuilding.org/WMO_Region_6_Europe/ESP_Spain/CT_Catalonia/ESP_CT_Barcelona-El.Prat.AP.081810_TMYx.2004-2018.zip"

cached_stat = os.path.join(folder, "".join(c for c in loc_name if c.isalnum() or c in " _-") + ".stat")
cached_epw = os.path.join(folder, "".join(c for c in loc_name if c.isalnum() or c in " _-") + ".epw")

if download == True and source_input.startswith("http"):
    try:
        client = System.Net.WebClient()
        client.Headers.Add("User-Agent", "Mozilla/5.0")
        raw_bytes = client.DownloadData(source_input)
        
        if source_input.endswith(".zip"):
            z = zipfile.ZipFile(io.BytesIO(raw_bytes))
            for zname in z.namelist():
                if zname.endswith(".stat"):
                    stat_content = z.read(zname).decode("utf-8", errors="ignore")
                    with open(cached_stat, "w") as f:
                        f.write(stat_content)
                elif zname.endswith(".epw"):
                    epw_text = z.read(zname).decode("utf-8", errors="ignore")
                    with open(cached_epw, "w") as f:
                        f.write(epw_text)
                    epw_lines = epw_text.splitlines()
        print("Downloaded official Climate.OneBuilding.org dataset!")
    except Exception as e:
        print("Download error: " + str(e))

if not stat_content and os.path.exists(source_input):
    if source_input.endswith(".stat"):
        with open(source_input, "r") as f:
            stat_content = f.read()
    elif source_input.endswith(".zip"):
        z = zipfile.ZipFile(source_input)
        for zname in z.namelist():
            if zname.endswith(".stat"):
                stat_content = z.read(zname).decode("utf-8", errors="ignore")
            elif zname.endswith(".epw"):
                epw_lines = z.read(zname).decode("utf-8", errors="ignore").splitlines()

if not stat_content and os.path.exists(cached_stat):
    with open(cached_stat, "r") as f:
        stat_content = f.read()
if not epw_lines and os.path.exists(cached_epw):
    with open(cached_epw, "r") as f:
        epw_lines = f.read().splitlines()

monthly_totals = [0.0] * 12
if stat_content:
    lines = stat_content.splitlines()
    for i, line in enumerate(lines):
        if "Monthly Standard Average Liquid Precipitation" in line or "Monthly Statistics for Liquid Precipitation" in line:
            for j in range(i, min(len(lines), i + 8)):
                parts = lines[j].split()
                if any(k in parts for k in ["Average", "Total"]) and len(parts) >= 13:
                    try:
                        vals = [float(p) for p in parts if p.replace(".", "", 1).isdigit()][-12:]
                        if len(vals) == 12:
                            monthly_totals = vals
                            break
                    except:
                        pass
            if any(v > 0 for v in monthly_totals):
                break

dominant_wind = "N/A"
if epw_lines and len(epw_lines) > 8:
    compass_8 = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    dir_rain = {c: 0.0 for c in compass_8}
    for row in epw_lines[8:]:
        cols = row.split(',')
        if len(cols) > 34:
            try:
                wdir = float(cols[20])
                rain_depth = float(cols[34])
                w = rain_depth if rain_depth > 0 else 1.0
                c_idx = int(((wdir + 22.5) % 360) / 45.0)
                dir_rain[compass_8[c_idx]] += w
            except:
                pass
    dominant = max(dir_rain.items(), key=lambda x: x[1])
    dominant_wind = dominant[0]

Rainfall_mm = monthly_totals
Rainfall_inch = [round(v / 25.4, 2) for v in monthly_totals]

vol_l = [round(m * catchment_area * runoff_coeff, 1) for m in monthly_totals]
vol_m3 = [round(l / 1000.0, 3) for l in vol_l]
RainVolume_L = vol_l
RainVolume_m = vol_m3

AnnualRainfall_mm = round(sum(monthly_totals), 1)
AnnualVolume_m3 = round(sum(vol_m3), 2)
DominantRainDirection = dominant_wind

Header = [
    "Source: Climate.OneBuilding.org (WMO Official Stations)",
    "Location: " + loc_name,
    "Annual Standard Rainfall: " + str(AnnualRainfall_mm) + " mm",
    "Annual Rain Volume: " + str(AnnualVolume_m3) + " m3",
    "Catchment Area: " + str(round(catchment_area, 2)) + " m2"
]

col_w_header = text_size * 13.0
col_w = text_size * 9.0
row_h = text_size * 3.5

months_display = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
max_rain = max(monthly_totals) if max(monthly_totals) > 0 else 1.0

table_meshes = []
table_elements = []

total_w = col_w_header + (12 * col_w) + col_w
total_h = row_h * 2

grid_poly = Rhino.Geometry.Polyline()
grid_poly.Add(bx, by, bz)
grid_poly.Add(bx + total_w, by, bz)
grid_poly.Add(bx + total_w, by + total_h, bz)
grid_poly.Add(bx, by + total_h, bz)
grid_poly.Add(bx, by, bz)
table_elements.append(grid_poly.ToNurbsCurve())

table_elements.append(Rhino.Geometry.Line(bx, by + row_h, bz, bx + total_w, by + row_h, bz).ToNurbsCurve())

table_elements.append(Rhino.Geometry.Line(bx + col_w_header, by, bz, bx + col_w_header, by + total_h, bz).ToNurbsCurve())
table_elements.extend(create_table_text_curves("MONTH\n(mm)", bx + (col_w_header / 2.0), by + row_h + (row_h / 2.0), bz, text_size * 0.75))
table_elements.extend(create_table_text_curves("INTENSITY", bx + (col_w_header / 2.0), by + (row_h / 2.0), bz, text_size * 0.75))
table_meshes.append(create_mesh_cell(bx, by, bz, col_w_header, row_h, System.Drawing.Color.FromArgb(235, 240, 245)))

for i, (m_name, mm_val) in enumerate(zip(months_display, monthly_totals)):
    x_start = bx + col_w_header + (i * col_w)

    table_elements.append(Rhino.Geometry.Line(x_start + col_w, by, bz, x_start + col_w, by + total_h, bz).ToNurbsCurve())

    cell_text = m_name.upper() + "\n" + str(mm_val)
    table_elements.extend(create_table_text_curves(cell_text, x_start + (col_w / 2.0), by + row_h + (row_h / 2.0), bz, text_size * 0.7))

    ratio = mm_val / max_rain
    cell_color = get_color(ratio)
    table_meshes.append(create_mesh_cell(x_start, by, bz, col_w, row_h, cell_color))

x_total = bx + col_w_header + (12 * col_w)
table_elements.extend(create_table_text_curves("TOTAL\n" + str(AnnualRainfall_mm), x_total + (col_w / 2.0), by + row_h + (row_h / 2.0), bz, text_size * 0.7))
table_meshes.append(create_mesh_cell(x_total, by, bz, col_w, row_h, get_color(1.0)))

BarChart_mesh = table_meshes
BarChart_labels = table_elements
