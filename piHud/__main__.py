
import sys
import obd
from MainScreen import MainScreen
from Config import Config
from PageMarker import PageMarker
from PyQt4 import QtGui, QtCore


# pygal optimizations
try:
	from pygal.svg import Svg
	# pygal always dumps its configs to JS and embeds them in the SVGs
	# we don't need that...
	Svg.add_scripts = lambda *args: None # completely disable the JS generator
except:
	pass




class PiHud(QtGui.QMainWindow):
	def __init__(self):
		super(PiHud, self).__init__()

		self.setWindowTitle("PiHud")

		# define the color palette
		palette = self.palette()
		palette.setColor(self.backgroundRole(), QtCore.Qt.black)
		self.setPalette(palette)
		
		# read the config file
		self.config = Config("piHud/config.json")

		# init OBD conncetion
		obd.debug.console = True
		self.connection = obd.Async(self.config.port)
		# for i in range(16):
			# self.connection.supported_commands.append(obd.commands[1][i]) 

		# make a screen stack
		self.stack = QtGui.QStackedWidget(self)
		self.setCentralWidget(self.stack)

		# read the config and make pages
		if len(self.config.pages) > 0:
			for page in self.config.pages:
				self.__add_page(page)
			self.stack.setCurrentIndex(0)
		else:
			self.__add_empty_page()

		self.pageMarker = PageMarker(self)
		self.init_context_menu()

		# start python-OBDs event loop going
		self.connection.start()
		self.showFullScreen()


	def __add_page(self, page_config):
		page = MainScreen(self, self.connection, page_config)
		self.stack.addWidget(page)
		self.stack.setCurrentWidget(page)


	def __add_empty_page(self):
		page_config = self.config.add_page()
		self.__add_page(page_config)
		self.config.save()


	def __delete_page(self):
		if self.stack.count() > 1:
			page = self.stack.currentWidget()
			self.stack.removeWidget(page)
			self.config.delete_page(page.page_config)
			page.deleteLater()
			self.config.save()

	def __next_page(self):
		# cycle through the screen stack
		self.stack.currentWidget().unwatch() # tell the current page to relinquish its sensors from python-OBD

		next_index = (self.stack.currentIndex() + 1) % len(self.stack)
		self.stack.setCurrentIndex(next_index)

		self.stack.currentWidget().rewatch() # tell the new page to re-watch its sensors


	def init_context_menu(self):
		# create the context menu
		self.menu = QtGui.QMenu()
		self.menu.addAction("New Page", self.__add_empty_page)
		self.menu.addAction("Delete Page", self.__delete_page)
		self.menu.addSeparator()

		subMenu = self.menu.addMenu("Add Widget")

		if len(self.connection.supported_commands) > 0:
			for command in self.connection.supported_commands:
				a = subMenu.addAction(command.name)
				a.setData(command)
		else:
			a = subMenu.addAction("No sensors available")
			a.setDisabled(True)


	def contextMenuEvent(self, e):
		action = self.menu.exec_(self.mapToGlobal(e.pos()))
		if action is not None:
			command = action.data().toPyObject()
			# if this is a command creation action, make the new widget
			# there's got to be a better way to do this...
			if command is not None:
				self.stack.currentWidget().make_default_widget(command)


	def keyPressEvent(self, event):
		key = event.key()

		if key == QtCore.Qt.Key_Escape:
			self.close()

		elif key == QtCore.Qt.Key_Tab:
			self.__next_page()


	def closeEvent(self, e):
		self.connection.close()
		quit()




if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	pihud = PiHud()

	# Start QT event loop, exit upon return
	sys.exit(app.exec_())
