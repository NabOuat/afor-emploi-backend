#!/usr/bin/env python
"""
GUI pour importer les données acteur depuis les fichiers CSV
- tagence._toacteur.csv
- toperateur_toacteur.csv
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import threading
from datetime import datetime
import uuid

load_dotenv()

class ActeurImporterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Import Acteur - CSV vers PostgreSQL")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        self.database_url = os.getenv('DATABASE_URL')
        self.import_thread = None
        self.is_importing = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configurer l'interface utilisateur"""
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Titre
        title_label = ttk.Label(main_frame, text="📊 Import des Acteurs", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Frame fichiers
        files_frame = ttk.LabelFrame(main_frame, text="📁 Fichier à importer", padding="10")
        files_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Sélection du fichier
        ttk.Label(files_frame, text="Fichier CSV:").grid(row=0, column=0, sticky=tk.W)
        self.file_path = tk.StringVar()
        
        ttk.Entry(files_frame, textvariable=self.file_path, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(files_frame, text="Parcourir", 
                  command=lambda: self.browse_file(self.file_path)).grid(row=0, column=2)
        
        # Info sur le fichier
        self.file_info_label = ttk.Label(files_frame, text="Aucun fichier sélectionné", 
                                        foreground="gray")
        self.file_info_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Frame options
        options_frame = ttk.LabelFrame(main_frame, text="⚙️ Options", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.skip_duplicates = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Ignorer les doublons (ON CONFLICT DO NOTHING)",
                       variable=self.skip_duplicates).grid(row=0, column=0, sticky=tk.W)
        
        self.type_acteur = tk.StringVar(value="Consultant")
        ttk.Label(options_frame, text="Type d'acteur:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(options_frame, textvariable=self.type_acteur, width=30).grid(row=1, column=1, sticky=tk.W)
        
        # Frame progression
        progress_frame = ttk.LabelFrame(main_frame, text="📈 Progression", padding="10")
        progress_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="Prêt à importer")
        self.progress_label.grid(row=1, column=0, columnspan=2, sticky=tk.W)
        
        # Frame logs
        logs_frame = ttk.LabelFrame(main_frame, text="📋 Logs", padding="10")
        logs_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        scrollbar = ttk.Scrollbar(logs_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.logs_text = tk.Text(logs_frame, height=12, width=100, yscrollcommand=scrollbar.set)
        self.logs_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.logs_text.yview)
        
        # Frame boutons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=5, column=0, columnspan=3, pady=10)
        
        self.import_button = ttk.Button(buttons_frame, text="▶️ Démarrer l'import", 
                                       command=self.start_import)
        self.import_button.grid(row=0, column=0, padx=5)
        
        self.clear_button = ttk.Button(buttons_frame, text="🗑️ Effacer les logs", 
                                      command=self.clear_logs)
        self.clear_button.grid(row=0, column=1, padx=5)
        
        ttk.Button(buttons_frame, text="❌ Quitter", 
                  command=self.root.quit).grid(row=0, column=2, padx=5)
        
        # Configurer le redimensionnement
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
    
    def browse_file(self, var):
        """Parcourir pour sélectionner un fichier"""
        filename = filedialog.askopenfilename(
            title="Sélectionner un fichier CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            var.set(filename)
            self.update_file_info(filename)
    
    def log(self, message):
        """Ajouter un message aux logs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.logs_text.see(tk.END)
        self.root.update()
    
    def clear_logs(self):
        """Effacer les logs"""
        self.logs_text.delete(1.0, tk.END)
    
    def update_file_info(self, filepath):
        """Mettre à jour les informations du fichier"""
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath) / 1024
            file_name = os.path.basename(filepath)
            self.file_info_label.config(
                text=f"✓ {file_name} ({file_size:.1f} KB)",
                foreground="green"
            )
        else:
            self.file_info_label.config(
                text="❌ Fichier non trouvé",
                foreground="red"
            )
    
    def validate_file(self):
        """Valider le fichier sélectionné"""
        file_path = self.file_path.get()
        
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier valide")
            return False
        
        if not self.database_url:
            messagebox.showerror("Erreur", "DATABASE_URL non définie dans .env")
            return False
        
        return True
    
    def detect_file_type(self, filepath):
        """Détecter le type de fichier (agence ou operateur)"""
        filename = os.path.basename(filepath).lower()
        if 'agence' in filename or 'tagence' in filename:
            return 'agence'
        elif 'operateur' in filename or 'toperateur' in filename:
            return 'operateur'
        else:
            return 'unknown'
    
    def parse_csv_agence(self, filepath):
        """Parser le fichier tagence._toacteur.csv"""
        acteurs = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row_num, row in enumerate(reader, 1):
                    if not row or not row[0].strip():
                        continue
                    
                    try:
                        acteur_id = row[0].strip()
                        nom = row[1].strip() if len(row) > 1 else ""
                        contact_1 = row[2].strip() if len(row) > 2 and row[2].strip() else None
                        contact_2 = row[3].strip() if len(row) > 3 and row[3].strip() else None
                        
                        if acteur_id and nom:
                            acteurs.append({
                                'id': acteur_id,
                                'nom': nom,
                                'type_acteur': self.type_acteur.get(),
                                'contact_1': contact_1,
                                'contact_2': contact_2,
                                'adresse_1': None,
                                'adresse_2': None,
                                'email_1': None,
                                'email_2': None
                            })
                    except Exception as e:
                        self.log(f"⚠️  Ligne {row_num} (Agence): {str(e)}")
                        continue
        
        except Exception as e:
            self.log(f"❌ Erreur lecture Agence: {str(e)}")
            return []
        
        return acteurs
    
    def parse_csv_operateur(self, filepath):
        """Parser le fichier toperateur_toacteur.csv"""
        acteurs = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row_num, row in enumerate(reader, 1):
                    if not row or not row[0].strip():
                        continue
                    
                    try:
                        acteur_id = row[0].strip()
                        nom = row[1].strip() if len(row) > 1 else ""
                        contact_1 = row[2].strip() if len(row) > 2 and row[2].strip() else None
                        contact_2 = row[3].strip() if len(row) > 3 and row[3].strip() else None
                        adresse_1 = row[4].strip() if len(row) > 4 and row[4].strip() else None
                        adresse_2 = row[5].strip() if len(row) > 5 and row[5].strip() else None
                        email_1 = row[6].strip() if len(row) > 6 and row[6].strip() else None
                        email_2 = row[7].strip() if len(row) > 7 and row[7].strip() else None
                        
                        if acteur_id and nom:
                            acteurs.append({
                                'id': acteur_id,
                                'nom': nom,
                                'type_acteur': self.type_acteur.get(),
                                'contact_1': contact_1,
                                'contact_2': contact_2,
                                'adresse_1': adresse_1,
                                'adresse_2': adresse_2,
                                'email_1': email_1,
                                'email_2': email_2
                            })
                    except Exception as e:
                        self.log(f"⚠️  Ligne {row_num} (Opérateur): {str(e)}")
                        continue
        
        except Exception as e:
            self.log(f"❌ Erreur lecture Opérateur: {str(e)}")
            return []
        
        return acteurs
    
    def import_acteurs(self, acteurs):
        """Importer les acteurs dans la base de données"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            inserted = 0
            skipped = 0
            errors = 0
            
            total = len(acteurs)
            
            for idx, acteur in enumerate(acteurs, 1):
                try:
                    if self.skip_duplicates.get():
                        query = sql.SQL("""
                            INSERT INTO acteur 
                            (id, nom, type_acteur, contact_1, contact_2, adresse_1, adresse_2, email_1, email_2)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO NOTHING
                        """)
                    else:
                        query = sql.SQL("""
                            INSERT INTO acteur 
                            (id, nom, type_acteur, contact_1, contact_2, adresse_1, adresse_2, email_1, email_2)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                nom = EXCLUDED.nom,
                                type_acteur = EXCLUDED.type_acteur,
                                contact_1 = EXCLUDED.contact_1,
                                contact_2 = EXCLUDED.contact_2,
                                adresse_1 = EXCLUDED.adresse_1,
                                adresse_2 = EXCLUDED.adresse_2,
                                email_1 = EXCLUDED.email_1,
                                email_2 = EXCLUDED.email_2
                        """)
                    
                    cursor.execute(query, (
                        acteur['id'],
                        acteur['nom'],
                        acteur['type_acteur'],
                        acteur['contact_1'],
                        acteur['contact_2'],
                        acteur['adresse_1'],
                        acteur['adresse_2'],
                        acteur['email_1'],
                        acteur['email_2']
                    ))
                    
                    inserted += 1
                    
                    # Mise à jour de la progression
                    progress = (idx / total) * 100
                    self.progress_var.set(progress)
                    self.progress_label.config(text=f"Traitement: {idx}/{total} ({progress:.1f}%)")
                    
                    if idx % 10 == 0:
                        self.log(f"✓ {idx}/{total} enregistrements traités...")
                
                except psycopg2.Error as e:
                    if "duplicate key" in str(e).lower():
                        skipped += 1
                    else:
                        errors += 1
                        self.log(f"❌ Erreur acteur {acteur['id']}: {str(e)}")
                    continue
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return inserted, skipped, errors
        
        except psycopg2.Error as e:
            self.log(f"❌ Erreur de connexion: {str(e)}")
            return 0, 0, len(acteurs)
    
    def start_import(self):
        """Démarrer l'import dans un thread séparé"""
        if self.is_importing:
            messagebox.showwarning("Attention", "Un import est déjà en cours")
            return
        
        if not self.validate_file():
            return
        
        self.is_importing = True
        self.import_button.config(state=tk.DISABLED)
        self.clear_logs()
        
        self.import_thread = threading.Thread(target=self.do_import)
        self.import_thread.daemon = True
        self.import_thread.start()
    
    def do_import(self):
        """Effectuer l'import"""
        try:
            file_path = self.file_path.get()
            file_type = self.detect_file_type(file_path)
            
            self.log("🔄 Démarrage de l'import...")
            self.log(f"📁 Fichier: {os.path.basename(file_path)}")
            self.log(f"� Type détecté: {file_type}")
            self.log("")
            
            # Parser le fichier selon son type
            self.log("📖 Lecture du fichier...")
            
            if file_type == 'agence':
                acteurs = self.parse_csv_agence(file_path)
            elif file_type == 'operateur':
                acteurs = self.parse_csv_operateur(file_path)
            else:
                # Essayer de détecter automatiquement
                self.log("⚠️  Type inconnu, tentative de détection automatique...")
                acteurs = self.parse_csv_operateur(file_path)
                if not acteurs:
                    acteurs = self.parse_csv_agence(file_path)
            
            self.log(f"✓ {len(acteurs)} acteurs trouvés")
            
            if not acteurs:
                self.log("❌ Aucun acteur trouvé dans le fichier")
                messagebox.showwarning("Attention", "Aucun acteur trouvé dans le fichier")
                return
            
            self.log("")
            
            # Importer dans la base de données
            self.log("💾 Import dans la base de données...")
            inserted, skipped, errors = self.import_acteurs(acteurs)
            
            # Résumé
            self.log("\n" + "="*60)
            self.log("✅ IMPORT TERMINÉ")
            self.log("="*60)
            self.log(f"✓ Enregistrements insérés: {inserted}")
            self.log(f"⚠️  Enregistrements ignorés: {skipped}")
            self.log(f"❌ Erreurs: {errors}")
            self.log("="*60)
            
            self.progress_var.set(100)
            self.progress_label.config(text="Import terminé!")
            
            messagebox.showinfo("Succès", 
                              f"Import terminé!\n\n"
                              f"Insérés: {inserted}\n"
                              f"Ignorés: {skipped}\n"
                              f"Erreurs: {errors}")
        
        except Exception as e:
            self.log(f"❌ Erreur générale: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur lors de l'import: {str(e)}")
        
        finally:
            self.is_importing = False
            self.import_button.config(state=tk.NORMAL)


def main():
    root = tk.Tk()
    app = ActeurImporterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
