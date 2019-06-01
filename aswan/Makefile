aswan.py:	utils.py \
			aggregator.py report.py tabulator.py \
			ui_tabulatordialog.py ui_mainwindow.py \
			tabulatordialog.py mainwindow.py 

ui_tabulatordialog.py:	tabulatordialog.ui
	pyuic5 -x tabulatordialog.ui > ui_tabulatordialog.py

ui_mainwindow.py:	mainwindow.ui
	pyuic5 -x mainwindow.ui > ui_mainwindow.py

package-win:	aswan.ico aswan.py
	pyinstaller --noconfirm --onefile --windowed aswan.py -i aswan.ico --add-data aswan.ico;.

package-mac:	aswan.icns aswan.py
	pyinstaller --noconfirm --onefile --windowed aswan.py -i aswan.icns

package-linux:	aswan.png aswan.py
	pyinstaller --noconfirm --onefile --windowed aswan.py -i aswan.png

mac:	package-mac
	./dist/aswan.app/Contents/MacOS/aswan
