#!/usr/bin/env python
"""
Interface graphique Tkinter pour importer les données fic_personne
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
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        self.root.minsize(600, 500)
        
        # Variables
        self.csv_file_path = tk.StringVar()
        self.import_thread = None
        self.is_importing = False
        
        # Créer l'interface
        self.create_widgets()
        self.center_window()
    
    def center_window(self):
        """Centrer la fenêtre sur l'écran"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Créer les widgets de l'interface"""
        
        # Configurer les poids des lignes et colonnes
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Frame principal avec scrollbar
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.grid_rowconfigure(5, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Titre
        title_label = ttk.Label(
            main_frame, 
            text="Import de Données - Fic Personne",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Section sélection fichier
        file_frame = ttk.LabelFrame(main_frame, text="Sélection du fichier CSV", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(file_frame, text="Fichier:").grid(row=0, column=0, sticky=tk.W)
        
        file_entry = ttk.Entry(
            file_frame, 
            textvariable=self.csv_file_path,
            width=50,
            state='readonly'
        )
        file_entry.grid(row=0, column=1, padx=(10, 10), sticky=(tk.W, tk.E))
        
        browse_btn = ttk.Button(
            file_frame,
            text="Parcourir...",
            command=self.browse_file
        )
        browse_btn.grid(row=0, column=2, padx=(0, 0))
        
        # Section informations fichier
        info_frame = ttk.LabelFrame(main_frame, text="Informations du fichier", padding="10")
        info_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(info_frame, text="Chemin:").grid(row=0, column=0, sticky=tk.W)
        self.path_label = ttk.Label(info_frame, text="Aucun fichier sélectionné", foreground="gray")
        self.path_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(info_frame, text="Taille:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.size_label = ttk.Label(info_frame, text="--", foreground="gray")
        self.size_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        ttk.Label(info_frame, text="Statut:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.status_label = ttk.Label(info_frame, text="Prêt", foreground="green")
        self.status_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        # Section base de données
        db_frame = ttk.LabelFrame(main_frame, text="Connexion Base de Données", padding="10")
        db_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(db_frame, text="Base de données:").grid(row=0, column=0, sticky=tk.W)
        db_url = os.getenv('DATABASE_URL', 'Non configurée')
        db_display = db_url.split('@')[1] if '@' in db_url else db_url
        self.db_label = ttk.Label(db_frame, text=db_display, foreground="blue")
        self.db_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # Section progression
        progress_frame = ttk.LabelFrame(main_frame, text="Progression", padding="10")
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='indeterminate'
        )
        self.progress_bar.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.progress_label = ttk.Label(progress_frame, text="En attente...", foreground="gray")
        self.progress_label.grid(row=1, column=0, columnspan=3, sticky=tk.W)
        
        # Section résultats
        result_frame = ttk.LabelFrame(main_frame, text="Résultats", padding="10")
        result_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Text widget pour les résultats
        self.result_text = tk.Text(
            result_frame,
            height=8,
            width=60,
            wrap=tk.WORD,
            state='disabled'
        )
        self.result_text.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        scrollbar.grid(row=0, column=3, sticky=(tk.N, tk.S))
        self.result_text.config(yscrollcommand=scrollbar.set)
        
        # Boutons d'action
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.import_btn = ttk.Button(
            button_frame,
            text="Démarrer l'import",
            command=self.start_import,
            state='normal'
        )
        self.import_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.cancel_btn = ttk.Button(
            button_frame,
            text="Annuler",
            command=self.cancel_import,
            state='disabled'
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = ttk.Button(
            button_frame,
            text="Effacer les résultats",
            command=self.clear_results
        )
        clear_btn.pack(side=tk.LEFT)
        
        exit_btn = ttk.Button(
            button_frame,
            text="Quitter",
            command=self.root.quit
        )
        exit_btn.pack(side=tk.RIGHT)
    
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
            self.status_label.config(text="Fichier valide", foreground="green")
        else:
            self.path_label.config(text="Fichier non trouvé", foreground="red")
            self.size_label.config(text="--", foreground="gray")
            self.status_label.config(text="Fichier invalide", foreground="red")
            self.import_btn.config(state='disabled')
    
    def start_import(self):
        """Démarrer l'import dans un thread séparé"""
        csv_file = self.csv_file_path.get()
        
        if not csv_file or not os.path.exists(csv_file):
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier valide")
            return
        
        # Désactiver les boutons
        self.import_btn.config(state='disabled')
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
    
    def run(self):
        """Lancer l'interface"""
        # Configurer les tags de texte
        self.result_text.tag_config("info", foreground="black")
        self.result_text.tag_config("success", foreground="green")
        self.result_text.tag_config("warning", foreground="orange")
        self.result_text.tag_config("error", foreground="red")
        
        self.root.mainloop()

def main():
    """Fonction principale"""
    root = tk.Tk()
    app = FicPersonneImporterGUI(root)
    app.run()

if __name__ == '__main__':
    main()
