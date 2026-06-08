from flask import Flask, jsonify, request
from config import config
from import_service import FicPersonneImporter
from db import Database
import os
from dotenv import load_dotenv

load_dotenv()

def create_app(config_name=None):
    """Factory function pour créer l'application Flask"""
    
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Enregistrer les routes
    register_routes(app)
    
    return app

def register_routes(app):
    """Enregistrer les routes de l'application"""
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Vérifier la santé de l'application"""
        db = Database()
        if db.connect():
            db.disconnect()
            return jsonify({
                'status': 'healthy',
                'message': 'Application et base de données sont opérationnelles'
            }), 200
        else:
            return jsonify({
                'status': 'unhealthy',
                'message': 'Impossible de se connecter à la base de données'
            }), 500
    
    @app.route('/api/import/fic-personne', methods=['POST'])
    def import_fic_personne():
        """
        Importer les données fic_personne depuis un CSV
        
        Body JSON:
        {
            "csv_file_path": "/chemin/vers/fic_personne.txt"
        }
        """
        try:
            data = request.get_json()
            csv_file_path = data.get('csv_file_path')
            
            if not csv_file_path:
                return jsonify({
                    'status': 'error',
                    'message': 'Le chemin du fichier CSV est requis'
                }), 400
            
            if not os.path.exists(csv_file_path):
                return jsonify({
                    'status': 'error',
                    'message': f'Fichier non trouvé: {csv_file_path}'
                }), 404
            
            # Créer l'importeur et lancer l'import
            importer = FicPersonneImporter(app.config['DATABASE_URL'])
            success = importer.import_from_csv(csv_file_path)
            
            summary = importer.print_summary()
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': 'Import terminé avec succès',
                    'summary': summary
                }), 200
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Erreur lors de l\'import',
                    'summary': summary
                }), 500
        
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Erreur serveur: {str(e)}'
            }), 500
    
    @app.route('/api/stats/fic-personne', methods=['GET'])
    def get_fic_personne_stats():
        """Récupérer les statistiques de la table fic_personne"""
        try:
            db = Database(app.config['DATABASE_URL'])
            if not db.connect():
                return jsonify({
                    'status': 'error',
                    'message': 'Impossible de se connecter à la base de données'
                }), 500
            
            count = db.count_fic_personne()
            db.disconnect()
            
            return jsonify({
                'status': 'success',
                'table': 'fic_personne',
                'total_records': count
            }), 200
        
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Erreur: {str(e)}'
            }), 500
    
    @app.route('/api/verify/acteurs', methods=['GET'])
    def verify_acteurs():
        """Vérifier les acteurs disponibles"""
        try:
            db = Database(app.config['DATABASE_URL'])
            if not db.connect():
                return jsonify({
                    'status': 'error',
                    'message': 'Impossible de se connecter à la base de données'
                }), 500
            
            acteurs = db.fetch_all("SELECT id, nom, type_acteur FROM acteur LIMIT 20")
            db.disconnect()
            
            return jsonify({
                'status': 'success',
                'acteurs': [
                    {'id': a[0], 'nom': a[1], 'type': a[2]} for a in acteurs
                ]
            }), 200
        
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Erreur: {str(e)}'
            }), 500
    
    @app.route('/api/verify/projets', methods=['GET'])
    def verify_projets():
        """Vérifier les projets disponibles"""
        try:
            db = Database(app.config['DATABASE_URL'])
            if not db.connect():
                return jsonify({
                    'status': 'error',
                    'message': 'Impossible de se connecter à la base de données'
                }), 500
            
            projets = db.fetch_all("SELECT id, nom FROM projet LIMIT 20")
            db.disconnect()
            
            return jsonify({
                'status': 'success',
                'projets': [
                    {'id': p[0], 'nom': p[1]} for p in projets
                ]
            }), 200
        
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Erreur: {str(e)}'
            }), 500
    
    @app.errorhandler(404)
    def not_found(error):
        """Gérer les erreurs 404"""
        return jsonify({
            'status': 'error',
            'message': 'Ressource non trouvée'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Gérer les erreurs 500"""
        return jsonify({
            'status': 'error',
            'message': 'Erreur serveur interne'
        }), 500
