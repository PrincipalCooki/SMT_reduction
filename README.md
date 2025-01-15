# Funktionssynthese mit SMT

## Enthaltene Dateien

Wie auf dem Aufgabenblatt beschrieben enthält dieses Archive folgende Dateien:

* `fsynth.py`: Vorlage für die eigene Lösung.
  **Laden Sie lediglich diese Datei in Ilias hoch unter gleichem Dateinamen.**
* `problems`: Ordner mit vorgefertigten Probleminstanzen zum Testen Ihrer Lösung.
* `gensamples.py`: Helfer-Skript, das zufällige Spezifikationsdatenpunkte ("samples") für eine hinterlegte Lösung
  generiert.
* `validator.py`: Ein Skript, das die abgegebenen Lösungen validiert. Insbesondere wird die Ausgabe von `fsynth.py` auf
  Äquivalenz mit der hinterlegten Lösung überprüft.
* `yamlfilter.py`: Ein Filter, um die hinterlegten Lösungen aus den YAML-Dateien zu entfernen.
* `z3test.py`: Ein Skript, um die z3-Installation zu testen.
* `runandpaint.sh`: Führt `fsynth.py` aus und schickt die Ausgabe über `network2x.py`   nach `dot` um Ihre Schaltung zu
  rendern. `runandpaint.sh` öffnet das Schaltungsbild in Bildbetrachter.
* `printer.py`: Helfer-Klasse um die YAML-Dokument für die Ausgabe zu erzeugen.
* `network2x.py`: Wandelt die Ausgabe nach SMTlib oder Dot.
* `findsize.py`: Suche nach minimaler Tiefe und Weite eines Netzes.

## Zeiten zur Orientierung

Unsere Musterlösung löst die vorgefertigten Probleminstanzen mit den folgenden Zeiten:

* `sat_const_bool.yaml`: 0.2s
* `sat_const_int.yaml`: 0.3s
* `sat_distinct.yaml`: 3.5s
* `sat_double.yaml`: 5.6s
* `sat_greater.yaml`: 0.6s
* `sat_linear.yaml`: 14.0s
* `sat_mod_div.yaml`: 366.3s
* `sat_negate.yaml`: 5.6s
* `unsat_const_int.yaml`: 0.2s
* `unsat_const_int_2.yaml`: 0.2s
* `unsat_contradiction.yaml`: 8.5s
* `unsat_mod.yaml`: 36.7s