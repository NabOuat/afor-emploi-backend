#!/usr/bin/env python
"""
Interface graphique CustomTkinter pour importer les données fic_personne
Avec une meilleure apparence et des boutons bien distincts
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
from dotenv import load_dotenv
from import_service import FicPersonneImporter

load_dotenv()

# Configurer le thème
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class FicPersonneImporterGUI:
    """Interface graphique pour l'import de fic_personne avec CustomTkinter"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Import Fic Personne - AFOR")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)
        
        # Variables
        self.csv_file_path = ctk.StringVar()
        self.import_thread = None
        self.is_importing = False
        
        # Créer l'interface
        self.create_widgets()
    
    def create_widgets(self):
        """Créer les widgets de l'interface"""
        
        # Frame principal
        main_frame = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=15, pady=15)
        
        # === TITRE ===
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔄 IMPORT DE DONNÉES - FIC PERSONNE",
            font=("Arial", 18, "bold"),
            text_color="#00FF00"
        )
        title_label.pack(pady=(0, 20))
        
        # === SECTION 1: SÉLECTION FICHIER ===
        file_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="#1a1a1a")
        file_frame.pack(fill=ctk.X, pady=10)
        
        file_label = ctk.CTkLabel(
            file_frame,
            text="📁 Sélection du fichier CSV",
            font=("Arial", 12, "bold"),
            text_color="#00BFFF"
        )
        file_label.pack(anchor=ctk.W, padx=15, pady=(10, 5))
        
        file_input_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        file_input_frame.pack(fill=ctk.X, padx=15, pady=(5, 10))
        
        file_entry = ctk.CTkEntry(
            file_input_frame,
            textvariable=self.csv_file_path,
            placeholder_text="Aucun fichier sélectionné",
            height=35,
            font=("Arial", 10)
        )
        file_entry.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=(0, 10))
        
        browse_btn = ctk.CTkButton(
            file_input_frame,
            text="📂 Parcourir",
            command=self.browse_file,
            width=120,
            height=35,
            font=("Arial", 11, "bold"),
            fg_color="#FF6B6B",
            hover_color="#FF5252"
        )
        browse_btn.pack(side=ctk.LEFT)
        
        # === SECTION 2: INFORMATIONS FICHIER ===
        info_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="#1a1a1a")
        info_frame.pack(fill=ctk.X, pady=10)
        
        info_label = ctk.CTkLabel(
            info_frame,
            text="ℹ️  Informations du fichier",
            font=("Arial", 12, "bold"),
            text_color="#00BFFF"
        )
        info_label.pack(anchor=ctk.W, padx=15, pady=(10, 10))
        
        # Chemin
        path_title = ctk.CTkLabel(info_frame, text="Chemin:", font=("Arial", 10, "bold"))
        path_title.pack(anchor=ctk.W, padx=25)
        self.path_label = ctk.CTkLabel(
            info_frame,
            text="Aucun fichier sélectionné",
            font=("Arial", 10),
            text_color="#CCCCCC"
        )
        self.path_label.pack(anchor=ctk.W, padx=40, pady=(0, 5))
        
        # Taille
        size_title = ctk.CTkLabel(info_frame, text="Taille:", font=("Arial", 10, "bold"))
        size_title.pack(anchor=ctk.W, padx=25, pady=(5, 0))
        self.size_label = ctk.CTkLabel(
            info_frame,
            text="--",
            font=("Arial", 10),
            text_color="#CCCCCC"
        )
        self.size_label.pack(anchor=ctk.W, padx=40, pady=(0, 5))
        
        # Statut
        status_title = ctk.CTkLabel(info_frame, text="Statut:", font=("Arial", 10, "bold"))
        status_title.pack(anchor=ctk.W, padx=25, pady=(5, 0))
        self.status_label = ctk.CTkLabel(
            info_frame,
            text="✓ Prêt",
            font=("Arial", 10, "bold"),
            text_color="#00FF00"
        )
        self.status_label.pack(anchor=ctk.W, padx=40, pady=(0, 10))
        
        # === SECTION 3: BASE DE DONNÉES ===
        db_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="#1a1a1a")
        db_frame.pack(fill=ctk.X, pady=10)
        
        db_label = ctk.CTkLabel(
            db_frame,
            text="🔗 Connexion Base de Données",
            font=("Arial", 12, "bold"),
            text_color="#00BFFF"
        )
        db_label.pack(anchor=ctk.W, padx=15, pady=(10, 10))
        
        db_url = os.getenv('DATABASE_URL', 'Non configurée')
        db_display = db_url.split('@')[1] if '@' in db_url else db_url
        self.db_label = ctk.CTkLabel(
            db_frame,
            text=db_display,
            font=("Arial", 10),
            text_color="#00FF00"
        )
        self.db_label.pack(anchor=ctk.W, padx=25, pady=(0, 10))
        
        # === SECTION 4: PROGRESSION ===
        progress_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="#1a1a1a")
        progress_frame.pack(fill=ctk.X, pady=10)
        
        progress_label = ctk.CTkLabel(
            progress_frame,
            text="⏳ Progression",
            font=("Arial", 12, "bold"),
            text_color="#00BFFF"
        )
        progress_label.pack(anchor=ctk.W, padx=15, pady=(10, 10))
        
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=20,
            corner_radius=5
        )
        self.progress_bar.pack(fill=ctk.X, padx=15, pady=(0, 10))
        self.progress_bar.set(0)
        
        self.progress_text = ctk.CTkLabel(
            progress_frame,
            text="En attente...",
            font=("Arial", 10),
            text_color="#CCCCCC"
        )
        self.progress_text.pack(anchor=ctk.W, padx=15, pady=(0, 10))
        
        # === SECTION 5: RÉSULTATS ===
        result_frame = ctk.CTkFrame(main_frame, corner_radius=10, fg_color="#1a1a1a")
        result_frame.pack(fill=ctk.BOTH, expand=True, pady=10)
        
        result_label = ctk.CTkLabel(
            result_frame,
            text="📊 Résultats",
            font=("Arial", 12, "bold"),
            text_color="#00BFFF"
        )
        result_label.pack(anchor=ctk.W, padx=15, pady=(10, 10))
        
        self.result_text = ctk.CTkTextbox(
            result_frame,
            height=150,
            font=("Courier", 10),
            text_color="#CCCCCC",
            fg_color="#0a0a0a"
        )
        self.result_text.pack(fill=ctk.BOTH, expand=True, padx=15, pady=(0, 10))
        
        # === SECTION 6: BOUTONS D'ACTION ===
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill=ctk.X, pady=(10, 0))
        
        # Bouton Commencer l'envoi (VERT - Principal)
        self.import_btn = ctk.CTkButton(
            button_frame,
            text="▶ COMMENCER L'ENVOI DES DONNÉES",
            command=self.start_import,
            height=45,
            font=("Arial", 12, "bold"),
            fg_color="#00FF00",
            hover_color="#00DD00",
            text_color="#000000",
            corner_radius=8
        )
        self.import_btn.pack(side=ctk.LEFT, padx=(0, 10), fill=ctk.X, expand=True)
        
        # Bouton Arrêter (ROUGE)
        self.cancel_btn = ctk.CTkButton(
            button_frame,
            text="⏹ ARRÊTER L'ENVOI",
            command=self.cancel_import,
            height=45,
            font=("Arial", 11, "bold"),
            fg_color="#FF6B6B",
            hover_color="#FF5252",
            text_color="#FFFFFF",
            corner_radius=8,
            state="disabled"
        )
        self.cancel_btn.pack(side=ctk.LEFT, padx=(0, 10), fill=ctk.X, expand=True)
        
        # Bouton Effacer (ORANGE)
        clear_btn = ctk.CTkButton(
            button_frame,
            text="🗑 EFFACER",
            command=self.clear_results,
            height=45,
            font=("Arial", 11, "bold"),
            fg_color="#FFA500",
            hover_color="#FF8C00",
            text_color="#000000",
            corner_radius=8
        )
        clear_btn.pack(side=ctk.LEFT, padx=(0, 10), fill=ctk.X, expand=True)
        
        # Bouton Quitter (GRIS)
        exit_btn = ctk.CTkButton(
            button_frame,
            text="❌ QUITTER",
            command=self.root.quit,
            height=45,
            font=("Arial", 11, "bold"),
            fg_color="#555555",
            hover_color="#333333",
            text_color="#FFFFFF",
            corner_radius=8
        )
        exit_btn.pack(side=ctk.RIGHT, fill=ctk.X, expand=True)
    
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
            self.path_label.configure(text=file_path, text_color="#00FF00")
            
            # Taille
            size_bytes = os.path.getsize(file_path)
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.2f} KB"
            else:
                size_str = f"{size_bytes / 1024 / 1024:.2f} MB"
            self.size_label.configure(text=size_str, text_color="#00FF00")
            
            # Statut
            self.status_label.configure(text="✓ Fichier valide", text_color="#00FF00")
        else:
            self.path_label.configure(text="Fichier non trouvé", text_color="#FF6B6B")
            self.size_label.configure(text="--", text_color="#FF6B6B")
            self.status_label.configure(text="✗ Fichier invalide", text_color="#FF6B6B")
    
    def start_import(self):
        """Démarrer l'import dans un thread séparé"""
        csv_file = self.csv_file_path.get()
        
        if not csv_file or not os.path.exists(csv_file):
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier valide")
            return
        
        # Désactiver les boutons
        self.import_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.is_importing = True
        
        # Réinitialiser la barre de progression
        self.progress_bar.set(0)
        self.progress_text.configure(text="Import en cours...", text_color="#00BFFF")
        
        # Lancer l'import dans un thread
        self.import_thread = threading.Thread(target=self.import_worker, args=(csv_file,))
        self.import_thread.daemon = True
        self.import_thread.start()
    
    def import_worker(self, csv_file):
        """Worker pour l'import (exécuté dans un thread)"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                self.append_result("❌ DATABASE_URL non définie dans .env\n")
                return
            
            self.append_result(f"📂 Fichier source: {csv_file}\n")
            self.append_result(f"🔗 Connexion à la base de données...\n")
            
            importer = FicPersonneImporter(database_url)
            success = importer.import_from_csv(csv_file)
            
            # Afficher les résultats
            self.append_result("\n" + "="*60 + "\n")
            self.append_result("RÉSUMÉ DE L'IMPORT\n")
            self.append_result("="*60 + "\n")
            self.append_result(f"✓ Enregistrements insérés: {importer.inserted}\n")
            self.append_result(f"⚠️  Enregistrements ignorés: {importer.skipped}\n")
            self.append_result(f"❌ Erreurs: {importer.errors}\n")
            self.append_result("="*60 + "\n")
            
            if success:
                self.append_result("\n✅ IMPORT TERMINÉ AVEC SUCCÈS!\n")
                self.progress_text.configure(text="✅ Import réussi!", text_color="#00FF00")
                self.progress_bar.set(1.0)
                messagebox.showinfo(
                    "Succès",
                    f"Import terminé avec succès!\n\n"
                    f"Insérés: {importer.inserted}\n"
                    f"Ignorés: {importer.skipped}\n"
                    f"Erreurs: {importer.errors}"
                )
            else:
                self.append_result("\n❌ L'IMPORT A RENCONTRÉ DES ERREURS\n")
                self.progress_text.configure(text="❌ Import échoué", text_color="#FF6B6B")
                messagebox.showerror("Erreur", "L'import a rencontré des erreurs. Consultez les résultats.")
        
        except Exception as e:
            self.append_result(f"\n❌ Erreur: {str(e)}\n")
            self.progress_text.configure(text="❌ Erreur", text_color="#FF6B6B")
            messagebox.showerror("Erreur", f"Une erreur s'est produite:\n{str(e)}")
        
        finally:
            # Réactiver les boutons
            self.import_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
            self.is_importing = False
    
    def append_result(self, text):
        """Ajouter du texte à la zone de résultats"""
        self.result_text.insert("end", text)
        self.result_text.see("end")
        self.root.update()
    
    def clear_results(self):
        """Effacer les résultats"""
        self.result_text.delete("1.0", "end")
        self.progress_text.configure(text="En attente...", text_color="#CCCCCC")
        self.progress_bar.set(0)
    
    def cancel_import(self):
        """Annuler l'import"""
        if self.is_importing:
            messagebox.showinfo("Info", "L'annulation n'est pas encore implémentée.\nAttendez la fin de l'import.")

def main():
    """Fonction principale"""
    root = ctk.CTk()
    app = FicPersonneImporterGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
