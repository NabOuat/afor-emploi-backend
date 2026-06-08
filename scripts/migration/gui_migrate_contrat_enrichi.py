import os
import csv
import psycopg2
import customtkinter as ctk
from tkinter import filedialog, messagebox
from datetime import datetime
import threading
from dotenv import load_dotenv

load_dotenv()

class ContratEnrichiMigrationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Migration Contrat Enrichi (fic_personne + contrat)")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.fic_personne_file = None
        self.contrat_file = None
        self.migrated = 0
        self.skipped = 0
        self.errors = 0
        self.fic_personne_data = {}
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configurer l'interface utilisateur"""
        # Titre
        title_label = ctk.CTkLabel(
            self.root,
            text="🔄 Migration Contrat Enrichi",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=20)
        
        # Frame pour fic_personne
        fic_frame = ctk.CTkFrame(self.root)
        fic_frame.pack(pady=10, padx=20, fill="x")
        
        fic_label = ctk.CTkLabel(
            fic_frame,
            text="📋 Fichier fic_personne.csv:",
            font=("Arial", 12, "bold")
        )
        fic_label.pack(side="left", padx=5)
        
        self.fic_display = ctk.CTkLabel(
            fic_frame,
            text="Aucun fichier sélectionné",
            font=("Arial", 11),
            text_color="gray"
        )
        self.fic_display.pack(side="left", padx=10, fill="x", expand=True)
        
        fic_browse_btn = ctk.CTkButton(
            fic_frame,
            text="📁 Parcourir",
            command=self.select_fic_personne_file,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            width=120
        )
        fic_browse_btn.pack(side="right", padx=5)
        
        # Frame pour contrat
        contrat_frame = ctk.CTkFrame(self.root)
        contrat_frame.pack(pady=10, padx=20, fill="x")
        
        contrat_label = ctk.CTkLabel(
            contrat_frame,
            text="📋 Fichier contrat.csv:",
            font=("Arial", 12, "bold")
        )
        contrat_label.pack(side="left", padx=5)
        
        self.contrat_display = ctk.CTkLabel(
            contrat_frame,
            text="Aucun fichier sélectionné",
            font=("Arial", 11),
            text_color="gray"
        )
        self.contrat_display.pack(side="left", padx=10, fill="x", expand=True)
        
        contrat_browse_btn = ctk.CTkButton(
            contrat_frame,
            text="📁 Parcourir",
            command=self.select_contrat_file,
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            width=120
        )
        contrat_browse_btn.pack(side="right", padx=5)
        
        # Frame pour les informations
        info_frame = ctk.CTkFrame(self.root)
        info_frame.pack(pady=15, padx=20, fill="both", expand=True)
        
        info_label = ctk.CTkLabel(
            info_frame,
            text="Informations de migration:",
            font=("Arial", 12, "bold")
        )
        info_label.pack(anchor="w", pady=(0, 10))
        
        # Zone de texte pour les logs
        self.log_text = ctk.CTkTextbox(
            info_frame,
            font=("Courier", 10),
            height=250
        )
        self.log_text.pack(fill="both", expand=True, pady=10)
        
        # Barre de progression
        progress_label = ctk.CTkLabel(
            self.root,
            text="Progression:",
            font=("Arial", 11)
        )
        progress_label.pack(anchor="w", padx=20, pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(
            self.root,
            mode="indeterminate"
        )
        self.progress_bar.pack(padx=20, fill="x", pady=(0, 10))
        
        # Frame pour les statistiques
        stats_frame = ctk.CTkFrame(self.root)
        stats_frame.pack(pady=10, padx=20, fill="x")
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="Migrés: 0 | Ignorés: 0 | Erreurs: 0",
            font=("Arial", 11)
        )
        self.stats_label.pack()
        
        # Frame pour les boutons
        button_frame = ctk.CTkFrame(self.root)
        button_frame.pack(pady=15, padx=20, fill="x")
        
        self.migrate_btn = ctk.CTkButton(
            button_frame,
            text="🚀 Commencer la migration",
            command=self.start_migration,
            fg_color="#1976D2",
            hover_color="#1565C0",
            font=("Arial", 12, "bold"),
            height=40
        )
        self.migrate_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑️ Effacer les logs",
            command=self.clear_logs,
            fg_color="#F57C00",
            hover_color="#E65100",
            font=("Arial", 12, "bold"),
            height=40
        )
        clear_btn.pack(side="left", padx=5, fill="x", expand=True)
    
    def select_fic_personne_file(self):
        """Sélectionner le fichier fic_personne.csv"""
        file_path = filedialog.askopenfilename(
            title="Sélectionner le fichier fic_personne.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            self.fic_personne_file = file_path
            filename = os.path.basename(file_path)
            self.fic_display.configure(text=filename, text_color="white")
            self.log_message(f"✓ Fichier fic_personne sélectionné: {filename}")
    
    def select_contrat_file(self):
        """Sélectionner le fichier contrat.csv"""
        file_path = filedialog.askopenfilename(
            title="Sélectionner le fichier contrat.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            self.contrat_file = file_path
            filename = os.path.basename(file_path)
            self.contrat_display.configure(text=filename, text_color="white")
            self.log_message(f"✓ Fichier contrat sélectionné: {filename}")
    
    def log_message(self, message):
        """Ajouter un message aux logs"""
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.root.update()
    
    def clear_logs(self):
        """Effacer les logs"""
        self.log_text.delete("1.0", "end")
        self.migrated = 0
        self.skipped = 0
        self.errors = 0
        self.update_stats()
    
    def update_stats(self):
        """Mettre à jour les statistiques"""
        self.stats_label.configure(
            text=f"Migrés: {self.migrated} | Ignorés: {self.skipped} | Erreurs: {self.errors}"
        )
    
    def start_migration(self):
        """Démarrer la migration"""
        if not self.fic_personne_file or not self.contrat_file:
            messagebox.showerror("Erreur", "Veuillez sélectionner les deux fichiers CSV")
            return
        
        self.migrate_btn.configure(state="disabled")
        self.progress_bar.start()
        
        # Démarrer la migration dans un thread
        thread = threading.Thread(target=self.perform_migration)
        thread.daemon = True
        thread.start()
    
    def load_fic_personne_data(self):
        """Charger les données de fic_personne en mémoire"""
        self.log_message("📂 Chargement des données fic_personne...")
        self.log_message("📋 Mapping fic_personne par position:")
        self.log_message("  0: id")
        self.log_message("  1: nom")
        self.log_message("  2: prenom")
        self.log_message("  3: contact")
        self.log_message("  4: date_naissance")
        self.log_message("  5: genre")
        self.log_message("  6: type_personne")
        self.log_message("  7: operateur_id")
        self.log_message("  10: diplome\n")
        
        try:
            with open(self.fic_personne_file, 'r', encoding='latin-1') as csvfile:
                reader = csv.reader(csvfile)
                
                for row_num, row in enumerate(reader, 1):
                    if len(row) < 2:
                        continue
                    
                    fic_id = row[0].strip() if len(row) > 0 else ''
                    type_personne = row[6].strip() if len(row) > 6 else ''
                    diplome = row[10].strip() if len(row) > 10 else ''
                    
                    if fic_id:
                        self.fic_personne_data[fic_id] = {
                            'diplome': diplome if diplome else None,
                            'type_personne': type_personne if type_personne else None
                        }
                
                self.log_message(f"✓ {len(self.fic_personne_data)} enregistrements fic_personne chargés\n")
        
        except Exception as e:
            self.log_message(f"❌ Erreur lors du chargement fic_personne: {str(e)}")
            raise
    
    def perform_migration(self):
        """Effectuer la migration"""
        try:
            self.log_message("🔄 Début de la migration...\n")
            
            # Charger les données fic_personne
            self.load_fic_personne_data()
            
            # Connexion à la base de données
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                self.log_message("❌ DATABASE_URL non définie dans .env")
                return
            
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            self.log_message("✓ Connexion à la base de données établie\n")
            
            # Lire le fichier contrat
            self.log_message(f"📂 Lecture du fichier contrat: {self.contrat_file}")
            
            with open(self.contrat_file, 'r', encoding='latin-1') as csvfile:
                self.log_message("📋 Mapping contrat par position:")
                self.log_message("  0: id")
                self.log_message("  1: poste_nom")
                self.log_message("  2: date_debut")
                self.log_message("  3: date_fin")
                self.log_message("  4: type_personne")
                self.log_message("  5: fic_personne_id")
                self.log_message("  6: (vide)")
                self.log_message("  7: categorie_poste")
                self.log_message("  8: diplome")
                self.log_message("  9: ecole\n")
                
                reader = csv.reader(csvfile)
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Mapper les colonnes par position
                        if len(row) < 6:
                            self.log_message(f"⚠️  Ligne {row_num}: Nombre de colonnes insuffisant")
                            self.skipped += 1
                            continue
                        
                        # Extraire les données du contrat
                        contrat_id = row[0].strip() if len(row) > 0 else ''
                        poste_nom = row[1].strip() if len(row) > 1 else ''
                        date_debut_str = row[2].strip() if len(row) > 2 else ''
                        date_fin_str = row[3].strip() if len(row) > 3 else ''
                        type_personne_csv = row[4].strip() if len(row) > 4 else ''
                        fic_personne_id = row[5].strip() if len(row) > 5 else ''
                        autre = row[6].strip() if len(row) > 6 else ''
                        categorie_poste = row[7].strip() if len(row) > 7 else ''
                        diplome_csv = row[8].strip() if len(row) > 8 else ''
                        ecole_csv = row[9].strip() if len(row) > 9 else ''
                        
                        # Vérifier les champs obligatoires
                        if not contrat_id or not fic_personne_id:
                            self.log_message(f"⚠️  Ligne {row_num}: Champs obligatoires manquants")
                            self.skipped += 1
                            continue
                        
                        # Récupérer les données enrichies de fic_personne
                        fic_data = self.fic_personne_data.get(fic_personne_id, {})
                        # Prioriser les données de fic_personne sur celles du CSV contrat
                        diplome = fic_data.get('diplome') or diplome_csv
                        type_personne = fic_data.get('type_personne') or type_personne_csv
                        # Utiliser ecole du fichier contrat uniquement
                        ecole = ecole_csv if ecole_csv else None
                        
                        # Parser les dates
                        date_debut = None
                        if date_debut_str:
                            try:
                                date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date()
                            except:
                                pass
                        
                        date_fin = None
                        if date_fin_str:
                            try:
                                date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date()
                            except:
                                pass
                        
                        # Utiliser des valeurs par défaut
                        if not poste_nom:
                            poste_nom = "Non spécifié"
                        
                        # Insérer dans la nouvelle table
                        cursor.execute("""
                            INSERT INTO contrat (
                                id, fic_personne_id, poste_nom, categorie_poste,
                                diplome, type_personne, ecole, date_debut, date_fin, autre
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                fic_personne_id = EXCLUDED.fic_personne_id,
                                poste_nom = EXCLUDED.poste_nom,
                                categorie_poste = EXCLUDED.categorie_poste,
                                diplome = EXCLUDED.diplome,
                                type_personne = EXCLUDED.type_personne,
                                ecole = EXCLUDED.ecole,
                                date_debut = EXCLUDED.date_debut,
                                date_fin = EXCLUDED.date_fin,
                                autre = EXCLUDED.autre
                        """, (
                            contrat_id,
                            fic_personne_id,
                            poste_nom,
                            categorie_poste if categorie_poste else None,
                            diplome if diplome else None,
                            type_personne if type_personne else None,
                            ecole if ecole else None,
                            date_debut,
                            date_fin,
                            autre if autre else None
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
        
        except Exception as e:
            self.log_message(f"❌ Erreur d'exécution: {str(e)}")
            messagebox.showerror("Erreur", f"Erreur: {str(e)}")
            self.progress_bar.stop()
            self.migrate_btn.configure(state="normal")

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    app = ContratEnrichiMigrationGUI(root)
    root.mainloop()
