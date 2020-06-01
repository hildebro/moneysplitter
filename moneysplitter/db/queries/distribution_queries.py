from ..models.purchase_distribution import PurchaseDistribution


def find(session, distribution_id):
    distribution = session \
        .query(PurchaseDistribution) \
        .filter(PurchaseDistribution.id == distribution_id) \
        .one()
    return distribution
