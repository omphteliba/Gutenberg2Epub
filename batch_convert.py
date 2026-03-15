import os
import subprocess
import argparse

def run_batch(source_root, output_base):
    """
    Durchsucht source_root nach index.html Dateien und startet die Konvertierung.
    """
    # Absolute Pfade sind sicherer
    source_root = os.path.abspath(source_root)
    output_base = os.path.abspath(output_base)

    print(f"Starte Scan in: {source_root}")
    print(f"Ausgabeordner: {output_base}")

    # os.walk geht rekursiv durch alle Unterordner
    for root, dirs, files in os.walk(source_root):
        # Wenn eine index.html da ist, ist es ein Gutenberg-Buch
        if 'index.html' in files:
            # Sicherheitscheck: Nicht in bereits erstellten temp-Ordnern suchen
            if "temp" in root.lower() or "css" in root.lower() or "images" in root.lower():
                continue

            print(f"\n[ Buch gefunden ] {root}")
            
# ... oben bleibt alles gleich ...

            try:
                # 1. Schritt: localprocess.py aufrufen
                print(f"   -> Sammle Daten (localprocess)...")
                
                # FIX: Wir entfernen 'encoding' oder setzen es auf 'latin-1' 
                # und nutzen 'errors="replace"', damit Sonderzeichen den Prozess nicht stoppen.
                proc_local = subprocess.run(
                    ["python", "localprocess.py", root, "-d", output_base],
                    capture_output=True, 
                    text=True,
                    encoding='latin-1', # Latin-1 kommt mit deutschen Umlauten unter Windows besser klar
                    errors='replace'    # Ersetzt nicht decodierbare Zeichen statt abzustürzen
                )

                # Sicherheitscheck: Hat proc_local.stdout überhaupt Inhalt?
                if proc_local.stdout:
                    temp_path = None
                    for line in proc_local.stdout.splitlines():
                        if line.startswith("TEMP_PATH:"):
                            temp_path = line.split(":", 1)[1].strip()
                else:
                    temp_path = None

                # 2. Schritt: converter.py aufrufen
                if temp_path and os.path.exists(temp_path):
                    print(f"   -> Erstelle ePub (converter)...")
                    # Hier brauchen wir meist kein capture_output, 
                    # da wir nur auf den Abschluss warten.
                    subprocess.run(
                        ["python", "converter.py", "-d", temp_path],
                        check=True
                    )
                    print(f"   [ OK ] Konvertierung abgeschlossen.")
                else:
                    print(f"   [ FEHLER ] localprocess hat keinen Pfad geliefert.")
                    if proc_local.stderr:
                        print(f"   Details: {proc_local.stderr}")

            except Exception as e:
                # Hier fangen wir den Fehler ab, damit das Skript beim nächsten Buch weitermacht
                print(f"   [ KRITISCHER FEHLER ] bei {root}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch Konvertierung für Gutenberg NAS Archiv")
    parser.add_argument("source", help="NAS Pfad zum Scannen (z.B. \\\\TRUENAS\\...\\16)")
    parser.add_argument("-d", "--output", default="batch_output", help="Zielordner für die ePubs")
    
    args = parser.parse_args()
    
    if os.path.exists(args.source):
        run_batch(args.source, args.output)
    else:
        print(f"Quellpfad {args.source} existiert nicht!")