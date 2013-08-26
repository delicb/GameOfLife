__author__ = "Bojan Delic <bojan@delic.in.rs>"
__mail__ = "bojan@delic.in.rs"

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt


class GOLMatrix(QtCore.QObject):
    # TODO: Naci kako ovo da se spoji u jedan signal sa razlicitim parametrima
    # Tako da jedan signal nema parametre, a drugi ima dict
    # nesto kao clicked() i clicked(bool)
    changed = QtCore.pyqtSignal(dict)
    reseted = QtCore.pyqtSignal()
    
    def __init__(self):
        super(GOLMatrix, self).__init__()
        self.from_survive = 2
        self.to_survive = 3
        self.come_to_life = 3
        self.cur_population = set()
        self.next_population = set()
        
    @QtCore.pyqtSlot(int)
    def set_from_survive(self, from_survive):
        self.from_survive = from_survive
        
    @QtCore.pyqtSlot(int)
    def set_to_survive(self, to_survive):
        self.to_survive = to_survive
        
    @QtCore.pyqtSlot(int)
    def set_come_to_life(self, come_to_life):
        self.come_to_life = come_to_life
        
    def is_alive(self, x, y):
        ''' Vraca True ako je celija (x, y) ziva, False inace'''
        return (x, y) in self.cur_population
    
    def set_alive(self, x, y):
        ''' Ozivljava celiju (x, y).'''
        if not self.is_alive(x, y):
            self.cur_population.add((x, y))
        self.changed.emit({(x, y): True})

    def set_dead(self, x, y):
        ''' Ubija celiju (x, y) '''
        if self.is_alive(x, y):
            self.cur_population.remove((x, y))
        self.changed.emit({(x, y): False})
    
    def get_neighbours(self, x, y):
        ''' Vraca sve susede celije (x, y).'''
        return ((x-1, y-1), (x, y-1), (x+1, y-1),
                (x+1, y), (x+1, y+1), (x, y+1),
                (x-1, y+1), (x-1, y))
    
    def get_live_cells(self):
        ''' Vraca celokupnu zivu populaciju.'''
        return self.cur_population
        
    def count_live_neighbours(self, x, y):
        ''' Vraca broj zivih suseda celije (x, y). '''
        return sum(map(lambda coord: self.is_alive(coord[0], coord[1]), self.get_neighbours(x, y)))
    
    def get_next_state(self, x, y):
        '''Vraca stanje celije na (x, y) u sledecoj iteraciji.
        
        Vraca True ako celija treba da bude ziva, False ako treba da bude mrtva.'''
        live_neighbours = self.count_live_neighbours(x, y)
        return ((self.is_alive(x, y) and self.from_survive <= live_neighbours <= self.to_survive) or
           (not self.is_alive(x, y) and live_neighbours == self.come_to_life))
    
    def reset(self):
        self.cur_population = set()
        self.reseted.emit()
        
    def shrink_world(self):
        ''' Ubija sve celije koje se ne vide na canvasu.
        
        Trenutna implementacija ubija celije koje nisu u pravougaoniku (-3, -3, 53, 83),
        ali ovo bi trebalo uraditi tako da uzme u obzir vidljivu povrsinu na ekranu.'''
        def should_survive(cell):
            return cell[0] > -3 and cell[0] < 83 and cell[1] > -3 and cell[1] < 53
        self.cur_population = set(filter(should_survive, self.cur_population))
        
    def next_iteration(self):
        ''' Sracunava stanje sledenje generacije. '''
        # TODO: Optimizovati ovo, vec za par stotina zivih celija se vidi usporenje, 
        # kad dodje do 1000 vise nije upotrebljivo
        self.next_population = set()
        checked = set() # celije koje smo vec proverili ne moramo opet
        # za svaku zivu jedinku proveravamo samo da li treba menjati njeno ili stanje njenih suseda
        for live in self.get_live_cells():
            for neighbour in self.get_neighbours(*live):
                if neighbour in checked: continue
                if not neighbour in self.next_population and self.get_next_state(*neighbour): 
                    self.next_population.add(neighbour)
                checked.add(neighbour)
        self.cur_population, self.next_population = self.next_population, self.cur_population
        
        self.shrink_world()
        
        self.reseted.emit()
        
        
    def to_string(self):
        # TODO: Pamtiti i parametre from_survive, to_survice i come_to_life
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
        # TODO: Bolji nacin za odredjivanje ovih offseta
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
    
    @QtCore.pyqtSlot(dict)
    def redo_part(self, part):
        for (x, y), value in part.items():
            if value:
                self.add_cell(x, y)
            else:
                self.remove_cell(x, y)
    
    @QtCore.pyqtSlot()
    def redo_all(self):
        ''' Iscrtava scenu ispocetka '''
        self.clear()
        for x, y in self.matrix.get_live_cells():
            self.add_cell(x, y)
        
    def next_iteration(self):
        ''' Trazi od matrice da sracuna sledecu genreaciju.'''
        self.matrix.next_iteration()
        
    def reset(self):
        ''' Resetuje stanje, ubija sve zive celije. Prakticno pravi novu matricu stanja. '''
        self.matrix.reset()
        
    def get_postion(self, x, y):
        ''' Vraca poziciju celije (x, y) u koordinatnom sistemu scene.'''
        return QtCore.QPointF(x*self.square_size+self.border_width, y*self.square_size+self.border_width)    
    
    def add_cell(self, x, y):
        ''' Dodaje celiju na koordinate (x, y).'''
        item = Cell(size=self.square_size)
        item.setPos(self.get_postion(x, y))
        self.addItem(item)
        
    def remove_cell(self, x, y):
        ''' Uklanja celiju sa koordinata (x, y).'''
        self.removeItem(self.itemAt(self.get_postion(x, y)))


class BoardView(QtGui.QGraphicsView):
    def __init__(self, *args, **kwargs):
        super(BoardView, self).__init__(*args, **kwargs)
        self.setCacheMode(self.CacheBackground)
        #self.setViewportUpdateMode(self.BoundingRectViewportUpdate)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # TODO: ovo uzeti iz nekih podesavanja
        self.square_size = 20
        self.border_width = 5
        
        # krecemo iz gornjeg levog ugla
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # ne treba nam scroll bar
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
        ''' Iscrtava pozadinu. '''
        painter.setPen(Qt.DotLine)
        # uspravne linije
        for i in xrange(int(rect.left() + self.border_width), int(rect.right() - self.border_width), self.square_size):
            painter.drawLine(i, rect.bottom() + self.border_width, i, rect.top() - self.border_width)
        # vodoravne linije
        for i in xrange(int(rect.top() + self.border_width), int(rect.bottom() - self.border_width), self.square_size):
            painter.drawLine(rect.left() + self.border_width, i, rect.right() - self.border_width, i)
        
        
        painter.setPen(QtGui.QPen(Qt.black, self.border_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        border = QtCore.QRectF(rect.left() + self.border_width, rect.top() + self.border_width, 
                             rect.width() - 2*self.border_width, rect.height() - 2*self.border_width)
        painter.drawRect(border)

    def resizeEvent(self, event):
        # Ovo zakucava pocetak koordinatnog sistema scene u gornji levi ugao view-a
        # NOTE: Kako poravnati celije sa pozadinom bez ovog zakucavanja?
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