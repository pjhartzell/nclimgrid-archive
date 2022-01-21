from pystac.catalog import CatalogType

from stactools.nclimgrid.stac import create_collection
from stactools.nclimgrid.utils import generate_months

months = generate_months("19801", "198001")
destination = "test-collection.json"

collection = create_collection(
    "https://nclimgridwesteurope.blob.core.windows.net/nclimgrid/nclimgrid-daily",
    destination,
    "daily",
    months,
    cogify=True)

collection.update_extent_from_items()

# Normalize hrefs
stac_path = "test_collection"
collection.normalize_hrefs(stac_path)

# Save the collection
collection.save(catalog_type=CatalogType.SELF_CONTAINED)
print(f'STAC written to {stac_path}')