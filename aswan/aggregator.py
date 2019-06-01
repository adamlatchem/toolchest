""" Code to aggregate incoming tables """


class Aggregator():
    """ Takes a table stream, performs any aggregation and inserts / updates
    cells in the model. """

    def __init__(self, tabulator):
        super().__init__()
        self.tabulator = tabulator

    def update(self, report):
        """ Get next table and aggregate data into the final report """
        table = self.tabulator.update()
        rows = table['rows']
        metadata = table['metadata']
        key_column = metadata.get('key')

        row_key = None
        for row in rows:
            row = row[:125]

            if key_column:
                if len(row) < key_column:
                    raise Exception(f'Row is missing a key {row}')
                row_key = row[key_column]

            existing_row = report.try_get_row_by_key(row_key)
            if existing_row is not None:
                report.update_in_place(existing_row, row)
            else:
                report.append_row_for_key(row_key, row)

        return table
