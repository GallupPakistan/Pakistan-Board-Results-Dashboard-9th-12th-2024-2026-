"""config/settings.py - identity + constants for the combined dashboard."""
APP_NAME = "BISE Results"
APP_SUBTITLE = "9th-12th Combined Dashboard"
APP_ICON = "school"
PAGE_ICON = "🎓"
LAST_UPDATED = "08 Oct 2026"

CLASSES = ["9th", "10th", "11th", "12th"]
YEARS = [2024, 2025, 2026]
DEFAULT_CLASS = "12th"      # every page opens on 12th class ...
DEFAULT_YEAR = 2026         # ... and 2026
CLASS_COLORS = {"9th": "#3B82F6", "10th": "#C9A84C", "11th": "#22C55E", "12th": "#A855F7"}

PROVINCE_BOARD_MAP = {
    "Federal": ["FBISE"],
    "Punjab": ["Lahore", "Rawalpindi", "Gujranwala", "Faisalabad", "Sargodha", "Sahiwal", "Bahawalpur", "DG Khan"],
    "Khyber Pakhtunkhwa": ["Peshawar", "Swat", "Abbottabad", "Mardan", "Kohat", "Bannu"],
}
BOARD_PROVINCE = {b: p for p, bs in PROVINCE_BOARD_MAP.items() for b in bs}
