#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application GUI pour gérer les engagements et les relier aux projets
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import json
from typing import List, Dict, Optional
import uuid

class EngagementManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestionnaire d'Engagements")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # Configuration de l'API
        self.api_url = "http://localhost:8000/api"
        
        # Données
        self.engagements: List[Dict] = []
        self.projets: List[Dict] = []
        self.projet_engagements: List[Dict] = []
        
        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Créer l'interface
        self.create_widgets()
        self.load_data()
        
    def create_widgets(self):
        """Créer les widgets de l'interface"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Titre
        title_label = ttk.Label(main_frame, text="Gestionnaire d'Engagements", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # ===== SECTION ENGAGEMENTS =====
        engagement_frame = ttk.LabelFrame(main_frame, text="Engagements", padding="10")
        engagement_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Boutons d'action
        button_frame = ttk.Frame(engagement_frame)
        button_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(button_frame, text="➕ Créer Engagement", command=self.create_engagement).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Supprimer", command=self.delete_engagement).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Rafraîchir", command=self.load_data).pack(side=tk.LEFT, padx=5)
        
        # Tableau des engagements
        columns = ("Nom", "Description")
        self.engagement_tree = ttk.Treeview(engagement_frame, columns=columns, height=10)
        self.engagement_tree.column("#0", width=0, stretch=tk.NO)
        self.engagement_tree.column("Nom", anchor=tk.W, width=150)
        self.engagement_tree.column("Description", anchor=tk.W, width=250)
        
        self.engagement_tree.heading("#0", text="", anchor=tk.W)
        self.engagement_tree.heading("Nom", text="Nom", anchor=tk.W)
        self.engagement_tree.heading("Description", text="Description", anchor=tk.W)
        
        self.engagement_tree.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(engagement_frame, orient=tk.VERTICAL, command=self.engagement_tree.yview)
        scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S))
        self.engagement_tree.configure(yscroll=scrollbar.set)
        
        # ===== SECTION LIAISON ENGAGEMENT-PROJET =====
        liaison_frame = ttk.LabelFrame(main_frame, text="Lier Engagement à Projet(s)", padding="10")
        liaison_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Sélection engagement
        ttk.Label(liaison_frame, text="Engagement:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.engagement_var = tk.StringVar()
        self.engagement_combo = ttk.Combobox(liaison_frame, textvariable=self.engagement_var, state="readonly", width=25)
        self.engagement_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        self.engagement_combo.bind("<<ComboboxSelected>>", self.on_engagement_selected)
        
        # Sélection projets
        ttk.Label(liaison_frame, text="Projets:").grid(row=1, column=0, sticky=(tk.W, tk.N), pady=5)
        
        # Listbox pour les projets
        self.projet_listbox = tk.Listbox(liaison_frame, height=8, selectmode=tk.MULTIPLE)
        self.projet_listbox.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Scrollbar pour les projets
        projet_scrollbar = ttk.Scrollbar(liaison_frame, orient=tk.VERTICAL, command=self.projet_listbox.yview)
        projet_scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S))
        self.projet_listbox.configure(yscroll=projet_scrollbar.set)
        
        # Boutons de liaison
        ttk.Button(liaison_frame, text="✅ Lier Projets", command=self.link_projects).grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # ===== SECTION LIAISONS EXISTANTES =====
        liaisons_frame = ttk.LabelFrame(main_frame, text="Liaisons Existantes", padding="10")
        liaisons_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Tableau des liaisons
        columns = ("Engagement", "Projet")
        self.liaisons_tree = ttk.Treeview(liaisons_frame, columns=columns, height=8)
        self.liaisons_tree.column("#0", width=0, stretch=tk.NO)
        self.liaisons_tree.column("Engagement", anchor=tk.W, width=200)
        self.liaisons_tree.column("Projet", anchor=tk.W, width=300)
        
        self.liaisons_tree.heading("#0", text="", anchor=tk.W)
        self.liaisons_tree.heading("Engagement", text="Engagement", anchor=tk.W)
        self.liaisons_tree.heading("Projet", text="Projet", anchor=tk.W)
        
        self.liaisons_tree.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        liaisons_scrollbar = ttk.Scrollbar(liaisons_frame, orient=tk.VERTICAL, command=self.liaisons_tree.yview)
        liaisons_scrollbar.grid(row=0, column=2, sticky=(tk.N, tk.S))
        self.liaisons_tree.configure(yscroll=liaisons_scrollbar.set)
        
        # Bouton supprimer liaison
        ttk.Button(liaisons_frame, text="🗑️ Supprimer Liaison", command=self.delete_liaison).grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Configurer les poids des lignes et colonnes
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
    def load_data(self):
        """Charger les données depuis l'API"""
        try:
            # Charger les engagements
            response = requests.get(f"{self.api_url}/engagements/")
            if response.status_code == 200:
                self.engagements = response.json()
            
            # Charger les projets
            response = requests.get(f"{self.api_url}/projets/")
            if response.status_code == 200:
                self.projets = response.json()
            
            # Charger les liaisons engagement-projet
            # On va les récupérer via une requête personnalisée ou les construire
            self.load_liaisons()
            
            self.refresh_ui()
            messagebox.showinfo("Succès", "Données chargées avec succès")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des données: {str(e)}")
    
    def load_liaisons(self):
        """Charger les liaisons engagement-projet"""
        try:
            # Récupérer toutes les liaisons
            response = requests.get(f"{self.api_url}/engagements/liaisons")
            if response.status_code == 200:
                self.projet_engagements = response.json()
            else:
                self.projet_engagements = []
        except Exception as e:
            print(f"Erreur lors du chargement des liaisons: {str(e)}")
            self.projet_engagements = []
    
    def refresh_ui(self):
        """Rafraîchir l'interface"""
        # Rafraîchir le tableau des engagements
        for item in self.engagement_tree.get_children():
            self.engagement_tree.delete(item)
        
        for engagement in self.engagements:
            self.engagement_tree.insert("", tk.END, values=(engagement.get("nom", ""), engagement.get("description", "")))
        
        # Rafraîchir le combo des engagements
        engagement_names = [e.get("nom", "") for e in self.engagements]
        self.engagement_combo["values"] = engagement_names
        
        # Rafraîchir la listbox des projets
        self.projet_listbox.delete(0, tk.END)
        for projet in self.projets:
            self.projet_listbox.insert(tk.END, projet.get("nom", ""))
        
        # Rafraîchir le tableau des liaisons
        for item in self.liaisons_tree.get_children():
            self.liaisons_tree.delete(item)
        
        for liaison in self.projet_engagements:
            self.liaisons_tree.insert("", tk.END, values=(liaison.get("engagement_nom", ""), liaison.get("projet_nom", "")))
    
    def create_engagement(self):
        """Créer un nouvel engagement"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Créer Engagement")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Nom
        ttk.Label(dialog, text="Nom:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        nom_entry = ttk.Entry(dialog, width=30)
        nom_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        # Description
        ttk.Label(dialog, text="Description:").grid(row=1, column=0, sticky=(tk.W, tk.N), padx=10, pady=10)
        description_text = tk.Text(dialog, height=4, width=30)
        description_text.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=10)
        
        def save():
            nom = nom_entry.get().strip()
            description = description_text.get("1.0", tk.END).strip()
            
            if not nom:
                messagebox.showerror("Erreur", "Le nom est obligatoire")
                return
            
            try:
                # Créer l'engagement via l'API
                response = requests.post(
                    f"{self.api_url}/engagements/",
                    params={"nom": nom, "description": description}
                )
                
                if response.status_code in [200, 201]:
                    messagebox.showinfo("Succès", "Engagement créé avec succès")
                    dialog.destroy()
                    self.load_data()
                else:
                    error_msg = response.json().get('detail', 'Erreur inconnue') if response.text else 'Erreur inconnue'
                    messagebox.showerror("Erreur", f"Erreur: {error_msg}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la création: {str(e)}")
        
        ttk.Button(dialog, text="Créer", command=save).grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        dialog.columnconfigure(1, weight=1)
        dialog.rowconfigure(1, weight=1)
    
    def delete_engagement(self):
        """Supprimer un engagement sélectionné"""
        selection = self.engagement_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un engagement à supprimer")
            return
        
        item = selection[0]
        values = self.engagement_tree.item(item, "values")
        nom = values[0]
        
        if messagebox.askyesno("Confirmation", f"Supprimer l'engagement '{nom}'?"):
            try:
                # Trouver l'ID de l'engagement
                engagement = next((e for e in self.engagements if e.get("nom") == nom), None)
                if engagement:
                    response = requests.delete(f"{self.api_url}/engagements/{engagement['id']}")
                    if response.status_code == 200:
                        messagebox.showinfo("Succès", "Engagement supprimé")
                        self.load_data()
                    else:
                        messagebox.showerror("Erreur", "Erreur lors de la suppression")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur: {str(e)}")
    
    def on_engagement_selected(self, event):
        """Quand un engagement est sélectionné"""
        # On peut charger les projets liés à cet engagement
        pass
    
    def link_projects(self):
        """Lier l'engagement sélectionné aux projets sélectionnés"""
        engagement_nom = self.engagement_var.get()
        if not engagement_nom:
            messagebox.showwarning("Attention", "Sélectionnez un engagement")
            return
        
        selected_indices = self.projet_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Attention", "Sélectionnez au moins un projet")
            return
        
        try:
            # Trouver l'ID de l'engagement
            engagement = next((e for e in self.engagements if e.get("nom") == engagement_nom), None)
            if not engagement:
                messagebox.showerror("Erreur", "Engagement non trouvé")
                return
            
            engagement_id = engagement["id"]
            
            # Lier chaque projet sélectionné
            for index in selected_indices:
                projet_nom = self.projet_listbox.get(index)
                projet = next((p for p in self.projets if p.get("nom") == projet_nom), None)
                
                if projet:
                    response = requests.post(
                        f"{self.api_url}/engagements/link-project",
                        params={
                            "projet_id": projet["id"],
                            "engagement_id": engagement_id
                        }
                    )
                    
                    if response.status_code != 200:
                        messagebox.showerror("Erreur", f"Erreur lors de la liaison de {projet_nom}")
            
            messagebox.showinfo("Succès", "Liaisons créées avec succès")
            self.load_data()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur: {str(e)}")
    
    def delete_liaison(self):
        """Supprimer une liaison"""
        selection = self.liaisons_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez une liaison à supprimer")
            return
        
        item = selection[0]
        values = self.liaisons_tree.item(item, "values")
        engagement_nom = values[0]
        projet_nom = values[1]
        
        if messagebox.askyesno("Confirmation", f"Supprimer la liaison '{engagement_nom}' - '{projet_nom}'?"):
            try:
                # Trouver les IDs
                engagement = next((e for e in self.engagements if e.get("nom") == engagement_nom), None)
                projet = next((p for p in self.projets if p.get("nom") == projet_nom), None)
                
                if engagement and projet:
                    response = requests.delete(
                        f"{self.api_url}/engagements/unlink-project",
                        params={
                            "projet_id": projet["id"],
                            "engagement_id": engagement["id"]
                        }
                    )
                    
                    if response.status_code == 200:
                        messagebox.showinfo("Succès", "Liaison supprimée")
                        self.load_data()
                    else:
                        messagebox.showerror("Erreur", "Erreur lors de la suppression")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur: {str(e)}")


def main():
    root = tk.Tk()
    app = EngagementManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
