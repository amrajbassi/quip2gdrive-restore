from flask import Flask, render_template, request, jsonify, send_file
import os
from config import config
from models import db, QuipMigrationFile, QuipMigrationFolder, GoogleDriveFile, MigrationLog, QuipDocument
from datetime import datetime
import tempfile
import subprocess
import re
from bs4 import BeautifulSoup

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize database
    db.init_app(app)
    
    return app

app = create_app()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/google-drive-files')
def google_drive_files_page():
    return render_template('google_drive_files.html')

@app.route('/api/health')
def health_check():
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'healthy', 
        'message': 'Flask app is running',
        'database': db_status
    })

@app.route('/api/data', methods=['GET', 'POST'])
def handle_data():
    if request.method == 'GET':
        return jsonify({'message': 'GET request received', 'data': []})
    elif request.method == 'POST':
        data = request.get_json()
        return jsonify({'message': 'POST request received', 'data': data})

@app.route('/api/google-drive-files', methods=['GET'])
def get_google_drive_files():
    """Get all Google Drive files from database"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Get paginated results from quip_migration_files table
        # Only include files that have a google_drive_id
        query = QuipMigrationFile.query.filter(
            QuipMigrationFile.google_drive_id.isnot(None)
        ).order_by(QuipMigrationFile.quip_id)
        
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        files = pagination.items
        
        return jsonify({
            'status': 'success',
            'total_count': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
            'files': [
                {
                    'id': file.quip_migration_file_id,
                    'quip_document_id': file.quip_id,
                    'google_drive_file_id': file.google_drive_id,
                    'google_drive_file_name': file.obfuscated_name,
                    'google_drive_file_url': f"https://docs.google.com/document/d/{file.google_drive_id}/edit",
                    'document_type': file.document_type,
                    'author': file.author,
                    'when_quip_created': file.when_quip_created.isoformat() if file.when_quip_created else None,
                    'when_migration_completed': file.when_migration_completed.isoformat() if file.when_migration_completed else None
                }
                for file in files
            ]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get all Quip migration files from database"""
    try:
        # Get files and folders
        files = QuipMigrationFile.query.limit(100).all()
        folders = QuipMigrationFolder.query.limit(100).all()
        
        return jsonify({
            'status': 'success',
            'files_count': len(files),
            'folders_count': len(folders),
            'files': [
                {
                    'quip_migration_file_id': file.quip_migration_file_id,
                    'quip_id': file.quip_id,
                    'obfuscated_name': file.obfuscated_name,
                    'google_drive_id': file.google_drive_id,
                    'document_type': file.document_type,
                    'author': file.author,
                    'when_quip_created': file.when_quip_created.isoformat() if file.when_quip_created else None,
                    'when_migration_completed': file.when_migration_completed.isoformat() if file.when_migration_completed else None
                }
                for file in files
            ],
            'folders': [
                {
                    'quip_migration_folder_id': folder.quip_migration_folder_id,
                    'quip_id': folder.quip_id,
                    'obfuscated_name': folder.obfuscated_name,
                    'google_drive_id': folder.google_drive_id,
                    'parent_folder': folder.parent_folder,
                    'inherit_mode': folder.inherit_mode,
                    'member_count': len(folder.member_ids) if folder.member_ids else 0
                }
                for folder in folders
            ]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/documents/<document_id>', methods=['GET'])
def get_document(document_id):
    """Get a specific Quip document by quip_id"""
    try:
        # Search in both files and folders
        file = QuipMigrationFile.query.filter_by(quip_id=document_id).first()
        folder = QuipMigrationFolder.query.filter_by(quip_id=document_id).first()
        
        if file:
            return jsonify({
                'status': 'success',
                'type': 'file',
                'document': {
                    'quip_migration_file_id': file.quip_migration_file_id,
                    'quip_id': file.quip_id,
                    'obfuscated_name': file.obfuscated_name,
                    'google_drive_id': file.google_drive_id,
                    'document_type': file.document_type,
                    'author': file.author,
                    'html_content': file.html_content,
                    'when_quip_created': file.when_quip_created.isoformat() if file.when_quip_created else None,
                    'when_migration_completed': file.when_migration_completed.isoformat() if file.when_migration_completed else None
                }
            })
        elif folder:
            return jsonify({
                'status': 'success',
                'type': 'folder',
                'document': {
                    'quip_migration_folder_id': folder.quip_migration_folder_id,
                    'quip_id': folder.quip_id,
                    'obfuscated_name': folder.obfuscated_name,
                    'google_drive_id': folder.google_drive_id,
                    'document_type': folder.document_type,
                    'author': folder.author,
                    'html_content': folder.html_content,
                    'when_quip_created': folder.when_quip_created.isoformat() if folder.when_quip_created else None,
                    'when_migration_completed': folder.when_migration_completed.isoformat() if folder.when_migration_completed else None
                }
            })
        else:
            return jsonify({'status': 'error', 'message': 'Document not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_documents():
    """Search Quip documents by quip_id or Google Drive files by google_drive_file_id"""
    try:
        document_id = request.args.get('document_id', '').strip()
        search_type = request.args.get('search_type', 'quip').lower()  # 'quip' or 'google'
        
        if not document_id:
            return jsonify({
                'status': 'error',
                'message': 'document_id parameter is required'
            }), 400
        
        if search_type not in ['quip', 'google']:
            return jsonify({
                'status': 'error',
                'message': 'search_type must be either "quip" or "google"'
            }), 400
        
        if search_type == 'quip':
            # Search for Quip document in both files and folders
            quip_file = QuipMigrationFile.query.filter_by(quip_id=document_id).first()
            quip_folder = QuipMigrationFolder.query.filter_by(quip_id=document_id).first()
            
            if not quip_file and not quip_folder:
                return jsonify({
                    'status': 'error',
                    'message': f'Quip document with ID "{document_id}" not found'
                }), 404
            
            # Determine which document we found
            if quip_file:
                quip_document = quip_file
                document_type = 'file'
            else:
                quip_document = quip_folder
                document_type = 'folder'
            
            # Search for corresponding Google Drive file
            # Since Google Drive info is already in QuipMigrationFile, we don't need to look it up separately
            result = {
                'status': 'success',
                'search_type': 'quip',
                'document_type': document_type,
                'quip_document': {
                    'quip_id': quip_document.quip_id,
                    'obfuscated_name': quip_document.obfuscated_name,
                    'google_drive_id': quip_document.google_drive_id,
                    'document_type': quip_document.document_type,
                    'author': quip_document.author,
                    'when_quip_created': quip_document.when_quip_created.isoformat() if quip_document.when_quip_created else None,
                    'when_migration_completed': quip_document.when_migration_completed.isoformat() if quip_document.when_migration_completed else None
                },
                'google_drive_file': {
                    'id': quip_document.quip_migration_file_id if hasattr(quip_document, 'quip_migration_file_id') else quip_document.quip_migration_folder_id,
                    'google_drive_file_id': quip_document.google_drive_id,
                    'google_drive_file_name': quip_document.obfuscated_name,
                    'google_drive_file_url': f"https://docs.google.com/document/d/{quip_document.google_drive_id}/edit" if quip_document.google_drive_id else None,
                    'created_at': quip_document.when_quip_created.isoformat() if quip_document.when_quip_created else None
                } if quip_document.google_drive_id else None
            }
            
            return jsonify(result)
            
        else:  # search_type == 'google'
            # Search for Google Drive file by google_drive_id in quip_migration_files table
            quip_file = QuipMigrationFile.query.filter_by(google_drive_id=document_id).first()
            quip_folder = QuipMigrationFolder.query.filter_by(google_drive_id=document_id).first()
            
            if not quip_file and not quip_folder:
                return jsonify({
                    'status': 'error',
                    'message': f'Google Drive file with ID "{document_id}" not found'
                }), 404
            
            # Determine which document we found
            if quip_file:
                quip_document = quip_file
                document_type = 'file'
            else:
                quip_document = quip_folder
                document_type = 'folder'
            
            result = {
                'status': 'success',
                'search_type': 'google',
                'document_type': document_type,
                'google_drive_file': {
                    'id': quip_document.quip_migration_file_id if hasattr(quip_document, 'quip_migration_file_id') else quip_document.quip_migration_folder_id,
                    'google_drive_file_id': quip_document.google_drive_id,
                    'google_drive_file_name': quip_document.obfuscated_name,
                    'google_drive_file_url': f"https://docs.google.com/document/d/{quip_document.google_drive_id}/edit",
                    'created_at': quip_document.when_quip_created.isoformat() if quip_document.when_quip_created else None
                },
                'quip_document': {
                    'quip_id': quip_document.quip_id,
                    'obfuscated_name': quip_document.obfuscated_name,
                    'google_drive_id': quip_document.google_drive_id,
                    'document_type': quip_document.document_type if hasattr(quip_document, 'document_type') else 'folder',
                    'author': quip_document.author if hasattr(quip_document, 'author') else None,
                    'when_quip_created': quip_document.when_quip_created.isoformat() if quip_document.when_quip_created else None,
                    'when_migration_completed': quip_document.when_migration_completed.isoformat() if hasattr(quip_document, 'when_migration_completed') and quip_document.when_migration_completed else None
                }
            }
            
            return jsonify(result)
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/migration-logs', methods=['GET'])
def get_migration_logs():
    """Get migration logs"""
    try:
        logs = MigrationLog.query.order_by(MigrationLog.created_at.desc()).limit(100).all()
        return jsonify({
            'status': 'success',
            'count': len(logs),
            'logs': [
                {
                    'id': log.id,
                    'document_id': log.document_id,
                    'action': log.action,
                    'status': log.status,
                    'message': log.message,
                    'created_at': log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get migration statistics"""
    try:
        total_files = QuipMigrationFile.query.count()
        total_folders = QuipMigrationFolder.query.count()
        
        # Count migrated files (those with google_drive_id)
        migrated_files = QuipMigrationFile.query.filter(QuipMigrationFile.google_drive_id.isnot(None)).count()
        migrated_folders = QuipMigrationFolder.query.filter(QuipMigrationFolder.google_drive_id.isnot(None)).count()
        
        # Count pending files (those without google_drive_id)
        pending_files = QuipMigrationFile.query.filter(QuipMigrationFile.google_drive_id.is_(None)).count()
        pending_folders = QuipMigrationFolder.query.filter(QuipMigrationFolder.google_drive_id.is_(None)).count()
        
        total_logs = MigrationLog.query.count()
        recent_logs = MigrationLog.query.filter(
            MigrationLog.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        return jsonify({
            'status': 'success',
            'statistics': {
                'documents': {
                    'total': total_files + total_folders,
                    'files': total_files,
                    'folders': total_folders,
                    'migrated': migrated_files + migrated_folders,
                    'pending': pending_files + pending_folders
                },
                'logs': {
                    'total': total_logs,
                    'today': recent_logs
                }
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/import-dump', methods=['POST'])
def import_dump():
    """Import the SQL dump file"""
    try:
        dump_file_path = 'quip-migration-db-dump.sql'
        
        if not os.path.exists(dump_file_path):
            return jsonify({
                'status': 'error', 
                'message': f'Dump file not found at {dump_file_path}. Please place the SQL dump file in the project root directory.'
            }), 404
        
        # Create a log entry for the import
        log = MigrationLog(
            document_id='SYSTEM',
            action='import_dump',
            status='pending',
            message=f'Starting import of {dump_file_path}'
        )
        db.session.add(log)
        db.session.commit()
        
        try:
            # Get database URL from config
            from config import config
            db_url = config['default'].SQLALCHEMY_DATABASE_URI
            
            # Extract connection details from database URL
            # Expected format: postgresql://username:password@host:port/database
            import urllib.parse
            parsed = urllib.parse.urlparse(db_url)
            
            # Build psql command
            psql_cmd = [
                'psql',
                '-h', parsed.hostname or 'localhost',
                '-p', str(parsed.port or 5432),
                '-U', parsed.username or os.getenv('USER', 'amraj'),  # Use current user if no username specified
                '-d', parsed.path[1:] if parsed.path else 'quip_migration',
                '-f', dump_file_path
            ]
            
            # Set password environment variable if provided
            env = os.environ.copy()
            if parsed.password:
                env['PGPASSWORD'] = parsed.password
            
            # Run the import command
            result = subprocess.run(
                psql_cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                # Update log entry to success
                log.status = 'completed'
                log.message = f'Successfully imported {dump_file_path}. Output: {result.stdout[-500:]}'  # Last 500 chars
                db.session.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': 'SQL dump imported successfully',
                    'log_id': log.id,
                    'file_size': os.path.getsize(dump_file_path),
                    'output': result.stdout[-1000:]  # Last 1000 chars of output
                })
            else:
                # Update log entry to failed
                log.status = 'failed'
                log.message = f'Import failed: {result.stderr}'
                db.session.commit()
                
                return jsonify({
                    'status': 'error',
                    'message': f'Import failed: {result.stderr}',
                    'log_id': log.id
                }), 500
                
        except subprocess.TimeoutExpired:
            log.status = 'failed'
            log.message = 'Import timed out after 5 minutes'
            db.session.commit()
            
            return jsonify({
                'status': 'error',
                'message': 'Import timed out after 5 minutes'
            }), 500
            
        except Exception as e:
            log.status = 'failed'
            log.message = f'Import error: {str(e)}'
            db.session.commit()
            
            return jsonify({
                'status': 'error',
                'message': f'Import error: {str(e)}'
            }), 500
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/restore-file', methods=['POST'])
def restore_file():
    """Restore a Quip document by converting HTML content to a downloadable format"""
    try:
        data = request.get_json()
        document_id = data.get('document_id', '').strip()
        output_format = data.get('format', 'docx')  # docx, pdf, html
        
        if not document_id:
            return jsonify({
                'status': 'error',
                'message': 'document_id parameter is required'
            }), 400
        
        # Search for the document in both files and folders
        quip_file = QuipMigrationFile.query.filter(
            (QuipMigrationFile.google_drive_id == document_id) |
            (QuipMigrationFile.quip_id == document_id)
        ).first()
        
        quip_folder = QuipMigrationFolder.query.filter(
            (QuipMigrationFolder.google_drive_id == document_id) |
            (QuipMigrationFolder.quip_id == document_id)
        ).first()
        
        if not quip_file and not quip_folder:
            return jsonify({
                'status': 'error',
                'message': f'Document with ID "{document_id}" not found'
            }), 404
        
        # Determine which document we found
        if quip_file:
            quip_document = quip_file
            document_type = 'file'
        else:
            quip_document = quip_folder
            document_type = 'folder'
        
        # Get HTML content
        html_content = quip_document.html_content
        if not html_content:
            return jsonify({
                'status': 'error',
                'message': 'No HTML content found for this document'
            }), 404
        
        # Clean and process HTML content
        cleaned_html = clean_quip_html(html_content)
        
        # Extract title
        title = extract_title_from_html(cleaned_html)
        if not title:
            title = quip_document.obfuscated_name or f"quip_document_{document_id}"
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as html_file:
            html_file.write(cleaned_html)
            html_file_path = html_file.name
        
        output_filename = f"{sanitize_filename(title)}.{output_format}"
        
        if output_format == 'html':
            # For HTML, just return the cleaned content
            return jsonify({
                'status': 'success',
                'filename': output_filename,
                'content': cleaned_html,
                'title': title,
                'document_type': document_type
            })
        
        elif output_format == 'docx':
            # Convert to DOCX using pandoc
            docx_path = convert_to_docx(html_file_path, output_filename)
            if docx_path:
                return send_file(
                    docx_path,
                    as_attachment=True,
                    download_name=output_filename,
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to convert document to DOCX format'
                }), 500
        
        elif output_format == 'pdf':
            # Convert to PDF using pandoc
            pdf_path = convert_to_pdf(html_file_path, output_filename)
            if pdf_path:
                return send_file(
                    pdf_path,
                    as_attachment=True,
                    download_name=output_filename,
                    mimetype='application/pdf'
                )
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to convert document to PDF format'
                }), 500
        
        else:
            return jsonify({
                'status': 'error',
                'message': f'Unsupported output format: {output_format}'
            }), 400
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def clean_quip_html(html_content):
    """Clean and process Quip HTML content"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style tags
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Remove Quip-specific classes and attributes
        for tag in soup.find_all(True):
            # Remove Quip-specific classes
            if tag.get('class'):
                tag['class'] = [cls for cls in tag['class'] if not cls.startswith('quip-')]
                if not tag['class']:
                    del tag['class']
            
            # Remove Quip-specific attributes
            quip_attrs = [attr for attr in tag.attrs.keys() if attr.startswith('data-quip-')]
            for attr in quip_attrs:
                del tag[attr]
        
        # Convert to string and clean up
        cleaned_html = str(soup)
        
        # Remove extra whitespace and normalize
        cleaned_html = re.sub(r'\s+', ' ', cleaned_html)
        cleaned_html = re.sub(r'>\s+<', '><', cleaned_html)
        
        return cleaned_html
        
    except Exception as e:
        # If BeautifulSoup fails, return original content
        return html_content

def extract_title_from_html(html_content):
    """Extract title from HTML content"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try to find h1 tag first
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        # Try to find title tag
        title = soup.find('title')
        if title:
            return title.get_text().strip()
        
        # Try to find any heading
        for i in range(1, 7):
            heading = soup.find(f'h{i}')
            if heading:
                return heading.get_text().strip()
        
        return None
        
    except Exception:
        return None

def sanitize_filename(filename):
    """Sanitize filename for safe file system usage"""
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove extra spaces and dots
    filename = re.sub(r'\s+', ' ', filename).strip()
    filename = filename.strip('.')
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    return filename

def convert_to_docx(html_file_path, output_filename):
    """Convert HTML to DOCX using pandoc"""
    try:
        output_path = os.path.join(tempfile.gettempdir(), output_filename)
        
        # Check if pandoc is available
        pandoc_check = subprocess.run(['which', 'pandoc'], capture_output=True, text=True)
        if pandoc_check.returncode != 0:
            raise Exception("Pandoc is not installed. Please install pandoc to convert documents.")
        
        # Run pandoc command
        result = subprocess.run([
            'pandoc',
            '-f', 'html',
            '-t', 'docx',
            '-o', output_path,
            html_file_path
        ], capture_output=True, text=True, timeout=60)  # 60 second timeout
        
        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
        else:
            error_msg = result.stderr if result.stderr else "Unknown pandoc error"
            raise Exception(f"Pandoc conversion failed: {error_msg}")
            
    except subprocess.TimeoutExpired:
        raise Exception("Document conversion timed out after 60 seconds")
    except FileNotFoundError:
        raise Exception("Pandoc is not installed. Please install pandoc to convert documents.")
    except Exception as e:
        raise Exception(f"Conversion error: {str(e)}")

def convert_to_pdf(html_file_path, output_filename):
    """Convert HTML to PDF using pandoc"""
    try:
        output_path = os.path.join(tempfile.gettempdir(), output_filename)
        
        # Check if pandoc is available
        pandoc_check = subprocess.run(['which', 'pandoc'], capture_output=True, text=True)
        if pandoc_check.returncode != 0:
            raise Exception("Pandoc is not installed. Please install pandoc to convert documents.")
        
        # Try pandoc with LaTeX for PDF conversion
        result = subprocess.run([
            'pandoc',
            '-f', 'html',
            '-t', 'pdf',
            '--pdf-engine=pdflatex',
            '-o', output_path,
            html_file_path
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
        else:
            error_msg = result.stderr if result.stderr else "Unknown conversion error"
            if "pdflatex not found" in error_msg:
                raise Exception(
                    "PDF conversion requires LaTeX. To enable PDF conversion, please install LaTeX:\n"
                    "1. Install MacTeX: brew install --cask mactex\n"
                    "2. Or use DOCX format instead, which doesn't require LaTeX\n"
                    "Error: " + error_msg
                )
            else:
                raise Exception(f"PDF conversion failed: {error_msg}")
            
    except subprocess.TimeoutExpired:
        raise Exception("Document conversion timed out after 60 seconds")
    except FileNotFoundError:
        raise Exception("Required conversion tools are not installed. Please install pandoc and LaTeX for PDF conversion.")
    except Exception as e:
        raise Exception(f"Conversion error: {str(e)}")

if __name__ == '__main__':
    with app.app_context():
        # Create all database tables
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0', port=5003) 