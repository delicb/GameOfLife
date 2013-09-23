__author__ = "Bojan Delic <bojan@delic.in.rs>"
__mail__ = "bojan@delic.in.rs"

try:
    from PyQt4 import QtGui, QtCore
    from PyQt4.QtCore import Qt
except ImportError:
    from PySide import QtGui, QtCore
    from PySide.QtCore import Qt


class GOLMatrix(QtCore.QObject):
    # TODO: How to merge these two signals into one signal with parameter
    # overload (something like clicked() and clicked(bool))
    changed = QtCore.Signal(dict)
    reseted = QtCore.Signal()

    def __init__(self):
        super(GOLMatrix, self).__init__()
        self.from_survive = 2
        self.to_survive = 3
        self.come_to_life = 3
        self.cur_population = set()
        self.next_population = set()

    @QtCore.Slot(int)
    def set_from_survive(self, from_survive):
        self.from_survive = from_survive

    @QtCore.Slot(int)
    def set_to_survive(self, to_survive):
        self.to_survive = to_survive

    @QtCore.Slot(int)
    def set_come_to_life(self, come_to_life):
        self.come_to_life = come_to_life

    def is_alive(self, x, y):
        ''' Returns `True` if cell (x, y) is alive, `False` otherwise.'''
        return (x, y) in self.cur_population

    def set_alive(self, x, y):
        ''' Marks cell (x, y) as alive.'''
        if not self.is_alive(x, y):
            self.cur_population.add((x, y))
        self.changed.emit({(x, y): True})

    def set_dead(self, x, y):
        ''' Kills cell (x, y) '''
        if self.is_alive(x, y):
            self.cur_population.remove((x, y))
        self.changed.emit({(x, y): False})

    def get_neighbours(self, x, y):
        ''' Returns all neighbors of cell (x, y).'''
        return ((x-1, y-1), (x, y-1), (x+1, y-1),
                (x+1, y), (x+1, y+1), (x, y+1),
                (x-1, y+1), (x-1, y))

    def get_live_cells(self):
        ''' Returns all alive cells.'''
        return self.cur_population

    def count_live_neighbours(self, x, y):
        ''' Returns number of alive neighbors of cell (x, y). '''
        return sum(map(lambda coord: self.is_alive(coord[0], coord[1]), self.get_neighbours(x, y)))

    def get_next_state(self, x, y):
        ''' Returns state of cell (x, y) for next iteration.

        Return `True` if cell should be alive, `False` otherwise.'''
        live_neighbours = self.count_live_neighbours(x, y)
        return ((self.is_alive(x, y) and self.from_survive <= live_neighbours <= self.to_survive) or
                (not self.is_alive(x, y) and live_neighbours == self.come_to_life))

    def reset(self):
        self.cur_population = set()
        self.reseted.emit()

    def shrink_world(self):
        ''' Kills all cells that are not visible on canvas.

        Current implementation kill all cells that are not in (-3, -3, 53, 83),
        but this should be done in respect to visible area on screen.
        '''

        def should_survive(cell):
            return cell[0] > -3 and cell[0] < 83 and cell[1] > -3 and cell[1] < 53
        self.cur_population = set(filter(should_survive, self.cur_population))

    def next_iteration(self):
        ''' Calculates state of next generation.. '''
        # TODO: This should be optimized. For only a few hundred alive cells
        # show down ins visible.
        self.next_population = set()
        checked = set()  # no need to check cell that are already checked
        # for every live cell check if its state should be changed or state
        # of its neighbors
        for live in self.get_live_cells():
            for neighbour in self.get_neighbours(*live):
                if neighbour in checked:
                    continue
                if not neighbour in self.next_population and self.get_next_state(*neighbour):
                    self.next_population.add(neighbour)
                checked.add(neighbour)
        self.cur_population, self.next_population = self.next_population, self.cur_population

        self.shrink_world()

        self.reseted.emit()

    def to_string(self):
        # TODO: Remember `from_survive`, `to_survive` and `come_to_life`
        import pprint
        return pprint.pformat(self.get_live_cells())

    @classmethod
    def from_string(cls, s):
        m = GOLMatrix()
        m.cur_population = eval(s)
        return m


class Cell(QtGui.QGraphicsItem):
    def __init__(self, *args, **kwargs):
        self.size = kwargs.pop('size')
        super(Cell, self).__init__(*args, **kwargs)

    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.size, self.size)

    def shape(self):
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter, options, widget):
        painter.setBrush(Qt.black)
        # TODO: Better way to determine offset?
        painter.drawEllipse(3, 3, self.size - 6, self.size - 6)


class Board(QtGui.QGraphicsScene):
    def __init__(self, *args, **kwargs):
        self.border_width = kwargs.pop('border_width')
        self.square_size = kwargs.pop('square_size')
        super(Board, self).__init__(*args, **kwargs)
        self.set_matrix(GOLMatrix())

    def set_matrix(self, matrix):
        self.matrix = matrix
        self.matrix.reseted.connect(self.redo_all)
        self.matrix.changed.connect(self.redo_part)

    @QtCore.Slot(dict)
    def redo_part(self, part):
        for (x, y), value in part.items():
            if value:
                self.add_cell(x, y)
            else:
                self.remove_cell(x, y)

    @QtCore.Slot()
    def redo_all(self):
        ''' Redraws scene. '''
        self.clear()
        for x, y in self.matrix.get_live_cells():
            self.add_cell(x, y)

    def next_iteration(self):
        ''' Requests form matrix to calculate next iteration.'''
        self.matrix.next_iteration()

    def reset(self):
        ''' Resets state (kills all cells)'''
        self.matrix.reset()

    def get_postion(self, x, y):
        ''' Returns position of cell (x, y) in scene coordinate system.'''
        return QtCore.QPointF(x*self.square_size+self.border_width,
                              y*self.square_size+self.border_width)

    def add_cell(self, x, y):
        ''' Adds cell to (x, y) coordinates.'''
        item = Cell(size=self.square_size)
        item.setPos(self.get_postion(x, y))
        self.addItem(item)

    def remove_cell(self, x, y):
        ''' Removes cell from (x, y) coordinates.'''
        self.removeItem(self.itemAt(self.get_postion(x, y)))


class BoardView(QtGui.QGraphicsView):
    def __init__(self, *args, **kwargs):
        super(BoardView, self).__init__(*args, **kwargs)
        self.setCacheMode(self.CacheBackground)
        #self.setViewportUpdateMode(self.BoundingRectViewportUpdate)
        self.setRenderHint(QtGui.QPainter.Antialiasing)

        # TODO: Take this from settings
        self.square_size = 20
        self.border_width = 5

        # Start from top left corner
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # No need for scroll bar
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scene = Board(self, square_size=self.square_size, border_width=self.border_width)
        self.setScene(self.scene)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.scene.next_iteration)

    def mousePressEvent(self, event):
        pos = self.mapToScene(event.pos())
        item = self.scene.itemAt(pos)
        x = int((pos.x() - self.border_width) / self.square_size)
        y = int((pos.y() - self.border_width) / self.square_size)
        if item:
            self.scene.matrix.set_dead(x, y)
        else:
            self.scene.matrix.set_alive(x, y)

        super(BoardView, self).mousePressEvent(event)

    def drawBackground(self, painter, rect):
        ''' Background drawing. '''
        painter.setPen(Qt.DotLine)
        # vertical lines
        for i in xrange(int(rect.left() + self.border_width),
                        int(rect.right() - self.border_width),
                        self.square_size):
            painter.drawLine(i, rect.bottom() + self.border_width, i,
                             rect.top() - self.border_width)
        # horizontal lines
        for i in xrange(int(rect.top() + self.border_width),
                        int(rect.bottom() - self.border_width),
                        self.square_size):
            painter.drawLine(rect.left() + self.border_width, i,
                             rect.right() - self.border_width, i)

        painter.setPen(QtGui.QPen(Qt.black, self.border_width, Qt.SolidLine,
                                  Qt.RoundCap, Qt.RoundJoin))
        border = QtCore.QRectF(rect.left() + self.border_width,
                               rect.top() + self.border_width,
                               rect.width() - 2*self.border_width,
                               rect.height() - 2*self.border_width)
        painter.drawRect(border)

    def resizeEvent(self, event):
        # Fixes start of coordinate system to top-left corner of view
        self.setSceneRect(QtCore.QRectF(0, 0, self.width(), self.height()))
        super(BoardView, self).resizeEvent(event)

    def update_timer(self, value):
        self.timer.setInterval(value)

    def start(self):
        self.timer.start()

    def stop(self):
        self.timer.stop()

    def reset(self):
        self.stop()
        self.scene.reset()
