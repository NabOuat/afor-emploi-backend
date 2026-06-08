#!/usr/bin/env python
"""
Interface graphique Tkinter pour importer les données fic_personne - Version 2
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
from dotenv import load_dotenv
from import_service import FicPersonneImporter

load_dotenv()

class FicPersonneImporterGUI:
    """Interface graphique pour l'import de fic_personne"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Import Fic Personne - AFOR")
        self.root.geometry("900x750")
        
        # Variables
        self.csv_file_path = tk.StringVar()
        self.import_thread = None
        self.is_importing = False
        
        # Créer l'interface
        self.create_widgets()
    
    def create_widgets(self):
        """Créer les widgets de l'interface"""
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # === TITRE ===
        title_label = ttk.Label(
            main_frame, 
            text="🔄 Import de Données - Fic Personne",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 15))
        
        # === SECTION 1: SÉLECTION FICHIER ===
        file_frame = ttk.LabelFrame(main_frame, text="📁 Sélection du fichier CSV", padding=10)
        file_frame.pack(fill=tk.X, pady=10)
        
        file_input_frame = ttk.Frame(file_frame)
        file_input_frame.pack(fill=tk.X)
        
        ttk.Label(file_input_frame, text="Fichier:").pack(side=tk.LEFT)
        
        file_entry = ttk.Entry(
            file_input_frame, 
            textvariable=self.csv_file_path,
            width=60,
            state='readonly'
        )
        file_entry.pack(side=tk.LEFT, padx=(10, 10), fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(
            file_input_frame,
            text="Parcourir...",
            command=self.browse_file,
            width=15
        )
        browse_btn.pack(side=tk.LEFT)
        
        # === SECTION 2: INFORMATIONS FICHIER ===
        info_frame = ttk.LabelFrame(main_frame, text="ℹ️  Informations du fichier", padding=10)
        info_frame.pack(fill=tk.X, pady=10)
        
        # Chemin
        ttk.Label(info_frame, text="Chemin:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        self.path_label = ttk.Label(info_frame, text="Aucun fichier sélectionné", foreground="gray")
        self.path_label.pack(anchor=tk.W, padx=(20, 0))
        
        # Taille
        ttk.Label(info_frame, text="Taille:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(5, 0))
        self.size_label = ttk.Label(info_frame, text="--", foreground="gray")
        self.size_label.pack(anchor=tk.W, padx=(20, 0))
        
        # Statut
        ttk.Label(info_frame, text="Statut:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(5, 0))
        self.status_label = ttk.Label(info_frame, text="Prêt", foreground="green")
        self.status_label.pack(anchor=tk.W, padx=(20, 0))
        
        # === SECTION 3: BASE DE DONNÉES ===
        db_frame = ttk.LabelFrame(main_frame, text="🔗 Connexion Base de Données", padding=10)
        db_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(db_frame, text="Base de données:", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        db_url = os.getenv('DATABASE_URL', 'Non configurée')
        db_display = db_url.split('@')[1] if '@' in db_url else db_url
        self.db_label = ttk.Label(db_frame, text=db_display, foreground="blue")
        self.db_label.pack(anchor=tk.W, padx=(20, 0))
        
        # === SECTION 4: PROGRESSION ===
        progress_frame = ttk.LabelFrame(main_frame, text="⏳ Progression", padding=10)
        progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='indeterminate',
            length=400
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="En attente...", foreground="gray")
        self.progress_label.pack(anchor=tk.W)
        
        # === SECTION 5: RÉSULTATS ===
        result_frame = ttk.LabelFrame(main_frame, text="📊 Résultats", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Text widget pour les résultats
        self.result_text = tk.Text(
            result_frame,
            height=10,
            width=80,
            wrap=tk.WORD,
            state='disabled',
            font=("Courier", 9)
        )
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=scrollbar.set)
        
        # === SECTION 6: BOUTONS D'ACTION ===
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.import_btn = ttk.Button(
            button_frame,
            text="▶ Commencer l'envoi des données",
            command=self.start_import,
            width=25
        )
        self.import_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_btn = ttk.Button(
            button_frame,
            text="⏹ Arrêter l'envoi",
            command=self.cancel_import,
            state='disabled',
            width=20
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = ttk.Button(
            button_frame,
            text="🗑 Effacer les résultats",
            command=self.clear_results,
            width=20
        )
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        exit_btn = ttk.Button(
            button_frame,
            text="❌ Fermer l'application",
            command=self.root.quit,
            width=20
        )
        exit_btn.pack(side=tk.RIGHT)
        
        # Configurer les tags de texte
        self.result_text.tag_config("info", foreground="black")
        self.result_text.tag_config("success", foreground="green", font=("Courier", 9, "bold"))
        self.result_text.tag_config("warning", foreground="orange", font=("Courier", 9, "bold"))
        self.result_text.tag_config("error", foreground="red", font=("Courier", 9, "bold"))
    
    def browse_file(self):
        """Ouvrir le dialogue de sélection de fichier"""
        file_path = filedialog.askopenfilename(
            title="Sélectionner le fichier CSV fic_personne",
            filetypes=[("Fichiers texte", "*.txt"), ("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
            initialdir=r"c:\Users\OUATTARA AFOR\Desktop\The Box\Web\Emploi\images"
        )
        
        if file_path:
            self.csv_file_path.set(file_path)
            self.update_file_info(file_path)
    
    def update_file_info(self, file_path):
        """Mettre à jour les informations du fichier"""
        if os.path.exists(file_path):
            # Chemin
            self.path_label.config(text=file_path, foreground="black")
            
            # Taille
            size_bytes = os.path.getsize(file_path)
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.2f} KB"
            else:
                size_str = f"{size_bytes / 1024 / 1024:.2f} MB"
            self.size_label.config(text=size_str, foreground="black")
            
            # Statut
            self.status_label.config(text="✓ Fichier valide", foreground="green")
        else:
            self.path_label.config(text="Fichier non trouvé", foreground="red")
            self.size_label.config(text="--", foreground="gray")
            self.status_label.config(text="✗ Fichier invalide", foreground="red")
    
    def start_import(self):
        """Démarrer l'import dans un thread séparé"""
        csv_file = self.csv_file_path.get()
        
        if not csv_file or not os.path.exists(csv_file):
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier valide")
            return
        
        # Désactiver les boutons
        self.import_btn.config(state='disabled')
        self.cancel_btn.config(state='normal')
        self.is_importing = True
        
        # Démarrer la progression
        self.progress_bar.start()
        self.progress_label.config(text="Import en cours...", foreground="blue")
        
        # Lancer l'import dans un thread
        self.import_thread = threading.Thread(target=self.import_worker, args=(csv_file,))
        self.import_thread.daemon = True
        self.import_thread.start()
    
    def import_worker(self, csv_file):
        """Worker pour l'import (exécuté dans un thread)"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                self.append_result("❌ DATABASE_URL non définie dans .env\n", "error")
                return
            
            self.append_result(f"📂 Fichier source: {csv_file}\n", "info")
            self.append_result(f"🔗 Connexion à la base de données...\n", "info")
            
            importer = FicPersonneImporter(database_url)
            success = importer.import_from_csv(csv_file)
            
            # Afficher les résultats
            self.append_result("\n" + "="*60 + "\n", "info")
            self.append_result("RÉSUMÉ DE L'IMPORT\n", "info")
            self.append_result("="*60 + "\n", "info")
            self.append_result(f"✓ Enregistrements insérés: {importer.inserted}\n", "success")
            self.append_result(f"⚠️  Enregistrements ignorés: {importer.skipped}\n", "warning")
            self.append_result(f"❌ Erreurs: {importer.errors}\n", "error" if importer.errors > 0 else "info")
            self.append_result("="*60 + "\n", "info")
            
            if success:
                self.append_result("\n✅ Import terminé avec succès!\n", "success")
                messagebox.showinfo("Succès", f"Import terminé!\n\nInsérés: {importer.inserted}\nIgnorés: {importer.skipped}\nErreurs: {importer.errors}")
            else:
                self.append_result("\n❌ L'import a rencontré des erreurs\n", "error")
                messagebox.showerror("Erreur", "L'import a rencontré des erreurs. Consultez les résultats.")
        
        except Exception as e:
            self.append_result(f"\n❌ Erreur: {str(e)}\n", "error")
            messagebox.showerror("Erreur", f"Une erreur s'est produite:\n{str(e)}")
        
        finally:
            # Arrêter la progression
            self.progress_bar.stop()
            self.progress_label.config(text="Import terminé", foreground="green")
            self.import_btn.config(state='normal')
            self.cancel_btn.config(state='disabled')
            self.is_importing = False
    
    def append_result(self, text, tag="info"):
        """Ajouter du texte à la zone de résultats"""
        self.result_text.config(state='normal')
        self.result_text.insert(tk.END, text, tag)
        self.result_text.see(tk.END)
        self.result_text.config(state='disabled')
        self.root.update()
    
    def clear_results(self):
        """Effacer les résultats"""
        self.result_text.config(state='normal')
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state='disabled')
        self.progress_label.config(text="En attente...", foreground="gray")
    
    def cancel_import(self):
        """Annuler l'import"""
        if self.is_importing:
            messagebox.showinfo("Info", "L'annulation n'est pas encore implémentée.\nAttendez la fin de l'import.")

def main():
    """Fonction principale"""
    root = tk.Tk()
    app = FicPersonneImporterGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
