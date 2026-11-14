from .demo import DemoBoutiqueAAdapter, DemoBoutiqueBAdapter

# In production, each adapter would call a retailer API, product feed, or
# another agreed integration. The demo adapters return deterministic data.
ADAPTERS = {
    1: DemoBoutiqueAAdapter(),
    2: DemoBoutiqueBAdapter(),
}


def get_adapter(boutique_id: int):
    return ADAPTERS.get(boutique_id)
