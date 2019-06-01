""" The realtime report shown to the user. """
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QStandardItem, QStandardItemModel


class CellAnimator(object):
    """ State machine used ot animate cell styles. Animation is performed based
    on a frame timer. The transitions are precomputed so the main animation
    logic is fast. """
    NEW_COLOUR = QColor(180, 255, 180)
    UPDATED_COLOUR = [QColor(c, 255, c)
                      for c in [180 + (12 * c) for c in range(0, 5)]]
    RECENT_COLOUR = QColor(240, 255, 240)
    NORMAL_COLOUR = QColor(255, 255, 255)

    def __init__(self, model, row, column, row_is_new, blink_cell):
        super().__init__()
        self.column = column
        self.row = row
        self.start_frame = model.frame
        self.blink_end_frame = model.frame + 2 * len(self.UPDATED_COLOUR)
        self.remove_frame = model.frame + 10 * 60
        self.state = []
        if row_is_new:
            self.state.append('new')
        else:
            self.state.append('recent')
        if blink_cell:
            self.state.append('blink')

    def animate(self, model, frame, last_data_frame):
        """ Animate the cell style based on the frame time """
        if self.start_frame != last_data_frame:
            self.remove_frame = self.blink_end_frame
        if self.remove_frame <= frame:
            self.state.append('remove')
        if self.state:
            state = self.state.pop()
            index = model.index(self.row, self.column)
            if state == 'new':
                model.setData(index, self.NEW_COLOUR, Qt.BackgroundRole)
            elif state == 'recent':
                model.setData(index, self.RECENT_COLOUR, Qt.BackgroundRole)
            elif state == 'remove':
                model.setData(index, self.NORMAL_COLOUR, Qt.BackgroundRole)
                return True
            else:
                ttl = self.blink_end_frame - frame - len(self.UPDATED_COLOUR)
                if ttl > 0:
                    model.setData(
                        index, self.UPDATED_COLOUR[ttl - 1], Qt.BackgroundRole)
                    self.state.append(state)
                else:
                    model.setData(index, self.RECENT_COLOUR, Qt.BackgroundRole)
        return False


class Report(QStandardItemModel):
    """ The Model containing the final aggregated report. """

    def __init__(self, aggregator):
        super().__init__()
        self.aggregator = aggregator
        self.clear()

    def try_get_row_by_key(self, row_key):
        """ Return row index in report of key or None if not found"""
        if row_key and row_key in self.row_index:
            return self.row_index[row_key]

    def append_row_for_key(self, row_key, row):
        """ Append a row to the report for a given row_key or just append
        if there is no row key. """
        if row_key is not None and row_key in self.row_index:
            raise Exception(f'Row key "{row_key}" already added to index')
        new_row = self.rowCount() or 0
        qt_row = [QStandardItem(x) for x in row]
        self.appendRow(qt_row)
        self.row_index[row_key] = new_row
        for column in range(self.columnCount()):
            self.animate(CellAnimator(self, new_row, column, True, False))

    def update_in_place(self, existing_row, row):
        """ Use of setData ensures sorted views auto sort correctly. """
        qt_row = [QStandardItem(x) for x in row]
        for column in range(self.columnCount()):
            index = self.index(existing_row, column)
            old_data = self.data(index)
            new_data = None
            if column < len(row):
                new_data = row[column]
            if old_data != new_data:
                self.setData(index, new_data)
            self.animate(CellAnimator(self, existing_row,
                                      column, False, old_data != new_data))
            if column == 0:
                self.itemFromIndex(index).appendRow(qt_row)

    def animate(self, animator):
        """ Ensure there is only one animation per cell. """
        key = f'{animator.row}x{animator.column}'
        self.animated_cells[key] = animator

    def clear(self):
        """ Reset the report and empty all previous data. """
        super().clear()
        self.animated_cells = {}
        self.row_index = {}
        self.frame = 0
        self.last_data_frame = 0

    def update(self):
        """ Update the report by updating the aggregator. """
        table = self.aggregator.update(self)

        if table['rows']:
            self.last_data_frame = self.frame
        animation_complete = [k for (k, v) in self.animated_cells.items()
                              if v.animate(self, self.frame, self.last_data_frame)]
        for key in animation_complete:
            del self.animated_cells[key]
        self.frame += 1

        return table
