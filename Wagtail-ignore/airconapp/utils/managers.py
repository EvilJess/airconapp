import operator

from django.db.models.query import QuerySet
from django.db.models import Q


def inits(seq):
    """
    http://hackage.haskell.org/package/base-4.7.0.1/docs/Data-List.html#v:inits
    """
    acc = []
    for item in seq:
        acc.append(item)
        yield acc[:]


def split_order(order, reversed):
    """
    Splits a QuerySet order_by parameter in to its component parts
    - field name and if it is ascending -
    inverted if `reversed == True`

    >>> split_order('date', False)
    ('date', True)

    >>> split_order('-date', False)
    ('date', False)

    >>> split_order('date', True)
    ('date', False)

    >>> split_order('-date', True)
    ('date', True)
    """
    if order[0] == '-':
        field = order[1:]
        asc = reversed
    else:
        field = order
        asc = not reversed
    return (field, asc)


order_comparisons = {
    True: 'gt',
    False: 'lt',
}


class SiblingsInOrderQuerySet(QuerySet):

    def next_in_order(self, reference):
        """
        Get the next item in a QuerySet, in relation to the reference object
        passed in.
        """
        is_reversed = not self.query.standard_ordering
        order_by = [split_order(order, is_reversed)
                    for order in self.query.order_by]

        q = Q()
        for order_items in inits(order_by):
            (final_field, final_asc) = order_items.pop()
            q_eq = reduce(operator.and_, (
                Q(**{field: getattr(reference, field)})
                for (field, _) in order_items), Q())

            ord_field = '{0}__{1}'.format(
                final_field, order_comparisons[final_asc])
            q_ord = Q(**{ord_field: getattr(reference, final_field)})

            q = q | (q_eq & q_ord)

        return self.filter(q).first()

    def previous_in_order(self, reference):
        """
        Get the previous item in a QuerySet, in relation to the reference
        object passed in.
        """
        return self.reverse().next_in_order(reference)
