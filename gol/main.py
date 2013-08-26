__author__ = "Bojan Delic <bojan@delic.in.rs>"
__mail__ = "bojan@delic.in.rs"

from PyQt4 import QtGui, QtCore
from main_window import Ui_MainWindow 

class MainWindow(QtGui.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        #self.setFixedSize(self.width(), self.height())
        
        statusbar = self.statusBar()
        
        self.label = QtGui.QLabel('300')
        statusbar.addPermanentWidget(self.label)
        
        slider = QtGui.QSlider(QtCore.Qt.Horizontal, statusbar)
        slider.setMinimum(50)
        slider.setMaximum(1000)
        slider.setValue(300)
        statusbar.addPermanentWidget(slider)
        
        slider.valueChanged.connect(self.ui.board.update_timer)
        slider.valueChanged.connect(self.update_label)
        
        self.statusBar().showMessage("Ovo je Game of Life")

        self.from_survive = QtGui.QSpinBox(self.ui.toolBar)
        self.from_survive.setMaximum(6)
        self.from_survive.setMinimum(1)
        self.from_survive.setValue(2)
        self.ui.toolBar.addSeparator()
        self.ui.toolBar.addWidget(QtGui.QLabel('From survive: '))
        self.ui.toolBar.addWidget(self.from_survive)
        
        self.to_survive = QtGui.QSpinBox(self.ui.toolBar)
        self.to_survive.setMaximum(7)
        self.to_survive.setMinimum(2)
        self.to_survive.setValue(3)
        self.ui.toolBar.addSeparator()
        self.ui.toolBar.addWidget(QtGui.QLabel('To survive: '))
        self.ui.toolBar.addWidget(self.to_survive)
        
        self.come_to_life = QtGui.QSpinBox(self.ui.toolBar)
        self.come_to_life.setMaximum(7)
        self.come_to_life.setMinimum(2)
        self.come_to_life.setValue(3)
        self.ui.toolBar.addSeparator()
        self.ui.toolBar.addWidget(QtGui.QLabel('Come to life: '))
        self.ui.toolBar.addWidget(self.come_to_life)
        
        self.from_survive.valueChanged.connect(self.ui.board.scene.matrix.set_from_survive)
        self.to_survive.valueChanged.connect(self.ui.board.scene.matrix.set_to_survive)
        self.come_to_life.valueChanged.connect(self.ui.board.scene.matrix.set_come_to_life)
        
        self.ui.board.scene.matrix.changed.connect(self.update_statusbar)
        self.ui.board.scene.matrix.reseted.connect(self.update_statusbar)
        
    
    def update_statusbar(self):
        self.ui.statusBar.showMessage('Live cells: %d' % len(self.ui.board.scene.matrix.get_live_cells()))
    
    def update_label(self, value):
        self.label.setText(str(value))
        
    @QtCore.pyqtSlot()
    def on_actionSave_triggered(self):
        file_name = QtGui.QFileDialog.getSaveFileName(self)
        f = open(file_name, 'w')
        f.write(self.ui.board.scene.matrix.to_string())
    
    @QtCore.pyqtSlot()
    def on_actionOpen_triggered(self):
        from gol import GOLMatrix
        f = QtGui.QFileDialog.getOpenFileName(self)
        self.ui.board.scene.set_matrix(GOLMatrix.from_string(open(f, 'r').read())) 
        self.ui.board.scene.matrix.reseted.emit()

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
