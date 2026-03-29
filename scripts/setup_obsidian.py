"""
setup_obsidian.py — Configure this repo as an Obsidian vault.

Creates .obsidian/ settings with:
- Graph View: sector-based color coding, high repel force for 1,735 nodes
- App settings: native [[wikilink]] format preserved
- Gitignore: workspace.json excluded (personal layout)

Usage:
  python scripts/setup_obsidian.py
"""

import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBSIDIAN_DIR = os.path.join(PROJECT_ROOT, ".obsidian")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "Pilot_Reports")
GITIGNORE_PATH = os.path.join(PROJECT_ROOT, ".gitignore")

# Sector groupings → color (RGB decimal)
# Calculated from: int("RRGGBB", 16)
SECTOR_COLOR_GROUPS = [
    {
        "name": "科技半導體",
        "color_hex": "#3498db",  # blue
        "sectors": [
            "Semiconductors",
            "Semiconductor Equipment & Materials",
            "Electronic Components",
            "Computer Hardware",
            "Communication Equipment",
            "Consumer Electronics",
            "Software - Application",
            "Software - Infrastructure",
            "Information Technology Services",
            "Electronics & Computer Distribution",
            "Scientific & Technical Instruments",
            "Internet Content & Information",
            "Internet Retail",
        ],
    },
    {
        "name": "工業製造",
        "color_hex": "#f39c12",  # orange
        "sectors": [
            "Specialty Industrial Machinery",
            "Metal Fabrication",
            "Electrical Equipment & Parts",
            "Building Products & Equipment",
            "Tools & Accessories",
            "Aerospace & Defense",
            "Engineering & Construction",
            "Auto Parts",
            "Industrial Distribution",
            "Pollution & Treatment Controls",
            "Building Materials",
            "Conglomerates",
        ],
    },
    {
        "name": "金融保險",
        "color_hex": "#2ecc71",  # green
        "sectors": [
            "Banks",
            "Banks - Regional",
            "Insurance - Life",
            "Insurance - Property & Casualty",
            "Insurance - Diversified",
            "Insurance - Reinsurance",
            "Insurance Brokers",
            "Capital Markets",
            "Credit Services",
            "Financial Conglomerates",
            "Asset Management",
        ],
    },
    {
        "name": "材料化工",
        "color_hex": "#e67e22",  # dark orange
        "sectors": [
            "Chemicals",
            "Specialty Chemicals",
            "Steel",
            "Aluminum",
            "Copper",
            "Other Industrial Metals & Mining",
            "Thermal Coal",
        ],
    },
    {
        "name": "醫療生技",
        "color_hex": "#1abc9c",  # teal
        "sectors": [
            "Biotech - Therapeutics",
            "Biotechnology",
            "Drug Manufacturers - Specialty & Generic",
            "Medical Devices",
        ],
    },
    {
        "name": "能源電力",
        "color_hex": "#9b59b6",  # purple
        "sectors": [
            "Solar",
            "Utilities - Renewable",
            "Utilities - Regulated Electric",
            "Utilities - Regulated Gas",
            "Utilities - Regulated Water",
            "Oil & Gas Equipment & Services",
            "Oil & Gas Refining & Marketing",
        ],
    },
    {
        "name": "消費零售",
        "color_hex": "#e74c3c",  # red
        "sectors": [
            "Apparel Manufacturing",
            "Apparel Retail",
            "Footwear & Accessories",
            "Textile Manufacturing",
            "Household & Personal Products",
            "Packaging & Containers",
            "Furnishings, Fixtures & Appliances",
            "Specialty Retail",
            "Department Stores",
            "Food Distribution",
            "Packaged Foods",
            "Beverages - Non-Alcoholic",
            "Farm Products",
            "Grocery Stores",
            "Leisure",
        ],
    },
    {
        "name": "交通運輸",
        "color_hex": "#7f8c8d",  # gray
        "sectors": [
            "Integrated Freight & Logistics",
            "Marine Shipping",
            "Airlines",
            "Railroads",
            "Trucking",
            "Auto Manufacturers",
            "Auto & Truck Dealerships",
        ],
    },
    {
        "name": "不動產服務",
        "color_hex": "#795548",  # brown
        "sectors": [
            "Real Estate - Development",
            "Real Estate - Diversified",
            "Real Estate Services",
        ],
    },
    {
        "name": "媒體服務",
        "color_hex": "#546e7a",  # blue-gray
        "sectors": [
            "Broadcasting",
            "Entertainment",
            "Publishing",
            "Electronic Gaming & Multimedia",
            "Personal Services",
            "Education & Training Services",
            "Advertising Agencies",
            "Consulting Services",
            "Specialty Business Services",
            "Staffing & Employment Services",
            "Gambling",
            "Lodging",
            "Telecom Services",
            "Recreational Vehicles",
            "Lumber & Wood Production",
            "Waste Management",
            "Home Improvement Retail",
            "Security & Protection Services",
            "Business Equipment & Supplies",
            "Agricultural Inputs",
        ],
    },
]


def hex_to_decimal(hex_color):
    """Convert #RRGGBB to decimal integer."""
    return int(hex_color.lstrip("#"), 16)


def get_available_sectors():
    """Get list of sector folders that actually exist."""
    if not os.path.isdir(REPORTS_DIR):
        return set()
    return set(os.listdir(REPORTS_DIR))


def build_graph_json(available_sectors):
    """Build Obsidian graph.json with sector color groups."""
    color_groups = []
    for group in SECTOR_COLOR_GROUPS:
        # Only include sectors that exist in the repo
        matching = [s for s in group["sectors"] if s in available_sectors]
        if not matching:
            continue
        # Build query: path:"Pilot_Reports/Sector1" OR path:"Pilot_Reports/Sector2"
        parts = [f'path:"Pilot_Reports/{s}"' for s in matching]
        query = " OR ".join(parts)
        color_groups.append({
            "query": query,
            "color": {
                "a": 1,
                "rgb": hex_to_decimal(group["color_hex"]),
            },
        })

    return {
        "collapse-filter": True,
        "search": "",
        "showTags": False,
        "showAttachments": False,
        "hideUnresolved": False,
        "showOrphans": False,
        "collapse-color-groups": False,
        "colorGroups": color_groups,
        "collapse-display": True,
        "showArrow": False,
        "textFadeMultiplier": 0,
        "nodeSizeMultiplier": 1.3,
        "lineSizeMultiplier": 1.0,
        "collapse-forces": False,
        "centerStrength": 0.518,
        "repelStrength": 14,
        "linkStrength": 0.7,
        "linkDistance": 40,
        "scale": 0.5,
        "close": False,
    }


def update_gitignore():
    """Add Obsidian workspace.json and other generated paths to .gitignore."""
    additions = [
        "# Obsidian personal workspace (不 commit 個人佈局)",
        ".obsidian/workspace.json",
        ".obsidian/workspace-mobile.json",
        "# 操作日誌",
        "logs/",
        "# 靜態網站輸出",
        "site/",
    ]

    existing = ""
    if os.path.exists(GITIGNORE_PATH):
        with open(GITIGNORE_PATH, "r", encoding="utf-8") as f:
            existing = f.read()

    new_lines = []
    for line in additions:
        if line not in existing:
            new_lines.append(line)

    if new_lines:
        with open(GITIGNORE_PATH, "a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(new_lines) + "\n")
        print(f"  .gitignore: added {len(new_lines)} entries")
    else:
        print("  .gitignore: already up to date")


def main():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("Setting up Obsidian vault configuration...")
    os.makedirs(OBSIDIAN_DIR, exist_ok=True)

    # 1. app.json — already exists, just confirm
    app_json_path = os.path.join(OBSIDIAN_DIR, "app.json")
    if os.path.exists(app_json_path):
        print("  app.json: exists")
    else:
        print("  app.json: not found — please run from repo root")

    # 2. graph.json — color groups by sector
    available_sectors = get_available_sectors()
    print(f"  Detected {len(available_sectors)} sector folders")
    graph_config = build_graph_json(available_sectors)
    graph_json_path = os.path.join(OBSIDIAN_DIR, "graph.json")
    with open(graph_json_path, "w", encoding="utf-8") as f:
        json.dump(graph_config, f, ensure_ascii=False, indent=2)
    print(f"  graph.json: written ({len(graph_config['colorGroups'])} color groups)")

    # 3. Update .gitignore
    update_gitignore()

    print("\nDone. Open the vault in Obsidian:")
    print(f"  obsidian://open?vault=My-TW-Coverage")
    print(f"  Or: File → Open Vault → {PROJECT_ROOT}")
    print("\nRecommended next steps in Obsidian:")
    print("  1. Ctrl+G → Graph View (check color coding)")
    print("  2. Ctrl+O → Quick Switcher (search any ticker)")
    print("  3. See docs/obsidian-guide.md for full usage guide")


if __name__ == "__main__":
    main()
