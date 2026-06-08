import os
import csv
import psycopg2
import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import datetime
import threading
from dotenv import load_dotenv

load_dotenv()

class MigrationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Migration fic_personne_localisation")
        self.root.geometry("900x700")
        
        self.csv_file = None
        self.migrated = 0
        self.skipped = 0
        self.errors = 0
        
        # Frame principal
        main_frame = ctk.CTkFrame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Titre
        title = ctk.CTkLabel(main_frame, text="🚀 Migration fic_personne_localisation", 
                            font=("Arial", 18, "bold"))
        title.pack(pady=10)
        
        # Frame sélection fichier
        file_frame = ctk.CTkFrame(main_frame)
        file_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(file_frame, text="Fichier CSV:", font=("Arial", 12)).pack(side="left", padx=5)
        self.file_label = ctk.CTkLabel(file_frame, text="Aucun fichier sélectionné", 
                                       text_color="gray", font=("Arial", 11))
        self.file_label.pack(side="left", padx=5, fill="x", expand=True)
        
        self.browse_btn = ctk.CTkButton(file_frame, text="📁 Parcourir", 
                                        command=self.browse_file, width=120)
        self.browse_btn.pack(side="right", padx=5)
        
        # Frame boutons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        self.migrate_btn = ctk.CTkButton(button_frame, text="🚀 Commencer la migration", 
                                         command=self.start_migration, 
                                         fg_color="green", hover_color="darkgreen")
        self.migrate_btn.pack(side="left", padx=5)
        
        # Barre de progression
        self.progress_bar = ctk.CTkProgressBar(main_frame, mode="indeterminate")
        self.progress_bar.pack(fill="x", pady=10)
        
        # Frame statistiques
        stats_frame = ctk.CTkFrame(main_frame)
        stats_frame.pack(fill="x", pady=10)
        
        self.stats_label = ctk.CTkLabel(stats_frame, text="Migrés: 0 | Ignorés: 0 | Erreurs: 0", 
                                        font=("Arial", 11))
        self.stats_label.pack(side="left", padx=5)
        
        # Logs
        ctk.CTkLabel(main_frame, text="📝 Logs:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10, 5))
        
        self.log_text = ctk.CTkTextbox(main_frame, height=300, font=("Courier", 10))
        self.log_text.pack(fill="both", expand=True, pady=5)
        
    def browse_file(self):
        file = filedialog.askopenfilename(
            title="Sélectionner un fichier CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file:
            self.csv_file = file
            self.file_label.configure(text=file.split("\\")[-1])
    
    def log_message(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.root.update()
    
    def update_stats(self):
        self.stats_label.configure(
            text=f"Migrés: {self.migrated} | Ignorés: {self.skipped} | Erreurs: {self.errors}"
        )
    
    def start_migration(self):
        if not self.csv_file:
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier CSV")
            return
        
        self.migrated = 0
        self.skipped = 0
        self.errors = 0
        self.log_text.delete("1.0", "end")
        
        self.migrate_btn.configure(state="disabled")
        self.progress_bar.start()
        
        thread = threading.Thread(target=self.perform_migration)
        thread.start()
    
    def perform_migration(self):
        """Effectuer la migration"""
        try:
            self.log_message("🔄 Début de la migration...\n")
            
            # Connexion à la base de données
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                self.log_message("❌ DATABASE_URL non définie dans .env")
                return
            
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            self.log_message("✓ Connexion à la base de données établie")
            
            # Lire le fichier CSV
            self.log_message(f"📂 Lecture du fichier: {self.csv_file}")
            
            with open(self.csv_file, 'r', encoding='latin-1') as csvfile:
                # Lire la première ligne pour vérifier si c'est un en-tête
                first_line = csvfile.readline().strip()
                csvfile.seek(0)
                
                # Déterminer si la première ligne est un en-tête
                reader = csv.reader(csvfile)
                first_row = next(reader)
                
                # Vérifier si c'est un en-tête
                has_header = any(col in first_row for col in ['id', 'contrat_id', 'region_id', 'date_debut'])
                
                csvfile.seek(0)
                
                if has_header:
                    reader = csv.DictReader(csvfile)
                    self.log_message(f"✓ Colonnes détectées: {', '.join(reader.fieldnames)}\n")
                else:
                    # CSV sans en-tête - mapper les colonnes par position
                    self.log_message("⚠️  CSV sans en-tête détecté")
                    self.log_message("📋 Mapping des colonnes par position:")
                    self.log_message("  0: id")
                    self.log_message("  1: contrat_id")
                    self.log_message("  2: region_id")
                    self.log_message("  3: departement_id")
                    self.log_message("  4: sous_prefecture_id")
                    self.log_message("  5: date_debut")
                    self.log_message("  6: location (ignoré)\n")
                    
                    reader = csv.reader(csvfile)
                    rows = list(reader)
                    
                    for row_num, row in enumerate(rows, 1):
                        try:
                            # Mapper les colonnes par position
                            if len(row) < 2:
                                self.log_message(f"⚠️  Ligne {row_num}: Nombre de colonnes insuffisant")
                                self.skipped += 1
                                continue
                            
                            localisation_id = row[0].strip() if len(row) > 0 else ''
                            contrat_id = row[1].strip() if len(row) > 1 else ''
                            region_id = row[2].strip() if len(row) > 2 else ''
                            departement_id = row[3].strip() if len(row) > 3 else ''
                            sous_prefecture_id = row[4].strip() if len(row) > 4 else ''
                            date_debut_str = row[5].strip() if len(row) > 5 else ''
                            
                            # Vérifier les champs obligatoires
                            if not localisation_id or not contrat_id:
                                self.log_message(f"⚠️  Ligne {row_num}: Champs obligatoires manquants")
                                self.skipped += 1
                                continue
                            
                            # Parser la date
                            date_debut = None
                            if date_debut_str:
                                try:
                                    date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date()
                                except:
                                    pass
                            
                            # Valider les IDs de clés étrangères
                            region_id = region_id if region_id else None
                            departement_id = departement_id if departement_id else None
                            sous_prefecture_id = sous_prefecture_id if sous_prefecture_id else None
                            
                            # Insérer dans la nouvelle table
                            cursor.execute("""
                                INSERT INTO fic_personne_localisation (
                                    id, contrat_id, region_id, departement_id, 
                                    sous_prefecture_id, date_debut
                                ) VALUES (%s, %s, %s, %s, %s, %s)
                                ON CONFLICT (id) DO UPDATE SET
                                    contrat_id = EXCLUDED.contrat_id,
                                    region_id = EXCLUDED.region_id,
                                    departement_id = EXCLUDED.departement_id,
                                    sous_prefecture_id = EXCLUDED.sous_prefecture_id,
                                    date_debut = EXCLUDED.date_debut
                            """, (
                                localisation_id,
                                contrat_id,
                                region_id,
                                departement_id,
                                sous_prefecture_id,
                                date_debut
                            ))
                            
                            self.migrated += 1
                            
                            # Afficher la progression tous les 100 enregistrements
                            if self.migrated % 100 == 0:
                                self.log_message(f"✓ {self.migrated} enregistrements migrés...")
                                self.update_stats()
                        
                        except psycopg2.Error as e:
                            self.log_message(f"❌ Erreur ligne {row_num}: {str(e)}")
                            self.errors += 1
                            conn.rollback()
                            continue
                    
                    # Valider la transaction
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    self.log_message(f"\n{'='*60}")
                    self.log_message(f"✓ Migration terminée!")
                    self.log_message(f"  - Enregistrements migrés: {self.migrated}")
                    self.log_message(f"  - Enregistrements ignorés: {self.skipped}")
                    self.log_message(f"  - Erreurs: {self.errors}")
                    self.log_message(f"{'='*60}")
                    
                    self.update_stats()
                    messagebox.showinfo("Succès", f"Migration réussie!\n\nMigrés: {self.migrated}\nIgnorés: {self.skipped}\nErreurs: {self.errors}")
                    self.progress_bar.stop()
                    self.migrate_btn.configure(state="normal")
                    return
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Extraire les données
                        localisation_id = row.get('id', '').strip()
                        contrat_id = row.get('contrat_id', '').strip()
                        region_id = row.get('region_id', '').strip()
                        departement_id = row.get('departement_id', '').strip()
                        sous_prefecture_id = row.get('sous_prefecture_id', '').strip()
                        date_debut_str = row.get('date_debut', '').strip()
                        
                        # Vérifier les champs obligatoires
                        if not localisation_id or not contrat_id:
                            self.log_message(f"⚠️  Ligne {row_num}: Champs obligatoires manquants")
                            self.skipped += 1
                            continue
                        
                        # Parser la date
                        date_debut = None
                        if date_debut_str:
                            try:
                                date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date()
                            except:
                                pass
                        
                        # Valider les IDs de clés étrangères
                        region_id = region_id if region_id else None
                        departement_id = departement_id if departement_id else None
                        sous_prefecture_id = sous_prefecture_id if sous_prefecture_id else None
                        
                        # Insérer dans la nouvelle table
                        cursor.execute("""
                            INSERT INTO fic_personne_localisation (
                                id, contrat_id, region_id, departement_id, 
                                sous_prefecture_id, date_debut
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                contrat_id = EXCLUDED.contrat_id,
                                region_id = EXCLUDED.region_id,
                                departement_id = EXCLUDED.departement_id,
                                sous_prefecture_id = EXCLUDED.sous_prefecture_id,
                                date_debut = EXCLUDED.date_debut
                        """, (
                            localisation_id,
                            contrat_id,
                            region_id,
                            departement_id,
                            sous_prefecture_id,
                            date_debut
                        ))
                        
                        self.migrated += 1
                        
                        if self.migrated % 100 == 0:
                            self.log_message(f"✓ {self.migrated} enregistrements migrés...")
                            self.update_stats()
                    
                    except psycopg2.Error as e:
                        self.log_message(f"❌ Erreur ligne {row_num}: {str(e)}")
                        self.errors += 1
                        conn.rollback()
                        continue
                
                # Valider la transaction
                conn.commit()
                cursor.close()
                conn.close()
                
                self.log_message(f"\n{'='*60}")
                self.log_message(f"✓ Migration terminée!")
                self.log_message(f"  - Enregistrements migrés: {self.migrated}")
                self.log_message(f"  - Enregistrements ignorés: {self.skipped}")
                self.log_message(f"  - Erreurs: {self.errors}")
                self.log_message(f"{'='*60}")
                
                self.update_stats()
                messagebox.showinfo("Succès", f"Migration réussie!\n\nMigrés: {self.migrated}\nIgnorés: {self.skipped}\nErreurs: {self.errors}")
                self.progress_bar.stop()
                self.migrate_btn.configure(state="normal")
        
        except Exception as e:
            self.log_message(f"❌ Erreur d'exécution: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur: {str(e)}")
            self.progress_bar.stop()
            self.migrate_btn.configure(state="normal")

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    app = MigrationGUI(root)
    root.mainloop()
